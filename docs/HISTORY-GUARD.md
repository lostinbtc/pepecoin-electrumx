# Legacy history guard

ElectrumX 1.18.0's legacy history keys contain a two-byte flush ID. Do not raise,
wrap, or reset that counter manually: doing so can collide with existing history.

The startup guard checks the database before the server starts. At 50,000 flushes
(configurable below 65,535), or after an interrupted compaction, it requests the
provided offline compactor. It then verifies the state again and refuses startup
if the database is still unsafe or cannot be read. New databases are not created
by the check. The compactor now returns a failing exit status on errors.

These are the safeguards already deployed by Pepecoin Service, not a new database
format. The entrypoint uses `exec` so Docker stop signals reach ElectrumX. They are
separate from the Brotli/PHP security patch and do not alter Electrum RPC handlers.

Startup checks do not replace monitoring for a continuously running server. Read
`db_flush_count` through local administrative `getinfo`, and schedule a controlled
maintenance restart before the threshold is exhausted. A separate operator-managed
maintenance timer is not included in this portable package. Always stop the daemon
and back up its database before running offline compaction manually. Never run the
guard or compactor against a database being used by a running server.

Tests use isolated temporary LevelDB directories, not production volumes:

```sh
docker run --rm --entrypoint python \
  -v "$PWD/tests:/tests:ro" pepecoin-electrumx-electrumx \
  -m unittest discover -s /tests -p test_history_guard.py
```

Adjust the image name to your Compose project. No test needs Core credentials.
