import unittest
from shamirsplit import split_secret, reconstruct_secret, InsufficientSharesError
class ShamirSplitTests(unittest.TestCase):
    def test_reconstruct_from_threshold(self):
        secret = "سر مشروع وهج الهبيط".encode("utf-8")
        shares = split_secret(secret, 5, 3)
        self.assertEqual(reconstruct_secret(shares[:3], 3), secret)
        self.assertEqual(reconstruct_secret([shares[0], shares[2], shares[4]], 3), secret)

    def test_more_than_threshold(self):
        secret = bytes(range(256))
        shares = split_secret(secret, 7, 4)
        self.assertEqual(reconstruct_secret(shares, 4), secret)

    def test_insufficient_shares(self):
        shares = split_secret(b"hello", 4, 3)

        with self.assertRaises(InsufficientSharesError):
            reconstruct_secret(shares[:2], 3)

    def test_insufficient_shares(self):
        shares = split_secret(b"hello", 4, 3)

        with self.assertRaises(InsufficientSharesError):
            reconstruct_secret(shares[:2], 3)


if __name__ == "__main__":
    unittest.main()
