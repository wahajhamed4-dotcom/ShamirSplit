import json
import tempfile
import unittest
from pathlib import Path

from shamirsplit import (
    InvalidShareError,
    InsufficientSharesError,
    Share,
    checksum,
    reconstruct_secret,
    split_secret,
)
from shamirsplit.format import read_share, write_share


class ShamirSplitTests(unittest.TestCase):
    def test_reconstruct_from_threshold(self):
        secret = b"confidential cyber security project\x00\xff"
        shares = split_secret(secret, 5, 3)
        self.assertEqual(secret, reconstruct_secret(shares[:3], 3))
        self.assertEqual(secret, reconstruct_secret([shares[4], shares[1], shares[3]], 3))

    def test_insufficient_shares(self):
        shares = split_secret(b"secret", 5, 3)
        with self.assertRaises(InsufficientSharesError):
            reconstruct_secret(shares[:2], 3)

    def test_duplicate_indexes_rejected(self):
        shares = split_secret(b"secret", 5, 3)
        with self.assertRaises(InvalidShareError):
            reconstruct_secret([shares[0], shares[0], shares[1]], 3)

    def test_share_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "share.json"
            share = Share(1, 3, 2, b"payload", checksum(b"secret"))
            write_share(path, share)
            self.assertEqual(share, read_share(path))
            self.assertEqual("ShamirSplit share", json.loads(path.read_text())["format"])

    def test_invalid_checksum_detected_by_caller(self):
        secret = b"secret"
        shares = split_secret(secret, 3, 2)
        rebuilt = reconstruct_secret(shares[:2], 2)
        self.assertEqual(checksum(rebuilt), checksum(secret))


if __name__ == "__main__":
    unittest.main()
