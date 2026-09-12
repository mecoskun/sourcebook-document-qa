# Portfolio roadmap and resume notes

Updated: 2026-09-12. User approved this sequence; only step 1 is active now.

1. **Document Q&A reliability (active):** broaden wording and document-format checks; improve uncertainty handling; record failures and limitations.
2. **Choose shared CPU hosting (pending):** benchmark response time and memory, compare providers against the initial USD 20–30/month target before purchase. The 4B model measured about 5.3 GB locally; allow OS/API headroom.
3. **Enable live public Q&A (pending):** deploy HTTPS backend, configure usage controls, connect the GitHub Pages interface.
4. **Portfolio polish (pending):** screenshots, architecture, examples, limitations, setup instructions.
5. **YouTube summarizer (pending):** separate project/repository, existing transcripts only; no audio/video processing. Reuse the shared model, MCP management, deployment, and usage controls.
6. **Publish and connect both projects (pending):** GitHub repositories and demo pages with cross-links and shared infrastructure controls.

## Established decisions

No paid LLM API or GPU required for the current design. Public source on mecoskun GitHub. GitHub Pages hosts static UI; Python and CPU inference need separate hosting. Nothing paid has been provisioned. Public Sourcebook currently serves explicitly labeled recorded examples; local Sourcebook supports live uploads.

## Resume pointers

Project: `document-qa`. Source: https://github.com/mecoskun/sourcebook-document-qa . Preview: https://mecoskun.github.io/sourcebook-document-qa/ . Read this roadmap, PROJECT_BRIEF.md, and the latest reliability report before continuing. Do not treat pending phases as completed.

The earlier informal vacation question exposed a false rejection by the evidence checker. Cited-only evidence and wording guidance fixed the exact case; 24 offline tests and eight focused model checks passed at that stage. The original 20-case baseline remains separate from later regressions.

## Reliability progress, 2026-09-12

Completed the first broader reliability pass. Fixed DOCX body ordering and repeated the first table row with subsequent rows so header context survives retrieval. Table citations now identify table and row. Added an offline regression and a reproducible 12-case live upload evaluation covering DOCX tables, PDF page citations, TXT paraphrases, missing facts, and a planted document instruction. 25 offline tests pass. Live report: 11 initial automated passes; the remaining output was an exact cited statement that the weekend policy is unspecified. After explicitly accepting that safe behavior, 12/12 pass. Raw answers and the review note are retained in reliability-results.json.

Next reliability work before selecting hosting: representative non-sensitive real-world documents, complex/merged/nested tables, conflicting documents and longer multi-part questions. Synthetic fixtures do not establish production accuracy. No hosting purchase or YouTube work has started. Backend restarted to activate extraction changes; temporary uploads must be reloaded.
