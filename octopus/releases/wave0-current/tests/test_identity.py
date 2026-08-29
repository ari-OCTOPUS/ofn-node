from __future__ import annotations

from octopus_sensorium.identity import derive_board_id, load_identity, read_serial


def test_board_id_not_hostname():
    identity = load_identity()
    assert identity.board_id != identity.hostname
    assert identity.board_id.startswith("sensorium-opi5pro-")
    assert identity.serial
    assert identity.machine_id


def test_derive_from_known_serial():
    assert derive_board_id("68e44cdfcb8d57ce") == "sensorium-opi5pro-68e44cdf"


def test_read_serial_matches_cpuinfo(tmp_path):
    cpu = tmp_path / "cpuinfo"
    cpu.write_text("processor : 0\nSerial\t: 68e44cdfcb8d57ce\n")
    assert read_serial(cpu) == "68e44cdfcb8d57ce"
