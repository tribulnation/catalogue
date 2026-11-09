"""When an exchange-close price is a fair reference: inside its listing's trading session.

Stock feeds (Yahoo, Twelve Data, Alpha Vantage) report the last print of the home
exchange; outside its session that is the previous close, while perpetuals keep
trading around the clock. Comparing the two after earnings or a crash looks like a
wrong external ID: intel and its 2x fund INTW on 2026-10-30 (#360/#361), applovin on
2026-11-05 (#391/#392), draftkings on 2026-11-06 (#393/#395). So an equity is compared
with such a reference only when the observation falls inside its exchange's regular
session and the quote is fresh. Exchange holidays aren't modelled; on one the quote
is not fresh, which skips it all the same.
"""

from datetime import datetime, time, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from .catalogue import Catalogue
from .observations import Observations, timestamp

CLOSE_SOURCES = {'yahoo', 'twelvedata', 'alphavantage'}
"""Sources that report an exchange's last print rather than a continuous price."""
EQUITY = {'stock', 'fund'}
"""Asset categories that trade in exchange sessions."""
FRESH = timedelta(minutes=30)
"""Largest gap between the observation and the reference quote inside a session."""
SESSIONS: dict[str, tuple[str, time, time]] = {
  '': ('America/New_York', time(9, 30), time(16, 0)),
  'HK': ('Asia/Hong_Kong', time(9, 30), time(16, 0)),
  'T': ('Asia/Tokyo', time(9, 0), time(15, 30)),
  'KS': ('Asia/Seoul', time(9, 0), time(15, 30)),
  'TW': ('Asia/Taipei', time(9, 0), time(13, 30)),
  'TWO': ('Asia/Taipei', time(9, 0), time(13, 30)),
  'SS': ('Asia/Shanghai', time(9, 30), time(15, 0)),
  'SZ': ('Asia/Shanghai', time(9, 30), time(15, 0)),
  'L': ('Europe/London', time(8, 0), time(16, 30)),
  'IS': ('Europe/Istanbul', time(10, 0), time(18, 0)),
}
"""Regular session by Yahoo ticker suffix (none: a US listing), in exchange local time."""


def exchange(asset: dict[str, Any]) -> str | None:
  """
  The asset's home exchange, as its Yahoo ticker suffix (`''` for a US listing).

  Args:
    asset: The asset record.
  """
  ticker = (asset.get('external') or {}).get('yahoo')
  if not ticker:
    return ''
  suffix = ticker.rsplit('.', 1)[1] if '.' in ticker else ''
  return suffix if suffix in SESSIONS else None


def in_session(suffix: str, at: datetime) -> bool:
  """
  Whether `at` falls in the regular session of the exchange with that suffix, on a weekday.

  Args:
    suffix: The Yahoo ticker suffix.
    at: The moment, timezone-aware.
  """
  zone, opens, closes = SESSIONS[suffix]
  local = at.astimezone(ZoneInfo(zone))
  return local.weekday() < 5 and opens <= local.time() < closes


def closing_reference(catalogue: Catalogue, obs: Observations, asset: str, quotes: dict[str, dict]) -> str | None:
  """
  Why an asset's reference price can't be compared now, if it can't.

  Only equities priced by exchange-close sources alone are judged; a reference with a
  continuous source (CoinGecko, CoinMarketCap) is always fair.

  Args:
    catalogue: The catalogue.
    obs: The observations; the slot is the listings' `as_of`.
    asset: The canonical asset ID.
    quotes: The asset's provider quotes, by source.

  Returns:
    `None` when the comparison is fair, else the reason it isn't.
  """
  record = catalogue.assets.get(asset) or {}
  if record.get('category') not in EQUITY or not quotes or not set(quotes) <= CLOSE_SOURCES:
    return None
  slot = timestamp(obs.get('listings_as_of') or (obs.get('prices') or {}).get('as_of'))
  if slot is None:
    return 'no observation time'
  suffix = exchange(record)
  if suffix is None:
    return 'unknown home exchange'
  if not in_session(suffix, slot):
    return 'outside the listing session'
  times = [t for t in (timestamp(quote.get('as_of')) for quote in quotes.values()) if t is not None]
  if not times or slot - max(times) > FRESH:
    return 'reference quote is not fresh'
  return None
