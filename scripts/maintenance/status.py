"""Catalogue listing status (`delisted`) that disagrees with what the venue lists."""

from dataclasses import dataclass
from datetime import timedelta
from types import SimpleNamespace
from typing import Any, Literal

from .catalogue import Catalogue, MarketKey
from .finding import Finding, Severity, make, market_subject
from .observations import Market, Observations, timestamp

LIVE_QUOTE = timedelta(hours=1)
"""How recent a market's last quote must be for it to count as live."""


@dataclass
class Disagreement:
  """One instrument whose `delisted` flag the venue contradicts."""

  kind: Literal['stale', 'delisted-live']
  key: MarketKey
  instrument: dict[str, Any]
  market: Market | None
  severity: Severity
  why: str


def quoted_live(market: Market, as_of: str | None) -> bool:
  """
  Whether the market was quoted within `LIVE_QUOTE` of the observation time.

  A venue's rules surface can leave out markets it still quotes: Binance's
  `exchangeInfo` omits its TradFi perpetuals, which catalogue-ops reported as stale
  218 times while they traded. A live quote settles it.

  Args:
    market: The venue market.
    as_of: When the listings were read.
  """
  quoted, now = timestamp(market['last_quote_ts']), timestamp(as_of)
  return quoted is not None and now is not None and now - quoted <= LIVE_QUOTE


def disagreements(
  instruments: dict[MarketKey, dict[str, Any]],
  markets: dict[MarketKey, Market],
  exchanges: dict[str, str],
  as_of: str | None = None,
) -> list[Disagreement]:
  """
  Listed instruments the venue no longer trades, and delisted ones it trades again.

  Only exchanges that were read are compared: an instrument on an exchange the
  observations don't cover is out of scope, not stale. Zero volume or open interest
  is never a delisting: HIP-3 deployers register markets before they open, and
  io:NVDA, io:AAPL, io:CRCL and para:ANTH were wrongly marked delisted that way.

  - Listed in the catalogue, not returned by the venue: stale, medium.
  - Listed, and the venue says delisted or settled: stale, medium.
  - Listed, and the venue says halted with no live quote: stale, low (halts are
    often temporary).
  - Delisted in the catalogue, and the venue trades it or has it pending open:
    delisted-live, medium.

  Args:
    instruments: A platform's catalogue instruments; each carries `kind`.
    markets: The platform's venue markets.
    exchanges: The exchanges read, by ID, with their kind.
    as_of: When the listings were read, to judge live quotes.
  """
  out: list[Disagreement] = []
  for key, instrument in sorted(instruments.items()):
    if exchanges.get(key[0]) != instrument['kind']:
      continue
    market = markets.get(key)
    delisted = bool(instrument.get('delisted'))
    live = market is not None and (
      market['tradable'] is True or market['status'] == 'pending' or quoted_live(market, as_of)
    )
    if not delisted:
      if market is None:
        out.append(Disagreement('stale', key, instrument, None, 'medium', 'not returned by the venue'))
      elif live:
        continue
      elif market['status'] in ('delisted', 'settled'):
        out.append(Disagreement('stale', key, instrument, market, 'medium', f'{market["status"]} on the venue'))
      elif market['tradable'] is False:
        out.append(Disagreement('stale', key, instrument, market, 'low', f'{market["status"]} on the venue, not tradable'))
    elif live:
      out.append(Disagreement('delisted-live', key, instrument, market, 'medium', f'{market["status"]} on the venue'))  # type: ignore[index]
  return out


def run(catalogue: Catalogue, obs: Observations) -> tuple[list[Finding], dict]:
  """
  `stale-listing` and `delisted-live` over every platform whose listings were read in full.

  Args:
    catalogue: The catalogue.
    obs: The observations; needs `listings`.
  """
  findings: list[Finding] = []
  ran: list[str] = []
  skip: dict[str, str] = {}
  for platform, listing in sorted(obs['listings'].items()):
    if not listing['complete']:
      skip[platform] = 'market read incomplete'
      continue
    ran.append(platform)
    found = disagreements(
      catalogue.instruments.get(platform, {}), listing['markets'], listing['exchanges'], obs.get('listings_as_of'),
    )
    for d in found:
      subject = market_subject(*d.key)
      market = d.market
      evidence = {
        'exchange': d.key[0],
        'market': d.key[1],
        'venue_lists_it': market is not None,
        'status': market and market['status'],
        'last_quote_ts': market and market['last_quote_ts'],
        'usd_volume_24h': market and market['volume_24h_usd'],
        'usd_open_interest': market and market['open_interest_usd'],
      }
      if d.kind == 'stale':
        findings.append(make(
          'stale-listing', platform=platform, subject=subject, severity=d.severity,
          summary=f'{platform} {subject} is listed in the catalogue but {d.why}', evidence=evidence,
        ))
      else:
        findings.append(make(
          'delisted-live', platform=platform, subject=subject, severity=d.severity,
          summary=f'{platform} {subject} is marked delisted but is {d.why}', evidence=evidence,
        ))
  coverage = {'ran': ran, 'skip': skip}
  return findings, {'stale-listing': coverage, 'delisted-live': coverage}


GROUP = SimpleNamespace(NAMES=('stale-listing', 'delisted-live'), INPUTS=('listings',), run=run)
GROUPS = [GROUP]
