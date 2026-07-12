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

def round_price(price: Decimal):
  if price >= 0.1:
    return round(price, 2)
  else:
    _, digits, exp = price.as_tuple()
    if not isinstance(exp, int):
      return price # shouldn't happen, but just in case
    first_digit_exp = abs(exp) - len(digits) + 1
    digits = first_digit_exp + 2
    return round(price, digits)

def round_date(date: datetime):
  if date.hour > 12:
    date = date + timedelta(days=1)
  return date