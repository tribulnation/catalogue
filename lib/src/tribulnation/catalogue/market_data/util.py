from typing_extensions import Iterable, TypeVar
from datetime import datetime, timedelta
from decimal import Decimal
import itertools

T = TypeVar('T')

def batch(iterable: Iterable[T], size: int) -> Iterable[list[T]]:
  it = iter(iterable)
  batch = list(itertools.islice(it, size))
  while batch:
    yield batch
    batch = list(itertools.islice(it, size))

def parse_price(value: Decimal | float | str) -> Decimal:
  """
  Convert a provider price to `Decimal` without losing or inventing precision.

  Floats go through their shortest repr, so `1.15914` stays `1.15914` instead of
  `1.1591400000000000591...`. Prices are never rounded here: round for display only.
  """
  return Decimal(str(value))

def round_date(date: datetime):
  if date.hour > 12:
    date = date + timedelta(days=1)
  return date