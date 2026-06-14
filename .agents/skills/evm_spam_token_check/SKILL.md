---
name: EVM Spam Token Check
description: Investigate whether an EVM contract address on a specified network is a spam, scam, phishing, honeypot, or suspicious token/NFT using web search, block explorers, reputation APIs, and direct RPC calls. Use when given a chain/network and token or NFT contract address and asked to classify risk with evidence.
---

# EVM Spam Token Check

## Goal

Given an EVM network and contract address, determine whether the asset is clearly spam/scam, potentially suspicious, likely legitimate, or unknown. Produce an evidence-first report with links, raw facts, and a concise verdict.

Do not assume the address is an ERC-20. First determine whether it is ERC-20, ERC-721, ERC-1155, proxy, non-token contract, or EOA.

## Inputs

Required:
- Network or chain ID
- Contract address

Optional:
- Wallet address that received the token
- User context, such as "this showed up in my wallet" or "I am considering trading it"

## Investigation Workflow

1. Normalize the network and address.
   - Map common names to chain IDs and explorers, for example Ethereum `1`, Optimism `10`, Base `8453`, Arbitrum One `42161`, Polygon `137`, BSC `56`.
   - Validate checksum format when possible, but do not reject solely for mixed/lowercase input.

2. Establish contract basics.
   - Use RPC `eth_getCode`; if code is `0x`, report `not_contract`.
   - Check explorer pages and APIs for contract type, creator, creation transaction, verification status, proxy status, labels, public tags, token type, holder count, and token transfers.
   - Prefer official explorers, Blockscout-compatible APIs, and chain-specific explorer APIs when available.

3. Identify token standard.
   - ERC-20 signals: `name()`, `symbol()`, `decimals()`, `totalSupply()`, `balanceOf(address)`, `transfer(address,uint256)`.
   - ERC-721 signals: `ownerOf(uint256)`, `tokenURI(uint256)`, ERC-165 interface `0x80ac58cd`.
   - ERC-1155 signals: `uri(uint256)`, `balanceOf(address,uint256)`, `safeTransferFrom(address,address,uint256,uint256,bytes)`, ERC-165 interface `0xd9b67a26`.
   - If selectors or calls conflict, report the ambiguity.

4. Pull metadata and embedded URLs.
   - For ERC-20: read `name`, `symbol`, `decimals`, `totalSupply`.
   - For ERC-721/ERC-1155: read `tokenURI` or `uri` for representative IDs when discoverable from transfers or explorer metadata.
   - Inspect metadata URLs, image URLs, external URLs, and domains.
   - Treat dead domains, claim/allocation domains, wallet-drainer-looking domains, and brand-mismatched domains as strong suspicious signals.
   - Do not visit interactive dApp pages with a wallet. Fetch metadata only with safe HTTP requests.

5. Check trading and liquidity for fungible tokens.
   - Query DexScreener, GeckoTerminal, or DEX/router/pair contracts.
   - Record whether pairs exist, liquidity depth, pair age, volume, buys/sells, and token price.
   - No DEX pair is suspicious for a tradeable ERC-20, but neutral for NFTs or non-tradeable contracts.

6. Check public reputation.
   - Search for the exact address, creator address, metadata domain, token name, symbol, and "`address scam`".
   - Query available reputation/security APIs, such as GoPlus, Honeypot.is, TokenSniffer-like pages, explorer labels, and known token lists.
   - Absence from reputation APIs is not proof of safety.

7. Check source and privileged controls.
   - If verified, scan source/ABI for owner-only or role-only controls:
     `mint`, `burnFrom`, `blacklist`, `whitelist`, `setTax`, `setFee`, `setFees`, `pause`, `setTradingEnabled`, `setMaxTx`, `setMaxWallet`, `excludeFromFee`, `setRouter`, `setPair`, `withdraw`, `rescueTokens`, `upgradeTo`.
   - For proxies, inspect implementation and admin/owner.
   - If unverified, report that static safety cannot be established.

8. Check distribution behavior.
   - Look for batch mints, mass airdrops, many one-way transfers, holder concentration, and creator-held supply.
   - For NFTs, brand impersonation plus airdrop behavior is a major red flag.
   - For ERC-20s, concentrated supply, unlocked LP, and fresh deployer are suspicious.

## Verdicts

Use one of:

- `clear_spam`: Strong evidence of phishing, impersonation, honeypot behavior, malicious controls, scam labels, dead claim domains, or mass airdrop spam.
- `potential_spam`: Meaningful risk signals but not enough to prove maliciousness.
- `unknown`: Insufficient data; no strong positive or negative evidence.
- `probably_ok`: Positive evidence of legitimacy and no material red flags.

Prefer caution. Only use `probably_ok` when there is affirmative support, such as known token lists, verified source, reputable project association, healthy trading/liquidity, and no major reputation warnings.

## Strong Signals

Classify as `clear_spam` when several of these appear together, or one is decisive:
- Known scam/phishing label from explorer or reputation API.
- Honeypot or cannot-sell result from a reputable API.
- Metadata links to a claim, allocation, reward, airdrop, or wallet-connect style domain unrelated to the apparent brand.
- Metadata impersonates a known project, NFT collection, stablecoin, exchange, or airdrop.
- Dead or newly created metadata domain used for claimed rewards or admissions.
- Unverified NFT contract that mass-airdrops branded-looking items.
- Contract source shows owner can block transfers, seize balances, or arbitrarily trap holders.

Classify as `potential_spam` when these appear without decisive evidence:
- Unverified contract.
- Unknown proxy implementation/admin.
- Owner can mint, pause, blacklist, or change fees.
- Tiny or no liquidity for a supposedly tradeable ERC-20.
- Extreme holder concentration or creator-held supply.
- Fresh deployer with many similar deployments.
- No public footprint for a token that claims to be official.

## Output Format

Return a concise report:

```text
Verdict: clear_spam | potential_spam | unknown | probably_ok
Asset type: ERC-20 | ERC-721 | ERC-1155 | proxy | non-token contract | EOA | unknown
Network: <network name / chain ID>
Address: <address>

Key evidence:
- <fact with source/link>
- <fact with source/link>
- <fact with source/link>

Reasoning:
<short paragraph explaining why the evidence supports the verdict>

Sources:
- <explorer link>
- <transaction link>
- <DEX/reputation/search links used>
```

Include raw values when useful:
- Creator/owner address
- Creation transaction
- Verification/proxy status
- Token name/symbol/decimals/supply
- Metadata URI/domain
- DEX pair/liquidity result
- Holder count or notable transfer pattern

## Quality Bar

- Cite links for claims from web/explorer pages.
- Separate facts from inference.
- Say what could not be checked.
- Do not overstate safety from missing data.
- Warn the user not to interact with suspicious domains or grant approvals when phishing or airdrop spam is likely.
