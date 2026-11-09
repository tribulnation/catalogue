"""Generator scripts' diffs as findings: `--report-json` of `hyperliquid.py`, `gtrade.py`
and `check_binance_spot_gaps.py`.

Each report reads ``{"source", "generated_at", "platforms": [...], "checks": [...],
"findings": [...]}``: the platforms and checks it covered, and what it found.
A finding whose fix code can decide carries it in `evidence["draft"]`:

  {"file": "data/instruments/perpetual/hyperliquid.json", "id": "xyz:MU",
   "add": {...instrument...}            # a new instrument
   | "set": {"delisted": true}, "unset": ["url"]   # fields to change on an existing one
   | "remove": true}

`scripts/maintain.py --extra FILE` merges such reports into a run, so their findings get
the same exceptions and the same output.
"""

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Iterable

from .finding import Finding, make, market_subject

MIN_VOLUME_USD = 100_000


def write(path: Path, source: str, platforms: Iterable[str], checks: Iterable[str], findings: list[Finding]) -> None:
  """
  Write a generator report.

  Args:
    path: The JSON file.
    source: The script that produced it.
    platforms: The catalogue platforms it covered.
    checks: The checks it covered there.
    findings: Its findings.
  """
  path.write_text(json.dumps({
    'source': source,
    'generated_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
    'platforms': sorted(set(platforms)),
    'checks': sorted(set(checks)),
    'findings': findings,
  }, indent=1, ensure_ascii=False, default=str) + '\n')


def load(path: Path) -> dict[str, Any]:
  """
  Read a generator report.

  Args:
    path: The JSON file.
  """
  report = json.loads(path.read_text())
  for key in ('source', 'platforms', 'checks', 'findings'):
    if key not in report:
      raise ValueError(f'{path}: not a generator report (no {key!r})')
  return report


def flag(platform: str, file: str, id: str, exchange: str, *, catalogue_delisted: bool, venue_delisted: bool | None, evidence: dict) -> Finding | None:
  """
  The finding for a `delisted` flag the venue contradicts, with its draft.

  Args:
    platform: The catalogue platform.
    file: The instruments file, relative to the repository.
    id: The instrument ID.
    exchange: Its catalogue exchange.
    catalogue_delisted: The catalogue's flag.
    venue_delisted: The venue's, or `None` when the venue no longer returns it.
    evidence: What the generator saw.
  """
  subject = market_subject(exchange, id)
  if venue_delisted is None:
    if catalogue_delisted:
      return None
    return make(
      'stale-listing', platform=platform, subject=subject, severity='medium',
      summary=f'{platform} {subject} is listed in the catalogue but not returned by the venue',
      evidence={**evidence, 'venue_lists_it': False},
    )
  if venue_delisted == catalogue_delisted:
    return None
  if venue_delisted:
    return make(
      'stale-listing', platform=platform, subject=subject, severity='medium',
      summary=f'{platform} {subject} is listed in the catalogue but delisted on the venue',
      evidence={**evidence, 'venue_lists_it': True, 'draft': {'file': file, 'id': id, 'set': {'delisted': True}, 'unset': ['url']}},
    )
  return make(
    'delisted-live', platform=platform, subject=subject, severity='medium',
    summary=f'{platform} {subject} is marked delisted but listed on the venue',
    evidence={**evidence, 'venue_lists_it': True, 'draft': {'file': file, 'id': id, 'unset': ['delisted']}},
  )


def missing(platform: str, file: str, id: str, exchange: str, *, instrument: dict | None, volume_usd: float | None, evidence: dict) -> Finding:
  """
  The finding for a venue market the catalogue lacks; with a draft when the generator resolved it.

  Args:
    platform: The catalogue platform.
    file: The instruments file, relative to the repository.
    id: The instrument ID.
    exchange: Its catalogue exchange.
    instrument: The instrument the generator would add, or `None` if it couldn't resolve one.
    volume_usd: The market's 24h USD volume, if known.
    evidence: What the generator saw.
  """
  subject = market_subject(exchange, id)
  draft = {'draft': {'file': file, 'id': id, 'add': instrument}} if instrument is not None else {}
  return make(
    'untranslated-market', platform=platform, subject=subject,
    severity='medium' if volume_usd is not None and volume_usd >= MIN_VOLUME_USD else 'low',
    summary=f'{platform} perp market {subject} is not in the catalogue' + ('' if draft else ' (unresolved)'),
    evidence={**evidence, 'usd_volume_24h': volume_usd, **draft},
  )
