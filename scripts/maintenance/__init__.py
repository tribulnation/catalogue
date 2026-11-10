"""Catalogue maintenance checks: pure functions from venue observations to findings.

Each check compares what venues report (exported by whoever runs the checks, as JSON
files described in `observations.py`) with the catalogue data, and returns findings.
No check touches the network: fetching belongs to the caller or to a script's
`--live` wrapper. `scripts/maintain.py` runs them all and applies
`maintenance/exceptions.toml`.

Fingerprints read `<check>:<platform>:<subject>`, byte-identical to the ones
catalogue-ops published in its issues, so a finding keeps its identity across both
systems.
"""
