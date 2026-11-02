"""Quanto perpetuals: price in one currency, P&L 1:1 in another."""

from pathlib import Path
import unittest

from tribulnation.catalogue.data import load, validate
from tribulnation.catalogue.data.schema import Perpetual

DATA = Path(__file__).resolve().parents[2] / 'data'
CATALOGUE = load.all(DATA)


def errors(instrument: Perpetual) -> list[str]:
  return validate.perpetual_instruments({'binance': {'X': instrument}}, CATALOGUE.assets)


class QuantoValidationTest(unittest.TestCase):
  """`quanto` must be stated where it changes the notional, and only there."""

  def test_hkd_stock_settled_in_usdt_must_say(self):
    """A stock priced in HK$ and settled in USDT is rejected until it states `quanto`."""
    instrument: Perpetual = {'base': 'tencent-holdings', 'quote': 'hong-kong-dollar', 'settlement': 'tether'}
    self.assertEqual(len(errors(instrument)), 1)
    self.assertIn('QUANTO', errors(instrument)[0])
    self.assertEqual(errors({**instrument, 'quanto': True}), [])
    self.assertEqual(errors({**instrument, 'quanto': False}), [])

  def test_delisted_must_say_too(self):
    """Delisted instruments still carry history that is sized by it."""
    instrument: Perpetual = {'base': 'sk-hynix', 'quote': 'south-korean-won', 'settlement': 'usd-coin', 'delisted': True}
    self.assertEqual(len(errors(instrument)), 1)

  def test_same_currency_needs_nothing(self):
    """USDT-quoted, USDC-settled is one currency (both pegged to `usd`): no marker needed."""
    self.assertEqual(errors({'base': 'apple', 'quote': 'tether', 'settlement': 'usd-coin'}), [])

  def test_same_currency_rejects_marker(self):
    """`quanto` is meaningless when quote and settlement are the same currency."""
    self.assertEqual(len(errors({'base': 'apple', 'quote': 'tether', 'settlement': 'usd-coin', 'quanto': True})), 1)

  def test_non_boolean_rejected(self):
    self.assertEqual(len(errors({'base': 'tencent-holdings', 'quote': 'hong-kong-dollar', 'settlement': 'tether', 'quanto': 'yes'})), 1)  # type: ignore[typeddict-item]

  def test_shipped_catalogue_validates(self):
    self.assertEqual(validate.perpetual_instruments(CATALOGUE.perpetual_instruments, CATALOGUE.assets), [])


class QuantoLookupTest(unittest.TestCase):
  """`perpetual_for` exposes the marker."""

  def test_binance_hk_stock_perps(self):
    """Binance's HK stock-code perps are priced in HK$ and pay USDT 1:1 per HK$ point."""
    for id, base in (('HK0700USDT', 'tencent-holdings'), ('HK0992USDT', 'lenovo-group'),
                     ('HK1810USDT', 'xiaomi'), ('HK0625USDT', 'shein')):
      perp = CATALOGUE.perpetual_for('binance', id)
      assert perp is not None
      self.assertEqual((perp.base, perp.quote, perp.settlement, perp.quanto),
                       (base, 'hong-kong-dollar', 'tether', True))

  def test_mexc_hk_stock_perps(self):
    for id in ('HK0700_USDT', 'HK0992_USDT', 'HK1810_USDT'):
      perp = CATALOGUE.perpetual_for('mexc', id)
      assert perp is not None
      self.assertEqual((perp.quote, perp.settlement, perp.quanto), ('hong-kong-dollar', 'tether', True))

  def test_usd_priced_twin_is_not_quanto(self):
    """`TENCENTUSDT` is the same share priced in USD: an ordinary linear perp."""
    perp = CATALOGUE.perpetual_for('binance', 'TENCENTUSDT')
    assert perp is not None
    self.assertEqual((perp.quote, perp.quanto), ('tether', False))


if __name__ == '__main__':
  unittest.main()
