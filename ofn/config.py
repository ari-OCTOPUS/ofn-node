"""Runtime configuration from the environment. No secrets in code, ever.

Every value has a safe default that keeps the node inert: outbound flags off,
budget conservative, paths under the user's own directories. A node started
with no configuration at all does nothing harmful — it simply has nothing
switched on.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Mapping

from .adapters import remote_brain


def _flag(name: str) -> bool:
    """Only "1" means on. Not "true", not "yes" — one spelling, no ambiguity."""
    return os.environ.get(name, "0") == "1"


def _int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, "") or default)
    except ValueError:
        return default


def _float(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, "") or default)
    except ValueError:
        return default


@dataclass(frozen=True)
class Config:
    state_dir: str
    packs_dir: str
    utilisation: float
    estimated_capacity_tokens: int
    session_secret: str
    bot_tokens: Mapping[str, str]
    owner_user_ids: tuple[str, ...]
    # tenant -> the Telegram accounts allowed to open that partner's shell.
    # A tenant absent from this map has no partners, which means no entry.
    partner_user_ids: Mapping[str, tuple[str, ...]]
    remote_api_key: str
    remote_base_url: str
    ports: Mapping[str, int]
    hosts: Mapping[str, str]
    owner_host: str
    wire_outbound: bool = False
    base_closed_gates: tuple[str, ...] = field(default_factory=tuple)

    @property
    def ledger_path(self) -> str:
        return os.path.join(self.state_dir, "ledger.sqlite")

    @property
    def facts_path(self) -> str:
        return os.path.join(self.state_dir, "facts.sqlite")

    @property
    def outbox_path(self) -> str:
        return os.path.join(self.state_dir, "outbox.sqlite")

    @property
    def products_path(self) -> str:
        return os.environ.get("OFN_PRODUCTS_DB") or os.path.join(
            self.state_dir, "products.sqlite")

    @property
    def studio_path(self) -> str:
        """Collections, drafts, media order, and what actually went out."""
        return os.environ.get("OFN_STUDIO_DB") or os.path.join(
            self.state_dir, "studio.sqlite")

    @property
    def audience_path(self) -> str:
        """Subscribers, money, and how much of the audience she owns.

        Created before there is a single subscriber. The month a business
        starts is the month churn is decided, and a table added afterwards
        cannot describe it.
        """
        return os.environ.get("OFN_AUDIENCE_DB") or os.path.join(
            self.state_dir, "audience.sqlite")

    @property
    def consent_path(self) -> str:
        """Who agreed to appear in content, and where it ended up.

        In the state directory with every other database, not in the repo.
        The studio brief writes it as `~/ofn/consent.sqlite`; that would put
        consent records inside a git working tree, one `git add -A` away from
        being committed. It also keeps it out of the nightly backup and out
        of the boot integrity check, which are the two things this file most
        needs to be inside.
        """
        return os.environ.get("OFN_CONSENT_DB") or os.path.join(
            self.state_dir, "consent.sqlite")

    @property
    def photos_root(self) -> str:
        """Where photo bytes live — beside the database, not inside it.

        Kept out of SQLite so a 40 MB product does not turn every read of the
        row into a 40 MB read, and so a backup can copy the small file often
        and the large directory rarely.
        """
        return os.environ.get("OFN_PHOTOS_DIR") or os.path.join(
            self.state_dir, "photos")

    @property
    def backup_root(self) -> str:
        return os.path.join(self.state_dir, "backups")

    @property
    def db_paths(self) -> Mapping[str, str]:
        # products belongs here for the same reason the other three do: this
        # is the set the boot probe integrity-checks and the backup copies.
        # A database that is not in this map is one nobody notices has gone
        # bad until somebody opens it looking for a year of work.
        return {"ledger": self.ledger_path, "facts": self.facts_path,
                "outbox": self.outbox_path, "products": self.products_path,
                "consent": self.consent_path,
                "studio": self.studio_path,
                "audience": self.audience_path}


def load() -> Config:
    home = os.path.expanduser("~")
    state = os.environ.get("OFN_STATE_DIR") or os.path.join(
        home, ".local", "share", "ofn")
    packs = os.environ.get("OFN_PACKS_DIR") or os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "packs")
    domain = os.environ.get("OFN_DOMAIN", "master-painting.com")

    # miner_isolation stays shut until D-8's items 1-3 are done and the owner
    # says so. It only bites once a pack declares it — no mining pack exists
    # yet, so arming it here costs nothing and means the wiring is already in
    # place the day one does.
    gates: list[str] = ["secret_rotation", "miner_isolation"]
    extra = os.environ.get("OFN_EXTRA_CLOSED_GATES", "")
    gates += [g.strip() for g in extra.split(",") if g.strip()]

    return Config(
        state_dir=state,
        packs_dir=packs,
        utilisation=_float("OFN_UTILISATION", 0.40),
        estimated_capacity_tokens=_int("OFN_ESTIMATED_CAPACITY_TOKENS",
                                       180_000_000),
        session_secret=os.environ.get("OFN_SESSION_SECRET", ""),
        bot_tokens={
            "ziman": os.environ.get("OFN_BOT_TOKEN_ZIMAN", ""),
            "lead": os.environ.get("OFN_BOT_TOKEN_LEAD", ""),
            "studio": os.environ.get("OFN_BOT_TOKEN_STUDIO", ""),
            "__owner__": os.environ.get("OFN_BOT_TOKEN_OWNER", ""),
        },
        partner_user_ids={
            leg: tuple(
                u.strip() for u in
                os.environ.get(f"OFN_PARTNER_USER_IDS_{leg.upper()}", "").split(",")
                if u.strip())
            for leg in ("ziman", "lead", "studio")
        },
        owner_user_ids=tuple(
            u.strip() for u in os.environ.get("OFN_OWNER_USER_IDS", "").split(",")
            if u.strip()),
        remote_api_key=os.environ.get("OFN_REMOTE_API_KEY", ""),
        # The provider's API is OpenAI-compatible, which is the one piece of
        # good news about depending on it: moving to another vendor is a URL
        # change rather than a rewrite. Keeping that as an env var rather than
        # a constant is what makes the escape hatch real instead of theoretical
        # — and it is what lets the deployment probe be tested against a stub.
        remote_base_url=os.environ.get("OFN_REMOTE_BASE_URL",
                                       remote_brain.DEFAULT_BASE_URL),
        ports={"ziman": 8791, "lead": 8792, "studio": 8793, "owner": 8794},
        hosts={f"ziman.{domain}": "ziman", f"lead.{domain}": "lead",
               f"studio.{domain}": "studio",
               # Saba's mini app is reached at `app.<domain>/sabaapp`. Both
               # hostnames resolve to the same leg on the same port; the
               # second exists because that is the URL the bot's menu button
               # points at, and a Telegram Web App URL is not something a
               # partner can be asked to change later.
               f"app.{domain}": "studio"},
        owner_host=f"panel.{domain}",
        wire_outbound=_flag("OFN_WIRE_OUTBOUND"),
        base_closed_gates=tuple(gates),
    )


def epoch_seconds() -> int:
    return int(time.time())


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
