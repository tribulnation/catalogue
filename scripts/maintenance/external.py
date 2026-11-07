"""Asset prices: external IDs that are missing, dead, duplicated or name the wrong coin,
and liquid markets far from the price their catalogue assets imply."""

from statistics import median
from types import SimpleNamespace
from typing import Any, TypedDict

from datetime import timedelta

from . import prices, sessions
from .catalogue import Catalogue
from .finding import CATALOGUE, Finding, make, market_subject
from .observations import Observations, timestamp

MIN_VOLUME_USD = 100_000
"""24h USD volume from which a market counts as liquid."""
PRICE_DEVIATION = 0.2
"""Relative gap between venue-implied and reference price above which a check fires."""
MIN_MARKETS = 2
"""Independent platforms a market price must agree on before it outvotes a source."""
EVIDENCE_MARKETS = 4
"""Markets quoted as evidence."""
MIN_SLOTS = 2
"""Observation slots a `mismatched-external` deviation must hold in, the current one included."""
HISTORY = timedelta(hours=24)
"""How far back earlier slots count."""


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
  When `prices.json` has `asked` (the exporter priced only some assets, say to stay
  within an API budget), a source counts only for the assets it was asked about, so
  an asset left out of the run can't look dead either.

  Args:
    catalogue: The catalogue.
    obs: The observations.
    markets: Liquid markets by base asset.
  """
  healthy = prices.healthy(obs)
  asked = (obs.get('prices') or {}).get('asked')
  findings = []
  for id, found in sorted(markets.items()):
    asset = catalogue.assets.get(id)
    if asset is None or asset.get('pegged_to') or prices.quotes(obs, id):
      continue
    external = {
      source: value for source, value in (asset.get('external') or {}).items()
      if source in healthy and (asked is None or id in (asked.get(source) or ()))
    }
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


def persists(obs: Observations, asset: str, reference: float, deviation: float) -> int:
  """
  In how many slots, the current one included, the venues sat on the same side of the
  reference by more than `PRICE_DEVIATION`.

  Earlier slots come from `prices.json` `history`, within `HISTORY` of the current one;
  each is judged against its own `reference_usd` when it has one. A row with no
  timestamp, or a timestamp already counted, confirms nothing, and with no current
  observation time nothing can be confirmed.

  Args:
    obs: The observations.
    asset: The canonical asset ID.
    reference: The current reference price.
    deviation: The current signed deviation (implied / reference - 1).
  """
  now = timestamp(obs.get('listings_as_of') or (obs.get('prices') or {}).get('as_of'))
  if now is None:
    return 1
  seen = set()
  for row in prices.history(obs, asset):
    at = timestamp(row.get('ts'))
    if at is None or at in seen or not timedelta(0) < now - at <= HISTORY:
      continue
    then = float(row['implied_usd']) / float(row.get('reference_usd') or reference) - 1
    if abs(then) > PRICE_DEVIATION and (then > 0) == (deviation > 0):
      seen.add(at)
  return 1 + len(seen)


def mismatched(
  catalogue: Catalogue, obs: Observations, markets: dict[str, list[AssetMarket]], notes: dict[str, list[str]] | None = None,
) -> list[Finding]:
  """
  `mismatched-external`: assets the venues and the price sources disagree about.

  The venues outvote the sources only when `MIN_MARKETS` platforms agree, which
  separates a wrong ID from one venue's odd market. Three more conditions keep a
  moving or one-sided reference from passing for a wrong ID; an asset that fails one
  is listed in `notes` instead:

  - `reference_split`: its providers disagree with each other (a bimodal reference);
  - `closing_reference`: an equity whose reference is an exchange close, observed
    outside its session or with a stale quote (`sessions.closing_reference`);
  - `unconfirmed`: the deviation holds in fewer than `MIN_SLOTS` slots.

  Args:
    catalogue: The catalogue.
    obs: The observations.
    markets: Liquid markets by base asset.
    notes: Collects the assets set aside, by reason.
  """
  notes = {} if notes is None else notes
  findings = []
  for id, found in sorted(markets.items()):
    asset = catalogue.assets.get(id)
    reference = prices.reference(catalogue, obs, id)
    platforms = sorted({m['platform'] for m in found})
    if asset is None or not reference or len(platforms) < MIN_MARKETS:
      continue
    implied = float(median(m['implied_usd'] for m in found))
    deviation = implied / reference - 1
    if abs(deviation) <= PRICE_DEVIATION:
      continue
    quotes = prices.quotes(obs, id)
    if prices.split(obs, id, PRICE_DEVIATION):
      notes.setdefault('reference_split', []).append(id)
      continue
    if sessions.closing_reference(catalogue, obs, id, quotes) is not None:
      notes.setdefault('closing_reference', []).append(id)
      continue
    slots = persists(obs, id, reference, deviation)
    if slots < MIN_SLOTS:
      notes.setdefault('unconfirmed', []).append(id)
      continue
    external = dict(asset.get('external') or {})
    findings.append(make(
      'mismatched-external',
      platform=CATALOGUE,
      subject=id,
      severity='high',
      summary=(
        f'asset {id} ({asset.get("symbol")}) trades at {implied:.6g} USD across {len(platforms)} platforms, '
        f'{abs(deviation):.0%} away from the {reference:.6g} its external IDs ({_ids(external)}) report'
      ),
      evidence={
        'asset': id, 'symbol': asset.get('symbol'), 'display_name': asset.get('display_name'),
        'external': external, 'reference_usd': reference, 'providers': quotes,
        'implied_usd': implied, 'deviation': abs(deviation), 'slots': slots, 'platforms': platforms,
        'liquid_markets': evidence(found),
      },
    ))
  return findings


def price(
  catalogue: Catalogue, obs: Observations, disputed: set[str], notes: dict[str, list[str]] | None = None,
) -> list[Finding]:
  """
  `price`: liquid markets far from `base price × multiplier ÷ quote price`.

  A large gap on a liquid market almost always means the catalogue maps the market,
  or one of its assets, to the wrong coin. The quote is the catalogue's, so a quanto
  perpetual (`quote: hong-kong-dollar`, settled in USDT) is compared in HK dollars.
  Delisted, non-tradable and illiquid markets are skipped, and so are assets
  `mismatched-external` reports or set aside: each of their markets would repeat that
  one disagreement about the reference. An
  equity base priced by an exchange close outside its session is noted as
  `closing_reference` instead (`sessions.closing_reference`).

  Args:
    catalogue: The catalogue.
    obs: The observations.
    disputed: Assets `mismatched-external` reported or set aside.
    notes: Collects the markets set aside, by reason.
  """
  notes = {} if notes is None else notes
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
      base_quotes = prices.quotes(obs, instrument['base'])
      if sessions.closing_reference(catalogue, obs, instrument['base'], base_quotes) is not None:
        notes.setdefault('closing_reference', []).append(f'{platform}:{subject}')
        continue
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
  set_aside: dict[str, list[str]] = {}
  priced_aside: dict[str, list[str]] = {}
  wrong = mismatched(catalogue, obs, markets, set_aside)
  findings = [
    *missing(catalogue, markets, obs.get('liquid') or {}),
    *dead(catalogue, obs, markets),
    *wrong,
    *price(catalogue, obs, {f['subject'] for f in wrong} | {id for ids in set_aside.values() for id in ids}, priced_aside),
  ]
  assets = {'ran': [CATALOGUE], 'skip': {}}
  return findings, {
    'missing-external': assets,
    'dead-external': assets if prices.healthy(obs) else {'ran': [], 'skip': {CATALOGUE: 'no source answered'}},
    'mismatched-external': {**assets, **({'notes': set_aside} if set_aside else {})},
    'price': {'ran': sorted(obs['listings']), 'skip': {}, **({'notes': priced_aside} if priced_aside else {})},
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
