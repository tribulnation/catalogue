"""Regression checks for native instrument IDs versus trading-page IDs."""

import unittest
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from instrument_urls import PERPETUAL_RULES, SPOT_RULES, Symbols, fill


class BitgetUrlsTest(unittest.TestCase):
  """Keep UTA links distinct from unverified Classic trading-page routes."""

  def test_product_urls(self):
    """UTA coin pages retain the native suffix exactly once."""
    symbols = Symbols(Path(__file__).resolve().parents[1] / 'data')
    cases = [
      ('BTCUSDT', 'tether', 'usdt/BTCUSDT'),
      ('BTCPERP', 'usd-coin', 'usdc/BTCPERP'),
      ('BTCUSD', 'bitcoin', 'coin/BTCUSD_CM'),
      ('BTCUSD_CM', 'bitcoin', 'coin/BTCUSD_CM'),
    ]
    for id, settlement, path in cases:
      with self.subTest(id=id):
        self.assertEqual(
          PERPETUAL_RULES['bitget'](id, {'settlement': settlement}, symbols),
          f'https://www.bitget.com/futures/{path}',
        )

  def test_classic_does_not_link_to_uta(self):
    """Missing Classic routes must not silently point at the UTA instrument."""
    symbols = Symbols(Path(__file__).resolve().parents[1] / 'data')
    self.assertIsNone(PERPETUAL_RULES['bitget'](
      'BTCUSD', {'exchange': 'coin-classic', 'settlement': 'bitcoin'}, symbols,
    ))

  def test_regeneration_removes_unverified_and_delisted_urls(self):
    """A skipped rule removes a stale URL without dropping the instrument."""
    symbols = Symbols(Path(__file__).resolve().parents[1] / 'data')
    rows = {
      'BTCUSD': {'exchange': 'coin-classic', 'settlement': 'bitcoin', 'url': 'wrong'},
      'BTCUSD_CM': {'exchange': 'coin', 'settlement': 'bitcoin'},
      'OLDUSD': {'exchange': 'coin-classic', 'delisted': True, 'url': 'gone'},
    }
    with TemporaryDirectory() as folder:
      path = Path(folder) / 'bitget.json'
      path.write_text(json.dumps(rows))
      result = fill(Path(folder), {'bitget': PERPETUAL_RULES['bitget']}, symbols, overwrite=True)
      updated = json.loads(path.read_text())
    self.assertEqual(result, (1, 1))
    self.assertNotIn('url', updated['BTCUSD'])
    self.assertNotIn('url', updated['OLDUSD'])
    self.assertEqual(updated['BTCUSD_CM']['url'], 'https://www.bitget.com/futures/coin/BTCUSD_CM')


class CoinbaseUrlsTest(unittest.TestCase):
  """Advanced Trade pages require the full native product ID."""

  def test_intx_suffix_is_preserved_in_the_web_url(self):
    """The web route must not strip the product's International Exchange suffix."""
    symbols = Symbols(Path(__file__).resolve().parents[1] / 'data')
    for id in ('BTC-PERP-INTX', 'ETH-PERP-INTX', '1000BONK-PERP-INTX'):
      self.assertEqual(
        PERPETUAL_RULES['coinbase'](id, {}, symbols),
        f'https://www.coinbase.com/advanced-trade/perpetuals/{id}',
      )


class ExtendedUrlsTest(unittest.TestCase):
  """Perpetual pages use the native market name, scaled and 24/5 names included."""

  def test_market_name_is_the_path(self):
    """`/trade/<market>` is the app's canonical route; `/perp/<market>` redirects to it."""
    symbols = Symbols(Path(__file__).resolve().parents[1] / 'data')
    for id in ('BTC-USD', '1000PEPE-USD', 'kBOME-USD', 'AAPL_24_5-USD', 'SPX500m-USD'):
      with self.subTest(id=id):
        self.assertEqual(
          PERPETUAL_RULES['extended'](id, {}, symbols),
          f'https://app.extended.exchange/trade/{id}',
        )


class GrvtUrlsTest(unittest.TestCase):
  """Perpetual pages use `<BASE>-<QUOTE>`, not the API's `<BASE>_<QUOTE>_Perp` name."""

  def test_instrument_name_maps_to_page(self):
    """GRVT's own API links `BTC_USDT_Perp` to `/exchange/perpetual/BTC-USDT`."""
    symbols = Symbols(Path(__file__).resolve().parents[1] / 'data')
    for id, path in (('BTC_USDT_Perp', 'BTC-USDT'), ('KPEPE_USDT_Perp', 'KPEPE-USDT')):
      with self.subTest(id=id):
        self.assertEqual(
          PERPETUAL_RULES['grvt'](id, {}, symbols),
          f'https://grvt.io/exchange/perpetual/{path}',
        )


