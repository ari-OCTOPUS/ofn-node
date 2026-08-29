from octopus_sensorium.snapshot import load_latest


def current() -> dict | None:
    return load_latest()
