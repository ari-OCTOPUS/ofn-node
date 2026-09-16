# INSTALL BRIEF - Board2 GitHub read-only PAT (ofn/wire fetch only)

**Audience:** Marketing / operator on DietPi Board2  
**Board:** `ari@192.168.0.138`  
**Token id:** `OCTOPUS-BOARD2-GITHUB-READONLY-20260822`  
**Scope:** HTTPS **read-only** fetch/clone for **ofn/wire** only. No write. No chat/evidence paste of PAT. No `git add` of PAT files.

**Owner auth:** see `OWNER-AUTHORIZATION.json` in this evidence folder.  
**Laptop staging (do not open in editor/chat):**  
`C:\Users\Armin\AppData\Local\Temp\octopus-github-readonly.pat` (expect ~94 bytes, nonempty)

---

## 0) Preconditions

- You have SSH/SCP access as `ari` to `192.168.0.138`.
- Do **not** print the PAT. Prefer `wc -c` / `stat` length checks only.
- Do **not** commit. Do **not** `git add -A`. Do **not** push.

---

## 1) Copy staging file to Board2 (mode 600)

From the **Windows laptop** (PowerShell or OpenSSH `scp`):

```powershell
ssh ari@192.168.0.138 "mkdir -p /home/ari/.secrets && chmod 700 /home/ari/.secrets"
scp "$env:LOCALAPPDATA\Temp\octopus-github-readonly.pat" ari@192.168.0.138:/home/ari/.secrets/github-readonly.pat
ssh ari@192.168.0.138 "chmod 600 /home/ari/.secrets/github-readonly.pat && wc -c /home/ari/.secrets/github-readonly.pat"
```

Expect byte count ≈ 94 (nonempty). Do not `cat` the file.

---

## 2) Identify ofn/wire remote URL (do not invent)

On Board2:

```bash
# Primary: live remotes in the wire working copy (preferred)
cd /home/ari/.local/state/ofn-wire/repo 2>/dev/null || cd "$(dirname "$(readlink -f "$(command -v ofn-wire-send.sh)" 2>/dev/null)" 2>/dev/null)" 
# If path unknown, locate:
find /home/ari -maxdepth 5 -type d -name 'ofn-wire' 2>/dev/null
# Then:
git -C /home/ari/.local/state/ofn-wire/repo remote -v
git -C /home/ari/.local/state/ofn-wire/repo branch -a | head
```

**Documented hint only (Windows mirror docs under `F:\octopus-wire`):**  
`https://github.com/ari322/ofn-node.git` branch `ofn/wire`.  
If Board2 remotes differ, **use the Board2 remote**, not the Windows hint. If no GitHub HTTPS remote exists, stop and report remotes — do not invent a repo.

Set:

```bash
OFN_WIRE_URL="<https URL from git remote -v for ofn/wire / origin>"
```

---

## 3) Configure GitHub HTTPS credential (prefer store, then drop plaintext)

GitHub HTTPS PAT pattern: username `x-access-token`, password = PAT.

### Preferred: `git credential-store` then remove board plaintext

On Board2 (still no `cat` of PAT into logs):

```bash
git config --global credential.helper store
# One-shot approve without echoing token to shell history if possible:
# read PAT from file into credential fill (file never printed):
{
  printf 'protocol=https\nhost=github.com\nusername=x-access-token\npassword='
  tr -d '\r\n' < /home/ari/.secrets/github-readonly.pat
  printf '\n\n'
} | git credential approve

# Verify store file perms (contains secret — mode 600):
chmod 600 ~/.git-credentials 2>/dev/null || true
ls -la ~/.git-credentials
```

After a successful `git ls-remote` (step 4), **prefer deleting** `/home/ari/.secrets/github-readonly.pat` so only `~/.git-credentials` holds the secret. If something still needs the file path, keep it mode `600` and document why.

### Alternative: `~/.git-credentials` line directly

Same security class as store; ensure mode `600`:

```bash
# Format (do not paste this line into chat/evidence with real PAT):
# https://x-access-token:YOUR_PAT@github.com
umask 077
# Build line from file without printing:
printf 'https://x-access-token:%s@github.com\n' "$(tr -d '\r\n' < /home/ari/.secrets/github-readonly.pat)" > ~/.git-credentials
chmod 600 ~/.git-credentials
git config --global credential.helper store
```

