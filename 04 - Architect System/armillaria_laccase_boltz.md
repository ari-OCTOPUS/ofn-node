# Armillaria laccase — Boltz-2.1 structure record

**Target:** *Armillaria ostoyae* (= *A. solidipes*) laccase (multicopper oxidase)
**UniProt:** A0A2H3BEE1 · **Gene:** ARMSODRAFT_896879 · **Length:** 522 aa
**Why this protein:** laccase پلِ دو پایهٔ بقاست — اکسیداسیونِ لیگنین (تجزیهٔ چوب → تغذیه) و سنتزِ ملانین (→ زره).

## Boltz-2.1 prediction
- **prediction_id:** `sab_pred_2FX9Vwsz0azwiZ0GCM79`
- **model:** boltz-2.1 (v2026-03-01) · **cost:** ~$0.10 · **compute:** ~47 s
- **data retained until:** 2026-07-11 (URLs below are ~30-min signed links; قابلِ تولیدِ مجدد از prediction_id)

| metric | value | معنا |
|--------|-------|------|
| structure_confidence | 0.915 | فولدِ بسیار مطمئن |
| pTM | 0.941 | توپولوژیِ کلیِ مطمئن |
| complex_pLDDT | 0.909 | اطمینانِ per-residue بالا |
| complex_PDE | 0.498 | خطای فاصلهٔ پیش‌بینی‌شده |

## Conserved multicopper-oxidase Cu motifs (from sequence)
`HWHG` · `WYHSH` · `HPFHLHGH` · `WFLHCHIDWH`  → جایگاه‌های مسِ نوعِ T1/T2/T3.

## Download (signed, time-limited — refresh via prediction_id)
- **structure (mmCIF):** https://boltz-platform-prod-compute-api-storage.s3.us-east-1.amazonaws.com/org/b62d202d-4b83-5366-9600-12d2d318c3f7/workspace/ws_EMdgceAEmC72GZN5oZqf/prediction/sab_pred_2FX9Vwsz0azwiZ0GCM79/output/public/sample_0_predicted_structure.cif
- **full archive (.tar.gz):** …/prediction/sab_pred_2FX9Vwsz0azwiZ0GCM79/output/public/prediction_archive.tar.gz
- برای باز کردن: ChimeraX / PyMOL / Mol* (فایلِ CIF).

## Sequence (FASTA)
```
>A0A2H3BEE1 laccase Armillaria solidipes ARMSODRAFT_896879
MASSLFSLLVLTLGLPSSRGQRQGTIGPVGDLVVSNGLVNPDGFERLAALANSQIDGSLI
TGNKGDVFQINVVNQLDNDTILQSTSIHWHGLFQKGTGWADGPPGVNQASICPIVKGDSF
LYTFDSTDQAGTFWYHSHLSTQYCDGLRGPLVIYDPNDPHADLYDVDDDSTSILTLSDWY
HTPAKQLTFPSPDAILINGIGRWSQDPTHDLAVVNVTKGTRYRIRMLNVGCDAAYTVSID
SHLMTIIEVDGVNHVPYTVDEIQIFAGQRYSFVLNADQDIGNYWIRANPSVGTLGFEGGI
NSAILRYNGAPDAEPGNVSFTSVLKMNETQLVPLENPGAPGSPVAGGVDVAKNLAFAFTS
SATFTVNGFTFVPPTTPVLLQLLSGAQNANDLLPEGSVYPLPLNATVEISMPGGVIGGGH
PFHLHGHTFDVIRSAGSTVYNYENPVRRDVVNIGTTGDNVTIRFTTDNPGPWFLHCHIDW
HLQAGFAIVFAEAVEQWNSTIDPTDQWDQLCPIYNATPPEDL
```

## Next step
Boltz small-molecule screen (laccase inhibitors → rational fungicide): kojic acid, tropolone, salicylhydroxamic acid, diethyldithiocarbamate, guaiacol, ferulic acid, PABA.
