import { codeToHtml } from 'shiki';

const INSTALL = `pip install tribulnation-catalogue`;

const QUICKSTART = `\
from tribulnation.catalogue import Catalogue, MarketData

catalogue = Catalogue.load()
sdk = MarketData.new('usd', 'coingecko', 'twelvedata')

btc  = catalogue.assets['bitcoin']
gold = catalogue.assets['gold']

price     = await sdk.current_price(btc)    # via CoinGecko
xau_price = await sdk.current_price(gold)   # via Twelve Data
mc        = await sdk.market_cap(btc)       # market cap in USD
hist      = await sdk.historical_price(btc, datetime(2024, 1, 1))`;

const RETRY = `sdk = MarketData.new('usd', 'coingecko', max_retries=3, base_delay=2.0)`;

const LOGGER = `sdk = MarketData.new('usd', 'coingecko', logger=None)`;

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
			retry: await h(RETRY, 'python'),
			logger: await h(LOGGER, 'python'),
			externalIds: await h(EXTERNAL_IDS, 'jsonc')
		}
	};
}
