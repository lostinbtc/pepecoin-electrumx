"""Bounded, network-local regressions for transport memory-exhaustion fixes."""
import asyncio
import gc
import json
import sys
import unittest

from aiorpcx import RPCSession, serve_ws
from multidict import CIMultiDict
from websockets.asyncio.client import connect
from websockets.asyncio.messages import MAX_FRAGMENTS
from websockets.exceptions import ConnectionClosed


class Fixture(RPCSession):
    async def handle_request(self, request):
        if request.method == 'server.version':
            return ['security-fixture', '1.4']
        raise AssertionError('Unexpected fixture method')


class WebsocketSecurityTests(unittest.IsolatedAsyncioTestCase):
    async def test_fragment_limit_and_connection_recovery(self):
        self.assertLessEqual(MAX_FRAGMENTS, 8192)
        async with serve_ws(Fixture, '127.0.0.1', 0) as server:
            url = 'ws://127.0.0.1:' + str(server.sockets[0].getsockname()[1])

            async def ordinary_request():
                async with connect(url) as ws:
                    await ws.send(json.dumps({'jsonrpc': '2.0', 'id': 1,
                                              'method': 'server.version', 'params': []}))
                    response = json.loads(await asyncio.wait_for(ws.recv(), 3))
                    self.assertEqual(response.get('result'), ['security-fixture', '1.4'])

            async def fragments():
                for _ in range(MAX_FRAGMENTS + 5):
                    yield b''
                await asyncio.sleep(0.2)

            await ordinary_request()
            try:
                async with connect(url) as ws:
                    await asyncio.wait_for(ws.send(fragments()), 5)
                    await asyncio.wait_for(ws.recv(), 3)
            except ConnectionClosed as error:
                self.assertIsNotNone(error.rcvd)
                self.assertEqual(error.rcvd.code, 1009)
            else:
                self.fail('Excessive empty fragments were accepted')
            await ordinary_request()


class MultidictSecurityTests(unittest.TestCase):
    def test_items_view_operations_release_references(self):
        for operation in [lambda d, rows: rows | d.items(), lambda d, rows: d.items() - rows]:
            with self.subTest(operation=operation):
                d = CIMultiDict(seed='x')
                value = object()
                rows = [('key' + str(i), value) for i in range(1000)]
                gc.collect()
                before = sys.getrefcount(value)
                operation(d, rows)
                gc.collect()
                self.assertEqual(sys.getrefcount(value), before)


if __name__ == '__main__':
    unittest.main()
