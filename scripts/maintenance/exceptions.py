"""Findings a person reviewed and judged intentional: `maintenance/exceptions.toml`.

An entry suppresses every finding whose fingerprint matches its `fingerprint`, a
case-sensitive shell-style glob (`fnmatchcase`). An `untranslated-asset` entry also
suppresses the untranslated markets whose venue base or quote is that asset, since
such a market can't be added before its asset is.

Each entry needs a `reason` and a `ref` (the issue or PR where it was decided). An
entry that no current finding matches stays valid only with `dormant = true`, so the
file can't silently collect dead rules.
"""

from fnmatch import fnmatchcase
from pathlib import Path
import re
import tomllib
from typing import Iterable, NotRequired, TypedDict

from .finding import CHECKS, Finding

FILE = Path(__file__).resolve().parents[2] / 'maintenance' / 'exceptions.toml'
KEYS = {'fingerprint', 'reason', 'ref', 'dormant'}
REF = re.compile(r'^(?:[\w.-]+/[\w.-]+)?#\d+$|^https://\S+$')
"""`#123`, `owner/repo#123` or a URL."""


class Exception_(TypedDict):
  """One reviewed, intentional finding pattern."""

  fingerprint: str
  """Fingerprint, or a shell-style glob over fingerprints."""
  reason: str
  ref: str
  dormant: NotRequired[bool]


def load(path: Path = FILE) -> list[Exception_]:
  """
  Read the `[[exception]]` entries of an exceptions file.

  Args:
    path: The TOML file; a missing file means no exceptions.
  """
  if not path.exists():
    return []
  raw = tomllib.loads(path.read_text(encoding='utf-8'))
  return [Exception_(**entry) for entry in raw.get('exception', [])]  # type: ignore[typeddict-item]


def errors(entries: Iterable[dict]) -> list[str]:
  """
  What is wrong with exception entries: unknown keys, missing reason or reference.

  Args:
    entries: The raw entries.
  """
  out = []
  for n, entry in enumerate(entries, 1):
    where = f'exception {n} ({entry.get("fingerprint", "?")})'
    unknown = set(entry) - KEYS
    if unknown:
      out.append(f'{where}: unknown keys {sorted(unknown)}')
    fp = entry.get('fingerprint')
    if not isinstance(fp, str) or fp.count(':') < 2:
      out.append(f'{where}: fingerprint must read <check>:<platform>:<subject>')
    elif not any(fnmatchcase(check, fp.split(':', 1)[0]) for check in CHECKS):
      out.append(f'{where}: matches no check')
    if not isinstance(entry.get('reason'), str) or not entry['reason'].strip():
      out.append(f'{where}: needs a reason')
    if not isinstance(entry.get('ref'), str) or not REF.match(entry['ref'].strip()):
      out.append(f'{where}: needs a ref to the issue or PR that decided it (#123, owner/repo#123 or a URL)')
    if 'dormant' in entry and not isinstance(entry['dormant'], bool):
      out.append(f'{where}: dormant must be true or false')
  return out


def suppressed_by(f: Finding, entries: Iterable[Exception_]) -> Exception_ | None:
  """
  The first exception whose fingerprint glob matches the finding.

  Args:
    f: The finding.
    entries: The exceptions.
  """
  for entry in entries:
    if fnmatchcase(f['fingerprint'], entry['fingerprint']):
      return entry
  return None


def market_of_suppressed_asset(f: Finding, suppressed: set[str]) -> str | None:
  """
  The suppressed asset finding an untranslated market trades, if any.

  Matching on the venue's own base and quote, rather than on the market ID, keeps the
  asset's case: Bitget's rToken `rACAD` trades as `RACADUSDT`, which a market ID glob
  couldn't tell from `RAYUSDT`. A translated asset has no finding, so its markets
  still report.

  Args:
    f: The finding.
    suppressed: Fingerprints of the suppressed findings.
  """
  pair = f['evidence'].get('venue_pair')
  if f['check'] != 'untranslated-market' or not pair:
    return None
  for side in ('base', 'quote'):
    asset = f'untranslated-asset:{f["platform"]}:{pair.get(side)}'
    if pair.get(side) and asset in suppressed:
      return asset
  return None


class Split(TypedDict):
  """Findings, with the suppressed ones set aside and annotated."""

  findings: list[Finding]
  suppressed: list[dict]
  """Each suppressed finding plus `exception` (the glob, or the asset finding) and `reason`."""


def apply(findings: Iterable[Finding], entries: list[Exception_]) -> Split:
  """
  Split findings into kept and suppressed.

  Args:
    findings: Every finding of a run.
    entries: The exceptions.
  """
  findings = list(findings)
  matched = {f['fingerprint']: entry for f in findings if (entry := suppressed_by(f, entries))}
  kept: list[Finding] = []
  suppressed: list[dict] = []
  for f in findings:
    entry = matched.get(f['fingerprint'])
    if entry is not None:
      suppressed.append({**f, 'exception': entry['fingerprint'], 'reason': entry['reason'], 'ref': entry['ref']})
      continue
    asset = market_of_suppressed_asset(f, set(matched))
    if asset is not None:
      entry = matched[asset]
      suppressed.append({**f, 'exception': asset, 'reason': entry['reason'], 'ref': entry['ref']})
      continue
    kept.append(f)
  return Split(findings=kept, suppressed=suppressed)


def unmatched(entries: Iterable[Exception_], fingerprints: Iterable[str]) -> list[Exception_]:
  """
  Non-dormant exceptions no fingerprint matches.

  Args:
    entries: The exceptions.
    fingerprints: The fingerprints to match against.
  """
  fingerprints = list(fingerprints)
  return [
    entry for entry in entries
    if not entry.get('dormant') and not any(fnmatchcase(fp, entry['fingerprint']) for fp in fingerprints)
  ]
