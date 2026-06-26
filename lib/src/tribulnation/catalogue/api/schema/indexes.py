"""Index types — all are plain dicts, typed here for documentation and OpenAPI."""

# Maps symbol → list of canonical asset IDs
SymbolsIndex = dict[str, list[str]]

# Maps provider-specific ID → canonical asset ID
ExternalIndex = dict[str, str]

# Maps target asset ID → list of asset IDs that are pegged to it
PegsIndex = dict[str, list[str]]
