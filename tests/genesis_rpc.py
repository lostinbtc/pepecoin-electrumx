"""Read-only synthetic Core RPC containing the public Pepecoin genesis block."""
import argparse
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, required=True)
    args = parser.parse_args()
    fixture = json.loads((Path(__file__).resolve().parents[1] /
        'electrumx/tests/blocks/pepecoin_mainnet_0.json').read_text())

    def respond(request):
        method, params = request['method'], request.get('params', [])
        error = None
        if method == 'getblockcount':
            result = 0
        elif method == 'getblockchaininfo':
            result = {'chain': 'main', 'blocks': 0, 'headers': 0, 'pruned': False,
                      'bestblockhash': fixture['hash'], 'initialblockdownload': False}
        elif method == 'getblockhash' and params == [0]:
            result = fixture['hash']
        elif method == 'getblock' and params[0] == fixture['hash']:
            result = fixture if len(params) > 1 and params[1] else fixture['block']
        elif method == 'getrawmempool':
            result = []
        elif method == 'getnetworkinfo':
            result = {'version': 1140900, 'subversion': '/genesis-test/', 'relayfee': 0.001}
        elif method in ('estimatefee', 'estimatesmartfee'):
            result = -1 if method == 'estimatefee' else {'feerate': -1}
        else:
            result, error = None, {'code': -32601, 'message': 'Not supported by genesis fixture'}
        return {'id': request.get('id'), 'result': result, 'error': error}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            request = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            result = [respond(item) for item in request] if isinstance(request, list) else respond(request)
            body = json.dumps(result).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    HTTPServer(('127.0.0.1', args.port), Handler).serve_forever()

if __name__ == '__main__':
    main()
