"""Asset prices: external IDs that are missing, dead, duplicated or name the wrong coin,
and liquid markets far from the price their catalogue assets imply."""

from statistics import median
from types import SimpleNamespace
from typing import Any, TypedDict

from . import prices
from .catalogue import Catalogue
from .finding import CATALOGUE, Finding, make, market_subject
from .observations import Observations

MIN_VOLUME_USD = 100_000
"""24h USD volume from which a market counts as liquid."""
PRICE_DEVIATION = 0.2
"""Relative gap between venue-implied and reference price above which a check fires."""
MIN_MARKETS = 2
"""Independent platforms a market price must agree on before it outvotes a source."""
EVIDENCE_MARKETS = 4
"""Markets quoted as evidence."""


class AssetMarket(TypedDict):
  """A liquid market that implies a USD price for its base asset."""

  platform: str
  market: str
  implied_usd: float
  usd_volume_24h: float


def _multiplier(instrument: dict[str, Any]) -> float:
  return float(instrument.get('multiplier', 1)) if instrument['kind'] == 'perp' else 1.0


def traded(catalogue: Catalogue, obs: Observations) -> dict[str, list[AssetMarket]]:
  """
  The liquid markets of each canonical base asset, with the USD price each implies.

  A market implies `price × quote price ÷ multiplier` for its base. Only listed,
  tradable markets with a price, a known quote price and enough volume count.

  Args:
    catalogue: The catalogue.
    obs: The observations.
  """
  found: dict[str, list[AssetMarket]] = {}
  for platform, listing in sorted((obs.get('listings') or {}).items()):
    rows = catalogue.instruments.get(platform, {})
    for key, market in sorted(listing['markets'].items()):
      instrument = rows.get(key)
      if instrument is None or market['price'] is None or market['tradable'] is False or instrument.get('delisted'):
        continue
      quote_usd = prices.reference(catalogue, obs, instrument['quote'])
      volume = market['volume_24h_usd']
      if not quote_usd or volume is None or volume < MIN_VOLUME_USD:
        continue
      found.setdefault(instrument['base'], []).append(AssetMarket(
        platform=platform,
        market=market_subject(*key),
        implied_usd=market['price'] * quote_usd / _multiplier(instrument),
        usd_volume_24h=volume,
      ))
  return found


def evidence(markets: list[AssetMarket]) -> list[AssetMarket]:
  """
  An asset's most liquid markets, as evidence.

  Args:
    markets: The asset's markets.
  """
  return sorted(markets, key=lambda m: m['usd_volume_24h'], reverse=True)[:EVIDENCE_MARKETS]


def _ids(external: dict[str, str]) -> str:
  return ', '.join(f'{source}={value}' for source, value in sorted(external.items())) or 'none'


def duplicates(catalogue: Catalogue) -> list[Finding]:
  """
  `duplicate-external`: external IDs two or more assets claim; at most one can be right.

  Needs no observations, so `scripts/validate.py` runs it in CI.

  Args:
    catalogue: The catalogue.
  """
  owners: dict[tuple[str, str], list[str]] = {}
  for id, asset in catalogue.assets.items():
    for source, external in (asset.get('external') or {}).items():
      owners.setdefault((source, str(external)), []).append(id)
  return [
    make(
      'duplicate-external',
      platform=CATALOGUE,
      subject=f'{source}:{external}',
      severity='high',
      summary=f'{source} ID {external} is claimed by {len(assets)} assets: {", ".join(sorted(assets))}',
      evidence={'source': source, 'external_id': external, 'assets': sorted(assets)},
    )
    for (source, external), assets in sorted(owners.items()) if len(assets) > 1
  ]


def missing(catalogue: Catalogue, markets: dict[str, list[AssetMarket]], liquid: dict[str, float]) -> list[Finding]:
  """
  `missing-external`: liquidly traded assets no source can price, for lack of an external ID.

  A pegged asset is priced through its peg and needs none.

  Args:
    catalogue: The catalogue.
    markets: Liquid markets by base asset.
    liquid: Further assets the caller knows to be liquid, with their 24h USD volume.
  """
  ids = set(markets) | {id for id, volume in liquid.items() if volume >= MIN_VOLUME_USD}
  findings = []
  for id in sorted(ids):
    asset = catalogue.assets.get(id)
    if asset is None or asset.get('external') or asset.get('pegged_to'):
      continue
    found = markets.get(id, [])
    findings.append(make(
      'missing-external',
      platform=CATALOGUE,
      subject=id,
      severity='medium',
      summary=f'asset {id} ({asset.get("symbol")}) is liquidly traded but has no external ID, so it can never be priced',
      evidence={
        'asset': id, 'symbol': asset.get('symbol'), 'display_name': asset.get('display_name'),
        'markets': len(found), 'liquid_markets': evidence(found), 'usd_volume_24h': liquid.get(id),
      },
    ))
  return findings


def dead(catalogue: Catalogue, obs: Observations, markets: dict[str, list[AssetMarket]]) -> list[Finding]:
  """
  `dead-external`: liquid assets whose external IDs got no price from a source that answered.

  Only sources that answered this run count, so an outage can't look like a dead ID.

  Args:
    catalogue: The catalogue.
    obs: The observations.
    markets: Liquid markets by base asset.
  """
  healthy = prices.healthy(obs)
  findings = []
  for id, found in sorted(markets.items()):
    asset = catalogue.assets.get(id)
    if asset is None or asset.get('pegged_to') or prices.quotes(obs, id):
      continue
    external = {source: value for source, value in (asset.get('external') or {}).items() if source in healthy}
    if not external:
      continue
    findings.append(make(
      'dead-external',
      platform=CATALOGUE,
      subject=id,
      severity='high',
      summary=(
        f'asset {id} ({asset.get("symbol")}) has external IDs ({_ids(external)}) that returned no price, '
        'while it trades on liquid markets'
      ),
      evidence={
        'asset': id, 'symbol': asset.get('symbol'), 'display_name': asset.get('display_name'),
        'external': external, 'sources_queried': healthy, 'liquid_markets': evidence(found),
      },
    ))
  return findings


