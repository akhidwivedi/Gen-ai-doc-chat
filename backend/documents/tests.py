"""
End-to-end API tests. Embeddings and the LLM are faked (no network / model
download needed); PDF/DOCX parsing and ChromaDB are real.

Run:  python manage.py test
"""
import hashlib
import shutil
import tempfile
from unittest.mock import patch

import pymupdf
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from docx import Document as DocxDocument
from rest_framework.test import APITestCase

from ai_services import AIServiceError

User = get_user_model()
TMP = tempfile.mkdtemp(prefix="docchat_test_")


def fake_embed_texts(texts, model_name, batch_size=32):
    """Deterministic 16-dim pseudo-embeddings (bag of hashed words)."""
    out = []
    for t in texts:
        v = [0.0] * 16
        for w in t.lower().split():
            v[int(hashlib.md5(w.encode()).hexdigest(), 16) % 16] += 1.0
        norm = sum(x * x for x in v) ** 0.5 or 1.0
        out.append([x / norm for x in v])
    return out


def fake_embed_query(text, model_name):
    return fake_embed_texts([text], model_name)[0]


class FakeLLMResponse:
    def __init__(self, content):
        self.content = content


class FakeLLM:
    """Stands in for the LangChain chat model inside `PROMPT | llm`."""

    def __call__(self, prompt_value, *a, **k):  # RunnableLambda-compatible
        return FakeLLMResponse("FAKE ANSWER based on context")


def make_pdf_bytes(text="The capital of France is Paris. " * 20):
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_textbox(pymupdf.Rect(50, 50, 550, 750), text)
    data = doc.tobytes()
    doc.close()
    return data


def make_docx_bytes():
    import io

    d = DocxDocument()
    d.add_paragraph("Quarterly revenue grew by twelve percent in Q3.")
    buf = io.BytesIO()
    d.save(buf)
    return buf.getvalue()


