"""Resolution of native ids to catalogue ids, on the repository's own data."""

from dataclasses import replace
from decimal import Decimal
from pathlib import Path
import unittest

from tribulnation.catalogue.data import load, validate

DATA = Path(__file__).resolve().parents[2] / 'data'
CATALOGUE = load.all(DATA)


class AssetForTest(unittest.TestCase):
  """`asset_for` per platform key kind."""

  def test_hyperliquid_spot_token_index(self):
    """Hyperliquid spot is keyed by token index, given as int or str; names do not resolve."""
    self.assertEqual(CATALOGUE.asset_for('hyperliquid', 150), 'hyperliquid')
    self.assertEqual(CATALOGUE.asset_for('hyperliquid', '0'), 'usd-coin')
    self.assertEqual(CATALOGUE.asset_for('hyperliquid', 268), 'tether')
    self.assertIsNone(CATALOGUE.asset_for('hyperliquid', 'HYPE'))

  def test_evm_contract_any_casing(self):
    """EVM contracts resolve from lowercase, checksummed or uppercase hex."""
    for address in (
      '0xaf88d065e77c8cc2239327c5edb3a432268e5831',
      '0xaf88d065e77c8cC2239327C5EDb3A432268e5831',
      '0xAF88D065E77C8CC2239327C5EDB3A432268E5831',
    ):
      self.assertEqual(CATALOGUE.asset_for('arbitrum', address), 'usd-coin')
    self.assertEqual(CATALOGUE.asset_for('arbitrum', '0xff970a61a04b1ca14834a43f5de4533ebddb5cc8'), 'bridged-usd-coin')

  def test_evm_native(self):
    """`native` names the gas coin, in any casing."""
    self.assertEqual(CATALOGUE.asset_for('ethereum', 'native'), 'ethereum')
    self.assertEqual(CATALOGUE.asset_for('arbitrum', 'NATIVE'), 'ethereum')

  def test_evm_unknown_contract(self):
    """An untranslated contract is None, not an error."""
    self.assertIsNone(CATALOGUE.asset_for('ethereum', '0x' + '00' * 20))

  def test_symbols_are_case_sensitive(self):
    """CEX and dYdX symbols match exactly."""
    self.assertEqual(CATALOGUE.asset_for('dydx', 'BTC'), 'bitcoin')
    self.assertEqual(CATALOGUE.asset_for('bitget', 'rSPY'), 'spdr-sp500-etf-trust-rtoken')
    self.assertIsNone(CATALOGUE.asset_for('bitget', 'RSPY'))

  def test_unknown_platform(self):
    """A platform without translations resolves nothing."""
    self.assertIsNone(CATALOGUE.asset_for('no-such-platform', 'BTC'))

  def test_translation_key(self):
    """Keys are normalised to the stored form."""
    self.assertEqual(
      CATALOGUE.translation_key('arbitrum', '0xaf88d065e77c8cc2239327c5edb3a432268e5831'),
      '0xaf88d065e77c8cC2239327C5EDb3A432268e5831',
    )
    self.assertEqual(CATALOGUE.translation_key('hyperliquid', 150), '150')
    self.assertEqual(CATALOGUE.translation_key('bitget', 'rSPY'), 'rSPY')


