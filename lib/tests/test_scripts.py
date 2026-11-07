"""Run every scripts/test_*.py under CI's `unittest discover -s lib/tests`.

validate.yml names only test_check_new_assets and test_check_id_stability, so
any other scripts test (test_instrument_urls, test_check_hyperliquid_delisted)
never ran in CI. Discovering them here covers every current and future one; the
two named files run twice, which costs about a second.
"""

from pathlib import Path
import unittest

SCRIPTS = Path(__file__).resolve().parents[2] / 'scripts'


def load_tests(loader: unittest.TestLoader, tests: unittest.TestSuite, pattern: str | None):
  """Add the scripts suite; a fresh loader keeps the outer discovery's state intact."""
  tests.addTests(
    unittest.TestLoader().discover(str(SCRIPTS), pattern='test_*.py', top_level_dir=str(SCRIPTS))
  )
  return tests
