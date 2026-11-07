"""Catalogue instruments whose base, quote or settlement asset disagrees with the venue."""

from types import SimpleNamespace
from typing import Any

import check_perp_quotes

from .catalogue import Catalogue, translate
from .finding import Finding, make, market_subject
from .observations import Market, Observations


SETTLEMENT_LABELLED = set(check_perp_quotes.PLATFORMS)
"""Platforms whose perpetuals' venue "quote" is always their settlement coin."""


def labels_settlement(instrument: dict[str, Any], platform: str) -> bool:
  """
  Whether the venue's quote symbol for this perpetual names its settlement, not its price currency.

  A perpetual's catalogue `quote` is the currency its price is in (AGENTS.md, "Quanto
  perpetuals"). A quanto contract is labelled by its margin coin: MEXC's
  `HK0700_USDT`, `HK1810_USDT` and `HK0992_USDT` print HK dollars and settle in USDT,
  and catalogue-ops reported them as base-quote errors in #383 and #387 after #382 had
  set them right. Lighter and Hyperliquid label every perpetual with its USDC
  settlement while the index is USDT or USD (`scripts/check_perp_quotes.py`).

  Args:
    instrument: The catalogue instrument.
    platform: Its platform.
  """
  if instrument['kind'] != 'perp' or instrument.get('quote') == instrument.get('settlement'):
    return False
  return 'quanto' in instrument or platform in SETTLEMENT_LABELLED


def compare(
  instrument: dict[str, Any], market: Market, translations: dict[str, str], platform: str = '',
) -> dict[str, Any] | None:
  """
  What the venue says the instrument's assets are, where that differs from the catalogue.

  The venue's own base, quote and settlement symbols are translated; a symbol with no
  translation is skipped (`untranslated-asset` reports it). A perpetual's venue base
  is also tried without a multiplier prefix. Where the venue's quote symbol names the
  settlement coin (`labels_settlement`), it is compared with the catalogue's
  settlement instead. When the market carries `index_quote` (the asset its index is
  priced in, inferred from index prices), that is compared with the catalogue's quote,
  also where the venue's quote symbol has no translation (Hyperliquid and Lighter
  label their perpetuals `USDC`, which has none).

  Args:
    instrument: The catalogue instrument; carries `kind`.
    market: The venue market.
    translations: The platform's asset translations.
    platform: The catalogue platform.

  Returns:
    `None` when they agree, else the evidence.
  """
  perp = instrument['kind'] == 'perp'
  observed: dict[str, str] = {}
  if (base := translate(translations, market['base'], multiplier=perp)) is not None:
    observed['base'] = base
  if (quote := translate(translations, market['quote'])) is not None:
    observed['quote'] = quote
  if perp and (settlement := translate(translations, market['settlement'])) is not None:
    observed['settlement'] = settlement
  index = market.get('index_quote') if perp else None
  if 'base' not in observed or ('quote' not in observed and not index):
    return None
  listed = {field: instrument.get(field) for field in [*observed, *(['quote'] if 'quote' not in observed else [])]}
  wrong = sorted(field for field in observed if observed[field] != listed[field])
  if 'quote' in wrong and labels_settlement(instrument, platform) and observed['quote'] == instrument.get('settlement'):
    wrong.remove('quote')
  if perp and index and index != instrument.get('quote') and 'quote' not in wrong:
    wrong.append('quote')
  if not wrong:
    return None
  return {
    'fields': wrong,
    'catalogue': listed,
    'venue_translated': observed,
    'venue_symbols': {'base': market['base'], 'quote': market['quote'], 'settlement': market['settlement']},
    'index_quote': index,
  }


def usdc_quotes(catalogue: Catalogue, exceptions: dict[str, str]) -> list[Finding]:
  """
  Lighter and Hyperliquid perpetuals quoted in USDC, their settlement coin.

  The rule of `scripts/check_perp_quotes.py`, with its exceptions file, as findings.

  Args:
    catalogue: The catalogue.
    exceptions: `scripts/perp_quote_exceptions.json`.
  """
  findings = []
  for platform in check_perp_quotes.PLATFORMS:
    for (exchange, id), instrument in sorted(catalogue.instruments.get(platform, {}).items()):
      if instrument['kind'] != 'perp' or instrument.get('quote') != check_perp_quotes.USDC:
        continue
      if f'{platform}:{id}' in exceptions:
        continue
      category = (catalogue.assets.get(instrument.get('base', '')) or {}).get('category')
      want = check_perp_quotes.HINT.get(category or '', 'usd')
      subject = market_subject(exchange, id)
      findings.append(make(
        'base-quote',
        platform=platform,
        subject=subject,
        severity='high',
        summary=f'{platform} {subject}: quoted in {check_perp_quotes.USDC}, its settlement coin; its index is usually {want}',
        evidence={
          'fields': ['quote'],
          'catalogue': {'base': instrument.get('base'), 'quote': instrument.get('quote'), 'settlement': instrument.get('settlement')},
          'rule': 'perp-quote-is-index-currency',
          'usual_quote': want,
        },
      ))
  return findings


def run(catalogue: Catalogue, obs: Observations) -> tuple[list[Finding], dict]:
  """
  `base-quote` over every platform with listings, plus the USDC-quote rule.

  Args:
    catalogue: The catalogue.
    obs: The observations; reads `listings`.
  """
  findings = usdc_quotes(catalogue, check_perp_quotes.load_exceptions())
  seen = {f['fingerprint'] for f in findings}
  ran = set(check_perp_quotes.PLATFORMS)
  for platform, listing in sorted((obs.get('listings') or {}).items()):
    ran.add(platform)
    rows = catalogue.instruments.get(platform, {})
    translations = catalogue.asset_translations.get(platform, {})
    for key, market in sorted(listing['markets'].items()):
      instrument = rows.get(key)
      if instrument is None:
        continue
      evidence = compare(instrument, market, translations, platform)
      if evidence is None:
        continue
      subject = market_subject(*key)
      f = make(
        'base-quote',
        platform=platform,
        subject=subject,
        severity='high',
        summary=(
          f'{platform} {subject}: catalogue says {"/".join(str(v) for v in evidence["catalogue"].values())}, '
          f'venue says {"/".join(evidence["venue_translated"].values())}'
          + (f' (index in {evidence["index_quote"]})' if evidence['index_quote'] else '')
        ),
        evidence=evidence,
      )
      if f['fingerprint'] not in seen:
        findings.append(f)
  return findings, {'base-quote': {'ran': sorted(ran), 'skip': {}}}


GROUP = SimpleNamespace(NAMES=('base-quote',), INPUTS=(), run=run)
GROUPS = [GROUP]
