import numpy as np
import pytest

from app.retrieval import DocumentIndex


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