class PerpetualForTest(unittest.TestCase):
  """`perpetual_for` on hyperliquid and dydx."""

  def test_hyperliquid(self):
    """A standard hyperliquid perp resolves base, quote, settlement and a unit multiplier."""
    btc = CATALOGUE.perpetual_for('hyperliquid', 'BTC')
    assert btc is not None
    self.assertEqual((btc.base, btc.quote, btc.settlement), ('bitcoin', 'tether', 'usd-coin'))
    self.assertEqual(btc.multiplier, Decimal(1))
    self.assertFalse(btc.delisted)

  def test_hyperliquid_multiplier(self):
    """`kPEPE` is 1000 PEPE per contract unit."""
    kpepe = CATALOGUE.perpetual_for('hyperliquid', 'kPEPE')
    assert kpepe is not None
    self.assertEqual((kpepe.base, kpepe.multiplier), ('pepe', Decimal(1000)))

  def test_hyperliquid_hip3(self):
    """HIP-3 perps are keyed `dex:COIN`."""
    silver = CATALOGUE.perpetual_for('hyperliquid', 'xyz:SILVER')
    assert silver is not None
    self.assertEqual(silver.base, 'silver')

  def test_dydx(self):
    """dYdX perps are keyed by ticker."""
    btc = CATALOGUE.perpetual_for('dydx', 'BTC-USD')
    assert btc is not None
    self.assertEqual((btc.base, btc.quote, btc.settlement), ('bitcoin', 'usd-coin', 'usd-coin'))

  def test_unknown(self):
    """Unknown perps and platforms are None."""
    self.assertIsNone(CATALOGUE.perpetual_for('hyperliquid', 'NOPE'))
    self.assertIsNone(CATALOGUE.perpetual_for('nowhere', 'BTC'))


class NetworkForTest(unittest.TestCase):
  """`network_for` on venue network codes."""

  def test_known(self):
    """A venue network code maps to a catalogue platform."""
    self.assertEqual(CATALOGUE.network_for('bybit', 'BSC (BEP20)'), 'bnb-chain')
    self.assertIsNone(CATALOGUE.network_for('bybit', 'nope'))


class AliasTest(unittest.TestCase):
  """`replaced_by` aliases are followed by every lookup and enforced by validation."""

  def setUp(self):
    """Merge `bridged-usd-coin` into `usd-coin` as an alias, leaving the data pointing at the old id."""
    assets = dict(CATALOGUE.assets)
    assets['bridged-usd-coin'] = {**assets['bridged-usd-coin'], 'replaced_by': 'usd-coin'}
    self.catalogue = replace(CATALOGUE, assets=assets)

  def test_lookups_follow_alias(self):
    """Translations to an alias resolve to its replacement."""
    self.assertEqual(self.catalogue.asset_for('arbitrum', '0xff970a61a04b1ca14834a43f5de4533ebddb5cc8'), 'usd-coin')
    self.assertEqual(self.catalogue.canonical_id('bridged-usd-coin'), 'usd-coin')
    asset = self.catalogue.asset('bridged-usd-coin')
    assert asset is not None
    self.assertEqual(asset['id'], 'usd-coin')

  def test_cycle_terminates(self):
    """A (invalid) cycle does not loop forever."""
    assets = dict(self.catalogue.assets)
    assets['usd-coin'] = {**assets['usd-coin'], 'replaced_by': 'bridged-usd-coin'}
    self.assertIn(replace(self.catalogue, assets=assets).canonical_id('usd-coin'), {'usd-coin', 'bridged-usd-coin'})

  def test_validation(self):
    """Alias targets must exist and not be aliases; data must not reference aliases."""
    self.assertEqual(validate.asset_aliases(self.catalogue.assets), [])
    references = validate.alias_references(self.catalogue)
    self.assertTrue(any('arbitrum' in error and 'bridged-usd-coin' in error for error in references))
    assets = dict(self.catalogue.assets)
    assets['bridged-usd-coin'] = {**assets['bridged-usd-coin'], 'replaced_by': 'no-such-asset'}
    self.assertEqual(len(validate.asset_aliases(assets)), 1)
    self.assertEqual(validate.alias_references(CATALOGUE), [])


class IdStabilityTest(unittest.TestCase):
  """`validate.id_stability` against an injected baseline."""

  def test_removal_fails_addition_passes(self):
    """Removed ids are errors; added ids are not."""
    baseline = {'asset': {'bitcoin', 'old-coin'}, 'platform': {'ethereum'}}
    current = {'asset': {'bitcoin', 'new-coin'}, 'platform': {'ethereum', 'base'}}
    errors = validate.id_stability(current, baseline)
    self.assertEqual(len(errors), 1)
    self.assertIn('"old-coin"', errors[0])
    self.assertIn('replaced_by', errors[0])


if __name__ == '__main__':
  unittest.main()
