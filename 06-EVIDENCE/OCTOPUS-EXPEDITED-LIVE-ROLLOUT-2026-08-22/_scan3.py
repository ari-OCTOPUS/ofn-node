from pathlib import Path
lines = Path(r"F:/backup/_ops/tests/test_wave_e_c3c4_20260821.py").read_text(encoding="utf-8").splitlines()
print("\n".join(f"{i+1}: {l}" for i,l in enumerate(lines[:220])))
print("---pass3 send_owner---")
lines2 = Path(r"F:/backup/_ops/loops/pass3_live.py").read_text(encoding="utf-8").splitlines()
print("\n".join(f"{i+105}: {l}" for i,l in enumerate(lines2[104:200])))
