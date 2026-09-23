# Blockchain category and CAIP-2 audit — 2026-09-23

Proposal only; no platform record is changed on this branch. 184 of 213
blockchain records lack `category`, `namespace` or `chain_id`. Every one was
researched; the companion JSON carries the per-record evidence.

## Method

- `namespace:chain_id` must be the exact [CAIP-2](https://github.com/ChainAgnostic/CAIPs/blob/main/CAIPs/caip-2.md)
  chain id, derived per that namespace's rules in
  [ChainAgnostic/namespaces](https://github.com/ChainAgnostic/namespaces).
- Registries (chainid.network, cosmos/chain-registry) were used to find
  candidates only. Each reference was then read back from the live chain:
  `eth_chainId`, Cosmos `node_info.network`, Substrate
  `chain_getBlockHash(0)`, Solana `getGenesisHash`, explorer block 0, etc.
- Which layer a record represents was decided from its description and from the
  exchange network codes that map to it in `data/network_translations`.
  Hybrid chains keep the side exchanges use; the other side would be a separate
  record, as with `kava` / `kava-evm`.

## Corrections to existing values

| Platform | Current | Proposed | Why |
|---|---|---|---|
| solana | `solana:mainnet-beta` | `solana:5eykt4UsFv8P8NJdTREpY1vzqKqZKvdp` | The solana namespace uses the first 32 chars of the genesis hash; `getGenesisHash` confirms it. |
| kava | `cosmos:kava_2222-10` | `cosmos:hashed-6d4e837e169119f0` | `_` is outside `[-a-zA-Z0-9]{1,32}`, so the chain id must be hashed: `sha256("kava_2222-10")[:16]`. |

The other nine existing values (bitcoin, bitcoin-cash, dogecoin, litecoin,
celestia, cosmos, injective, sei, kava-evm) were re-checked and are correct.

## Proposed categories

`category` should keep meaning "how the chain's tokens and accounts are
addressed", since that is what validation keys on. Counts include records that
already carry the field.

| Category | Records | Translation keys look like | Possible validation |
|---|---|---|---|
| `evm` (existing) | 85 | EIP-55 `0x` address | already enforced |
| `cosmos-sdk` | 26 | bank denom: `uatom`, `ibc/<hash>`, `factory/…` | denom regex |
| `substrate` | 25 | numeric asset id or `native` | integer keys |
| `utxo` | 21 | `native` (plus colored-coin ids on some) | only `native` unless allow-listed |
| `move` | 6 | type tag `0x…::module::COIN` or object id | type-tag regex |
| `antelope` | 4 | `<contract>:<SYMBOL>` account names | name regex |
| `svm` | 3 | base58 mint address | base58, 32-byte |

Three members is the bar used here; smaller families (stellar/pi-network,
cryptonote) stay uncategorised. `move` mixes Aptos-style accounts and
Sui-style objects; both use `0x…::m::T` type tags, so one category holds.

Deliberately **not** `evm`: `tron` (base58 `T…` addresses), `quai` (shard-encoded
addresses), `vechain` (0x addresses but no eip155 id and its own tx format),
`conflux-core` (`cfx:` addresses; `conflux-espace` is the EVM side).

## Proposed namespaces

Extend `BlockchainNamespace` with every ChainAgnostic namespace used below:
`polkadot` (25 records), `antelope` (4), `aptos` (2), and one each of
`algorand`, `aleo`, `arweave`, `avax`, `casper`, `ccd`, `conflux`,
`ergo`, `fil`, `flow`, `hedera`, `iota`, `klv`, `mina`, `monero`, `mvx`, `neo`,
`partisia`, `quai`, `stacks`, `starknet`, `stellar`, `sui`, `tezos`, `tron`, `tvm`,
`vechain`, `waves`, `xrpl`.

Traps found on the way:

- Avalanche's namespace is `avax` and TON's is `tvm` (`tvm:-239`), not the
  folder or chain name.
- Waves references are zero-padded (`waves:087`).
- Chains that share Bitcoin's genesis use their first post-fork block, as the
  bip122 spec does for Bitcoin Cash (eCash: block 661648).
- SVM and Aptos-stack forks reuse the parent namespace with their own
  reference: `solana:<genesis>` for eclipse and fogo, `aptos:126` for movement.
  The specs list only the parent's networks, so this is an interpretation.
- `chain_id` stays an int only for `eip155`; every other reference is a string.

## Proposed values

154 records get a namespace and chain id verified against the live chain;
6 more get only a category. Records that picked one side of a hybrid chain
are listed under [Hybrid records](#hybrid-records).

### evm (56)

| Platform | CAIP-2 | Conf. | Verified by |
|---|---|---|---|
| ab | `eip155:36888` | high | rpc.core.ab.org eth_chainId -> 0x9018 (36888) |
| adi | `eip155:36900` | high | rpc.adifoundation.ai eth_chainId -> 0x9024 (36900) |
| arbitrum-nova | `eip155:42170` | high | nova.arbitrum.io/rpc eth_chainId -> 0xa4ba (42170) |
| arc | `eip155:5042` | high | rpc.mainnet.arc.io eth_chainId -> 0x13b2 (5042) |
| bitgert | `eip155:32520` | high | rpc-bitgert.icecreamswap.com eth_chainId -> 0x7f08 (32520) |
| bitlayer | `eip155:200901` | high | rpc.bitlayer.org eth_chainId -> 0x310c5 (200901) |
| camp-network | `eip155:484` | high | camp.cloud.blockscout.com/api/eth-rpc and 484.rpc.thirdweb.com eth_ch… |
| chiliz | `eip155:88888` | high | rpc.chiliz.com eth_chainId -> 0x15b38 (88888) |
| citrea | `eip155:4114` | high | rpc.mainnet.citrea.xyz eth_chainId -> 0x1012 (4114) |
| codex | `eip155:81224` | high | rpc.codex.xyz eth_chainId -> 0x13d48 (81224) |
| conflux-espace | `eip155:1030` | high | evm.confluxrpc.com eth_chainId -> 0x406 (1030) |
| core | `eip155:1116` | high | rpc.coredao.org eth_chainId -> 0x45c (1116) |
| electroneum | `eip155:52014` | high | rpc.electroneum.com eth_chainId -> 0xcb2e (52014) |
| ethereum-classic | `eip155:61` | high | etc.etcdesktop.com eth_chainId -> 0x3d (61) |
| ethereum-pow | `eip155:10001` | high | mainnet.ethereumpow.org eth_chainId -> 0x2711 (10001) |
| etherlink | `eip155:42793` | high | node.mainnet.etherlink.com eth_chainId -> 0xa729 (42793) |
| flare | `eip155:14` | high | flare-api.flare.network/ext/C/rpc eth_chainId -> 0xe (14) |
| fluent | `eip155:25363` | high | rpc.fluent.xyz eth_chainId -> 0x6313 (25363) |
| gensyn | `eip155:685689` | high | gensyn-mainnet.g.alchemy.com/public eth_chainId -> 0xa7679 (685689) |
| hashkey | `eip155:177` | high | mainnet.hsk.xyz eth_chainId -> 0xb1 (177) |
| hpp | `eip155:190415` | high | mainnet.hpp.io eth_chainId -> 0x2e7cf (190415) |
| immutable-zkevm | `eip155:13371` | high | rpc.immutable.com eth_chainId -> 0x343b (13371) |
| ink | `eip155:57073` | high | rpc-gel.inkonchain.com eth_chainId -> 0xdef1 (57073) |
| iotex | `eip155:4689` | high | babel-api.mainnet.iotex.io eth_chainId -> 0x1251 (4689) |
| katana | `eip155:747474` | high | rpc.katana.network eth_chainId -> 0xb67d2 (747474) |
| konet | `eip155:17217` | high | api.kon-wallet.com eth_chainId -> 0x4341 (17217) |
| lukso | `eip155:42` | high | rpc.mainnet.lukso.network eth_chainId -> 0x2a (42) |
| lumia | `eip155:994873017` | high | mainnet-rpc.lumia.org eth_chainId -> 0x3b4c8eb9 (994873017) |
| megaeth | `eip155:4326` | high | mainnet.megaeth.com/rpc eth_chainId -> 0x10e6 (4326) |
| merlin | `eip155:4200` | high | rpc.merlinchain.io eth_chainId -> 0x1068 (4200) |
| metis | `eip155:1088` | high | andromeda.metis.io eth_chainId -> 0x440 (1088) |
| mezo | `eip155:31612` | high | mezo-mainnet.boar.network eth_chainId -> 0x7b7c (31612) |
| neo-x | `eip155:47763` | high | mainnet-1.rpc.banelabs.org eth_chainId -> 0xba93 (47763) |
| numbers | `eip155:10507` | high | mainnetrpc.num.network eth_chainId -> 0x290b (10507) |
| oasys | `eip155:248` | high | rpc.mainnet.oasys.games eth_chainId -> 0xf8 (248) |
| peaq | `eip155:3338` | medium | quicknode1.peaq.xyz eth_chainId -> 0xd0a (3338); substrate side: chai… |
| pharos | `eip155:1672` | high | rpc.pharos.xyz eth_chainId -> 0x688 (1672) |
| plume | `eip155:98866` | high | rpc.plume.org eth_chainId -> 0x18232 (98866) |
| robinhood-chain | `eip155:4663` | high | rpc.mainnet.chain.robinhood.com eth_chainId -> 0x1237 (4663) |
| shape | `eip155:360` | high | mainnet.shape.network eth_chainId -> 0x168 (360) |
| shardeum | `eip155:8118` | high | api.shardeum.org eth_chainId -> 0x1fb6 (8118) |
| somnia | `eip155:5031` | high | api.infra.mainnet.somnia.network eth_chainId -> 0x13a7 (5031) |
| songbird | `eip155:19` | high | songbird-api.flare.network/ext/C/rpc eth_chainId -> 0x13 (19) |
| stable | `eip155:988` | high | rpc.stable.xyz eth_chainId -> 0x3dc (988) |
| story | `eip155:1514` | high | mainnet.storyrpc.io eth_chainId -> 0x5ea (1514) |
| telos-evm | `eip155:40` | high | rpc.telos.net eth_chainId -> 0x28 (40) |
| theta | `eip155:361` | medium | eth-rpc-api.thetatoken.org/rpc eth_chainId -> 0x169 (361) |
| unichain | `eip155:130` | high | mainnet.unichain.org eth_chainId -> 0x82 (130) |
| viction | `eip155:88` | high | rpc.viction.xyz eth_chainId -> 0x58 (88) |
| wanchain | `eip155:888` | high | 888.rpc.thirdweb.com eth_chainId -> 0x378 (888) |
| wemix | `eip155:1111` | high | api.wemix.com eth_chainId -> 0x457 (1111) |
| x-layer | `eip155:196` | high | rpc.xlayer.tech eth_chainId -> 0xc4 (196) |
| xai | `eip155:660279` | high | xai-chain.net/rpc eth_chainId -> 0xa1337 (660279) |
| zero-gravity | `eip155:16661` | high | evmrpc.0g.ai eth_chainId -> 0x4115 (16661) |
| zetachain | `eip155:7000` | medium | zetachain-evm.blockpi.network eth_chainId -> 0x1b58 (7000); cosmos si… |
| zircuit | `eip155:48900` | high | mainnet.zircuit.com eth_chainId -> 0xbf04 (48900) |

### cosmos-sdk (26)

| Platform | CAIP-2 | Conf. | Verified by |
|---|---|---|---|
| akash | `cosmos:akashnet-2` | high | https://akash.rpc.uquad.org:443 GET /cosmos/base/tendermint/v1beta1/n… |
| axelar | `cosmos:axelar-dojo-1` | high | https://axelar-lcd.qubelabs.io:443 GET /cosmos/base/tendermint/v1beta… |
| babylon | `cosmos:bbn-1` | high | https://babylon-api.polkachu.com GET /cosmos/base/tendermint/v1beta1/… |
| band | `cosmos:laozi-mainnet` | high | https://laozi1.bandchain.org/api GET /cosmos/base/tendermint/v1beta1/… |
| celestia | `cosmos:celestia` | high | https://celestia.rpc.uquad.org:443 GET /cosmos/base/tendermint/v1beta… |
| coreum | `cosmos:coreum-mainnet-1` | high | https://rest-01.mainnet-1.tx.org GET /cosmos/base/tendermint/v1beta1/… |
| cosmos | `cosmos:cosmoshub-4` | high | https://rest.cosmoshub-main.ccvalidators.com:443 GET /cosmos/base/ten… |
| dymension | `cosmos:hashed-36eafc7f1029ed04` | high | https://api.dymension.nodestake.org GET /cosmos/base/tendermint/v1bet… |
| fetch-ai | `cosmos:fetchhub-4` | high | https://rest-fetchhub.fetch.ai GET /cosmos/base/tendermint/v1beta1/no… |
| initia | `cosmos:interwoven-1` | high | https://rest.initia.xyz GET /cosmos/base/tendermint/v1beta1/node_info… |
| injective | `cosmos:injective-1` | high | https://injective-api.highstakes.ch GET /cosmos/base/tendermint/v1bet… |
| kava | `cosmos:hashed-6d4e837e169119f0` | high | https://api.data.kava.io GET /cosmos/base/tendermint/v1beta1/node_inf… |
| mantra | `cosmos:mantra-1` | high | https://api.mantrachain.io GET /cosmos/base/tendermint/v1beta1/node_i… |
| neutron | `cosmos:neutron-1` | high | https://rest.neutron.solva.solutions:443 GET /cosmos/base/tendermint/… |
| nibiru | `cosmos:cataclysm-1` | high | https://lcd.nibiru.fi GET /cosmos/base/tendermint/v1beta1/node_info -… |
| noble | `cosmos:noble-1` | high | https://noble-api.polkachu.com GET /cosmos/base/tendermint/v1beta1/no… |
| oraichain | `cosmos:Oraichain` | high | http://lcd.orai.io GET /cosmos/base/tendermint/v1beta1/node_info -> d… |
| osmosis | `cosmos:osmosis-1` | high | https://lcd.osmosis.zone GET /cosmos/base/tendermint/v1beta1/node_inf… |
| persistence | `cosmos:core-1` | high | https://rest.core.persistence.one GET /cosmos/base/tendermint/v1beta1… |
| saga | `cosmos:ssc-1` | high | https://saga-rest.publicnode.com GET /cosmos/base/tendermint/v1beta1/… |
| secret | `cosmos:secret-4` | high | https://rest.lavenderfive.com:443/secretnetwork GET /cosmos/base/tend… |
| sei | `cosmos:pacific-1` | high | https://rest.sei-apis.com GET /cosmos/base/tendermint/v1beta1/node_in… |
| terra | `cosmos:phoenix-1` | high | https://terra-rest.publicnode.com GET /cosmos/base/tendermint/v1beta1… |
| terra-classic | `cosmos:columbus-5` | high | https://terra-classic-lcd.publicnode.com GET /cosmos/base/tendermint/… |
| thorchain | `cosmos:thorchain-1` | high | https://gateway.liquify.com/chain/thorchain_api GET /cosmos/base/tend… |
| zigchain | `cosmos:zigchain-1` | high | https://public-zigchain-lcd.numia.xyz GET /cosmos/base/tendermint/v1b… |

### substrate (22)

| Platform | CAIP-2 | Conf. | Verified by |
|---|---|---|---|
| acala | `polkadot:fc41b9bd8ef8fe53d58c7ea67c794c7e` | high | acala-rpc-0.aca-api.network chain_getBlockHash[0] -> 0xfc41b9bd8ef8fe… |
| aleph-zero | `polkadot:70255b4d28de0fc4e1a193d7e175ad1c` | high | ws.azero.dev chain_getBlockHash[0] -> 0x70255b4d28de0fc4e1a193d7e175a… |
| astar | `polkadot:9eb76c5184c4ab8679d2d5d819fdf90b` | medium | rpc.astar.network + astar.api.onfinality.io chain_getBlockHash[0] -> … |
| autonomys | `polkadot:66455a580aabff303720aa83adbe6c44` | high | rpc-0.mainnet.autonomys.xyz chain_getBlockHash[0] -> 0x66455a580aabff… |
| avail | `polkadot:b91746b45e0346cc2f815a520b9c6cb4` | high | mainnet-rpc.avail.so/rpc chain_getBlockHash[0] -> 0xb91746b45e0346cc2… |
| aventus | `polkadot:8b5c955b5c8fd7112562327e3859473d` | high | avn-parachain.mainnet.aventus.io and public-rpc.mainnet.aventus.io ch… |
| bifrost-kusama | `polkadot:9f28c6a68e0fc9646eff64935684f6ee` | high | bifrost-rpc.liebi.com chain_getBlockHash[0] -> 0x9f28c6a68e0fc9646eff… |
| bittensor | `polkadot:2f0555cc76fc2840a25a6ea3b9637146` | high | entrypoint-finney.opentensor.ai chain_getBlockHash[0] -> 0x2f0555cc76… |
| enjin | `polkadot:3af4ff48ec76d2efc8476730f423ac07` | medium | rpc.matrix.blockchain.enjin.io chain_getBlockHash[0] -> 0x3af4ff48ec7… |
| enjin-relaychain | `polkadot:d8761d3c88f26dc12875c00d3165f7d6` | high | rpc.relay.blockchain.enjin.io chain_getBlockHash[0] -> 0xd8761d3c88f2… |
| humanode | `polkadot:c56fa32442b2dad76f214b3ae07998e4` | medium | explorer-rpc-http.mainnet.stages.humanode.io chain_getBlockHash[0] ->… |
| hydration | `polkadot:afdc188f45c71dacbaa0b62e16a91f72` | high | rpc.hydradx.cloud chain_getBlockHash[0] -> 0xafdc188f45c71dacbaa0b62e… |
| kusama | `polkadot:b0a8d493285c2df73290dfb7e61f870f` | high | kusama-rpc.publicnode.com chain_getBlockHash[0] -> 0xb0a8d493285c2df7… |
| kusama-asset-hub | `polkadot:48239ef607d7928874027a43a6768920` | high | kusama-asset-hub-rpc.polkadot.io chain_getBlockHash[0] -> 0x48239ef60… |
| litentry | `polkadot:2fc8bb6ed7c0051bdcf4866c322ed32b` | high | rpc.litentry-parachain.litentry.io chain_getBlockHash[0] -> 0x2fc8bb6… |
| origintrail | `polkadot:e7e0962324a3b86c83404dbea483f25f` | medium | astrosat-parachain-rpc.origin-trail.network chain_getBlockHash[0] -> … |
| polkadot | `polkadot:91b171bb158e2d3848fa23a9f1c25182` | high | polkadot-rpc.publicnode.com chain_getBlockHash[0] -> 0x91b171bb158e2d… |
| polkadot-asset-hub | `polkadot:68d56f15f85d3136970ec16946040bc1` | high | polkadot-asset-hub-rpc.polkadot.io chain_getBlockHash[0] -> 0x68d56f1… |
| polymesh | `polkadot:6fbd74e5e1d0a61d52ccfe9d4adaed16` | high | mainnet-rpc.polymesh.network chain_getBlockHash[0] -> 0x6fbd74e5e1d0a… |
| robonomics | `polkadot:631ccc82a078481584041656af292834` | medium | kusama.rpc.robonomics.network chain_getBlockHash[0] -> 0x631ccc82a078… |
| shiden | `polkadot:f1cf9022c7ebb34b162d5b5e34e705a5` | medium | rpc.shiden.astar.network chain_getBlockHash[0] -> 0xf1cf9022c7ebb34b1… |
| zkverify | `polkadot:060e3dd3fa2904d031206bb913c95468` | high | zkverify-rpc.zkverify.io chain_getBlockHash[0] -> 0x060e3dd3fa2904d03… |

### utxo (20)

| Platform | CAIP-2 | Conf. | Verified by |
|---|---|---|---|
| avalanche-x-chain | `avax:imji8papUf2EhV3le337w1vgFauqkJg-` | high | api.avax.network/ext/info info.getBlockchainID(alias X) -> 2oYMBNV4eN… |
| bitcoin | `bip122:000000000019d6689c085ae165831e93` | high | mempool.space /api/block-height/0 and api.blockcypher.com/v1/btc/main… |
| bitcoin-cash | `bip122:000000000000000000651ef99cb9fcbe` | high | bchblockexplorer.com blockbook /api/v2/block-index/478559 and api.blo… |
| cardano | — | high | unverified for CAIP: no namespace in ChainAgnostic repo. Live api.koi… |
| dash | `bip122:00000ffd590b1485b3caadc19b22e637` | high | api.blockcypher.com/v1/dash/main/blocks/0 -> 00000ffd590b1485b3caadc1… |
| decred | `bip122:298e5cc3d985bfe7f81dc135f360abe0` | medium | dcrdata.decred.org /api/block/0/hash -> 298e5cc3d985bfe7f81dc135f360a… |
| digibyte | `bip122:7497ea1b465eb39f1c8f507bc877078f` | high | digiexplorer.info /api/block-height/0 -> 7497ea1b465eb39f1c8f507bc877… |
| dogecoin | `bip122:1a91e3dace36e2be3bf030a65679fe82` | high | api.blockcypher.com/v1/doge/main/blocks/0 -> 1a91e3dace36e2be3bf030a6… |
| ecash | `bip122:000000000000000004284c9d8b2c8ff7` | medium | chronik.e.cash /block/661648 (protobuf; decoded hash, height=661648) … |
| elastos | — | high | api.elastos.io/ela getblockhash 0 -> 05f458a5522851622cae2bb138498dec… |
| ergo | `ergo:b0244dfc267baca974a4caee06120321` | high | node.ergo.watch /info -> genesisBlockId b0244dfc267baca974a4caee06120… |
| flux | `bip122:00052461a5006c2e3b74ce48992a0869` | high | explorer.runonflux.io /api/block-index/0 -> 00052461a5006c2e3b74ce489… |
| hathor | — | high | node1.mainnet.hathor.network /v1a/version -> network 'mainnet' |
| kaspa | — | high | api.kaspa.org /info/blockdag -> networkName 'kaspa-mainnet' (no genes… |
| litecoin | `bip122:12a765e31ffd4059bada1e25190f6e98` | high | litecoinspace.org /api/block-height/0 and api.blockcypher.com/v1/ltc/… |
| pepecoin | `bip122:37981c0c48b8d48965376c8a42ece9a0` | medium | pepeblocks.com blockbook /api/v2/block-index/0 -> 37981c0c48b8d489653… |
| qtum | `bip122:000075aef83cf2853580f8ae8ce6f8c3` | medium | qtum.info /api/block/0 -> 000075aef83cf2853580f8ae8ce6f8c3096cfa21d98… |
| ravencoin | `bip122:0000006b444bc2f2ffe627be9d9e7e7a` | high | blockbook.ravencoin.org /api/v2/block-index/0 -> 0000006b444bc2f2ffe6… |
| siacoin | — | high | api.siascan.com /consensus/network -> name 'mainnet'; /consensus/tip/… |
| zcash | `bip122:00040fe8ec8471911baa1db1266ea15d` | high | api.blockchair.com/zcash/raw/block/0 raw header double-SHA256 compute… |

### move (5)

| Platform | CAIP-2 | Conf. | Verified by |
|---|---|---|---|
| aptos | `aptos:1` | high | fullnode.mainnet.aptoslabs.com GET /v1 -> chain_id 1 |
| iota | `iota:mainnet` | high | api.mainnet.iota.cafe iota_getChainIdentifier -> 6364aad5 (spec's iot… |
| movement | `aptos:126` | medium | mainnet.movementnetwork.xyz GET /v1 -> chain_id 126 (Aptos-compatible… |
| sui | `sui:mainnet` | high | graphql.mainnet.sui.io {chainIdentifier} -> 4btiuiMPvEENsttpZC7CZ53Dr… |
| supra | — | medium | rpc-mainnet.supra.com /rpc/v1/transactions/chain_id -> 8 (information… |

### svm (3)

| Platform | CAIP-2 | Conf. | Verified by |
|---|---|---|---|
| eclipse | `solana:EAQLJCV2mh23BsK2P9oYpV5CHVLDNHTx` | medium | mainnetbeta-rpc.eclipse.xyz getGenesisHash -> EAQLJCV2mh23BsK2P9oYpV5… |
| fogo | `solana:CDLtwKnaCoK157uaHQDj4fHu72AyD251` | medium | mainnet.fogo.io getGenesisHash -> CDLtwKnaCoK157uaHQDj4fHu72AyD2519Cp… |
| solana | `solana:5eykt4UsFv8P8NJdTREpY1vzqKqZKvdp` | high | api.mainnet-beta.solana.com getGenesisHash -> 5eykt4UsFv8P8NJdTREpY1v… |

### antelope (4)

| Platform | CAIP-2 | Conf. | Verified by |
|---|---|---|---|
| telos | `antelope:4667b205c6838ef70ff7988f6e8257e8` | high | telos.greymass.com /v1/chain/get_info -> chain_id 4667b205c6838ef70ff… |
| vaulta | `antelope:aca376f206b8fc25a6ed44dbdc66547c` | high | eos.greymass.com /v1/chain/get_info -> chain_id aca376f206b8fc25a6ed4… |
| wax | `antelope:1064487b3cd1a897ce03ae5b6a865651` | high | wax.greymass.com /v1/chain/get_info -> chain_id 1064487b3cd1a897ce03a… |
| xpr | `antelope:384da888112027f0321850a169f737c3` | high | proton.greymass.com /v1/chain/get_info -> chain_id 384da888112027f032… |

### No category (namespace only) (24)

| Platform | CAIP-2 | Conf. | Verified by |
|---|---|---|---|
| aleo | `aleo:0` | high | api.explorer.provable.com GET /v1/mainnet/latest/block -> header.meta… |
| algorand | `algorand:wGHE2Pwdvd7S12BL5FaOP20EGYesN73k` | high | mainnet-api.algonode.cloud GET /v2/transactions/params -> genesis-has… |
| arweave | `arweave:7wIU` | high | arweave.net GET /block/height/0 -> indep_hash 7wIU7KolICAjClMlcZ38LZz… |
| casper | `casper:casper` | high | node.mainnet.casper.network/rpc info_get_status -> chainspec_name 'ca… |
| conflux-core | `conflux:cfx` | high | main.confluxrpc.com cfx_getStatus -> networkId 0x405 (1029), ethereum… |
| filecoin | `fil:f` | high | api.node.glif.io/rpc/v1 Filecoin.StateNetworkName -> 'mainnet' (spec … |
| flow | `flow:mainnet` | high | rest-mainnet.onflow.org GET /v1/network/parameters -> chain_id 'flow-… |
| hedera | `hedera:mainnet` | high | partial: no in-protocol resolution method per spec; mainnet-public.mi… |
| klever | `klv:108` | high | node.mainnet.klever.org GET /node/status -> data.metrics.klv_chain_id… |
| mina | `mina:mainnet` | high | api.minascan.io/node/mainnet/v1/graphql {networkID} -> 'mina:mainnet' |
| monero | `monero:418015bb9ae982a1975da7d79277c270` | high | xmrchain.net /api/block/0 -> 418015bb9ae982a1975da7d79277c2705727a568… |
| multiversx | `mvx:1` | high | api.multiversx.com GET /constants -> chainId "1" (/network/config and… |
| neo-n3 | `neo:860833102` | high | mainnet1.neo.coz.io getversion -> protocol.network 860833102 |
| partisia | `partisia:Partisia_Blockchain` | high | reader.partisiablockchain.com /blockchain/chainId -> "Partisia Blockc… |
| quai | `quai:9` | medium | rpc.quai.network/cyprus1 quai_chainId -> 0x9 |
| stacks | `stacks:1` | high | api.hiro.so /v2/info -> network_id 1 |
| starknet | `starknet:SN_MAIN` | high | api.cartridge.gg/x/starknet/mainnet and starknet-rpc.publicnode.com s… |
| stellar | `stellar:pubnet` | high | horizon.stellar.org / -> network_passphrase 'Public Global Stellar Ne… |
| tezos | `tezos:NetXdQprcVkpaWU` | high | rpc.tzkt.io/mainnet /chains/main/chain_id -> NetXdQprcVkpaWU (also ap… |
| ton | `tvm:-239` | high | toncenter.com /api/v3/masterchainInfo -> global_id -239 (dton.io grap… |
| tron | `tron:728126428` | high | api.trongrid.io/jsonrpc eth_chainId -> 0x2b6653dc = 728126428 |
| vechain | `vechain:b1ac3413d346d43539627e6be7ec1b4a` | medium | mainnet.vechain.org /blocks/0 -> id 0x00000000851caf3cfdb6e899cf5958b… |
| waves | `waves:087` | high | nodes.wavesnodes.com: block-1 generator address 3P274YB5... and /addr… |
| xrpl | `xrpl:0` | high | xrplcluster.com server_info -> network_id 0 |

## Held back

Not ready to apply; each needs a live read or a human decision.

| Platform | Candidate | Blocker |
|---|---|---|
| concordium | `ccd:9dd9ca4d19e9393877d2c44b70f89acb` | Value is the spec's own example; ccdscan API unreachable. |
| kilt | `polkadot:a0453819cbf8b4df9423a5cd601f546c` | Value is the spec's own example; every RPC blocked or down. |
| genshiro | `polkadot:9b8cefc0eb5c568b527998bdd76c184e` | All RPCs dead; value from @polkadot/networks only. Chain may be defunct. |
| picasso | substrate, genesis unknown | All RPCs dead; Composable wound the chain down. |
| fractal-bitcoin | `bip122:00000000000000005a5c13fe33f6717c` (block 1) | Shares Bitcoin's genesis; no official fork-block convention exists for it. |
| gnoland | `cosmos:gnoland-1` | Tendermint2/GnoVM, not Cosmos SDK; using the cosmos namespace is a stretch. |
| mango | move | No mainnet RPC reachable; no CAIP-2 namespace. |
| matrix | — | No CAIP-2 namespace, no reachable RPC. |
| ultima | — | chainid.network lists 3416255149 but no RPC answers; EVM not confirmed. |

No CAIP-2 namespace and no category of 3+: `ao`, `beldex`, `canton`, `constellation`, `icon`, `internet-computer`, `iost`, `lightning`, `nano`, `near`, `nervos`, `oasis`, `pi-network`, `radix`, `v-systems`.

## Hybrid records

These chains run two environments. The proposal follows what exchanges deposit
to; a second record would be needed for the other side.

| Platform | Proposed side | Other side |
|---|---|---|
| sei | cosmos `pacific-1` (existing) | **Needs splitting now:** SEIEVM codes at seven exchanges map to `sei`. Add `sei-evm` (`eip155:1329`, live-checked) and repoint them. |
| zetachain | `eip155:7000` | `cosmos:hashed-…` of `zetachain_7000-1`; Bybit maps both ZETA and ZETAEVM here. |
| peaq | `eip155:3338` | `polkadot:d2a5d385932d1f650dae03ef8e274898` |
| theta | `eip155:361` | native chain id `mainnet` (no namespace) |
| astar, humanode, shiden, hydration, bittensor, litentry, origintrail, acala | substrate | EVM at eip155 592, 5234, 336, 222222, 964, 212013, 2043, 787 |
| injective, mantra, nibiru, dymension, zigchain, oraichain | cosmos | EVM at eip155 1776, 5888, 6900, 1100, 944, 108160679 |
| flow, filecoin, hedera, iota | native | EVM at eip155 747, 314, 295, 8822 |
| elastos | ELA main chain (utxo) | Elastos Smart Chain `eip155:20`; KuCoin `esc` is unmapped |
| oasis | consensus layer | Sapphire `eip155:23294` |
| robonomics | Kusama parachain | also a Polkadot parachain (`29f4371d…`) |

## Other findings

- `network_translations/mexc.json` `DOTASSETHUB` and `bitget.json`
  `PolkadotAssetHub` map to `polkadot`; they should be `polkadot-asset-hub`.
- `litentry` now reports its chain name as Heima (same genesis).
- `story` is listed as "Data Network" on chainid.network, matching its rebrand.
- Missing `native_asset` on ao, canton, constellation, eclipse, fogo, icon,
  iost and klever.
