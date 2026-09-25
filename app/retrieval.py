import math
import re
import uuid
from collections import Counter
from functools import cached_property

import numpy as np
from fastembed import TextEmbedding

from app.config import settings
from app.extraction import chunks

STOP_WORDS = set("what which when where why how should would could does do did we you they them their our your the a an and or of to in on at for with from before after regularly please according".split())


def terms(text):
    words = re.findall(r"[a-z0-9]+", text.lower())
    normalized = set()
    for word in words:
        if word in STOP_WORDS or len(word) <= 2:
            continue
        # Lightweight English suffix normalization, not a linguistic confidence score.
        for suffix in ("ation", "ing", "ed", "s"):
            if word.endswith(suffix) and len(word) - len(suffix) >= 4:
                word = word[:-len(suffix)]
                break
        normalized.add(word.rstrip("e") if len(word) > 4 else word)
    return normalized



class DocumentIndex:
    """Bounded, in-memory indexes. Session IDs come only from the trusted backend."""

    def __init__(self):
        self.sessions: dict[str, dict] = {}

    @cached_property
    def encoder(self):
        return TextEmbedding(model_name=settings.embedding_model,
                             cache_dir=str(settings.cache_dir), threads=2,
                             specific_model_path=str(settings.embedding_path),
                             local_files_only=True)

    def add(self, session: str, name: str, sections: list[dict]) -> dict:
        documents = self.sessions.get(session, {})
        if len(documents) >= settings.max_documents:
            raise ValueError("Remove a document before adding another (maximum five).")
        if session not in self.sessions and len(self.sessions) >= settings.max_sessions:
            raise ValueError("The demo is at capacity. Please try again later.")
        if sum(len(s["text"]) for s in sections) > settings.max_text_chars:
            raise ValueError("Document text limit exceeded.")
        passages = chunks(sections)
        if not passages:
            raise ValueError("No passages to index.")
        vectors = np.asarray(list(self.encoder.embed([p["text"] for p in passages])),
                             dtype=np.float32)
        vectors /= np.maximum(np.linalg.norm(vectors, axis=1, keepdims=True), 1e-9)
        doc_id = uuid.uuid4().hex
        document = {"id": doc_id, "name": name, "pages": len(sections),
                    "chunks": len(passages), "passages": passages, "vectors": vectors}
        self.sessions.setdefault(session, {})[doc_id] = document
        return self.summary(document)

    @staticmethod
    def summary(document):
        return {k: document[k] for k in ("id", "name", "pages", "chunks")}

    def list(self, session: str):
        return [self.summary(d) for d in self.sessions.get(session, {}).values()]

    def remove(self, session: str, document_id: str | None = None):
        if document_id is None:
            self.sessions.pop(session, None)
        elif document_id not in self.sessions.get(session, {}):
            raise ValueError("Document not found in this workspace.")
        else:
            del self.sessions[session][document_id]

    def search(self, session: str, question: str, limit: int = 4):
        documents = self.sessions.get(session, {})
        if not documents:
            return []
        vector = np.asarray(list(self.encoder.query_embed(question))[0], dtype=np.float32)
        vector /= max(float(np.linalg.norm(vector)), 1e-9)
        # Blend semantic similarity with rare query words; semantic-only ranking
        # can favor generic policy text over the passage containing the requested fact.
        pool = []
        for document in documents.values():
            scores = document["vectors"] @ vector
            for i, passage in enumerate(document["passages"]):
                pool.append(({"document_id": document["id"], "name": document["name"],
                              **passage, "score": round(float(scores[i]), 4)}, terms(passage["text"])))
        frequencies = Counter(term for _, words in pool for term in words)
        query_terms = terms(question)
        weights = {term: math.log(1 + len(pool) / (1 + frequencies[term])) for term in query_terms}
        total = sum(weights.values()) or 1
        candidates = []
        for item, words in pool:
            overlap = query_terms & words
            coverage = sum(weights[term] for term in overlap) / total
            score = item["score"]
            if score >= settings.min_similarity or (score >= settings.min_similarity - 0.05 and len(overlap) >= 2):
                candidates.append((score + 0.12 * coverage, item))
        ranked = sorted(candidates, key=lambda pair: -pair[0])[:limit]
        return [{**item, "label": f"S{i}"} for i, (_, item) in enumerate(ranked, 1)]
