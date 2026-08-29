#!/usr/bin/env python3
"""Write /etc/nats/nats-server.conf from env files. Passwords are never printed.

INCLUDE_PROVISIONER=1 adds sensorium-provisioner (one-shot JetStream admin).
The runtime sensorium user never receives $JS.API.STREAM.> or $JS.API.CONSUMER.>.
"""

from __future__ import annotations

import os
import pathlib
import pwd
import secrets

import bcrypt

LISTEN = os.environ.get("NATS_LISTEN", "192.168.0.182")
CA = pathlib.Path(os.environ.get("OCTOPUS_CA", "/root/octopus-ca"))
SECRETS = pathlib.Path(os.environ.get("OCTOPUS_SECRETS", "/etc/octopus/secrets"))
CONF = pathlib.Path("/etc/nats/nats-server.conf")
INCLUDE_PROVISIONER = os.environ.get("INCLUDE_PROVISIONER", "0") == "1"


def hash_pw(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt(rounds=11)).decode()


def load_or_create(path: pathlib.Path, user: str, mode: int) -> str:
    if path.exists():
        vals = dict(
            line.strip().split("=", 1)
            for line in path.read_text(encoding="utf-8").splitlines()
            if "=" in line and not line.strip().startswith("#")
        )
        return vals["NATS_PASSWORD"]
    pw = secrets.token_urlsafe(24)
    path.write_text(
        f"NATS_USER={user}\nNATS_PASSWORD={pw}\nNATS_URL=nats://{LISTEN}:4222\n",
        encoding="utf-8",
    )
    path.chmod(mode)
    return pw


def main() -> None:
    CA.mkdir(parents=True, exist_ok=True)
    SECRETS.mkdir(parents=True, exist_ok=True)
    sensorium_hash = hash_pw(load_or_create(SECRETS / "nats-sensorium.env", "sensorium", 0o640))
    load_or_create(CA / "nats-leg01.env", "leg01", 0o600)
    users_block = f"""    {{
      user: sensorium
      password: "{sensorium_hash}"
      permissions: {{
        publish: [
          "octopus.sensor.>",
          "octopus.sensorium.>",
          "octopus.world.>",
          "octopus.audit.>",
          "octopus.leg.*.response"
        ]
        subscribe: [
          "octopus.command.>",
          "octopus.leg.>",
          "_INBOX.>"
        ]
      }}
    }}
    {{
      user: leg01
      password: "{hash_pw(load_or_create(CA / "nats-leg01.env", "leg01", 0o600))}"
      permissions: {{
        publish: ["octopus.leg.01.>"]
        subscribe: [
          "octopus.sensor.feature.>",
          "octopus.world.>",
          "octopus.leg.01.response",
          "_INBOX.>"
        ]
      }}
    }}"""
    if INCLUDE_PROVISIONER:
        prov_hash = hash_pw(
            load_or_create(CA / "nats-provisioner.env", "sensorium-provisioner", 0o600)
        )
        users_block = f"""    {{
      user: sensorium-provisioner
      password: "{prov_hash}"
      permissions: {{
        publish: [
          "$JS.API.INFO",
          "$JS.API.STREAM.>",
          "$JS.API.CONSUMER.>"
        ]
        subscribe: ["_INBOX.>"]
      }}
    }}
{users_block}"""
    conf = f"""server_name: sensorium-opi5pro
listen: {LISTEN}:4222
http: 127.0.0.1:8222

jetstream {{
  store_dir: /var/lib/nats/jetstream
  max_memory_store: 256MB
  max_file_store: 8GB
}}

authorization {{
  users = [
{users_block}
  ]
}}
"""
    CONF.parent.mkdir(parents=True, exist_ok=True)
    CONF.write_text(conf, encoding="utf-8")
    CONF.chmod(0o640)
    os.chown(CONF, 0, pwd.getpwnam("nats").pw_gid)
    print("wrote", CONF, "provisioner", INCLUDE_PROVISIONER)


if __name__ == "__main__":
    main()
