# duplicate_transaction_no_audit_20260713

## Summary
- Remote DB: `fixture_m_lite` on `172.17.11.72`
- Non-empty duplicate `transaction_no` groups: 85
- Blank / empty `transaction_no` rows: 3395
- Important case: `202606020001` appears 10 times

## Recommended cleanup policy
- If `transaction_no` is intended to be unique, every non-empty duplicate group should be consolidated.
- Keep one canonical header per `transaction_no`, merge or reconcile item rows from the other headers, then remove the redundant headers.
- Treat blank `transaction_no` rows as separate data hygiene cleanup.

## Top duplicate groups
| transaction_no | count |
| --- | ---: |
| 202503120002 | 597 |
| 202503280001 | 207 |
| 202411250001 | 110 |
| 202506030002 | 100 |
| 2025092400901 | 64 |
| 20260213 | 45 |
| 202503180001 | 44 |
| 2025120203401 | 40 |
| 2026030503301 | 29 |
| 2026022502001 | 24 |
| 2026051502901 | 22 |
| 2026040803602 | 19 |
| 2026043000801 | 19 |
| 2026052802601 | 19 |
| 2026031202701 | 18 |
| 2026041604201 | 18 |
| 202503120001 | 17 |
| 202505290002 | 17 |
| 2026032603601 | 17 |
| 2026060504101 | 17 |
| 202606020001 | 10 |

## `202606020001` detail
- IDs: `11168, 11214, 11215, 11216, 11262, 11263, 11264, 11266, 11267, 11268`
- This is the transaction number tied to the user-described multi-fixture receipt flow.
- The last header (`11268`) contains 8 items and total quantity 60.
