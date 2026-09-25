import numpy as np
import pytest

from app.retrieval import DocumentIndex, terms


class Encoder:
    def embed(self, texts):
        return [np.array([1, 0]) if "vacation" in t else np.array([0, 1]) for t in texts]

    def query_embed(self, text):
        return self.embed([text])


def test_no_cross_workspace_retrieval_or_deletion():
    index = DocumentIndex()
    index.encoder = Encoder()
    first = index.add("alice", "private.txt", [{"location": "Section 1", "text": "vacation 20 days"}])
    index.add("bob", "other.txt", [{"location": "Section 1", "text": "payroll private"}])
    assert index.search("bob", "vacation") == []
    assert index.search("unknown", "vacation") == []
    assert index.search("alice", "vacation")[0]["name"] == "private.txt"
    with pytest.raises(ValueError):
        index.remove("bob", first["id"])
    index.remove("alice")
    assert index.list("alice") == []
    assert len(index.list("bob")) == 1


def test_hybrid_search_prefers_specific_fact_over_generic_semantic_match():
    class SimilarEncoder:
        def embed(self, texts):
            return [np.array([score, np.sqrt(1-score**2)]) for score in (0.82, 0.80)]
        def query_embed(self, text):
            return [np.array([1.0, 0.0])]
    index = DocumentIndex()
    index.encoder = SimilarEncoder()
    index.add("alice", "guide.txt", [
        {"location": "Section 1", "text": "Review organizational policy and procedures."},
        {"location": "Section 2", "text": "Check backup integrity before restoration."}])
    assert index.search("alice", "Check integrity before restoring backups", limit=1)[0]["location"] == "Section 2"
    assert "restor" in terms("restoring restoration restore")


def test_lexical_overlap_does_not_override_semantic_floor():
    index = DocumentIndex()
    index.encoder = Encoder()
    index.add("alice", "guide.txt", [{"location": "Section 1", "text": "vacation backup integrity"}])
    assert index.search("alice", "backup integrity") == []
