"""Execute inside the exact runtime image; no added packages or unverified TLS."""
import argparse
import asyncio
import hashlib
import json
import socket
import ssl

GENESIS = '37981c0c48b8d48965376c8a42ece9a0838daadb93ff975cb091f57f8c2a5faa'

def sha256d(data):
    return hashlib.sha256(hashlib.sha256(data).digest()).digest()

def rpc(port, method, params=None, context=None):
    connection = socket.create_connection(('127.0.0.1', port), timeout=30)
    if context:
        connection = context.wrap_socket(connection, server_hostname='localhost')
    with connection:
        stream = connection.makefile('rwb')
        stream.write((json.dumps({'id': 1, 'method': method, 'params': params or []}) + '\n').encode())
        stream.flush()
        result = json.loads(stream.readline())
    assert not result.get('error'), result.get('error')
    return result['result']

async def probe(args):
    from websockets.asyncio.client import connect
    context = ssl.create_default_context(cafile='/certs/cert.pem')
    reports = []
    for port, tls in [(args.tcp, None), (args.tls, context)]:
        version = rpc(port, 'server.version', ['release-verification', '1.4'], tls)
        features = rpc(port, 'server.features', context=tls)
        assert features['genesis_hash'] == GENESIS
        header = rpc(port, 'blockchain.headers.subscribe', context=tls)
        assert header['height'] >= args.height
        requested = rpc(port, 'blockchain.block.header', [args.height], tls)
        assert sha256d(bytes.fromhex(requested)[:80])[::-1].hex() == args.block_hash
        assert rpc(port, 'blockchain.scripthash.get_history', ['00' * 32], tls) == []
        balance = rpc(port, 'blockchain.scripthash.get_balance', ['00' * 32], tls)
        assert balance == {'confirmed': 0, 'unconfirmed': 0}
        if args.txid:
            proof = rpc(port, 'blockchain.transaction.get_merkle', [args.txid, args.height], tls)
            assert proof['block_height'] == args.height
            node, position = bytes.fromhex(args.txid)[::-1], proof['pos']
            for branch in proof['merkle']:
                sibling = bytes.fromhex(branch)[::-1]
                node = sha256d(sibling + node if position & 1 else node + sibling)
                position >>= 1
            assert node == bytes.fromhex(requested)[36:68], 'Invalid indexed transaction proof'
            raw = rpc(port, 'blockchain.transaction.get', [args.txid], tls)
            from electrumx.lib.coins import Pepecoin
            tx = Pepecoin.DESERIALIZER(bytes.fromhex(raw)).read_tx()
            assert tx.txid[::-1].hex() == args.txid
        reports.append({'port': port, 'verified_tls': tls is not None,
                        'version': version, 'height': header['height'], 'passed': True})
    async with connect(f'wss://localhost:{args.wss}', ssl=context, open_timeout=20) as connection:
        await connection.send(json.dumps({'id': 1, 'method': 'server.version',
                                         'params': ['release-verification', '1.4']}) + '\n')
        assert json.loads(await connection.recv()).get('result')
        await connection.send(json.dumps({'id': 2, 'method': 'blockchain.headers.subscribe', 'params': []}) + '\n')
        header = json.loads(await connection.recv())['result']
        assert header['height'] >= args.height
        reports.append({'port': args.wss, 'verified_tls': True, 'height': header['height'], 'passed': True})
    print(json.dumps(reports))

def main():
    parser = argparse.ArgumentParser()
    for flag in ['tcp', 'tls', 'wss', 'height']:
        parser.add_argument('--' + flag, type=int, required=True)
    parser.add_argument('--block-hash', required=True)
    parser.add_argument('--txid')
    asyncio.run(probe(parser.parse_args()))

if __name__ == '__main__':
    main()
