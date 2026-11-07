"""Run the checks over a catalogue and its observations, then apply the exceptions."""

from typing import Any, Iterable, Literal, NotRequired, TypedDict

from . import base_quote, exceptions as exceptions_, external, status, untranslated
from .catalogue import Catalogue
from .finding import CHECKS, SEVERITIES, Finding
from .observations import Observations

GROUPS: list[Any] = [*untranslated.GROUPS, *status.GROUPS, *base_quote.GROUPS, *external.GROUPS]
"""Check groups. Each has `NAMES` (the checks it reports), `INPUTS` (the observation
files it needs) and `run(catalogue, observations) -> (findings, coverage)`, where
coverage maps each name to `{"ran": [platforms], "skip": {platform: reason}}` and,
optionally, `notes` (counts worth showing, such as markets pending open)."""


class Coverage(TypedDict):
  """Where a check ran, and why it skipped the rest."""

  ran: list[str]
  skip: dict[str, str]
  notes: NotRequired[dict[str, Any]]


class CheckStatus(TypedDict):
  """One check's outcome in a run."""

  status: Literal['ran', 'skip']
  reason: str | None
  found: int
  suppressed: int
  platforms: Coverage


class Report(TypedDict):
  """A run's findings, suppressed findings and per-check status."""

  checks: dict[str, CheckStatus]
  findings: list[Finding]
  suppressed: list[dict]


def _order(f: Finding) -> tuple[int, str]:
  return SEVERITIES.index(f['severity']), f['fingerprint']


def run(
  catalogue: Catalogue,
  observations: Observations,
  exceptions: list[exceptions_.Exception_],
  *,
  only: Iterable[str] | None = None,
  groups: list[Any] | None = None,
) -> Report:
  """
  Run every check (or `only` those named) and split out the suppressed findings.

  A check whose inputs are missing is `skip`, never an empty `ran`.

  Args:
    catalogue: The catalogue.
    observations: The exported observations.
    exceptions: The reviewed exceptions.
    only: Check names to run; all when `None`.
    groups: Check modules, `GROUPS` by default.
  """
  wanted = set(only) if only is not None else set(CHECKS)
  unknown = wanted - set(CHECKS)
  if unknown:
    raise ValueError(f'unknown checks: {sorted(unknown)}')
  status: dict[str, CheckStatus] = {
    name: CheckStatus(status='skip', reason='not implemented', found=0, suppressed=0, platforms=Coverage(ran=[], skip={}))
    for name in CHECKS if name in wanted
  }
  findings: list[Finding] = []
  for group in GROUPS if groups is None else groups:
    names = [name for name in group.NAMES if name in wanted]
    if not names:
      continue
    missing = [name for name in group.INPUTS if name not in observations]
    if missing:
      for name in names:
        status[name]['reason'] = f'no {", ".join(missing)} observations'
      continue
    found, coverage = group.run(catalogue, observations)
    for name in names:
      cover = coverage.get(name) or Coverage(ran=[], skip={})
      status[name]['platforms'] = Coverage(ran=sorted(cover['ran']), skip=dict(sorted(cover['skip'].items())))
      if cover.get('notes'):
        status[name]['platforms']['notes'] = cover['notes']
      if cover['ran']:
        status[name]['status'], status[name]['reason'] = 'ran', None
      else:
        status[name]['reason'] = 'no platform covered'
    findings += [f for f in found if f['check'] in wanted]
  split = exceptions_.apply(sorted(findings, key=_order), exceptions)
  for f in split['findings']:
    status[f['check']]['found'] += 1
  for f in split['suppressed']:
    status[f['check']]['suppressed'] += 1
  return Report(checks=status, findings=split['findings'], suppressed=split['suppressed'])
