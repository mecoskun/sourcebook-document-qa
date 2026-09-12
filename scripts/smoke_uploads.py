"""Exercise actual multipart uploads and session isolation against the running app."""
import io
import json
from pathlib import Path

import httpx
from docx import Document
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject


def main():
    document = Document()
    document.add_paragraph("The support desk opens at 9 AM.")
    docx = io.BytesIO()
    document.save(docx)
    writer = PdfWriter()
    page = writer.add_blank_page(width=300, height=200)
    font = DictionaryObject({NameObject("/Type"): NameObject("/Font"),
        NameObject("/Subtype"): NameObject("/Type1"), NameObject("/BaseFont"): NameObject("/Helvetica")})
    page[NameObject("/Resources")] = DictionaryObject({NameObject("/Font"):
        DictionaryObject({NameObject("/F1"): writer._add_object(font)})})
    stream = DecodedStreamObject()
    stream.set_data(b"BT /F1 12 Tf 20 150 Td (Support closes at 5 PM.) Tj ET")
    page[NameObject("/Contents")] = writer._add_object(stream)
    pdf = io.BytesIO()
    writer.write(pdf)
    results = {}
    with httpx.Client(base_url="http://127.0.0.1:8000", timeout=190, trust_env=False) as client:
        response = client.post("/api/sessions")
        response.raise_for_status()
        alice = {"Authorization": "Bearer " + response.json()["token"]}
        response = client.post("/api/sessions")
        response.raise_for_status()
        bob = {"Authorization": "Bearer " + response.json()["token"]}
        try:
            for name, data in [("support.txt", b"The support team is available Monday to Friday."),
                               ("support.docx", docx.getvalue()), ("support.pdf", pdf.getvalue())]:
                response = client.post("/api/documents", headers=alice, files={"file": (name, data)})
                response.raise_for_status()
                assert response.json()["chunks"] >= 1
                results[name] = "indexed"
            own = client.get("/api/documents", headers=alice).json()
            assert len(own) == 3
            assert client.get("/api/documents", headers=bob).json() == []
            response = client.delete("/api/documents/" + own[0]["id"], headers=bob)
            assert response.status_code == 404
            response = client.post("/api/questions", headers=bob, json={"question": "When does support open?"})
            assert response.status_code == 400
            results["cross_session_list_delete_question"] = "isolated"
            response = client.post("/api/documents", headers=alice, files={"file": ("bad.pdf", b"not a pdf")})
            assert response.status_code == 400
            results["malformed_pdf"] = "rejected"
            response = client.post("/api/documents", headers=alice,
                                   files={"file": ("large.txt", b"a" * (10 * 1024 * 1024 + 1))})
            assert response.status_code == 413
            results["oversized_upload"] = "rejected"
            response = client.delete("/api/documents", headers=alice)
            response.raise_for_status()
            assert client.get("/api/documents", headers=alice).json() == []
            results["clear_workspace"] = "deleted"
        finally:
            client.delete("/api/documents", headers=alice)
            client.delete("/api/documents", headers=bob)
    output = Path(__file__).resolve().parents[1] / "docs/upload-smoke.json"
    output.write_text(json.dumps(results, indent=2) + "\n")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
