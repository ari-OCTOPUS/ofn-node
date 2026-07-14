"""Project-wide immutable governance constants."""

ELECTRICITY_CEILING_USD_PER_KWH = 0.05
MAX_ACTIVE_EXPERIMENTS_PER_NODE_GROUP = 1
DEFAULT_DEV_DEAD_WEEKS_THRESHOLD = 8

HARD_GATED_ACTIONS = {
    "wallet_access",
    "seed_access",
    "private_key_access",
    "buy",
    "sell",
    "withdraw",
    "deploy",
    "ssh_to_node",
    "start_mining",
    "stop_mining",
    "change_rig_config",
    "mine_above_electricity_ceiling",
}

ALLOWED_REPORT_ACTIONS = {
    "read_status",
    "validate_registry",
    "draft_coin_scout_report",
    "draft_death_watch_report",
    "draft_electricity_feasibility",
    "draft_risk_report",
}

CPU_ARM_PREFERRED_ALGOS = {
    "yespower",
    "yespowerr16",
    "yescrypt",
    "verushash",
    "randomx",
    "randomwow",
    "rx/0",
    "rx/c64",
    "ghostrider",
    "gr",
    "argon2d",
    "astrobwt",
}

GPU_OR_ASIC_DOMINATED_ALGOS = {
    "sha256",
    "sha256d",
    "kheavyhash",
    "ethash",
    "etchash",
    "kawpow",
    "autolykos2",
    "progpow",
    "scrypt",  # context-dependent, often ASIC/GPU competitive
}
