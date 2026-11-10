"""Run the catalogue maintenance checks over exported venue observations.

Every check in `scripts/maintenance/` is a pure function of the catalogue data and the
observation files (see `scripts/maintenance/observations.py` for their format); this
script reads both, runs the checks, applies `maintenance/exceptions.toml` and writes
the findings as JSON. Findings are data, not failures, so it exits 0 unless the
inputs are broken; `--strict` exits 1 on any finding and `--expect` on any
difference from a recorded result (CI runs the fixtures that way).

  PYTHONPATH=lib/src .venv/bin/python scripts/maintain.py \\
    --observations DIR [--data data] [--out findings.json] [--checks untranslated-market,...] \\
    [--extra hyperliquid.json ...]

Output: `{"catalogue_sha", "generated_at", "observations_as_of", "checks": {<name>:
{"status": "ran" | "skip", "reason", "found", "suppressed", "platforms"}},
"findings": [...], "suppressed": [...]}`. Fingerprints are catalogue-ops' own.
"""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys

from maintenance import catalogue, exceptions, generators, observations, runner


def catalogue_sha(data: Path) -> str | None:
  """The commit the data directory is checked out at, if it is in a Git repository."""
  try:
    out = subprocess.run(
      ['git', '-C', str(data), 'rev-parse', 'HEAD'], capture_output=True, text=True, check=True,
    )
  except (OSError, subprocess.CalledProcessError):
    return None
  return out.stdout.strip() or None


def expected_of(report: dict) -> dict:
  """The part of a report a fixture records: fingerprints with severity, and the suppressed ones."""
  return {
    'findings': {f['fingerprint']: f['severity'] for f in report['findings']},
    'suppressed': sorted(f['fingerprint'] for f in report['suppressed']),
    'skipped': sorted(name for name, check in report['checks'].items() if check['status'] == 'skip'),
  }


def differences(expected: dict, actual: dict) -> list[str]:
  """One line per difference between a recorded and a produced result."""
  lines = []
  for fp in sorted(expected['findings'].keys() | actual['findings'].keys()):
    want, got = expected['findings'].get(fp), actual['findings'].get(fp)
    if want != got:
      lines.append(f'{fp}: expected {want or "no finding"}, got {got or "no finding"}')
  for key in ('suppressed', 'skipped'):
    for fp in sorted(set(expected.get(key, [])) ^ set(actual[key])):
      lines.append(f'{key} {fp}: {"missing" if fp in expected.get(key, []) else "unexpected"}')
  return lines


def main(argv: list[str] | None = None) -> int:
  """CLI entry point."""
  parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
  parser.add_argument('--data', type=Path, default=Path('data'), help='Catalogue data directory.')
  parser.add_argument('--observations', type=Path, required=True, help='Directory of observation files.')
  parser.add_argument('--exceptions', type=Path, default=exceptions.FILE, help='Exceptions TOML file.')
  parser.add_argument('--out', type=Path, help='Write the report here (default: stdout).')
  parser.add_argument('--checks', action='append', help='Only these checks (comma-separated, repeatable).')
  parser.add_argument('--extra', type=Path, action='append', default=[],
                      help='Merge a generator report (--report-json of hyperliquid.py, gtrade.py, check_binance_spot_gaps.py).')
  parser.add_argument('--strict', action='store_true', help='Exit 1 when there is any finding.')
  parser.add_argument('--expect', type=Path, help='Exit 1 unless the result matches this recorded one.')
  parser.add_argument('--write-expect', action='store_true', help='Record the result into --expect instead.')
  args = parser.parse_args(argv)

  raw = []
  if args.exceptions.exists():
    import tomllib
    raw = tomllib.loads(args.exceptions.read_text(encoding='utf-8')).get('exception', [])
  problems = exceptions.errors(raw)
  if problems:
    for line in problems:
      print(f'{args.exceptions}: {line}', file=sys.stderr)
    return 2
  only = [name for value in args.checks for name in value.split(',') if name] if args.checks else None
  obs = observations.load(args.observations)
  extra = [generators.load(path) for path in args.extra]
  report = runner.run(catalogue.load(args.data), obs, exceptions.load(args.exceptions), only=only, extra=extra)
  out = {
    'catalogue_sha': catalogue_sha(args.data),
    'generated_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
    'observations_as_of': obs.get('listings_as_of') or (obs.get('prices') or {}).get('as_of'),
    **report,
  }
  text = json.dumps(out, indent=1, sort_keys=False, default=str) + '\n'
  if args.out:
    args.out.write_text(text)
  elif not args.expect:
    sys.stdout.write(text)

  ran = sum(1 for check in report['checks'].values() if check['status'] == 'ran')
  print(
    f'{len(report["findings"])} finding(s), {len(report["suppressed"])} suppressed; '
    f'{ran} of {len(report["checks"])} checks ran',
    file=sys.stderr,
  )
  if args.expect:
    actual = expected_of(report)
    if args.write_expect:
      args.expect.write_text(json.dumps(actual, indent=1, sort_keys=True) + '\n')
      return 0
    lines = differences(json.loads(args.expect.read_text()), actual)
    for line in lines:
      print(line, file=sys.stderr)
    return 1 if lines else 0
  return 1 if args.strict and report['findings'] else 0


if __name__ == '__main__':
  sys.exit(main())