class MarginTradeUrlsTest(unittest.TestCase):
  """Pairs use the app's `-` slug."""

  def test_urls(self):
    symbols = Symbols(Path(__file__).resolve().parents[1] / 'data')
    cases = [
      (PERPETUAL_RULES, 'BTC', 'https://margin.trade/trade/BTC'),
      (PERPETUAL_RULES, 'PEARL', 'https://margin.trade/trade/PEARL'),
      (SPOT_RULES, 'PEARL/USDC', 'https://margin.trade/trade/PEARL-USDC'),
    ]
    for rules, id, url in cases:
      with self.subTest(id=id):
        self.assertEqual(rules['margin-trade'](id, {}, symbols), url)


class TerminalCoverageDexUrlsTest(unittest.TestCase):
  """Routes read from each venue's own site links (2026-10-27)."""

  def test_routes(self):
    """Backpack's pages drop the C of USDC; Aevo lowercases; Variational drops -PERP."""
    symbols = Symbols(Path(__file__).resolve().parents[1] / 'data')
    cases = [
      (PERPETUAL_RULES, 'aevo', 'ETH-PERP', 'https://app.aevo.xyz/perpetual/eth'),
      (PERPETUAL_RULES, 'apex', 'BTCUSDT', 'https://omni.apex.exchange/trade/BTCUSDT'),
      (PERPETUAL_RULES, 'backpack', 'BTC_USDC_PERP', 'https://backpack.exchange/trade/BTC_USD_PERP'),
      (SPOT_RULES, 'backpack', 'BTC_USDC', 'https://backpack.exchange/trade/BTC_USD'),
      (PERPETUAL_RULES, 'bluefin', 'BTC-PERP', 'https://trade.bluefin.io/pro/BTC-PERP'),
      (SPOT_RULES, 'derive', 'DRV-USDC', 'https://app.derive.xyz/trade/spot?symbol=DRV-USDC'),
      (PERPETUAL_RULES, 'edgex', 'BTCUSDC', 'https://pro.edgex.exchange/en-US/perpetuals/BTCUSDC'),
      (PERPETUAL_RULES, 'paradex', 'BTC-USD-PERP', 'https://app.paradex.trade/trade/BTC-USD-PERP'),
      (PERPETUAL_RULES, 'variational', 'OPENAI-PERP', 'https://omni.variational.io/perpetual/OPENAI'),
    ]
    for rules, platform, id, url in cases:
      with self.subTest(platform=platform, id=id):
        self.assertEqual(rules[platform](id, {}, symbols), url)
class BingxUrlsTest(unittest.TestCase):
  """Spot pages drop the pair's `-`; perpetual pages keep the contract symbol."""

  def test_urls(self):
    symbols = Symbols(Path(__file__).resolve().parents[1] / 'data')
    cases = [
      (SPOT_RULES, 'BTC-USDT', 'https://bingx.com/en/spot/BTCUSDT/'),
      (PERPETUAL_RULES, 'BTC-USDT', 'https://bingx.com/en/perpetual/BTC-USDT/'),
      (PERPETUAL_RULES, 'ETH-USDC', 'https://bingx.com/en/perpetual/ETH-USDC/'),
    ]
    for rules, id, url in cases:
      with self.subTest(id=id):
        self.assertEqual(rules['bingx'](id, {}, symbols), url)


class CoinwPionexSpotUrlsTest(unittest.TestCase):
  """CoinW spot pages use the lower-case concatenated pair; Pionex keeps the `_` symbol."""

  def test_urls(self):
    symbols = Symbols(Path(__file__).resolve().parents[1] / 'data')
    self.assertEqual(SPOT_RULES['coinw']('BTC_USDT', {}, symbols), 'https://www.coinw.com/spot/btcusdt')
    self.assertEqual(SPOT_RULES['pionex']('ETH_BTC', {}, symbols), 'https://www.pionex.com/en/trade/ETH_BTC/Bot')



