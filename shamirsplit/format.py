"""Serialization helpers for ShamirSplit share files."""
from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any

from .core import InvalidShareError, Share


def share_to_dict(share: Share) -> dict[str, Any]:
    share.validate()
    return {
        "format": "ShamirSplit share",
        "version": share.version,
        "index": share.index,
        "total": share.total,
        "threshold": share.threshold,
        "payload": base64.b64encode(share.payload).decode("ascii"),
        "secret_sha256": share.secret_checksum,
    }


def share_from_dict(value: Any) -> Share:
    if not isinstance(value, dict):
        raise InvalidShareError("share file must contain a JSON object")
    try:
        if value.get("format") != "ShamirSplit share":
            raise InvalidShareError("unrecognized share format")
        payload = base64.b64decode(value["payload"], validate=True)
        share = Share(
            index=int(value["index"]),
            total=int(value["total"]),
            threshold=int(value["threshold"]),
            payload=payload,
            secret_checksum=str(value["secret_sha256"]),
            version=int(value.get("version", 1)),
        )
    except (KeyError, TypeError, ValueError, base64.binascii.Error) as exc:
        raise InvalidShareError(f"invalid share fields: {exc}") from exc
    share.validate()
    return share


def write_share(path: str | Path, share: Share) -> None:
    destination = Path(path)
    destination.write_text(json.dumps(share_to_dict(share), indent=2) + "\n", encoding="utf-8")


def read_share(path: str | Path) -> Share:
    source = Path(path)
    try:
        value = json.loads(source.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"share file not found: {source}") from exc
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InvalidShareError(f"cannot read share file {source}: {exc}") from exc
    return share_from_dict(value)
