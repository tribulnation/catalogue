"""Venue markets, assets and networks the catalogue can't translate for their platform."""

from types import SimpleNamespace

from .catalogue import Catalogue, translate
from .finding import Finding, Severity, make, market_subject
from .observations import Observations

MIN_VOLUME_USD = 100_000
"""24h USD volume from which an untranslated market is medium severity."""


def markets(catalogue: Catalogue, obs: Observations) -> tuple[list[Finding], dict]:
  """
  `untranslated-market`: venue markets with no catalogue instrument.

  A market the venue reports as not tradable (halted, settled such as dYdX's
  `FINAL_SETTLEMENT`, or delisted) is not worth adding and gives no finding. A market
  registered but not open yet (`pending`, e.g. a HIP-3 market before launch) is counted
  in the notes instead, to be looked at once it opens. Liquid markets are medium,
  the rest low.

  Args:
    catalogue: The catalogue.
    obs: The observations; needs `listings`.
  """
  findings: list[Finding] = []
  ran: list[str] = []
  pending: dict[str, list[str]] = {}
  for platform, listing in sorted(obs['listings'].items()):
    ran.append(platform)
    rows = catalogue.instruments.get(platform, {})
    for key, market in sorted(listing['markets'].items()):
      if key in rows or market['tradable'] is False:
        continue
      subject = market_subject(market['exchange'], market['market'])
      if market['status'] == 'pending':
        pending.setdefault(platform, []).append(subject)
        continue
      volume = market['volume_24h_usd']
      severity: Severity = 'medium' if volume is not None and volume >= MIN_VOLUME_USD else 'low'
      findings.append(make(
        'untranslated-market',
        platform=platform,
        subject=subject,
        severity=severity,
        summary=f'{platform} {market["kind"]} market {subject} is not in the catalogue',
        evidence={
          'exchange': market['exchange'],
          'market': market['market'],
          'kind': market['kind'],
          'status': market['status'],
          'venue_pair': {'base': market['base'], 'quote': market['quote'], 'settlement': market['settlement']},
          'usd_volume_24h': volume,
          'usd_open_interest': market['open_interest_usd'],
        },
      ))
  coverage = {'ran': ran, 'skip': {}}
  if pending:
    coverage['notes'] = {'pending_open': pending}
  return findings, {'untranslated-market': coverage}


def seen_assets(catalogue: Catalogue, obs: Observations) -> dict[str, dict[str, set[str]]]:
  """
  Per platform, every venue asset ID and where it was seen: `earn`, `wallet` or `market`.

  Market bases and quotes count only from markets the catalogue lacks and the venue
  trades (or whose status is unknown): a catalogued market already maps its assets,
  and a settled, delisted or not-yet-open one needs nothing yet.

  Args:
    catalogue: The catalogue.
    obs: The observations.
  """
  seen: dict[str, dict[str, set[str]]] = {}
  for platform, entry in (obs.get('asset_ids') or {}).items():
    assets = seen.setdefault(platform, {})
    for asset, sources in (entry.get('assets') or {}).items():
      assets.setdefault(asset, set()).update(sources)
  for platform, listing in (obs.get('listings') or {}).items():
    assets = seen.setdefault(platform, {})
    rows = catalogue.instruments.get(platform, {})
    for key, market in listing['markets'].items():
      if key in rows or market['tradable'] is False or market['status'] == 'pending':
        continue
      for symbol in (market['base'], market['quote']):
        if symbol:
          assets.setdefault(symbol, set()).add('market')
  return seen


def assets(catalogue: Catalogue, obs: Observations) -> tuple[list[Finding], dict]:
  """
  `untranslated-asset`: venue asset IDs with no `asset_translations` entry.

  Assets seen in earn products or markets are medium; wallet-only ones are low. A
  symbol seen only on contract rows is also tried without a multiplier prefix
  (`1000BONK`), and known spam addresses are skipped.

  Args:
    catalogue: The catalogue.
    obs: The observations; reads `asset_ids` and `listings`.
  """
  findings: list[Finding] = []
  seen = seen_assets(catalogue, obs)
  for platform, found in sorted(seen.items()):
    translations = catalogue.asset_translations.get(platform, {})
    spam = catalogue.spam.get(platform, set())
    for asset, sources in sorted(found.items()):
      if translate(translations, asset, multiplier=sources == {'market'}) is not None or asset.lower() in spam:
        continue
      severity: Severity = 'low' if sources == {'wallet'} else 'medium'
      findings.append(make(
        'untranslated-asset',
        platform=platform,
        subject=asset,
        severity=severity,
        summary=f'{platform} asset {asset} has no catalogue translation',
        evidence={'seen_in': sorted(sources)},
      ))
  return findings, {'untranslated-asset': {'ran': sorted(seen), 'skip': {}}}


def networks(catalogue: Catalogue, obs: Observations) -> tuple[list[Finding], dict]:
  """
  `untranslated-network`: wallet networks with no `network_translations` entry.

  Args:
    catalogue: The catalogue.
    obs: The observations; needs `networks`.
  """
  findings: list[Finding] = []
  for platform, entry in sorted(obs['networks'].items()):
    known = catalogue.network_translations.get(platform, {})
    for network in sorted(set(entry.get('networks') or [])):
      if network not in known:
        findings.append(make(
          'untranslated-network',
          platform=platform,
          subject=network,
          severity='low',
          summary=f'{platform} network {network} has no catalogue translation',
          evidence={},
        ))
  return findings, {'untranslated-network': {'ran': sorted(obs['networks']), 'skip': {}}}


MARKETS = SimpleNamespace(NAMES=('untranslated-market',), INPUTS=('listings',), run=markets)
ASSETS = SimpleNamespace(NAMES=('untranslated-asset',), INPUTS=(), run=assets)
NETWORKS = SimpleNamespace(NAMES=('untranslated-network',), INPUTS=('networks',), run=networks)
GROUPS = [MARKETS, ASSETS, NETWORKS]
