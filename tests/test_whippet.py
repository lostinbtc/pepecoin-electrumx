"""Whippet constants and synthetic AuxPoW wire-format regression tests.

Synthetic headers exercise parsing only; they are not valid consensus fixtures.
"""
import struct
import unittest
from electrumx.lib.coins import Coin, Pepecoin, Whippet
from electrumx.lib.hash import Base58, double_sha256

class WhippetTests(unittest.TestCase):
    def test_network_is_separate(self):
        self.assertIs(Coin.lookup_coin_class('Whippet', 'mainnet'), Whippet)
        self.assertNotEqual(Whippet.GENESIS_HASH, Pepecoin.GENESIS_HASH)
        self.assertNotEqual(Whippet.P2PKH_VERBYTE, Pepecoin.P2PKH_VERBYTE)
        address = Base58.encode_check(b'\x49' + bytes(range(20)))
        self.assertEqual(Whippet.pay_to_address_script(address),
                         b'\x76\xa9\x14' + bytes(range(20)) + b'\x88\xac')
        self.assertEqual(Whippet.RPC_PORT, 33665)
        self.assertEqual(Whippet.PEERS, [])

    def test_legacy_and_auxpow_headers(self):
        # Minimal serialized coinbase transaction for the parent proof.
        tx = (struct.pack('<I', 1) + b'\x01' + bytes(32) + b'\xff' * 4 +
              b'\x01\x00' + b'\xff' * 4 + b'\x01' + struct.pack('<Q', 1) +
              b'\x01\x51' + bytes(4))
        legacy = struct.pack('<I', 0x57500004) + bytes(76)
        self.assertEqual(Whippet.block_header(legacy + b'\x00', 100000), legacy)
        aux_header = struct.pack('<I', 0x57500104) + bytes(76)
        proof = tx + bytes(32) + b'\x00' + bytes(4) + b'\x00' + bytes(4) + bytes(80)
        raw = aux_header + proof + b'\x01' + tx
        parsed = Whippet.block(raw, 371337)
        self.assertEqual(parsed.header, aux_header + proof)
        self.assertEqual(Whippet.header_hash(parsed.header), double_sha256(aux_header))
        self.assertEqual(len(parsed.transactions), 1)
        self.assertEqual(parsed.transactions[0].txid, double_sha256(tx))

if __name__ == '__main__':
    unittest.main()