---

## 4) Prove read access

```bash
git ls-remote "$OFN_WIRE_URL" | head
# Expect refs (e.g. refs/heads/ofn/wire). Nonzero exit / auth error = stop and report.
# Optional narrower check:
git ls-remote "$OFN_WIRE_URL" refs/heads/ofn/wire
```

Do **not** push. Do **not** change remotes unless owner asked.

---

## 5) Shred / delete staging after success

**Laptop Temp:**

```powershell
$p = Join-Path $env:LOCALAPPDATA "Temp\octopus-github-readonly.pat"
if (Test-Path -LiteralPath $p) {
  # overwrite then delete (best-effort on NTFS)
  $len = (Get-Item -LiteralPath $p).Length
  $fs = [System.IO.File]::Open($p, 'Open', 'Write')
  $fs.Write((New-Object byte[] $len), 0, $len); $fs.Close()
  Remove-Item -LiteralPath $p -Force
}
```

**Board `.secrets` (prefer after credential store works):**

```bash
shred -u /home/ari/.secrets/github-readonly.pat 2>/dev/null || rm -f /home/ari/.secrets/github-readonly.pat
# Keep ~/.git-credentials mode 600 if that is the live helper store.
```

If credential helper still needs the board file, keep `/home/ari/.secrets/github-readonly.pat` mode `600` and note that in the receipt.

---

## 6) Receipts (NO plaintext PAT)

On Board2, write a receipt under the usual exchange drop (create if needed):

```bash
EX=/home/ari/TO-LAPTOP/exchange
mkdir -p "$EX"
TS=$(date -u +%Y%m%dT%H%M%SZ)
R="$EX/github-readonly-install-$TS.txt"
{
  echo "token_id=OCTOPUS-BOARD2-GITHUB-READONLY-20260822"
  echo "host=192.168.0.138 user=ari"
  echo "scope=ofn/wire HTTPS read-only"
  echo "ofn_wire_url=$OFN_WIRE_URL"
  echo "ls_remote_ok=yes"   # or no + error class only
  echo "credential_helper=$(git config --global --get credential.helper)"
  echo "secrets_file_present=$(test -f /home/ari/.secrets/github-readonly.pat && echo yes || echo no)"
  echo "git_credentials_present=$(test -f ~/.git-credentials && echo yes || echo no)"
  # hash of former secrets file only if still present; never dump contents:
  if test -f /home/ari/.secrets/github-readonly.pat; then
    echo "secrets_sha256=$(sha256sum /home/ari/.secrets/github-readonly.pat | awk '{print $1}')"
    echo "secrets_bytes=$(wc -c < /home/ari/.secrets/github-readonly.pat)"
  fi
  if test -f ~/.git-credentials; then
    echo "git_credentials_sha256=$(sha256sum ~/.git-credentials | awk '{print $1}')"
    echo "git_credentials_bytes=$(wc -c < ~/.git-credentials)"
  fi
  echo "laptop_temp_deleted=pending"  # confirm after Windows shred
} > "$R"
chmod 600 "$R"
```

Copy a **summary** (same fields; still no PAT) to the Windows evidence dir:

`F:\backup\06-EVIDENCE\OCTOPUS-BOARD2-GITHUB-READONLY-2026-08-22\`

e.g. `INSTALL-RECEIPT-SUMMARY.txt` via SCP/SMB from `$R`. Hash-of-file is OK; plaintext PAT is **forbidden**.

---

## Forbid checklist

- [ ] No write/push to GitHub repos  
- [ ] No PAT in chat, screenshots, or evidence plaintext  
- [ ] No `git add` of PAT / `.secrets` / `.git-credentials`  
- [ ] No broad “all of GitHub” credential beyond this HTTPS store for github.com read use  

---

## Done when

1. `git ls-remote <ofn/wire url>` returns refs  
2. Laptop Temp staging deleted  
3. Board prefers credential store; plaintext `.secrets` removed (or justified keep @600)  
4. Receipt in `TO-LAPTOP/exchange` + summary copy in evidence dir without PAT  
