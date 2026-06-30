import { codeToHtml } from 'shiki';

const INSTALL = `pip install tribulnation-catalogue`;

const QUICKSTART = `\
from tribulnation.catalogue import Catalogue, MarketData

catalogue = Catalogue.load()
sdk = MarketData.new('coingecko', 'twelvedata', quote='usd')

# Fetch all assets in one batched call
stats, errors = await sdk.current_stats(catalogue.assets)

btc = stats.get('bitcoin')  # Stats(price=Decimal('...'), market_cap=Decimal('...'))
xau = stats.get('gold')     # Stats(price=Decimal('...')) — via Twelve Data

# Historical price for a single asset
price, errors = await sdk.historical_price(catalogue.assets['bitcoin'], datetime(2024, 1, 1))`;

const EXTERNAL_IDS = `\
# data/assets/bitcoin.json
{ "external": { "coingecko": "bitcoin", "coinmarketcap": "1" } }

# data/assets/gold.json
{ "external": { "twelvedata": "XAU/USD" } }

# data/assets/west-texas-intermediate.json
{ "external": { "alphavantage": "WTI" } }`;

async function h(code: string, lang: string) {
	return { code, html: await codeToHtml(code, { lang, theme: 'github-dark' }) };
}

export async function load() {
	return {
		blocks: {
			install: await h(INSTALL, 'bash'),
			quickstart: await h(QUICKSTART, 'python'),
			externalIds: await h(EXTERNAL_IDS, 'jsonc')
		}
	};
}
