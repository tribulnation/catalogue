"""What the venues reported, as the files the caller exports for the checks.

Every file in the observations directory is optional. A check whose input is missing
reports `skip` rather than "no findings", so a gap in coverage stays visible.

`listings.json`::

  {"as_of": "2026-11-07T04:50:00Z",
   "platforms": {"<platform>": {
     "complete": true,               # every market surface of the platform was read
     "exchanges": {"<exchange id>": "spot" | "perp"},   # the exchanges that were read
     "markets": [{
       "exchange": "xyz", "market": "xyz:MU", "kind": "perp",
       "base": "MU", "quote": "USDC", "settlement": "USDC",   # venue symbols, nullable
       "status": "trading",            # trading | halted | pending | settled | delisted | unknown
       "tradable": true,               # optional; derived from status when absent
       "price": 101.2,                 # in quote units; else derived from bid/ask/last
       "bid": 101.1, "ask": 101.3, "last": 101.2,
       "volume_24h_usd": 2500000.0, "open_interest_usd": 900000.0,
       "last_quote_ts": "2026-11-07T04:49:12Z",
       "index_quote": "usd"            # optional: canonical asset the index is priced in
     }]}}}

`asset_ids.json`: ``{"platforms": {"<platform>": {"complete": true,
"assets": {"<venue asset id>": ["wallet", "earn"]}}}}``. Market bases and quotes are
added from the listings with source `market`.

`networks.json`: ``{"platforms": {"<platform>": {"complete": true, "networks": [...]}}}``.

`prices.json`::

  {"as_of": "...",
   "healthy_sources": ["coingecko", "coinmarketcap", "yahoo"],   # answered this run
   "assets": {"<asset id>": {"providers": {"coingecko": {"usd": 0.0321, "as_of": "..."}}}},
   "history": {"<asset id>": [{"ts": "...", "implied_usd": 0.0255, "platforms": 3}]}}

`history` holds earlier slots' venue-implied medians, newest last.

`liquid.json`: ``{"assets": {"<asset id>": <24h USD volume>}}``: assets the caller
knows to be liquidly traded, on top of those the listings show.
"""

from datetime import datetime
import json
from pathlib import Path
from typing import Any, Literal, NotRequired, TypedDict

Status = Literal['trading', 'halted', 'pending', 'settled', 'delisted', 'unknown']
STATUSES: tuple[Status, ...] = ('trading', 'halted', 'pending', 'settled', 'delisted', 'unknown')
TRADABLE: dict[str, bool | None] = {
  'trading': True,
  'halted': False,
  'settled': False,
  'delisted': False,
  'pending': None,
  'unknown': None,
}
"""What a status says about tradability; `None` is "registered but not open" or unknown."""
MAX_SPREAD = 0.05
"""Widest relative bid/ask spread whose mid still counts as the market's price."""
FILES = ('listings', 'asset_ids', 'networks', 'prices', 'liquid')


class Market(TypedDict):
  """One venue market."""

  exchange: str
  market: str
  kind: Literal['spot', 'perp']
  base: str | None
  quote: str | None
  settlement: str | None
  status: Status
  tradable: bool | None
  price: float | None
  volume_24h_usd: float | None
  open_interest_usd: float | None
  last_quote_ts: str | None
  index_quote: NotRequired[str]


class Listings(TypedDict):
  """One platform's markets."""

  complete: bool
  exchanges: dict[str, str]
  markets: dict[tuple[str, str], Market]


class Observations(TypedDict):
  """Everything exported for a run; a key is absent when its file was."""

  listings: NotRequired[dict[str, Listings]]
  listings_as_of: NotRequired[str | None]
  asset_ids: NotRequired[dict[str, dict[str, Any]]]
  networks: NotRequired[dict[str, dict[str, Any]]]
  prices: NotRequired[dict[str, Any]]
  liquid: NotRequired[dict[str, float]]


