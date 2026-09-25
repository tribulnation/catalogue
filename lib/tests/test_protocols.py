"""Protocol entries and correlation keys, on the repository's own data."""

from copy import deepcopy
from dataclasses import replace
from pathlib import Path
import unittest

from tribulnation.catalogue import CorrelationError, Protocol
from tribulnation.catalogue.data import load, validate

DATA = Path(__file__).resolve().parents[2] / 'data'
CATALOGUE = load.all(DATA)


class DomainTest(unittest.TestCase):
  """CCTP domain <-> network lookups."""

  def test_network_for_domain(self):
    """Known domains resolve to catalogue networks; unknown ones and protocols to None."""
    self.assertEqual(CATALOGUE.network_for_domain('cctp', 0), 'ethereum')
    self.assertEqual(CATALOGUE.network_for_domain('cctp', 3), 'arbitrum')
    self.assertEqual(CATALOGUE.network_for_domain('cctp', 4), 'noble')
    self.assertEqual(CATALOGUE.network_for_domain('cctp', 19), 'hyperevm')
    self.assertIsNone(CATALOGUE.network_for_domain('cctp', 9999))
    self.assertIsNone(CATALOGUE.network_for_domain('ibc', 0))
    self.assertIsNone(CATALOGUE.network_for_domain('no-such-protocol', 0))

  def test_domain_for_network(self):
    """The reverse lookup gives a chain its own domain."""
    self.assertEqual(CATALOGUE.domain_for_network('cctp', 'base'), 6)
    self.assertEqual(CATALOGUE.domain_for_network('cctp', 'noble'), 4)
    self.assertIsNone(CATALOGUE.domain_for_network('cctp', 'bitcoin'))

  def test_protocol(self):
    """Protocols are looked up by id."""
    cctp = CATALOGUE.protocol('cctp')
    assert cctp is not None
    self.assertEqual(cctp['correlation']['key'], 'cctp:{source_domain}:{nonce}')
    self.assertIsNone(CATALOGUE.protocol('no-such-protocol'))


class FormatTest(unittest.TestCase):
  """`format_correlation` builds canonical keys and rejects anything off-template."""

  def test_keys(self):
    """Every shipped protocol formats its documented key."""
    self.assertEqual(
      CATALOGUE.format_correlation('cctp', source_domain=4, nonce=12345), 'cctp:4:12345'
    )
    self.assertEqual(
      CATALOGUE.format_correlation(
        'ibc', sending_chain='dydx', channel='channel-0', sequence=42
      ),
      'ibc:dydx:channel-0:42',
    )
    self.assertEqual(
      CATALOGUE.format_correlation(
        'hlbridge', user='0xBA2F7CE3' + '00' * 16, nonce=1790358868879000
      ),
      'hlbridge:0xba2f7ce3' + '00' * 16 + ':1790358868879000',
    )
    self.assertEqual(
      CATALOGUE.format_correlation('gofast', order_id=b'\x00\xab'), 'gofast:0x00ab'
    )

  def test_canonical_inputs(self):
    """Decimal strings and any-case hex normalise to the same key as native values."""
    self.assertEqual(
      CATALOGUE.format_correlation('cctp', source_domain='4', nonce='12345'),
      'cctp:4:12345',
    )
    self.assertEqual(
      CATALOGUE.format_correlation('gofast', order_id='0xABCD'), 'gofast:0xabcd'
    )

  def test_errors(self):
    """Unknown protocol, missing, extra and mistyped fields are errors."""
    cases = [
      ('nope', {'x': 1}),
      ('cctp', {'source_domain': 4}),
      ('cctp', {'source_domain': 4, 'nonce': 1, 'version': 1}),
      ('cctp', {'source_domain': -1, 'nonce': 1}),
      ('cctp', {'source_domain': 4, 'nonce': '0x01'}),
      ('cctp', {'source_domain': 4, 'nonce': '007'}),
      ('cctp', {'source_domain': True, 'nonce': 1}),
      (
        'ibc',
        {'sending_chain': 'not-a-network', 'channel': 'channel-0', 'sequence': 1},
      ),
      ('ibc', {'sending_chain': 'dydx', 'channel': 'channel:0', 'sequence': 1}),
      ('ibc', {'sending_chain': 'dydx', 'channel': '', 'sequence': 1}),
      ('hlbridge', {'user': 'ba2f7ce3', 'nonce': 1}),
      ('gofast', {'order_id': 12}),
    ]
    for protocol, fields in cases:
      with (
        self.subTest(protocol=protocol, fields=fields),
        self.assertRaises(CorrelationError),
      ):
        CATALOGUE.format_correlation(protocol, **fields)

  def test_error_is_value_error(self):
    """Callers catching ValueError also catch correlation errors."""
    self.assertTrue(issubclass(CorrelationError, ValueError))


