#!/usr/bin/env python3
"""OCTOPUS RK35xx validation suite: dependency-free T2/T3/T4.

Target: Linux aarch64 / RK35xx / CPU-only llama.cpp / eMMC mmcblk0.
No NumPy, pandas, nvidia-smi, smartctl, powercap, or root required for reads.

Examples:
  python3 octopus_board_validation.py --audit
  python3 octopus_board_validation.py --t2
  python3 octopus_board_validation.py --t3
  python3 octopus_board_validation.py --t4 --sample-seconds 60 --interval 2
  python3 octopus_board_validation.py --all --sample-seconds 10
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import glob
import hashlib
import json
import math
import os
import platform
import random
import sys
import time
from pathlib import Path
from typing import Any, Iterable

SCRIPT_VERSION = "0.3.0-rk35xx"
SECTOR_BYTES = 512
DEFAULT_DEVICE = "mmcblk0"


def utc_stamp() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


def utc_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def read_text(path: str | Path) -> str | None:
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace").strip()
    except (OSError, PermissionError):
        return None


def read_int(path: str | Path) -> int | None:
    value = read_text(path)
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def sha256(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def atomic_json(path: Path, value: Any) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True), encoding="utf-8")
    os.replace(tmp, path)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def new_run_dir(base: str) -> Path:
    root = Path(base).resolve()
    for protected in (Path("/sys"), Path("/proc"), Path("/dev")):
        if root == protected or protected in root.parents:
            raise ValueError(f"Refusing to write validation output below {protected}")
    root.mkdir(parents=True, exist_ok=True)
    stem = f"run_{utc_stamp()}_p{os.getpid()}"
    for attempt in range(100):
        suffix = "" if attempt == 0 else f"_{attempt}"
        path = root / f"{stem}{suffix}"
        try:
            path.mkdir(exist_ok=False)
            return path
        except FileExistsError:
            continue
    raise RuntimeError("Could not allocate a unique validation run directory")


def environment_snapshot() -> dict[str, Any]:
    return {
        "captured_utc": utc_iso(),
        "script_version": SCRIPT_VERSION,
        "script_sha256": sha256(Path(__file__).resolve()),
        "python": sys.version,
        "executable": sys.executable,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "kernel": platform.release(),
        "hostname": platform.node(),
        "uid": os.getuid() if hasattr(os, "getuid") else None,
        "cwd": os.getcwd(),
        "stdlib_only": True,
    }


# ------------------------------- Audit --------------------------------------
def audit() -> dict[str, Any]:
    mmc_paths = sorted(glob.glob("/sys/class/mmc_host/mmc*/mmc*:*/"))
    result = {
        "environment": environment_snapshot(),
        "capabilities": {
            "mmcblk0_stat": Path("/sys/block/mmcblk0/stat").exists(),
            "thermal_zones": len(glob.glob("/sys/class/thermal/thermal_zone*/temp")),
            "cpu_freq_nodes": len(glob.glob("/sys/devices/system/cpu/cpu*/cpufreq/scaling_cur_freq")),
            "devfreq_nodes": len(glob.glob("/sys/class/devfreq/*/cur_freq")),
            "mmc_devices": mmc_paths,
            "powercap_present": Path("/sys/class/powercap").exists(),
            "nvidia_present": Path("/proc/driver/nvidia").exists(),
        },
        "constraints": {
            "t1_power_scaling_valid": False,
            "reason": "No calibrated power sensor is assumed; performance/thermal scaling only.",
            "t4_mode": "SCHEMA_SMOKE_TEST_AND_WEAR_TELEMETRY",
        },
    }
    return result


# ------------------------------- T2 -----------------------------------------
def kl_bits(p: list[float], q: list[float]) -> float:
    total = 0.0
    for pi, qi in zip(p, q):
        pi = max(pi, 1e-15)
        qi = max(qi, 1e-15)
        total += pi * math.log2(pi / qi)
    return total


def total_variation(p: list[float], q: list[float]) -> float:
    return 0.5 * sum(abs(a - b) for a, b in zip(p, q))


def belief_run(
    observations: list[int],
    precisions: list[float],
    hypotheses: int = 8,
    persistence_steps: int = 20,
    persistence_epsilon: float = 0.15,
    info_threshold_bits: float = 0.02,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    belief = [1.0 / hypotheses] * hypotheses
    beliefs: list[list[float]] = []
    information: list[float] = []

    for obs, precision in zip(observations, precisions):
        likelihood = [0.15 / (hypotheses - 1)] * hypotheses
        likelihood[obs] = 0.85
        likelihood = [x ** precision for x in likelihood]
        prior = belief[:]
        unnormalised = [prior[i] * likelihood[i] for i in range(hypotheses)]
        z = sum(unnormalised)
        belief = [x / z for x in unnormalised]
        information.append(kl_bits(belief, prior))
        beliefs.append(belief[:])

    rows: list[dict[str, Any]] = []
    gated_total = 0.0
    n_cog = 0
    for i, raw in enumerate(information):
        future_index = min(i + persistence_steps, len(beliefs) - 1)
        persistence_distance = total_variation(beliefs[i], beliefs[future_index])
        persistent = persistence_distance < persistence_epsilon
        gated = raw if persistent else 0.0
        counted = gated > info_threshold_bits
        gated_total += gated
        n_cog += int(counted)
        rows.append({
            "event": i,
            "observation": observations[i],
            "precision": precisions[i],
            "raw_information_bits": raw,
            "future_tv_distance": persistence_distance,
            "persistent": int(persistent),
            "gated_information_bits": gated,
            "counted_cognition": int(counted),
        })

    summary = {
        "events": len(observations),
        "raw_information_bits": sum(information),
        "persistent_information_bits": gated_total,
        "raw_bits": sum(information),
        "persistence_gated_bits": gated_total,
        "n_cog": n_cog,
        "theta_subj": None,
        "theta_subj_status": "NOT_CALCULATED_NO_CALIBRATED_MAPPING",
        "parameters": {
            "hypotheses": hypotheses,
            "persistence_steps": persistence_steps,
            "persistence_epsilon": persistence_epsilon,
            "info_threshold_bits": info_threshold_bits,
        },
    }
    return summary, rows


def run_t2(run_dir: Path, events: int = 1000, seed: int = 7) -> dict[str, Any]:
    rng = random.Random(seed)
    hypotheses = 8
    block = max(1, events // 40)
    shifts = []
    for k in range(40):
        shifts.extend([int((k * 3) % hypotheses)] * block)
    shifts = (shifts + [shifts[-1]] * events)[:events]

    scenarios = {
        "A_identical": ([3] * events, [1.0] * events),
        "B_noise_low_precision": (
            [rng.randrange(hypotheses) for _ in range(events)], [0.15] * events
        ),
        "C_noise_high_precision": (
            [rng.randrange(hypotheses) for _ in range(events)], [1.0] * events
        ),
        "D_persistent_regime_shifts": (shifts, [1.0] * events),
    }

    summaries: dict[str, dict[str, Any]] = {}
    for name, (obs, precision) in scenarios.items():
        summary, rows = belief_run(obs, precision)
        summaries[name] = summary
        write_csv(run_dir / f"t2_{name}_raw.csv", rows)

    g = {k: v["persistent_information_bits"] for k, v in summaries.items()}
    checks = {
        "identical_below_5pct_regime": g["A_identical"] < 0.05 * g["D_persistent_regime_shifts"],
        "low_precision_noise_below_25pct_regime": g["B_noise_low_precision"] < 0.25 * g["D_persistent_regime_shifts"],
        "persistent_regime_exceeds_high_precision_noise": g["D_persistent_regime_shifts"] > g["C_noise_high_precision"],
    }
    result = {
        "test": "T2",
        "scope": "DETERMINISTIC_METRIC_BEHAVIOUR_SIMULATION_NOT_SUBJECTIVE_TIME_PROOF",
        "metric_contract": {
            "raw_information": "KL information before persistence gating",
            "persistent_information": "KL information retained by the slow-scale persistence gate",
            "n_cog": "Count above the configured persistent-information threshold",
            "theta_subj": "Not calculated without a separately calibrated mapping",
        },
        "seed": seed,
        "summaries": summaries,
        "checks": checks,
        "verdict": "PASS" if all(checks.values()) else "FAIL",
    }
    atomic_json(run_dir / "t2_result.json", result)
    return result


# ------------------------------- T3 -----------------------------------------
def run_t3(run_dir: Path, events: int = 200, sleep_ms: float = 1.0) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    fake_wall_offset = 0.0
    for i in range(events):
        if i == events // 2:
            fake_wall_offset = -3600.0
        rows.append({
            "event": i,
            "monotonic_ns": time.monotonic_ns(),
            "synthetic_wall_s": time.time() + fake_wall_offset,
            "synthetic_offset_s": fake_wall_offset,
        })
        time.sleep(sleep_ms / 1000.0)

    monotonic_deltas = [rows[i]["monotonic_ns"] - rows[i - 1]["monotonic_ns"] for i in range(1, len(rows))]
    wall_deltas = [rows[i]["synthetic_wall_s"] - rows[i - 1]["synthetic_wall_s"] for i in range(1, len(rows))]
    mono_order = [x["event"] for x in sorted(rows, key=lambda x: x["monotonic_ns"])]
    wall_order = [x["event"] for x in sorted(rows, key=lambda x: x["synthetic_wall_s"])]
    checks = {
        "monotonic_never_decreased": all(x > 0 for x in monotonic_deltas),
        "wall_clock_jump_was_observed": any(x < 0 for x in wall_deltas),
        "monotonic_event_order_preserved": mono_order == list(range(events)),
        "wall_clock_event_order_broken": wall_order != list(range(events)),
    }
    write_csv(run_dir / "t3_raw.csv", rows)
    result = {
        "test": "T3",
        "scope": "SYNTHETIC_WALL_CLOCK_JUMP_UNIT_TEST_NO_SYSTEM_CLOCK_CHANGE",
        "ordering_clock": "MONOTONIC_WITHIN_BOOT",
        "wall_clock_role": "METADATA_ONLY",
        "cross_boot_ordering": "NOT_TESTED_REQUIRES_BOOT_ID_AND_HLC",
        "checks": checks,
        "minimum_monotonic_delta_ns": min(monotonic_deltas),
        "minimum_wall_delta_s": min(wall_deltas),
        "verdict": "PASS" if all(checks.values()) else "FAIL",
    }
    atomic_json(run_dir / "t3_result.json", result)
    return result


# ------------------------------- T4 -----------------------------------------
def parse_hex_byte(text: str | None, index: int = 0) -> int | None:
    if not text:
        return None
    tokens = text.replace(",", " ").split()
    if index >= len(tokens):
        return None
    try:
        return int(tokens[index], 16)
    except ValueError:
        return None


def mmc_health() -> list[dict[str, Any]]:
    devices = []
    for base in sorted(glob.glob("/sys/class/mmc_host/mmc*/mmc*:*/")):
        life_raw = read_text(Path(base) / "life_time")
        pre_raw = read_text(Path(base) / "pre_eol_info")
        if pre_raw is None:
            pre_raw = read_text(Path(base) / "pre_eol")
        life_a = parse_hex_byte(life_raw, 0)
        life_b = parse_hex_byte(life_raw, 1)
        pre = parse_hex_byte(pre_raw, 0)
        devices.append({
            "sysfs_path": base,
            "name": read_text(Path(base) / "name"),
            "cid": read_text(Path(base) / "cid"),
            "life_time_raw": life_raw,
            "life_time_a_code": life_a,
            "life_time_b_code": life_b,
            "life_time_a_interpretation": lifetime_interpretation(life_a),
            "life_time_b_interpretation": lifetime_interpretation(life_b),
            "pre_eol_raw": pre_raw,
            "pre_eol_code": pre,
            "pre_eol_interpretation": pre_eol_interpretation(pre),
        })
    return devices


def lifetime_interpretation(code: int | None) -> str:
    if code is None:
        return "UNAVAILABLE"
    if code == 0:
        return "NOT_DEFINED"
    if 1 <= code <= 10:
        lo, hi = (code - 1) * 10, code * 10
        return f"ESTIMATED_{lo}_TO_{hi}_PERCENT_USED"
    if code == 11:
        return "ESTIMATED_LIFETIME_EXCEEDED"
    return "RESERVED_OR_UNKNOWN"


def pre_eol_interpretation(code: int | None) -> str:
    return {
        None: "UNAVAILABLE",
        0: "NOT_DEFINED",
        1: "NORMAL",
        2: "WARNING_80_PERCENT_RESERVED_BLOCKS_CONSUMED",
        3: "URGENT_90_PERCENT_RESERVED_BLOCKS_CONSUMED",
    }.get(code, "RESERVED_OR_UNKNOWN")


def block_stat(device: str) -> dict[str, int] | None:
    values = read_text(f"/sys/block/{device}/stat")
    if not values:
        return None
    fields = [int(x) for x in values.split()]
    if len(fields) < 11:
        return None
    names = [
        "reads_completed", "reads_merged", "sectors_read", "read_ms",
        "writes_completed", "writes_merged", "sectors_written", "write_ms",
        "ios_in_progress", "io_ms", "weighted_io_ms",
    ]
    result = dict(zip(names, fields[:11]))
    result["bytes_read_512_sector_units"] = result["sectors_read"] * SECTOR_BYTES
    result["bytes_written_512_sector_units"] = result["sectors_written"] * SECTOR_BYTES
    return result


def thermal_snapshot() -> list[dict[str, Any]]:
    zones = []
    for temp_path in sorted(glob.glob("/sys/class/thermal/thermal_zone*/temp")):
        base = Path(temp_path).parent
        raw = read_int(temp_path)
        if raw is None:
            continue
        celsius = raw / 1000.0 if abs(raw) > 1000 else float(raw)
        zones.append({"zone": base.name, "type": read_text(base / "type"), "temp_c": celsius})
    return zones


def frequency_snapshot() -> dict[str, list[dict[str, Any]]]:
    cpu = []
    for path in sorted(glob.glob("/sys/devices/system/cpu/cpu*/cpufreq/scaling_cur_freq")):
        value = read_int(path)
        cpu.append({"path": path, "frequency_khz": value})
    devfreq = []
    for path in sorted(glob.glob("/sys/class/devfreq/*/cur_freq")):
        value = read_int(path)
        devfreq.append({"path": path, "frequency_hz": value})
    return {"cpu": cpu, "devfreq": devfreq}


def process_io_snapshot() -> dict[str, dict[str, Any]]:
    """Read per-process I/O counters without attributing them to one block device."""
    snapshot: dict[str, dict[str, Any]] = {}
    for io_path in sorted(glob.glob("/proc/[0-9]*/io")):
        base = Path(io_path).parent
        pid = base.name
        io_text = read_text(io_path)
        stat_text = read_text(base / "stat")
        if io_text is None or stat_text is None or ")" not in stat_text:
            continue

        stat_fields = stat_text.rsplit(")", 1)[1].split()
        if len(stat_fields) <= 19:
            continue
        try:
            starttime_ticks = int(stat_fields[19])
        except ValueError:
            continue

        counters: dict[str, int] = {}
        for line in io_text.splitlines():
            if ":" not in line:
                continue
            name, raw = line.split(":", 1)
            try:
                counters[name] = int(raw.strip())
            except ValueError:
                continue

        identity = f"{pid}:{starttime_ticks}"
        snapshot[identity] = {
            "pid": int(pid),
            "starttime_ticks": starttime_ticks,
            "comm": read_text(base / "comm"),
            "read_bytes": counters.get("read_bytes", 0),
            "write_bytes": counters.get("write_bytes", 0),
            "cancelled_write_bytes": counters.get("cancelled_write_bytes", 0),
        }
    return snapshot


def process_io_deltas(
    start: dict[str, dict[str, Any]],
    end: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    deltas: list[dict[str, Any]] = []
    for identity in sorted(start.keys() & end.keys()):
        before = start[identity]
        after = end[identity]
        read_delta = after["read_bytes"] - before["read_bytes"]
        write_delta = after["write_bytes"] - before["write_bytes"]
        cancelled_delta = (
            after["cancelled_write_bytes"] - before["cancelled_write_bytes"]
        )
        if read_delta == 0 and write_delta == 0 and cancelled_delta == 0:
            continue
        deltas.append({
            "identity": identity,
            "pid": after["pid"],
            "comm": after["comm"],
            "read_bytes_delta": read_delta,
            "write_bytes_delta": write_delta,
            "cancelled_write_bytes_delta": cancelled_delta,
            "net_write_bytes_proxy": write_delta - cancelled_delta,
        })
    return sorted(
        deltas,
        key=lambda row: (row["write_bytes_delta"], row["read_bytes_delta"]),
        reverse=True,
    )


def count_thermal_excursions(values: list[float], delta_c: float = 15.0) -> int:
    if not values:
        return 0
    low = values[0]
    armed = True
    cycles = 0
    for value in values[1:]:
        low = min(low, value)
        if armed and value - low >= delta_c:
            cycles += 1
            armed = False
        if not armed and value <= low + delta_c / 3:
            low = value
            armed = True
    return cycles


def run_t4(run_dir: Path, device: str, sample_seconds: int, interval: float) -> dict[str, Any]:
    start_stat = block_stat(device)
    start_process_io = process_io_snapshot()
    samples: list[dict[str, Any]] = []
    start_mono = time.monotonic()
    deadline = start_mono + max(0, sample_seconds)

    while True:
        elapsed = time.monotonic() - start_mono
        zones = thermal_snapshot()
        freqs = frequency_snapshot()
        sample = {
            "captured_utc": utc_iso(),
            "elapsed_s": elapsed,
            "loadavg": read_text("/proc/loadavg"),
            "block_stat": block_stat(device),
            "thermal": zones,
            "frequencies": freqs,
        }
        samples.append(sample)
        if time.monotonic() >= deadline:
            break
        time.sleep(max(0.1, min(interval, deadline - time.monotonic())))

    end_stat = block_stat(device)
    end_process_io = process_io_snapshot()
    process_deltas = process_io_deltas(start_process_io, end_process_io)
    delta = None
    if start_stat and end_stat:
        delta = {
            key: end_stat[key] - start_stat[key]
            for key in start_stat
            if isinstance(start_stat[key], int) and key in end_stat
        }
        elapsed = max(samples[-1]["elapsed_s"], 1e-9)
        delta["write_bytes_per_second"] = delta["bytes_written_512_sector_units"] / elapsed
        delta["read_bytes_per_second"] = delta["bytes_read_512_sector_units"] / elapsed

    zone_series: dict[str, list[float]] = {}
    for sample in samples:
        for zone in sample["thermal"]:
            key = f'{zone["zone"]}:{zone["type"]}'
            zone_series.setdefault(key, []).append(zone["temp_c"])

    thermal_summary = {
        zone: {
            "min_c": min(values),
            "mean_c": sum(values) / len(values),
            "max_c": max(values),
            "range_c": max(values) - min(values),
            "excursions_ge_15c": count_thermal_excursions(values, 15.0),
        }
        for zone, values in zone_series.items()
    }
    health = mmc_health()
    atomic_json(run_dir / "t4_samples.json", samples)
    atomic_json(run_dir / "t4_process_io_start.json", start_process_io)
    atomic_json(run_dir / "t4_process_io_end.json", end_process_io)
    result = {
        "test": "T4",
        "label": "SCHEMA_SMOKE_TEST",
        "device": device,
        "duration_s": samples[-1]["elapsed_s"],
        "sample_count": len(samples),
        "power_measurement": "UNAVAILABLE_NO_EXTERNAL_POWER_METER",
        "wear_lifetime_prediction": "NOT_CALCULATED_INSUFFICIENT_CALIBRATION",
        "start_block_stat": start_stat,
        "end_block_stat": end_stat,
        "delta": delta,
        "mmc_health": health,
        "thermal_summary": thermal_summary,
        "process_io_attribution": {
            "scope": "PROC_IO_DELTA_PROXY_NOT_BLOCK_DEVICE_OR_NAND_ATTRIBUTION",
            "matched_processes_with_io": len(process_deltas),
            "top_by_write_bytes": process_deltas[:20],
        },
        "checks": {
            "block_stat_available": start_stat is not None,
            "mmc_health_available": any(
                item["life_time_raw"] is not None or item["pre_eol_raw"] is not None
                for item in health
            ),
            "thermal_data_available": len(zone_series) > 0,
        },
        "verdict": "SCHEMA_SMOKE_TEST",
    }
    atomic_json(run_dir / "t4_result.json", result)
    return result


# ------------------------------- Main ---------------------------------------
def compact(result: dict[str, Any]) -> str:
    return json.dumps(result, indent=2, sort_keys=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit", action="store_true")
    parser.add_argument("--t2", action="store_true")
    parser.add_argument("--t3", action="store_true")
    parser.add_argument("--t4", action="store_true")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--device", default=DEFAULT_DEVICE)
    parser.add_argument("--sample-seconds", type=int, default=10)
    parser.add_argument("--interval", type=float, default=1.0)
    parser.add_argument("--output", default="validation_runs")
    args = parser.parse_args()

    selected = args.audit or args.t2 or args.t3 or args.t4 or args.all
    if not selected:
        parser.error("Choose --audit, --t2, --t3, --t4, or --all")

    run_dir = new_run_dir(args.output)
    env = environment_snapshot()
    atomic_json(run_dir / "environment.json", env)
    results: dict[str, Any] = {"environment": env, "run_dir": str(run_dir)}

    if args.audit or args.all:
        results["audit"] = audit()
        atomic_json(run_dir / "audit.json", results["audit"])
    if args.t2 or args.all:
        results["T2"] = run_t2(run_dir)
    if args.t3 or args.all:
        results["T3"] = run_t3(run_dir)
    if args.t4 or args.all:
        results["T4"] = run_t4(run_dir, args.device, args.sample_seconds, args.interval)

    atomic_json(run_dir / "summary.json", results)
    hashes = {}
    for path in sorted(run_dir.iterdir()):
        if path.is_file() and path.name != "SHA256SUMS.json":
            hashes[path.name] = sha256(path)
    atomic_json(run_dir / "SHA256SUMS.json", hashes)

    print(compact(results))
    print(f"SEALED_RUN_DIR={run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
