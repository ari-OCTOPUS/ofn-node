cd ~/ofn || { echo 'CD_FAIL'; exit 9; }
export PYTHONDONTWRITEBYTECODE=1
echo '=====ROW GAP-002'
o=$( { echo 'cHl0aG9uIC1tIHRvb2xzLm1lc2hfYXVkaXQgLS1ub2RlIDE4MCAtLWpzb24gfCBqcSAnWy5vdXRib3hbXXxzZWxlY3QoLnR0bD09bnVsbCldfGxlbmd0aCc=' | base64 -d | timeout 60 bash; } 2>&1 ); rc=$?
echo "RC=$rc"
echo "OUT=$o"

echo '=====ROW GAP-004'
o=$( { echo 'cHl0aG9uIC1tIHRvb2xzLmR1YWxfb3V0Ym94X3ZlcmlmeSAtLWpzb24gfCBqcSAtciAuc3RhdHVz' | base64 -d | timeout 60 bash; } 2>&1 ); rc=$?
echo "RC=$rc"
echo "OUT=$o"

echo '=====ROW GAP-006'
o=$( { echo 'cHl0aG9uIC1tIHRvb2xzLnF1ZXVlX2F1ZGl0IC0tYmF0Y2ggMTggLS1qc29uIHwganEgLXIgLmRlcGxveWVk' | base64 -d | timeout 60 bash; } 2>&1 ); rc=$?
echo "RC=$rc"
echo "OUT=$o"

echo '=====ROW GAP-008'
o=$( { echo 'cHl0aG9uIC1tIHB5dGVzdCB0ZXN0cy90ZXN0X2RyYWluX3NlbWFudGljcy5weSAtcSAtcCBubzpjYWNoZXByb3ZpZGVy' | base64 -d | timeout 60 bash; } 2>&1 ); rc=$?
echo "RC=$rc"
echo "OUT=$o"

echo '=====ROW GAP-009'
o=$( { echo 'cHl0aG9uIC1tIHRvb2xzLnB1bHNlIC0tZHJ5LXJ1biB8IHJnIC1jICLYr9qp2KrYsToi' | base64 -d | timeout 60 bash; } 2>&1 ); rc=$?
echo "RC=$rc"
echo "OUT=$o"

echo '=====ROW GAP-010'
o=$( { echo 'cmcgLWMgIk9XTkVSLVFVRVVFIiB0b29scy8gb2ZuLyAtLWdsb2IgIiF0ZXN0cy8qKiI=' | base64 -d | timeout 60 bash; } 2>&1 ); rc=$?
echo "RC=$rc"
echo "OUT=$o"

echo '=====ROW GAP-011'
o=$( { echo 'cmcgLWMgIlNJTEVOVF9GTElQIiB0b29scy9wdWxzZS5weSBvZm4vYWRhcHRlcnMv' | base64 -d | timeout 60 bash; } 2>&1 ); rc=$?
echo "RC=$rc"
echo "OUT=$o"

echo '=====ROW GAP-012'
o=$( { echo 'cHl0aG9uIC1tIHRvb2xzLmxlYXJuaW5nX2ZlZWRlciAtLWRyeS1ydW4gLS1qc29uIHwganEgLXIgLnJ1bnNfd3JpdHRlbg==' | base64 -d | timeout 60 bash; } 2>&1 ); rc=$?
echo "RC=$rc"
echo "OUT=$o"

echo '=====ROW GAP-013'
o=$( { echo 'cHl0aG9uIC1tIHB5dGVzdCB0ZXN0cy90ZXN0X3RlbGVncmFtX2dsYXNzX3J1bm5lci5weSAtcSAtcCBubzpjYWNoZXByb3ZpZGVy' | base64 -d | timeout 60 bash; } 2>&1 ); rc=$?
echo "RC=$rc"
echo "OUT=$o"

echo '=====ROW GAP-015'
o=$( { echo 'cmcgLWMgImJvYXJkX2V2ZW50cyIgb2ZuLyB0b29scy8gLS1nbG9iICIhdGVzdHMvKioi' | base64 -d | timeout 60 bash; } 2>&1 ); rc=$?
echo "RC=$rc"
echo "OUT=$o"

