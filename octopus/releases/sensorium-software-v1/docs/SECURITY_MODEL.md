# SECURITY_MODEL

Trust: root-v2 live, root-v1 revoked, signing OFFLINE_ONLY, no v2 private on board.
DevicePolicy=closed. PWM/GPIO/watchdog denied to user octopus.
Policy gate drops enforcing shadow output and all commands (command_trust_root_not_bound).
MQTT closed. Actuator authority NONE.