@override_settings(
    MEDIA_ROOT=f"{TMP}/media",
    CHROMA_DIR=f"{TMP}/chroma",
    LLM_PROVIDER="openai",
    OPENAI_API_KEY="test",
)
class DocChatAPITests(APITestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TMP, ignore_errors=True)

    def setUp(self):
        patches = [
            patch("ai_services.rag.embed_texts", fake_embed_texts),
            patch("ai_services.rag.embed_query", fake_embed_query),
            patch("ai_services.rag.get_llm", lambda *a, **k: _runnable_llm()),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)

    # ---- helpers ---------------------------------------------------------
    def register(self, username):
        r = self.client.post(
            "/api/auth/register/",
            {"username": username, "email": f"{username}@example.com", "password": "Str0ng!Pass#99"},
            format="json",
        )
        self.assertEqual(r.status_code, 201, r.content)
        return r.data["access"]

    def auth(self, token):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def upload(self, name="doc.pdf", data=None, content_type="application/pdf"):
        data = data if data is not None else make_pdf_bytes()
        return self.client.post(
            "/api/documents/",
            {"file": SimpleUploadedFile(name, data, content_type=content_type)},
            format="multipart",
        )

    # ---- auth ------------------------------------------------------------
    def test_register_login_me_and_protected(self):
        self.assertEqual(self.client.get("/api/documents/").status_code, 401)
        self.register("alice")
        r = self.client.post(
            "/api/auth/login/", {"username": "alice", "password": "Str0ng!Pass#99"}, format="json"
        )
        self.assertEqual(r.status_code, 200)
        self.auth(r.data["access"])
        self.assertEqual(self.client.get("/api/auth/me/").data["username"], "alice")
        rr = self.client.post("/api/auth/refresh/", {"refresh": r.data["refresh"]}, format="json")
        self.assertEqual(rr.status_code, 200)

    def test_weak_password_rejected(self):
        r = self.client.post(
            "/api/auth/register/",
            {"username": "bob", "email": "bob@example.com", "password": "123"},
            format="json",
        )
        self.assertEqual(r.status_code, 400)

    # ---- upload ----------------------------------------------------------
    def test_upload_pdf_docx_txt_ready(self):
        self.auth(self.register("alice"))
        for name, data in [
            ("a.pdf", make_pdf_bytes()),
            ("b.docx", make_docx_bytes()),
            ("c.txt", b"Plain text about llamas and alpacas. " * 10),
        ]:
            r = self.upload(name, data)
            self.assertEqual(r.status_code, 201, r.content)
            self.assertEqual(r.data["status"], "ready", r.data)
            self.assertGreater(r.data["chunk_count"], 0)
        self.assertEqual(len(self.client.get("/api/documents/").data), 3)

    def test_upload_validation(self):
        self.auth(self.register("alice"))
        self.assertEqual(self.upload("evil.exe", b"MZ....").status_code, 400)
        self.assertEqual(self.upload("fake.pdf", b"not really a pdf").status_code, 400)
        self.assertEqual(self.upload("fake.docx", b"not a zip").status_code, 400)
        self.assertEqual(self.upload("empty.txt", b"").status_code, 400)

    def test_scanned_pdf_marked_failed(self):
        self.auth(self.register("alice"))
        doc = pymupdf.open()
        doc.new_page()  # blank page => no text
        r = self.upload("blank.pdf", doc.tobytes())
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.data["status"], "failed")
        self.assertIn("No extractable text", r.data["error_message"])

    # ---- isolation -------------------------------------------------------
    def test_user_isolation(self):
        alice = self.register("alice")
        bob = self.register("bob")
        self.auth(alice)
        doc_id = self.upload().data["id"]
        self.client.post(f"/api/documents/{doc_id}/chat/", {"question": "capital?"}, format="json")

        self.auth(bob)
        self.assertEqual(self.client.get("/api/documents/").data, [])
        for method, url in [
            ("get", f"/api/documents/{doc_id}/"),
            ("delete", f"/api/documents/{doc_id}/"),
            ("get", f"/api/documents/{doc_id}/chat/"),
            ("delete", f"/api/documents/{doc_id}/chat/"),
            ("post", f"/api/documents/{doc_id}/summarize/"),
            ("post", f"/api/documents/{doc_id}/reprocess/"),
        ]:
            self.assertEqual(getattr(self.client, method)(url).status_code, 404, (method, url))
        r = self.client.post(f"/api/documents/{doc_id}/chat/", {"question": "hi"}, format="json")
        self.assertEqual(r.status_code, 404)

    def test_vector_store_isolation(self):
        """Even if a document id is known, another user's vectors are not returned."""
        from django.conf import settings

        from ai_services import vector_store

        self.auth(self.register("alice"))
        doc_id = self.upload().data["id"]
        alice = User.objects.get(username="alice")
        q = fake_embed_query("capital of France", "x")
        self.assertTrue(vector_store.query(settings.CHROMA_DIR, str(alice.id), doc_id, q, 3))
        self.assertEqual(vector_store.query(settings.CHROMA_DIR, "9999", doc_id, q, 3), [])

    # ---- chat ------------------------------------------------------------
    def test_chat_history_is_document_specific(self):
        self.auth(self.register("alice"))
        d1 = self.upload("one.pdf").data["id"]
        d2 = self.upload("two.pdf", make_pdf_bytes("Totally different text about Mars. " * 20)).data["id"]

        r = self.client.post(f"/api/documents/{d1}/chat/", {"question": "What is the capital?"}, format="json")
        self.assertEqual(r.status_code, 201, r.content)
        self.assertEqual(r.data["assistant_message"]["content"], "FAKE ANSWER based on context")
        self.assertTrue(r.data["assistant_message"]["sources"])

        h1 = self.client.get(f"/api/documents/{d1}/chat/").data
        h2 = self.client.get(f"/api/documents/{d2}/chat/").data
        self.assertEqual([m["role"] for m in h1], ["user", "assistant"])
        self.assertEqual(h2, [])

        self.assertEqual(self.client.delete(f"/api/documents/{d1}/chat/").status_code, 204)
        self.assertEqual(self.client.get(f"/api/documents/{d1}/chat/").data, [])

    def test_chat_validation_and_llm_error(self):
        self.auth(self.register("alice"))
        d = self.upload().data["id"]
        self.assertEqual(self.client.post(f"/api/documents/{d}/chat/", {"question": ""}, format="json").status_code, 400)
        with patch("ai_services.rag.get_llm", side_effect=AIServiceError("no key")):
            r = self.client.post(f"/api/documents/{d}/chat/", {"question": "hello"}, format="json")
        self.assertEqual(r.status_code, 503)
        self.assertEqual(self.client.get(f"/api/documents/{d}/chat/").data, [])  # nothing saved on failure

    # ---- summarize / delete ---------------------------------------------
    def test_summarize_and_delete_cleans_up(self):
        from django.conf import settings

        from ai_services import vector_store
        from documents.models import Document

        self.auth(self.register("alice"))
        d = self.upload().data["id"]
        r = self.client.post(f"/api/documents/{d}/summarize/")
        self.assertEqual(r.status_code, 200, r.content)
        self.assertTrue(r.data["summary"])

        path = Document.objects.get(pk=d).file.path
        uid = str(User.objects.get(username="alice").id)
        self.assertEqual(self.client.delete(f"/api/documents/{d}/").status_code, 204)
        self.assertFalse(Document.objects.filter(pk=d).exists())
        import os

        self.assertFalse(os.path.exists(path))
        self.assertEqual(
            vector_store.query(settings.CHROMA_DIR, uid, d, fake_embed_query("france", "x"), 3), []
        )


def _runnable_llm():
    from langchain_core.runnables import RunnableLambda

    return RunnableLambda(lambda _prompt: FakeLLMResponse("FAKE ANSWER based on context"))