echo '=====ROW GAP-017'
o=$( { echo 'cHl0aG9uIC1tIHRvb2xzLmRvY3RvciAtLWpzb24gfCBqcSAnWy51bml0c1tdfHNlbGVjdCgudHlwZT09Im9uZXNob3QiIGFuZCAuc3RhdHVzPT0iVU5LTk9XTiIpXXxsZW5ndGgn' | base64 -d | timeout 60 bash; } 2>&1 ); rc=$?
echo "RC=$rc"
echo "OUT=$o"

echo '=====ROW GAP-018'
o=$( { echo 'cHl0aG9uIC1tIHRvb2xzLmRvY3RvciAtLWNoZWNrIGltYXAgLS1qc29uIHwganEgLXIgLnN0YXR1cw==' | base64 -d | timeout 60 bash; } 2>&1 ); rc=$?
echo "RC=$rc"
echo "OUT=$o"

echo '=====ROW GAP-019'
o=$( { echo 'am91cm5hbGN0bCAtdSBvY3RvcHVzLWRvY3RvciAtbiAxIC0tbm8tcGFnZXI=' | base64 -d | timeout 60 bash; } 2>&1 ); rc=$?
echo "RC=$rc"
echo "OUT=$o"

echo '=====ROW GAP-022'
o=$( { echo 'cHl0aG9uIC1tIHRvb2xzLmhvbWVvc3RhdCAtLWpzb24gfCBqcSAnWy5zaWduYWxzW118c2VsZWN0KC5zb3VyY2U9PW51bGwgYW5kIC56b25lIT0iV0lTSExJU1QiKV18bGVuZ3RoJw==' | base64 -d | timeout 60 bash; } 2>&1 ); rc=$?
echo "RC=$rc"
echo "OUT=$o"

echo '=====ROW GAP-032'
o=$( { echo 'cHl0aG9uIC1tIHB5dGVzdCB0ZXN0cy90ZXN0X2J1ZGdldF9pZGVtcG90ZW5jeS5weSAtcSAtcCBubzpjYWNoZXByb3ZpZGVy' | base64 -d | timeout 60 bash; } 2>&1 ); rc=$?
echo "RC=$rc"
echo "OUT=$o"

echo '=====ROW GAP-033'
o=$( { echo 'cHl0aG9uIC1tIHRvb2xzLnZlcmlmeV9jaGFpbiAtLWZyb20temVybyAtLWpzb24gfCBqcSAtciAuc3RhdHVz' | base64 -d | timeout 60 bash; } 2>&1 ); rc=$?
echo "RC=$rc"
echo "OUT=$o"

echo '=====ROW GAP-037'
o=$( { echo 'cHl0aG9uIC1tIHB5dGVzdCB0ZXN0cy90ZXN0X2F1dGhvcml0eV9sYWRkZXIucHkgLXEgLWsgYTJfYmxvY2tlZCAtcCBubzpjYWNoZXByb3ZpZGVy' | base64 -d | timeout 60 bash; } 2>&1 ); rc=$?
echo "RC=$rc"
echo "OUT=$o"

echo '=====ROW GAP-038'
o=$( { echo 'cHl0aG9uIC1tIHB5dGVzdCB0ZXN0cy90ZXN0X25vX2xsbV9pbXBvcnRfaW5fcmVmbGV4LnB5IC1xIC1wIG5vOmNhY2hlcHJvdmlkZXI=' | base64 -d | timeout 60 bash; } 2>&1 ); rc=$?
echo "RC=$rc"
echo "OUT=$o"

echo '=====ROW GAP-039'
o=$( { echo 'cHl0aG9uIC1tIHB5dGVzdCB0ZXN0cy90ZXN0X25vX2V4ZWN1dG9yX2hhbmRsZV9pbl9jb2duaXRpb24ucHkgLXEgLXAgbm86Y2FjaGVwcm92aWRlcg==' | base64 -d | timeout 60 bash; } 2>&1 ); rc=$?
echo "RC=$rc"
echo "OUT=$o"

