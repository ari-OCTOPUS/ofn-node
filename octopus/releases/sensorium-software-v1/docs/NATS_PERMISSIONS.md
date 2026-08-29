# NATS_PERMISSIONS

Live users (names only): sensorium, leg01.

sensorium may publish octopus.sensor.>, octopus.sensorium.>, octopus.world.>, octopus.audit.>
and subscribe octopus.command.>, octopus.leg.>.

leg01 currently has publish octopus.leg.01.> while leg_authority=DENIED.
A maintenance bundle is prepared to deny-all/remove leg01. It is not applied without owner approval.
Passwords and bcrypt hashes are not documented here.
