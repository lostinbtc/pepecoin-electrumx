"""Pepecoin identity and legacy-header checks, independent of Whippet classes."""
import struct
import unittest
from electrumx.lib.coins import Coin, Pepecoin
from electrumx.lib.hash import Base58, double_sha256


class PepecoinTests(unittest.TestCase):
    def test_chain_identity_and_receiving_script(self):
        self.assertIs(Coin.lookup_coin_class('Pepecoin', 'mainnet'), Pepecoin)
        self.assertEqual(Pepecoin.GENESIS_HASH, '37981c0c48b8d48965376c8a42ece9a0838daadb93ff975cb091f57f8c2a5faa')
        self.assertEqual(Pepecoin.P2PKH_VERBYTE, b'\x38')
        address = Base58.encode_check(b'\x38' + bytes(range(20)))
        self.assertEqual(Pepecoin.pay_to_address_script(address), b'\x76\xa9\x14' + bytes(range(20)) + b'\x88\xac')

    def test_legacy_header_identity(self):
        header = struct.pack('<I', 0x20000002) + bytes(76)
        self.assertEqual(Pepecoin.block_header(header + b'\x00', 1200000), header)
        self.assertEqual(Pepecoin.header_hash(header), double_sha256(header))


if __name__ == '__main__':
    unittest.main()
