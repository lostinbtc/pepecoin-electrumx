import contextlib
import io
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import plyvel
from electrumx.cli import electrumx_compact_history as compactor
from electrumx.cli import electrumx_history_compaction_guard as guard


class HistoryGuardTests(unittest.TestCase):
    def test_default_and_valid_thresholds(self):
        for raw, expected in [(None, 50000), ('', 50000), ('1', 1), ('65534', 65534)]:
            with self.subTest(raw=raw):
                self.assertEqual(guard.parse_threshold(raw), expected)

    def test_unsafe_thresholds_fail(self):
        for raw in ['0', '-1', '65535', '999999', 'abc', '1.5']:
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                guard.parse_threshold(raw)

    def test_state_validation(self):
        self.assertIsNone(guard.parse_history_state(None))
        self.assertEqual(guard.parse_history_state(b"{'flush_count': 12}")['flush_count'], 12)
        for raw in [b'[]', b'{}', b"{'flush_count': True}", b"{'flush_count': -1}",
                    b"{'flush_count': 1, 'comp_cursor': 'bad'}", b'not python', b'\xff']:
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                guard.parse_history_state(raw)

    def test_threshold_and_interrupted_compaction(self):
        self.assertIsNone(guard.compaction_reason({'flush_count': 49999}, 50000))
        self.assertIsNotNone(guard.compaction_reason({'flush_count': 50000}, 50000))
        self.assertIsNotNone(guard.compaction_reason({'flush_count': 1, 'comp_cursor': 0}, 50000))
        self.assertIsNone(guard.compaction_reason(None, 50000))

    def test_missing_database_is_not_created(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'new-db'
            self.assertIsNone(guard.read_history_state(path, 'leveldb'))
            self.assertFalse(path.exists())

    def test_actual_leveldb_state_read_is_nonmutating(self):
        with tempfile.TemporaryDirectory() as tmp:
            original_cwd = Path.cwd()
            raw = b"{'flush_count': 50000, 'comp_cursor': -1}"
            with plyvel.DB(str(Path(tmp) / 'hist'), create_if_missing=True) as db:
                db.put(guard.STATE_KEY, raw)
            state = guard.read_history_state(Path(tmp), 'leveldb')
            self.assertEqual(state['flush_count'], 50000)
            self.assertEqual(Path.cwd(), original_cwd)
            with plyvel.DB(str(Path(tmp) / 'hist'), create_if_missing=False) as db:
                self.assertEqual(db.get(guard.STATE_KEY), raw)

    def test_main_exit_codes(self):
        for state, expected in [(None, 0), ({'flush_count': 10}, 0),
                                ({'flush_count': 50000}, 75),
                                ({'flush_count': 1, 'comp_cursor': 0}, 75)]:
            with self.subTest(state=state), patch.dict(os.environ, {'DB_DIRECTORY': '/unused'}, clear=True), \
                    patch.object(guard, 'read_history_state', return_value=state), \
                    contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(guard.main(), expected)
        with patch.dict(os.environ, {}, clear=True), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(guard.main(), 1)

    def test_compactor_propagates_failure(self):
        # Do not open or compact any real database in this test.
        for failed in [False, True]:
            loop = Mock()
            if failed:
                loop.run_until_complete.side_effect = RuntimeError('test failure')
            with self.subTest(failed=failed), patch.object(compactor.asyncio, 'get_event_loop', return_value=loop), \
                    patch.object(compactor, 'compact_history', new=Mock(return_value=None)), \
                    contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(compactor.main(), 1 if failed else 0)


if __name__ == '__main__':
    unittest.main()
