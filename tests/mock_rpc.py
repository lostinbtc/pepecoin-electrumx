"""Synthetic empty-node RPC fixture. No blockchain or private client data."""
import json
import socketserver


class RPC(socketserver.StreamRequestHandler):
    def handle(self):
        for line in self.rfile:
            req = json.loads(line)
            method = req['method']
            if method == 'getinfo':
                result = {'db height': 100, 'daemon height': 100, 'groups': 0,
                          'peers': {'total': 0}, 'request total': 0,
                          'sessions': {'count': 0, 'count with subs': 0, 'errors': 0},
                          'txs sent': 0, 'uptime': '1h', 'db_flush_count': 1}
            elif method in ('sessions', 'peers'):
                result = []
            else:
                raise ValueError('Unexpected fixture RPC method: ' + method)
            self.wfile.write((json.dumps({'jsonrpc': '2.0', 'id': req['id'], 'result': result}) + '\n').encode())
            self.wfile.flush()


if __name__ == '__main__':
    with socketserver.ThreadingTCPServer(('0.0.0.0', 8000), RPC) as server:
        server.serve_forever()
