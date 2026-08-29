"""Load signed board.yaml / registry.yaml. Unsigned config is a hard fail."""

from __future__ import annotations

import pathlib
from dataclasses import dataclass
from typing import Any

import yaml

from octopus_sensorium.verify import (
    ConfigValidityError,
    SignatureError,
    assert_validity_window,
    content_hash,
    load_root_public_key,
    load_signed,
)

CONFIG_DIR = pathlib.Path("/etc/octopus/config")
BOARD_PATH = CONFIG_DIR / "board.yaml"
REGISTRY_PATH = CONFIG_DIR / "registry.yaml"


@dataclass(frozen=True)
class SignedDocument:
    path: str
    payload_hash: str
    signature_verified: bool
    document: dict[str, Any]


def load_signed_yaml(path: pathlib.Path, pub: bytes | None = None) -> SignedDocument:
    pub = pub if pub is not None else load_root_public_key()
    payload = load_signed(path, pub)
    document = yaml.safe_load(payload)
    if not isinstance(document, dict):
        raise ConfigValidityError(f"{path} is not a mapping")
    assert_validity_window(document)
    return SignedDocument(
        path=str(path),
        payload_hash=content_hash(payload),
        signature_verified=True,
        document=document,
    )


def load_board_and_registry(
    board_path: pathlib.Path = BOARD_PATH,
    registry_path: pathlib.Path = REGISTRY_PATH,
) -> tuple[SignedDocument, SignedDocument]:
    pub = load_root_public_key()
    board = load_signed_yaml(board_path, pub)
    registry = load_signed_yaml(registry_path, pub)
    return board, registry