def mismatched(catalogue: Catalogue, obs: Observations, markets: dict[str, list[AssetMarket]]) -> list[Finding]:
  """
  `mismatched-external`: assets the venues and the price sources disagree about.

  The venues outvote the sources only when `MIN_MARKETS` platforms agree, which
  separates a wrong ID from one venue's odd market.

  Args:
    catalogue: The catalogue.
    obs: The observations.
    markets: Liquid markets by base asset.
  """
  findings = []
  for id, found in sorted(markets.items()):
    asset = catalogue.assets.get(id)
    reference = prices.reference(catalogue, obs, id)
    platforms = sorted({m['platform'] for m in found})
    if asset is None or not reference or len(platforms) < MIN_MARKETS:
      continue
    implied = float(median(m['implied_usd'] for m in found))
    deviation = abs(implied / reference - 1)
    if deviation <= PRICE_DEVIATION:
      continue
    external = dict(asset.get('external') or {})
    findings.append(make(
      'mismatched-external',
      platform=CATALOGUE,
      subject=id,
      severity='high',
      summary=(
        f'asset {id} ({asset.get("symbol")}) trades at {implied:.6g} USD across {len(platforms)} platforms, '
        f'{deviation:.0%} away from the {reference:.6g} its external IDs ({_ids(external)}) report'
      ),
      evidence={
        'asset': id, 'symbol': asset.get('symbol'), 'display_name': asset.get('display_name'),
        'external': external, 'reference_usd': reference, 'providers': prices.quotes(obs, id),
        'implied_usd': implied, 'deviation': deviation, 'platforms': platforms, 'liquid_markets': evidence(found),
      },
    ))
  return findings


def price(catalogue: Catalogue, obs: Observations, disputed: set[str]) -> list[Finding]:
  """
  `price`: liquid markets far from `base price × multiplier ÷ quote price`.

  A large gap on a liquid market almost always means the catalogue maps the market,
  or one of its assets, to the wrong coin. The quote is the catalogue's, so a quanto
  perpetual (`quote: hong-kong-dollar`, settled in USDT) is compared in HK dollars.
  Delisted, non-tradable and illiquid markets are skipped, and so are assets
  `mismatched-external` already reports: each of their markets would repeat it.

  Args:
    catalogue: The catalogue.
    obs: The observations.
    disputed: Assets with a `mismatched-external` finding.
  """
  findings = []
  for platform, listing in sorted((obs.get('listings') or {}).items()):
    rows = catalogue.instruments.get(platform, {})
    for key, market in sorted(listing['markets'].items()):
      instrument = rows.get(key)
      if instrument is None or market['price'] is None or market['tradable'] is False or instrument.get('delisted'):
        continue
      if instrument['base'] in disputed:
        continue
      base_usd = prices.reference(catalogue, obs, instrument['base'])
      quote_usd = prices.reference(catalogue, obs, instrument['quote'])
      volume = market['volume_24h_usd']
      if not base_usd or not quote_usd or volume is None or volume < MIN_VOLUME_USD:
        continue
      multiplier = _multiplier(instrument)
      expected = base_usd * multiplier / quote_usd
      deviation = abs(market['price'] / expected - 1)
      if deviation <= PRICE_DEVIATION:
        continue
      subject = market_subject(*key)
      findings.append(make(
        'price',
        platform=platform,
        subject=subject,
        severity='high',
        summary=(
          f'{platform} {subject} trades at {market["price"]:.6g}, {deviation:.0%} away from '
          f'the {expected:.6g} its catalogue assets imply'
        ),
        evidence={
          'price': market['price'], 'expected': expected, 'deviation': deviation,
          'base': instrument['base'], 'quote': instrument['quote'], 'base_usd': base_usd, 'quote_usd': quote_usd,
          'multiplier': multiplier, 'usd_volume_24h': volume, 'quanto': instrument.get('quanto'),
        },
      ))
  return findings


def run(catalogue: Catalogue, obs: Observations) -> tuple[list[Finding], dict]:
  """
  `missing-external`, `dead-external`, `mismatched-external` and `price`.

  Args:
    catalogue: The catalogue.
    obs: The observations; needs `listings` and `prices`.
  """
  markets = traded(catalogue, obs)
  wrong = mismatched(catalogue, obs, markets)
  findings = [
    *missing(catalogue, markets, obs.get('liquid') or {}),
    *dead(catalogue, obs, markets),
    *wrong,
    *price(catalogue, obs, {f['subject'] for f in wrong}),
  ]
  assets = {'ran': [CATALOGUE], 'skip': {}}
  return findings, {
    'missing-external': assets,
    'dead-external': assets if prices.healthy(obs) else {'ran': [], 'skip': {CATALOGUE: 'no source answered'}},
    'mismatched-external': assets,
    'price': {'ran': sorted(obs['listings']), 'skip': {}},
  }


def run_duplicates(catalogue: Catalogue, obs: Observations) -> tuple[list[Finding], dict]:
  """`duplicate-external`, which needs no observations."""
  return duplicates(catalogue), {'duplicate-external': {'ran': [CATALOGUE], 'skip': {}}}


GROUPS = [
  SimpleNamespace(
    NAMES=('missing-external', 'dead-external', 'mismatched-external', 'price'), INPUTS=('listings', 'prices'), run=run,
  ),
  SimpleNamespace(NAMES=('duplicate-external',), INPUTS=(), run=run_duplicates),
]
