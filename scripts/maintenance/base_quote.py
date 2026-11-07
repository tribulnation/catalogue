"""Catalogue instruments whose base, quote or settlement asset disagrees with the venue."""

from types import SimpleNamespace
from typing import Any

import check_perp_quotes

from .catalogue import Catalogue, translate
from .finding import Finding, make, market_subject
from .observations import Market, Observations


def compare(instrument: dict[str, Any], market: Market, translations: dict[str, str]) -> dict[str, Any] | None:
  """
  What the venue says the instrument's assets are, where that differs from the catalogue.

  The venue's own base, quote and settlement symbols are translated; a symbol with no
  translation is skipped (`untranslated-asset` reports it). A perpetual's venue base
  is also tried without a multiplier prefix. When the market carries `index_quote`
  (the asset its index is priced in, inferred from index prices), that is compared
  with the catalogue's quote too.

  Args:
    instrument: The catalogue instrument; carries `kind`.
    market: The venue market.
    translations: The platform's asset translations.

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
  if 'base' not in observed or 'quote' not in observed:
    return None
  listed = {field: instrument.get(field) for field in observed}
  wrong = sorted(field for field in observed if observed[field] != listed[field])
  index = market.get('index_quote')
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
      evidence = compare(instrument, market, translations)
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
