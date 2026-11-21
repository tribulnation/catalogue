"""Margin instruments: spot pairs traded on borrowed funds, loaded like spot ones."""

import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from tribulnation.catalogue.data import load, validate

DATA = Path(__file__).resolve().parents[2] / 'data'
CATALOGUE = load.all(DATA)


class MarginLoadTest(unittest.TestCase):
  """`margin_instruments` is keyed like `spot_instruments`, by platform then instrument id."""

  def test_bitget_lit(self):
    """Bitget's LITUSDT margin pair trades the Lighter token, as its spot pair does."""
    margin = CATALOGUE.margin_instruments['bitget']['LITUSDT']
    self.assertEqual(margin, {'exchange': 'margin', 'base': 'lighter', 'quote': 'tether'})
    self.assertEqual(CATALOGUE.spot_instruments['bitget']['LITUSDT']['base'], margin['base'])

  def test_every_margin_pair_matches_its_spot_pair(self):
    """A margin pair trades the spot book of the same symbol."""
    for platform, instruments in CATALOGUE.margin_instruments.items():
      for id, margin in instruments.items():
        spot = CATALOGUE.spot_instruments[platform][id]
        self.assertEqual((spot['base'], spot['quote']), (margin['base'], margin['quote']), f'{platform} {id}')

  def test_missing_folder_is_empty(self):
    """Data without an `instruments/margin` folder (e.g. an older archive) loads with none."""
    with tempfile.TemporaryDirectory() as folder:
      self.assertEqual(load.margin_instruments(Path(folder) / 'instruments' / 'margin'), {})

  def test_archive(self):
    """The `data.zip` loader reads the margin folder too."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as zf:
      zf.writestr('platforms/order.txt', '')
      zf.writestr('instruments/margin/bitget.json', json.dumps({'LITUSDT': {'exchange': 'margin', 'base': 'lighter', 'quote': 'tether'}}))
    catalogue = load.archive(buffer.getvalue())
    self.assertEqual(catalogue.margin_instruments['bitget']['LITUSDT']['base'], 'lighter')


class MarginValidationTest(unittest.TestCase):
  """Margin pairs reference existing assets and known platforms."""

  def test_shipped_catalogue_validates(self):
    self.assertEqual(validate.margin_instruments(CATALOGUE.margin_instruments, CATALOGUE.assets), [])

  def test_unknown_asset(self):
    errors = validate.margin_instruments({'bitget': {'XUSDT': {'base': 'no-such-asset', 'quote': 'tether'}}}, CATALOGUE.assets)
    self.assertEqual(len(errors), 1)
    self.assertIn('[MARGIN INSTRUMENT ERROR]', errors[0])


if __name__ == '__main__':
  unittest.main()
