"""Pure-Python Shamir secret sharing over GF(2^8)."""
from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass


class ShamirError(Exception):
    """Base exception for expected ShamirSplit errors."""


class InvalidShareError(ShamirError):
    """Raised when a share is malformed or incompatible."""


class InsufficientSharesError(ShamirError):
    """Raised when fewer than the required number of shares are supplied."""


# AES polynomial x^8 + x^4 + x^3 + x + 1.
def _gf_mul(a: int, b: int) -> int:
    result = 0
    while b:
        if b & 1:
            result ^= a
        a <<= 1
        if a & 0x100:
            a ^= 0x11B
        b >>= 1
    return result & 0xFF


def _gf_pow(a: int, exponent: int) -> int:
    result = 1
    while exponent:
        if exponent & 1:
            result = _gf_mul(result, a)
        a = _gf_mul(a, a)
        exponent >>= 1
    return result


def _gf_inv(value: int) -> int:
    if value == 0:
        raise ZeroDivisionError("zero has no multiplicative inverse in GF(256)")
    return _gf_pow(value, 254)


def _validate_parameters(total_shares: int, threshold: int) -> None:
    if not isinstance(total_shares, int) or not 2 <= total_shares <= 255:
        raise ValueError("total_shares must be an integer from 2 to 255")
    if not isinstance(threshold, int) or not 2 <= threshold <= total_shares:
        raise ValueError("threshold must be an integer from 2 to total_shares")


def _evaluate_polynomial(coefficients: list[int], x: int) -> int:
    value = 0
    for coefficient in reversed(coefficients):
        value = _gf_mul(value, x) ^ coefficient
    return value


def _interpolate_at_zero(points: list[tuple[int, int]]) -> int:
    value = 0
    for index, (x_i, y_i) in enumerate(points):
        numerator = 1
        denominator = 1
        for other_index, (x_j, _) in enumerate(points):
            if index == other_index:
                continue
            numerator = _gf_mul(numerator, x_j)
            denominator = _gf_mul(denominator, x_i ^ x_j)
        value ^= _gf_mul(y_i, _gf_mul(numerator, _gf_inv(denominator)))
    return value


def split_secret(secret: bytes, total_shares: int, threshold: int) -> list[tuple[int, bytes]]:
    """Split arbitrary bytes into ``total_shares`` where ``threshold`` recover it."""
    if not isinstance(secret, bytes):
        raise TypeError("secret must be bytes")
    if not secret:
        raise ValueError("secret cannot be empty")
    _validate_parameters(total_shares, threshold)

    shares = [bytearray(len(secret)) for _ in range(total_shares)]
    for position, original_byte in enumerate(secret):
        coefficients = [original_byte] + [secrets.randbelow(256) for _ in range(threshold - 1)]
        for share_index in range(total_shares):
            shares[share_index][position] = _evaluate_polynomial(coefficients, share_index + 1)
    return [(index + 1, bytes(payload)) for index, payload in enumerate(shares)]


def reconstruct_secret(shares: list[tuple[int, bytes]], threshold: int) -> bytes:
    """Reconstruct a secret from at least ``threshold`` distinct shares."""
    if not isinstance(shares, list) or not shares:
        raise InsufficientSharesError("at least one share is required")
    if not isinstance(threshold, int) or threshold < 2:
        raise ValueError("threshold must be at least 2")
    if len(shares) < threshold:
        raise InsufficientSharesError(
            f"{threshold} shares are required; received {len(shares)}"
        )

    selected = shares[:threshold]
    indexes = [index for index, _ in selected]
    if len(set(indexes)) != len(indexes) or any(not 1 <= index <= 255 for index in indexes):
        raise InvalidShareError("share indexes must be unique integers from 1 to 255")
    lengths = {len(payload) for _, payload in selected}
    if len(lengths) != 1 or not lengths.pop():
        raise InvalidShareError("shares must contain equally sized, non-empty payloads")

    result = bytearray(next(iter(shares))[1].__len__())
    for position in range(len(result)):
        points = [(index, payload[position]) for index, payload in selected]
        result[position] = _interpolate_at_zero(points)
    return bytes(result)


def checksum(data: bytes) -> str:
    """Return a stable SHA-256 checksum for integrity validation."""
    return hashlib.sha256(data).hexdigest()


@dataclass(frozen=True)
class Share:
    """In-memory representation of a serialized share."""

    index: int
    total: int
    threshold: int
    payload: bytes
    secret_checksum: str
    version: int = 1

    def validate(self) -> None:
        if self.version != 1:
            raise InvalidShareError(f"unsupported share version: {self.version}")
        _validate_parameters(self.total, self.threshold)
        if not 1 <= self.index <= self.total:
            raise InvalidShareError("share index is outside the declared range")
        if not self.payload:
            raise InvalidShareError("share payload cannot be empty")
        if len(self.secret_checksum) != 64:
            raise InvalidShareError("invalid secret checksum")


__all__ = [
    "InvalidShareError",
    "InsufficientSharesError",
    "ShamirError",
    "Share",
    "checksum",
    "reconstruct_secret",
    "split_secret",
]

# Exposed only for the package's self-tests; not part of the user API.
_gf_mul_for_tests = _gf_mul
_gf_inv_for_tests = _gf_inv
