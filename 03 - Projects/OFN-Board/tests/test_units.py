"""The systemd units, checked as text.

These are not behavioural tests — systemd is not running in the test process.
They pin three mistakes that were live on the board and that no Python test
could have caught, because none of them is Python:

  * a unit referenced in OnFailure= that was never written or installed,
  * buffered stdout making a healthy node look dead in the journal,
  * a '%' in a unit file, which systemd expands before the shell sees it.
"""

from __future__ import annotations

import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UNITS = os.path.join(ROOT, "deploy", "systemd")
INSTALLER = os.path.join(ROOT, "deploy", "install.sh")


def unit(name: str) -> str:
    with open(os.path.join(UNITS, name), encoding="utf-8") as fh:
        return fh.read()


def unit_names() -> list[str]:
    return sorted(n for n in os.listdir(UNITS)
                  if n.endswith((".service", ".timer")))


class TestEveryReferencedUnitExists(unittest.TestCase):
    def test_onfailure_targets_are_shipped(self):
        """`OnFailure=ofn-backup-alert.service` pointed at nothing, so a
        failed nightly backup notified no one and left no trace."""
        for name in unit_names():
            for target in re.findall(r"^OnFailure=(.+)$", unit(name), re.M):
                for dep in target.split():
                    with self.subTest(unit=name, target=dep):
                        self.assertTrue(
                            os.path.exists(os.path.join(UNITS, dep)),
                            f"{name} declares OnFailure={dep}, which is not "
                            f"in deploy/systemd")

    def test_the_installer_installs_every_unit(self):
        """A unit that exists in the repo but is never copied to
        /etc/systemd/system is the same silence in a different place."""
        with open(INSTALLER, encoding="utf-8") as fh:
            script = fh.read()
        for name in unit_names():
            with self.subTest(unit=name):
                self.assertIn(name, script,
                              f"install.sh never installs {name}")


class TestTheNodeLogsWhileItRuns(unittest.TestCase):
    def test_stdout_is_unbuffered(self):
        """Under systemd stdout is a pipe, so Python buffers it and the boot
        lines only appear when the process exits."""
        self.assertIn("PYTHONUNBUFFERED=1", unit("ofn.service"))


class TestUnitsDoNotTripOnSystemdSpecifiers(unittest.TestCase):
    def test_no_unescaped_percent_in_exec_lines(self):
        """systemd expands '%x' in unit files. A printf format string in an
        ExecStart is consumed before the shell runs, which is how an alert
        ends up appending blank lines."""
        for name in unit_names():
            for line in unit(name).splitlines():
                if not line.startswith(("ExecStart", "ExecStop", "ExecReload")):
                    continue
                with self.subTest(unit=name, line=line):
                    # '%%' is the escape; anything else is an expansion.
                    self.assertNotRegex(
                        line.replace("%%", ""), r"%",
                        f"{name}: '%' in {line!r} is a systemd specifier")


class TestTheAlertStaysInside(unittest.TestCase):
    def test_the_backup_alert_sends_nothing_outward(self):
        """Every outbound path on this node is the owner's decision. An alert
        unit is exactly the thing that would be tempted to bypass that."""
        # Executable lines only. Prose is allowed to say the word "email"
        # while explaining why there is no email.
        execs = "\n".join(line for line in
                          unit("ofn-backup-alert.service").splitlines()
                          if line.startswith("Exec"))
        for outbound in ("curl", "wget", "mail", "sendmail", "ssh", "nc ",
                         "http://", "https://"):
            with self.subTest(term=outbound):
                self.assertNotIn(outbound, execs)

    def test_the_alert_leaves_a_durable_mark(self):
        """It has to survive the power cut it is reporting around."""
        self.assertIn("backup-alerts.log", unit("ofn-backup-alert.service"))


if __name__ == "__main__":
    unittest.main()