echo '=====ROW GAP-040'
o=$( { echo 'cHl0aG9uIC1tIHRvb2xzLmNvdW50ZXJzIC0tanNvbiB8IGpxIC1yICdbLkVYVEVSTkFMX0FDVElPTlMsLk5FV19MQU5fTElTVEVORVJTLC5NQVlfQVVUSE9SSVpFXXxAY3N2Jw==' | base64 -d | timeout 60 bash; } 2>&1 ); rc=$?
echo "RC=$rc"
echo "OUT=$o"

echo '=====ROW GAP-041'
o=$( { echo 'c3RhdCAtYyAlcyBzdGF0ZS9tZW1vcnkvbWVtb3J5LmRi' | base64 -d | timeout 60 bash; } 2>&1 ); rc=$?
echo "RC=$rc"
echo "OUT=$o"

echo '=====ROW GAP-049'
o=$( { echo 'cHl0aG9uIC1tIHB5dGVzdCB0ZXN0cy90ZXN0X25vX2J1ZGdldF93aXRob3V0X293bmVyX251bWJlci5weSAtcSAtcCBubzpjYWNoZXByb3ZpZGVy' | base64 -d | timeout 60 bash; } 2>&1 ); rc=$?
echo "RC=$rc"
echo "OUT=$o"

echo '=====ROW GAP-050'
o=$( { echo 'cHl0aG9uIC1tIHRvb2xzLnF1ZXVlX2F1ZGl0IC0taWRzIDE1MTUsMTUxNiwxNTE3IC0tanNvbiB8IGpxICdbLltdfHNlbGVjdCgucm9vdF9jYXVzZT09bnVsbCldfGxlbmd0aCc=' | base64 -d | timeout 60 bash; } 2>&1 ); rc=$?
echo "RC=$rc"
echo "OUT=$o"

echo '=====ROW GAP-053'
o=$( { echo 'cHl0aG9uIC1tIHRvb2xzLnJ1bndheSAtLWpzb24gfCBqcSAtciAnWy5ydW53YXlfZGF5cywuc291cmNlXXxAY3N2Jw==' | base64 -d | timeout 60 bash; } 2>&1 ); rc=$?
echo "RC=$rc"
echo "OUT=$o"

echo '=====ROW GAP-054'
o=$( { echo 'cHl0aG9uIC1tIHRvb2xzLnRyZWFzdXJ5IC0tanNvbiB8IGpxIC1yIC5hdG9fcmVzZXJ2ZV9yYXRpbw==' | base64 -d | timeout 60 bash; } 2>&1 ); rc=$?
echo "RC=$rc"
echo "OUT=$o"

echo '=====ROW GAP-055'
o=$( { echo 'cHl0aG9uIC1tIHB5dGVzdCB0ZXN0cy90ZXN0X3N0cmF0ZWd5X25vdF9wZXJzaXN0ZW5jZV9jb3B5LnB5IC1xIC1wIG5vOmNhY2hlcHJvdmlkZXI=' | base64 -d | timeout 60 bash; } 2>&1 ); rc=$?
echo "RC=$rc"
echo "OUT=$o"

echo '=====ROW GAP-056'
o=$( { echo 'cHl0aG9uIC1tIHRvb2xzLmdhdGVfY2hlY2sgLS1nYXRlIDQgLS1qc29uIHwganEgLXIgLnN0YXR1cw==' | base64 -d | timeout 60 bash; } 2>&1 ); rc=$?
echo "RC=$rc"
echo "OUT=$o"

echo '=====ROW GAP-060'
o=$( { echo 'cHl0aG9uIC1tIHB5dGVzdCAtLWNvbGxlY3Qtb25seSAtcSAyPi9kZXYvbnVsbCB8IHRhaWwgLTEgLXAgbm86Y2FjaGVwcm92aWRlcg==' | base64 -d | timeout 60 bash; } 2>&1 ); rc=$?
echo "RC=$rc"
echo "OUT=$o"
