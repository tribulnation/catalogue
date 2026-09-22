# External provider coverage audit — 2026-09-22

This pass adds 314 verified CoinGecko IDs and 306 verified CoinMarketCap IDs to this branch. Coverage is now 978 CoinGecko and 998 CoinMarketCap asset records.

`centrifuge-2` is renamed to the canonical `centrifuge`; CoinGecko's provider ID remains `centrifuge-2`. The legacy Omni Network record now uses CoinGecko `omni-network` because `omni-2` currently identifies an unrelated Solana token.

Matches require an exact contract or project identity corroborated by issuer domains. Ticker equality alone is not accepted. Distinct wrappers, bridge claims and receipt versions remain separate. The companion JSON records applied evidence and unresolved provider gaps.
