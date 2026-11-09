"""Reference USD prices from the provider quotes in `prices.json`."""

from statistics import median
from typing import Any

from .catalogue import Catalogue
from .observations import Observations


def quotes(obs: Observations, asset: str) -> dict[str, dict[str, Any]]:
  """
  An asset's provider quotes with a positive USD price, by source.

  Args:
    obs: The observations.
    asset: The canonical asset ID.
  """
  entry = ((obs.get('prices') or {}).get('assets') or {}).get(asset) or {}
  return {
    source: quote for source, quote in (entry.get('providers') or {}).items()
    if isinstance(quote, dict) and quote.get('usd') and float(quote['usd']) > 0
  }


def healthy(obs: Observations) -> list[str]:
  """
  The price sources that answered this run.

  Args:
    obs: The observations.
  """
  return sorted((obs.get('prices') or {}).get('healthy_sources') or [])


def reference(catalogue: Catalogue, obs: Observations, asset: str, *, depth: int = 0) -> float | None:
  """
  An asset's reference USD price: the median of its provider quotes.

  The US dollar is 1. An asset no provider prices falls back to the asset it is
  pegged to (`pegged_to`), one level deep.

  Args:
    catalogue: The catalogue.
    obs: The observations.
    asset: The canonical asset ID.
  """
  if asset == 'usd':
    return 1.0
  found = quotes(obs, asset)
  if found:
    return float(median(float(quote['usd']) for quote in found.values()))
  peg = ((catalogue.assets.get(asset) or {}).get('pegged_to') or {}).get('asset')
  if peg and depth == 0:
    return reference(catalogue, obs, peg, depth=1)
  return None