class Terminal341UrlsTest(unittest.TestCase):
  """Rules added for the Terminal's market links (Terminal backoffice #341), each
  checked against the live trading page on 2026-10-31."""

  def test_trading_pages(self):
    symbols = Symbols(Path(__file__).resolve().parents[1] / 'data')
    cases = [
      (SPOT_RULES, 'bit2me', 'BTC/EURR', {}, 'https://pro.bit2me.com/exchange/BTC-EURR'),
      (SPOT_RULES, 'bitso', 'usdt_ars', {}, 'https://bitso.com/alpha/usdt/ars'),
      (SPOT_RULES, 'bitstamp', 'AAVE/USD', {}, 'https://www.bitstamp.net/trade/aaveusd/'),
      (PERPETUAL_RULES, 'bitstamp', 'BTC/USD-PERP', {}, 'https://www.bitstamp.net/trade/btcusd-perp/'),
      (PERPETUAL_RULES, 'blofin', 'SOL-USDT', {'settlement': 'tether'}, 'https://blofin.com/futures/SOL-USDT'),
      (PERPETUAL_RULES, 'derive', 'ETH-PERP', {}, 'https://app.derive.xyz/trade/perps?symbol=ETH-PERP'),
      (PERPETUAL_RULES, 'evedex', '1000PEPEUSD', {}, 'https://exchange.evedex.com/en/trade/1000PEPEUSD'),
      (PERPETUAL_RULES, 'helix', 'AAPL/USDC PERP', {}, 'https://helixapp.com/futures/aapl-usdc-perp'),
      (PERPETUAL_RULES, 'ostium', 'AAPL-USD', {}, 'https://app.ostium.com/trade?from=AAPL&to=USD'),
      (PERPETUAL_RULES, 'gtrade', 'base-usdc:USD/JPY', {}, 'https://gains.trade/trading#USD-JPY'),
      (PERPETUAL_RULES, 'gtrade', 'arbitrum-usdc:TSLA_1/USD', {}, None),
      (PERPETUAL_RULES, 'pacifica', '2Z', {}, 'https://app.pacifica.fi/trade/2Z'),
      (PERPETUAL_RULES, 'pionex', 'ETH_USDT_PERP', {}, 'https://www.pionex.com/en/futures/ETH.PERP_USDT/Manual'),
      (PERPETUAL_RULES, 'qfex', 'AAOI-USD', {}, 'https://www.qfex.com/trade/AAOI-USD'),
    ]
    for rules, platform, id, instrument, url in cases:
      with self.subTest(platform=platform, id=id):
        self.assertEqual(rules[platform](id, instrument, symbols), url)

  def test_blofin_unverified_margins_get_no_url(self):
    """Only the USDT-margined route was verified; USDC and coin-margined get none."""
    symbols = Symbols(Path(__file__).resolve().parents[1] / 'data')
    for settlement in ('usd-coin', 'bitcoin'):
      self.assertIsNone(PERPETUAL_RULES['blofin']('BTC-USD', {'settlement': settlement}, symbols))



class LighterUrlsTest(unittest.TestCase):
  """Lighter pages name a dollar-quoted market by its base leg alone."""

  def setUp(self):
    self.symbols = Symbols(Path(__file__).resolve().parents[1] / 'data')

  def test_dollar_quotes_name_the_base_only(self):
    """tether, usd and usd-coin quotes are all dollars; only a foreign quote adds a leg."""
    cases = [
      ({'base': 'ethereum', 'quote': 'tether'}, 'ETH'),
      ({'base': 'nvidia', 'quote': 'usd'}, 'NVDA'),
      ({'base': 'ethereum', 'quote': 'usd-coin'}, 'ETH'),
      ({'base': 'pepe', 'quote': 'tether', 'multiplier': 1000}, '1000PEPE'),
      ({'base': 'euro', 'quote': 'usd'}, 'EURUSD'),
      ({'base': 'tencent-holdings', 'quote': 'usd'}, 'TENCENT'),
      ({'base': 'usd', 'quote': 'japanese-yen', 'quanto': True}, 'USDJPY'),
      ({'base': 'usd', 'quote': 'south-korean-won', 'quanto': True}, 'USDKRW'),
    ]
    for instrument, page in cases:
      with self.subTest(page=page):
        self.assertEqual(
          PERPETUAL_RULES['lighter']('0', {'settlement': 'usd-coin', **instrument}, self.symbols),
          f'https://app.lighter.xyz/trade/{page}',
        )

  def test_committed_urls_match_the_rule(self):
    """Regenerating with --overwrite must leave every committed Lighter URL unchanged."""
    file = Path(__file__).resolve().parents[1] / 'data' / 'instruments' / 'perpetual' / 'lighter.json'
    rule = PERPETUAL_RULES['lighter']
    changed = {
      id: (instrument['url'], rule(id, instrument, self.symbols))
      for id, instrument in json.loads(file.read_text()).items()
      if 'url' in instrument and rule(id, instrument, self.symbols) != instrument['url']
    }
    self.assertEqual(changed, {})


if __name__ == '__main__':
  unittest.main()
