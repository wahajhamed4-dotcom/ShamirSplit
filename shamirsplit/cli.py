"""Command-line interface for ShamirSplit."""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from . import __version__
from .core import InvalidShareError, InsufficientSharesError, Share, checksum, reconstruct_secret, split_secret
from .format import read_share, write_share

LOGGER = logging.getLogger("shamirsplit")


def _load_config(path: str | None) -> dict:
    if not path:
        return {}
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"config file not found: {path}") from exc
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read config file: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError("config file must contain a JSON object")
    return value


def _add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--config", help="load defaults from a JSON config file")
    parser.add_argument("--log-level", choices=("CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"), default="WARNING")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="shamirsplit",
        description="Split a secret into shares and reconstruct it with a threshold.",
    )
    parser.add_argument("--version", action="version", version=f"ShamirSplit {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    split = subparsers.add_parser("split", help="split a secret file into shares")
    split.add_argument("input", help="path to the secret file")
    split.add_argument("-o", "--output-dir", default="shares", help="directory for generated share files")
    split.add_argument("-n", "--shares", type=int, help="total number of shares")
    split.add_argument("-t", "--threshold", type=int, help="minimum shares needed for reconstruction")
    _add_common(split)

    reconstruct = subparsers.add_parser("reconstruct", help="reconstruct a secret from share files")
    reconstruct.add_argument("shares", nargs="+", help="share files (at least threshold files)")
    reconstruct.add_argument("-o", "--output", required=True, help="destination for reconstructed secret")
    _add_common(reconstruct)
    return parser


def _configure_logging(level: str) -> None:
    logging.basicConfig(level=getattr(logging, level), format="%(levelname)s: %(message)s")


def command_split(args: argparse.Namespace) -> int:
    config = _load_config(args.config)
    total = args.shares if args.shares is not None else config.get("shares", 5)
    threshold = args.threshold if args.threshold is not None else config.get("threshold", 3)
    secret_path = Path(args.input)
    secret = secret_path.read_bytes()
    generated = split_secret(secret, total, threshold)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    digest = checksum(secret)
    for index, payload in generated:
        share = Share(index, total, threshold, payload, digest)
        destination = output_dir / f"share-{index:03d}.json"
        write_share(destination, share)
        LOGGER.info("wrote %s", destination)
    print(f"Created {len(generated)} shares in {output_dir} (threshold: {threshold}).")
    return 0


def command_reconstruct(args: argparse.Namespace) -> int:
    loaded = [read_share(path) for path in args.shares]
    first = loaded[0]
    if len(loaded) < first.threshold:
        raise InsufficientSharesError(f"{first.threshold} shares are required; received {len(loaded)}")
    if any((share.total, share.threshold, len(share.payload), share.secret_checksum) !=
           (first.total, first.threshold, len(first.payload), first.secret_checksum) for share in loaded):
        raise InvalidShareError("share files do not belong to the same secret set")
    pairs = [(share.index, share.payload) for share in loaded]
    secret = reconstruct_secret(pairs, first.threshold)
    if checksum(secret) != first.secret_checksum:
        raise InvalidShareError("checksum mismatch: shares may be corrupted or from different sets")
    destination = Path(args.output)
    destination.write_bytes(secret)
    print(f"Reconstructed secret written to {destination}.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        _configure_logging(getattr(args, "log_level", "WARNING"))
        if args.command == "split":
            return command_split(args)
        return command_reconstruct(args)
    except (OSError, ValueError, InvalidShareError, InsufficientSharesError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
