# Member 1 — Manual table and numerical-rule checklist

The plan requires manual verification of tables and numerical rules; the text
pipeline deliberately does **not** reshape table cells (see protocol §8). This is the
working list. Mark each row when it has been compared against the PDF by eye.

**How to check a page**

1. Open the PDF at the PDF page number, and compare with the chunk text for that
   page (`data/chunks.jsonl`, filter by `pdf_page`).
2. Confirm every number in the table appears in the chunk text, once, with the same
   value and unit (`HK$`, `/credit`, `/academic year`, `am/pm`).
3. Confirm the row/column association is still deducible from the text. If it is
   not, note the page here — it becomes a known limitation, not a silent failure.
4. For regulation pages (not just tables), confirm the numeric rule: retake limit
   (2), maximum study load (21 credits), normal load (15 credits), probation
   thresholds, deadlines, fees, fines.

**Highest-risk pages** (answer-critical numbers): printed 55–62 (fees), 87 (library
fines), 96–100 (opening hours), 108–111 (bad-weather arrangements).

| PDF | Printed | Detected tables (rows × cols) | Section | Checked |
|---:|---:|---|---|---|
| 24 | 13 | 2×2 | 4.C Use, Access and Change of Student Data | [ ] |
| 25 | 14 | 4×3, 2×2 | 4.D Normal Duration for Completion of a Programme | [ ] |
| 26 | 15 | 2×2 | 4.F Leave of Absence | [ ] |
| 29 | 18 | 4×4 | 4.I Zero Subject Enrolment and Retention of Study Place* | [ ] |
| 31 | 20 | 4×2 | 4.K Student Status | [ ] |
| 32 | 21 | 4×2 | 4.K Student Status | [ ] |
| 33 | 22 | 4×3 | 4.L Withdrawal of Study* | [ ] |
| 34 | 23 | 4×2 | 4.L Withdrawal of Study* | [ ] |
| 35 | 24 | 2×3 | 4.M Undergraduate Degree Programmes with Minor/Double Major/Secondary Major/Fast-track Programmes Study Options | [ ] |
| 36 | 25 | 2×3, 2×3 | 4.M Undergraduate Degree Programmes with Minor/Double Major/Secondary Major/Fast-track Programmes Study Options | [ ] |
| 38 | 27 | 2×3 | 4.M Undergraduate Degree Programmes with Minor/Double Major/Secondary Major/Fast-track Programmes Study Options | [ ] |
| 42 | 30 | 4×2, 4×6 | 5.B Subject Exemption and Credit Transfer | [ ] |
| 44 | 32 | 4×6, 2×3 | 5.B Subject Exemption and Credit Transfer | [ ] |
| 45 | 33 | 4×6 | 5.B Subject Exemption and Credit Transfer | [ ] |
| 48 | 36 | 4×2 | 5.H Nullification of Registration* | [ ] |
| 51 | 38 | 4×6 | 6.B Progression and De-registration* | [ ] |
| 56 | 43 | 2×4 | 6.H Late Assessment | [ ] |
| 57 | 44 | 1×4 | 6.I Academic Appeals | [ ] |
| 61 | 48 | 4×2 | 6.K Application for Graduation | [ ] |
| 65 | 51 | 2×6 | 7.C Award Parchment | [ ] |
| 66 | 52 | 2×2, 2×6 | 7.D Certification of Award & Replacement Award Parchment | [ ] |
| 70 | 55 | 2×9 | 8.C Payment Methods | [ ] |
| 71 | 56 | 4×9 | 8.C Payment Methods | [ ] |
| 75 | 60 | 2×3, 2×3 | 8.H Tuition Fees | [ ] |
| 76 | 61 | 5×6, 7×6, 2×6 | 8.H Tuition Fees | [ ] |
| 77 | 62 | 7×6 | 8.I Other Fees/Charges | [ ] |
| 89 | 71 | 4×2 | 11.C Use of University’s Name, Property and Premises | [ ] |
| 106 | 87 | 6×2 | 12.B Pao Yue-kong Library | [ ] |
| 109 | 90 | 7×2 | 12.C Student Affairs Office | [ ] |
| 115 | 96 | 12×4 | 12.C Student Affairs Office | [ ] |
| 116 | 97 | 9×3, 11×9 | 12.C Student Affairs Office | [ ] |
| 117 | 98 | 5×9, 10×7 | 12.C Student Affairs Office | [ ] |
| 118 | 99 | 3×3 | 12.C Student Affairs Office | [ ] |
| 119 | 100 | 8×3, 4×2 | 12.C Student Affairs Office | [ ] |
| 122 | 103 | 5×3, 6×3 | 12.F Other Communal Facilities | [ ] |
| 123 | 104 | 14×3 | 12.F Other Communal Facilities | [ ] |
| 128 | 108 | 27×4 | Appendix 1. Arrangements during Bad Weather | [ ] |
| 129 | 109 | 8×2 | Appendix 1.A Tropical Cyclone Warning and ‘Extreme Conditions’ | [ ] |
| 130 | 110 | 20×4 | Appendix 1.A Tropical Cyclone Warning and ‘Extreme Conditions’ | [ ] |
| 131 | 111 | 8×2 | Appendix 1.B Rainstorm Warning | [ ] |

## Non-table numeric rules to verify

| Rule | Location (printed page) | Value to confirm |
|---|---|---|
| Normal study load | 28 / 5.A | 15 credits per semester |
| Maximum study load | 28 / 5.A | 21 credits per semester |
| Retake limit | 33 / 5.C | maximum of two retakes |
| Probation study load cap | 28 / 5.A | not more than 15 credits |
| Maximum registration period | 14 / 4.E | normally twice normal duration, never more than 8 years |
| Caution money | 61 / 8.I | HK$400 |
| Late assessment / appeal fees | 56–57, 62 | check each figure |
| Library fines | 87 / 12.B | HK$80 / 160 / 320 escalation |

Add any additional numeric rule you verify, with page and value, so that the
benchmark's expected answers can cite it.
