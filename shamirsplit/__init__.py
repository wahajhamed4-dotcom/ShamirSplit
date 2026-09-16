"""ShamirSplit: threshold secret sharing for files and byte strings."""

from .core import (
    InvalidShareError,
    InsufficientSharesError,
    ShamirError,
    Share,
    checksum,
    reconstruct_secret,
    split_secret,
)
from .format import read_share, share_from_dict, share_to_dict, write_share

__version__ = "1.0.0"

__all__ = [
    "InvalidShareError",
    "InsufficientSharesError",
    "ShamirError",
    "Share",
    "checksum",
    "read_share",
    "reconstruct_secret",
    "share_from_dict",
    "share_to_dict",
    "split_secret",
    "write_share",
]
