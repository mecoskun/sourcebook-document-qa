# Portfolio project brief

## Agreed scope

Build Document Q&A first, then a separate transcript-only YouTube summarizer. Both applications will use one deployed open-source CPU model service. No paid LLM API. Initial shared infrastructure planning budget: USD 20–30/month, subject to hosted CPU benchmarks. Public source repositories and GitHub Pages interfaces; Python services hosted separately.

## Document Q&A

Working title: Sourcebook. Upload text-based PDF, DOCX, or UTF-8 TXT. Maximum 10 MB/file, 100 PDF pages, 150,000 extracted characters, 250 chunks, five documents/workspace. Ask independent questions through MCP retrieval and receive answers with source passages. DOCX/TXT use paragraph/section locations, not invented page numbers. Scanned PDFs and OCR are excluded.

## YouTube, next phase

Accept a video URL, retrieve its existing transcript through MCP, summarize the text. Explain when no transcript can be retrieved. No video/audio download, processing, or transcription. Reuse the HTTP model adapter, MCP lifecycle pattern, bounded usage, Docker approach, and UI conventions. The YouTube project has not yet been implemented.

## Boundaries

GitHub Pages cannot run Python. Public frontend configuration contains only the backend origin. The backend mediates inference; model ports stay private. Uploads and embeddings are temporary and isolated by unguessable session tokens. CPU latency and small-model quality need evaluation before hosting selection. Keep sample-only public previews explicitly labeled until the live backend is deployed.
