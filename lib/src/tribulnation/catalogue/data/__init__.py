"""### Tribulnation Catalogue

Central catalogue of (crypto-)assets, platforms and networks.
"""
from .schema import (
  Asset, AssetPeg, ExternalIds,
  BasePlatform, CexPlatform, DexPlatform, Blockchain, BlockchainCategory,
  BlockchainNamespace, Platform,
  Catalogue, Spot, Perpetual, Debt, Collateral, Pool, SpamAddress,
)