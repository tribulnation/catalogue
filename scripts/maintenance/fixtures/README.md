# Maintenance fixtures

A small catalogue (`data/`) and the observations a runner would export for it
(`observations/`), built from the evidence catalogue-ops published in its issues. CI runs

    python scripts/maintain.py --data scripts/maintenance/fixtures/data \
      --observations scripts/maintenance/fixtures/observations \
      --expect scripts/maintenance/fixtures/expected.json

and fails on any difference from `expected.json`. After changing a check on purpose,
re-record with `--write-expect` and review the diff of `expected.json`.

`issue_markers.txt` lists every fingerprint catalogue-ops published; the tests use it to
keep fingerprints byte-identical and every exception tied to something real.
