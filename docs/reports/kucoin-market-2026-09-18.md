# KuCoin public Market identity audit, 2026-09-18

The SDK public Market candidate uses exact exchange IDs `spot` and `perp`.
All 183 existing perpetual records now explicitly identify `exchange: perp`.
Native symbols, canonical assets and lifecycle metadata are unchanged.
This repairs exact joins; it does not qualify every Catalogue instrument for
SDK discovery. SDK scope is enabled spot and open linear perpetuals only.

Current public `/api/v2/symbols` and futures `/api/v1/contracts/active` observations:

- `ETHUSDM`, `SOLUSDM`, `XBTUSDM`, `XRPUSDM` are open inverse contracts;
  they remain outside the SDK's linear scope.
- `XBTMU26` is inverse and dated (`expireDate=1790323200000`), also excluded.
  Its existing placement in the perpetual file remains a separate schema/data review.
- `DOGEUSDCM`, `DOGEUSDM`, `DOTUSDM`, `PEPEUSDCM`, `SUIUSDM` were absent
  from the active futures listing.
- `ANKR-BTC`, `AR-BTC`, `BMX-USDT`, `CRO-BTC`, `IOST-ETH`, `MANA-ETH`,
  `SNX-ETH`, `TRAC-ETH`, `XDC-BTC` were absent from the spot listing.

Absence from current discovery does not establish delisting. These records retain
their existing lifecycle metadata and URLs pending individual lifecycle evidence.

The SDK probe also found 689 active spot IDs and 505 supported linear perpetual
IDs without Catalogue records. Exhaustive coverage is not claimed. BTC and ETH
references (`BTC-USDT`, `ETH-USDT`, `XBTUSDTM`, `ETHUSDTM`) already have canonical
mappings, so no new asset identities are needed for the initial qualification.
Unknown instruments must remain explicit mapping misses in Terminal.

Validation: Catalogue validation passed; the SDK candidate's strict KuCoin
consistency run against this data passed the existing coverage policy, including
exact exchange identities. Excluded/absent contracts remain deferred coverage,
not passed discovery checks. Related: https://github.com/tribulnation/sdk/issues/33.
