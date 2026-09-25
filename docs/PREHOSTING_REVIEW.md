# Pre-hosting reliability review

Completed 2026-09-25 for the bounded portfolio-demo scope.

## Changes

- Semantic retrieval now also uses rare query words and simple English suffix normalization. This recovered the restoration passage omitted from a multi-part backup answer.
- The evidence checker sees other retrieved passages as context, so silently selecting one conflicting policy can be rejected. Named-document questions remain supported.
- Short subject-free questions such as "When does it open?" request clarification without inference. This is a narrow grammar guard, not general language understanding.
- Founding-date questions without origin-related retrieved evidence are declined before inference. A document date cannot substitute for absent founding evidence. Positive controls confirm explicit founding and effective dates are still answerable.
- Merged/nested DOCX tables return a clear upload error instead of silently dropping or misinterpreting content. Simple tables preserve row/header context.

## Evidence

| Check | Result | Record |
|---|---|---|
| Offline tests | 41 passed | pytest suite |
| Real PDF, long synthetic DOCX, conflicting sources | 13/13; baseline 10/13 | prehosting-results.json; prehosting-baseline.json |
| PDF/DOCX/TXT format regression | 12/12 | reliability-results.json |
| Handbook rerun before final deterministic guard | 19/20; unsupported founding year | handbook-before-origin-guard.json |
| Final targeted dates, including the failed handbook question | 4/4 | date-regression.json |

The public fixture is the nine-page [NIST SP 1300 guide](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.1300.pdf), downloaded locally with a pinned checksum. Other fixtures are synthetic. No private user documents were published. Pattern-based checks were reviewed against answers and cited locations; they are not a general accuracy benchmark. The final narrow guard was checked with the targeted dates suite rather than rerunning every earlier inference case. Failed records are retained for transparency.

## Remaining limits and hosting handoff

Small-model errors remain possible. The guards cover specific failure classes; they do not solve arbitrary ambiguity or factual inference. Retrieval returns four passages, so unseen contradictions can be missed. Multi-part questions may receive a refusal. PDF layouts, first-row table-header assumptions, non-English documents, and broad new domains need further evaluation. No OCR, merged/nested DOCX tables, or conversational memory.

Proceed to shared CPU hosting comparison and benchmarking. Keep the model private, expose the API through HTTPS, use one API worker with current in-memory quotas, and benchmark the 6 GB model / 2 GB API container allowances plus OS overhead. The original USD 20–30/month figure remains a target, not a verified plan. Full container runtime/inference validation on the chosen host is still needed. The GitHub Pages preview remains recorded examples until a live backend is connected.
