"""Network-free checks for upstream session/peer hardening backports."""
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, Mock

from aiorpcx import RPCError
from electrumx.lib.peer import Peer
from electrumx.server.peers import PeerManager, NUM_PEERS_MAX_TOTAL
from electrumx.server.session import ElectrumX, SessionManager


def features(host='example.org'):
    return {'genesis_hash': 'ab' * 32, 'protocol_min': '1.4', 'protocol_max': '1.4',
            'server_version': 'fixture', 'hosts': {host: {'tcp_port': 50001}}}


class PeerSecurityTests(unittest.IsolatedAsyncioTestCase):
    async def test_invalid_announcements_do_not_mark_caller_as_peer(self):
        good = features()
        invalid = [None, [], {}, {**good, 'hosts': []}, {**good, 'hosts': {1: {}}},
                   {**good, 'hosts': {'example.org': []}}, {**good, 'protocol_min': 1},
                   {**good, 'server_version': 'x' * 8100},
                   {str(i): i for i in range(51)}]
        for value in invalid:
            with self.subTest(value_type=type(value).__name__):
                manager = SimpleNamespace(on_add_peer=AsyncMock(return_value=True))
                session = SimpleNamespace(is_peer=False, peer_mgr=manager, bump_cost=Mock(), remote_address=Mock())
                with self.assertRaises(RPCError):
                    await ElectrumX.add_peer(session, value)
                self.assertFalse(session.is_peer)
                manager.on_add_peer.assert_not_awaited()

    async def test_valid_announcements_remain_compatible(self):
        manager = SimpleNamespace(on_add_peer=AsyncMock(return_value=True))
        session = SimpleNamespace(is_peer=False, peer_mgr=manager, bump_cost=Mock(), remote_address=Mock())
        self.assertTrue(await ElectrumX.add_peer(session, features()))
        self.assertTrue(session.is_peer)
        manager.on_add_peer.assert_awaited_once()

    async def test_host_count_and_length_are_bounded(self):
        good = features()
        self.assertEqual(len(Peer.peers_from_features(good, 'fixture')), 1)
        many = {**good, 'hosts': {f'server{i}.example.org': {} for i in range(6)}}
        self.assertEqual(Peer.peers_from_features(many, 'fixture'), [])
        self.assertEqual(Peer.peers_from_features(features('x' * 256), 'fixture'), [])

    async def test_peer_graph_cannot_grow_past_limit(self):
        peers = {Peer(f'server{i}.example.org', features(f'server{i}.example.org'), source='fixture')
                 for i in range(NUM_PEERS_MAX_TOTAL)}
        manager = SimpleNamespace(peers=peers, proxy=None, logger=Mock())
        peer = Peer('additional.example.org', features('additional.example.org'), source='fixture')
        await PeerManager._note_peers(manager, [peer])
        self.assertEqual(len(manager.peers), NUM_PEERS_MAX_TOTAL)
        self.assertNotIn(peer, manager.peers)

    async def test_remote_peer_response_is_limited(self):
        rows = [['8.8.8.8', f'server{i}.example.org', ['v1.4', 't50001']] for i in range(200)]
        session = SimpleNamespace(send_request=AsyncMock(return_value=rows))
        peers = await PeerManager._send_peers_subscribe(SimpleNamespace(), session, 'fixture')
        self.assertEqual(len(peers), 100)

    async def test_nonpublic_announcements_are_rejected_without_dns(self):
        manager = SimpleNamespace(env=SimpleNamespace(peer_discovery='on', PD_ON='on'), logger=Mock())
        result = await PeerManager.on_add_peer(manager, features('127.0.0.1'), SimpleNamespace(host='8.8.8.8'))
        self.assertFalse(result)

    async def test_session_limit_pause_does_not_wait_for_open_sessions(self):
        server = SimpleNamespace(close=Mock(), wait_closed=AsyncMock(side_effect=AssertionError('would hang')))
        manager = SimpleNamespace(logger=Mock(), servers={'public': server})
        await SessionManager._stop_servers(manager, ['public'])
        server.close.assert_called_once()
        server.wait_closed.assert_not_awaited()


if __name__ == '__main__':
    unittest.main()