class ParseTest(unittest.TestCase):
  """`parse_correlation` inverts `format_correlation` and accepts only canonical keys."""

  def test_roundtrip(self):
    """Parsed fields format back to the same key."""
    for key in (
      'cctp:4:12345',
      'ibc:dydx:channel-0:42',
      'hlbridge:0x' + 'ab' * 20 + ':1790358868879000',
      'gofast:0x' + '01' * 32,
    ):
      with self.subTest(key=key):
        protocol, fields = CATALOGUE.parse_correlation(key)
        self.assertEqual(CATALOGUE.format_correlation(protocol, **fields), key)

  def test_typed_fields(self):
    """Integer fields come back as int, the rest as str."""
    self.assertEqual(
      CATALOGUE.parse_correlation('ibc:dydx:channel-0:42'),
      ('ibc', {'sending_chain': 'dydx', 'channel': 'channel-0', 'sequence': 42}),
    )
    self.assertEqual(
      CATALOGUE.parse_correlation('cctp:4:12345'),
      ('cctp', {'source_domain': 4, 'nonce': 12345}),
    )

  def test_errors(self):
    """Unknown namespaces, wrong arity and non-canonical values are errors."""
    for key in (
      'tx:arbitrum:0xabc',
      'cctp:4',
      'cctp:4:1:2',
      'cctp:04:1',
      'cctp:4:0x1',
      'gofast:0xABCD',
      'ibc:unknown-chain:channel-0:1',
      '',
    ):
      with self.subTest(key=key), self.assertRaises(CorrelationError):
        CATALOGUE.parse_correlation(key)


class ValidateTest(unittest.TestCase):
  """`validate.protocols` rejects malformed protocol entries."""

  def errors(self, **changes) -> list[str]:
    """Validation errors of the `cctp` entry with top-level `changes` applied."""
    entry: Protocol = {**deepcopy(CATALOGUE.protocols['cctp']), **changes}  # type: ignore[typeddict-item]
    return validate.protocols({'cctp': entry}, CATALOGUE.platforms)

  def test_repository_data(self):
    """The shipped protocols validate."""
    self.assertEqual(validate.protocols(CATALOGUE.protocols, CATALOGUE.platforms), [])
    self.assertEqual(validate.all(CATALOGUE, str(DATA.parent)), [])

  def test_placeholders_must_equal_fields(self):
    """A placeholder without a field, or a field without a placeholder, is an error."""
    self.assertTrue(
      self.errors(
        correlation={
          'key': 'cctp:{source_domain}',
          'fields': {'source_domain': 'uint', 'nonce': 'uint'},
        }
      )
    )
    self.assertTrue(
      self.errors(
        correlation={
          'key': 'cctp:{source_domain}:{nonce}',
          'fields': {'source_domain': 'uint'},
        }
      )
    )

  def test_unknown_type(self):
    """Field types come from a closed set."""
    self.assertTrue(
      self.errors(correlation={'key': 'cctp:{nonce}', 'fields': {'nonce': 'bytes32'}})
    )

  def test_namespace_is_id(self):
    """The key's namespace is the protocol id."""
    self.assertTrue(
      self.errors(correlation={'key': 'circle:{nonce}', 'fields': {'nonce': 'uint'}})
    )

  def test_malformed_segment(self):
    """Segments are whole placeholders or kebab-case literals."""
    self.assertTrue(
      self.errors(correlation={'key': 'cctp:v{nonce}', 'fields': {'nonce': 'uint'}})
    )

  def test_unknown_network(self):
    """Domains reference existing catalogue networks."""
    self.assertTrue(self.errors(domains={0: 'not-a-network'}))

  def test_duplicate_network(self):
    """One network has one domain."""
    self.assertTrue(self.errors(domains={0: 'ethereum', 1: 'ethereum'}))

  def test_id_matches_file(self):
    """The `id` field equals the file stem."""
    self.assertTrue(self.errors(id='circle'))

  def test_metadata(self):
    """An English description and at least one URL are required."""
    self.assertTrue(self.errors(about={'en': ''}))
    self.assertTrue(self.errors(urls={}))


class LiteralSegmentTest(unittest.TestCase):
  """Templates may carry literal segments between placeholders."""

  def test_literal(self):
    """A literal segment is written as-is and must match on parse."""
    entry: Protocol = {
      'id': 'demo',
      'display_name': 'Demo',
      'about': {'en': 'Demo.'},
      'urls': {'Docs': 'https://example.org'},
      'correlation': {'key': 'demo:deposit:{tx}', 'fields': {'tx': 'hex'}},
    }
    catalogue = replace(CATALOGUE, protocols={'demo': entry})
    self.assertEqual(validate.protocols(catalogue.protocols, catalogue.platforms), [])
    self.assertEqual(
      catalogue.format_correlation('demo', tx='0xAB'), 'demo:deposit:0xab'
    )
    self.assertEqual(
      catalogue.parse_correlation('demo:deposit:0xab'), ('demo', {'tx': '0xab'})
    )
    with self.assertRaises(CorrelationError):
      catalogue.parse_correlation('demo:withdraw:0xab')


if __name__ == '__main__':
  unittest.main()