def _number(value: Any) -> float | None:
  return None if value is None or value == '' else float(value)


def market_price(*, last: float | None, bid: float | None, ask: float | None, books: bool) -> float | None:
  """
  A market's price: the mid of a tight two-sided book, else the last trade.

  A book wider than `MAX_SPREAD` gives no price, and so does a missing book on an
  exchange that reports books, since the last trade there can be days old.

  Args:
    last: Last traded price.
    bid: Best bid.
    ask: Best ask.
    books: Whether the market's exchange reports books.
  """
  if bid is not None and ask is not None and bid > 0 and ask >= bid:
    mid = (bid + ask) / 2
    return mid if (ask - bid) / mid <= MAX_SPREAD else None
  if books:
    return None
  if last is not None and last > 0:
    return last
  return None


def _market(row: dict[str, Any], books: bool) -> Market:
  status = row.get('status') or 'unknown'
  if status not in STATUSES:
    raise ValueError(f'market {row.get("exchange")}:{row.get("market")}: unknown status {status!r}')
  tradable = row['tradable'] if 'tradable' in row else TRADABLE[status]
  price = _number(row.get('price'))
  if price is None:
    price = market_price(
      last=_number(row.get('last')), bid=_number(row.get('bid')), ask=_number(row.get('ask')), books=books,
    )
  market = Market(
    exchange=row.get('exchange') or '',
    market=str(row['market']),
    kind=row['kind'],
    base=row.get('base'),
    quote=row.get('quote'),
    settlement=row.get('settlement'),
    status=status,
    tradable=tradable,
    price=price,
    volume_24h_usd=_number(row.get('volume_24h_usd')),
    open_interest_usd=_number(row.get('open_interest_usd')),
    last_quote_ts=row.get('last_quote_ts'),
  )
  if row.get('index_quote'):
    market['index_quote'] = row['index_quote']
  return market


def parse_listings(raw: dict[str, Any]) -> dict[str, Listings]:
  """
  Index exported listings by platform and `(exchange, market)`.

  Args:
    raw: The parsed `listings.json`.
  """
  out: dict[str, Listings] = {}
  for platform, entry in (raw.get('platforms') or {}).items():
    rows = entry.get('markets') or []
    books: dict[str, bool] = {}
    for row in rows:
      books[row.get('exchange') or ''] = books.get(row.get('exchange') or '', False) or bool(row.get('bid') or row.get('ask'))
    markets = {}
    for row in rows:
      market = _market(row, books[row.get('exchange') or ''])
      markets[(market['exchange'], market['market'])] = market
    exchanges = dict(entry.get('exchanges') or {})
    for market in markets.values():
      exchanges.setdefault(market['exchange'], market['kind'])
    out[platform] = Listings(complete=bool(entry.get('complete', True)), exchanges=exchanges, markets=markets)
  return out


def load(directory: Path) -> Observations:
  """
  Read whichever observation files a directory has.

  Args:
    directory: The observations directory.
  """
  obs = Observations()
  for name in FILES:
    path = directory / f'{name}.json'
    if not path.exists():
      continue
    raw = json.loads(path.read_text(encoding='utf-8'))
    if name == 'listings':
      obs['listings'] = parse_listings(raw)
      obs['listings_as_of'] = raw.get('as_of')
    elif name == 'liquid':
      obs['liquid'] = {asset: float(volume or 0) for asset, volume in (raw.get('assets') or {}).items()}
    elif name == 'prices':
      obs['prices'] = raw
    else:
      obs[name] = raw.get('platforms') or {}  # type: ignore[literal-required]
  return obs


def timestamp(value: str | None) -> datetime | None:
  """
  Parse an ISO 8601 timestamp, accepting a trailing `Z`.

  Args:
    value: The timestamp, or `None`.
  """
  if not value:
    return None
  return datetime.fromisoformat(value.replace('Z', '+00:00'))
