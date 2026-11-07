"""The finding type every check returns, and its fingerprint."""

from typing import Any, Literal, Mapping, TypedDict

Severity = Literal['high', 'medium', 'low']
SEVERITIES: tuple[Severity, ...] = ('high', 'medium', 'low')

CHECKS = (
  'untranslated-asset',
  'untranslated-network',
  'untranslated-market',
  'stale-listing',
  'delisted-live',
  'base-quote',
  'price',
  'missing-external',
  'dead-external',
  'duplicate-external',
  'mismatched-external',
)
"""Every check name. catalogue-ops' `client-validation` is not one: a typed client
refusing a venue response is the reader's health, not a catalogue defect."""

CATALOGUE = 'catalogue'
"""The pseudo-platform of findings about assets rather than a venue."""


class Finding(TypedDict):
  """One thing the catalogue is missing or gets wrong."""

  fingerprint: str
  """`<check>:<platform>:<subject>`: stable across runs, so a finding is tracked, not repeated."""
  check: str
  platform: str
  subject: str
  severity: Severity
  summary: str
  evidence: dict[str, Any]
  """What the check saw, as JSON-serializable data."""


def fingerprint(check: str, platform: str, subject: str) -> str:
  """
  A finding's identity, exactly as catalogue-ops wrote it in `<!-- catalogue-ops:... -->`.

  Args:
    check: The check name.
    platform: The catalogue platform, or `catalogue` for asset findings.
    subject: What it's about, unique within the check and platform. A market is
      `<exchange>:<market id>`, with the exchange empty on Hyperliquid's main dex
      (`:BTC`) and the dex repeated on HIP-3 dexes (`xyz:xyz:MU`).
  """
  return f'{check}:{platform}:{subject}'


def parse(fp: str) -> tuple[str, str, str]:
  """
  Split a fingerprint into check, platform and subject (which may contain colons).

  Args:
    fp: The fingerprint.
  """
  check, platform, subject = fp.split(':', 2)
  return check, platform, subject


def market_subject(exchange: str, market: str) -> str:
  """
  A market's subject: `<exchange>:<market id>`.

  Args:
    exchange: The catalogue exchange ID (empty on Hyperliquid's main dex).
    market: The venue market ID.
  """
  return f'{exchange}:{market}'


def make(
  check: str,
  *,
  platform: str,
  subject: str,
  severity: Severity,
  summary: str,
  evidence: Mapping[str, Any],
) -> Finding:
  """
  Build a finding with its fingerprint.

  Args:
    check: The check that produced it; one of `CHECKS`.
    platform: The catalogue platform.
    subject: What it's about.
    severity: How much it matters.
    summary: One human-readable line.
    evidence: What the check saw.
  """
  if check not in CHECKS:
    raise ValueError(f'unknown check {check!r}')
  return Finding(
    fingerprint=fingerprint(check, platform, subject),
    check=check,
    platform=platform,
    subject=subject,
    severity=severity,
    summary=summary,
    evidence=dict(evidence),
  )
