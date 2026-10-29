"""
Deleting knowledge: nothing leaves the database until Gemini has let go of it,
so a failed Gemini call never leaves documents behind that no row points to.
"""
from unittest.mock import MagicMock

from app.gemini_store import service as gemini


def _client(fails=None):
    client = MagicMock()
    client.file_search_stores.documents.chunks.list.return_value = []
    if fails:
        client.file_search_stores.documents.delete.side_effect = fails
        client.file_search_stores.delete.side_effect = fails
    return client


def test_document_deletion_reports_success(monkeypatch):
    monkeypatch.setattr(gemini, "_get_client", lambda: _client())
    assert gemini.GeminiStoreService.delete_document("fileSearchStores/s/documents/d") is True
    assert gemini.GeminiStoreService.delete_store("fileSearchStores/s") is True


def test_missing_documents_count_as_deleted(monkeypatch):
    monkeypatch.setattr(gemini, "_get_client", lambda: _client(Exception("404 NOT_FOUND. Document not found")))
    assert gemini.GeminiStoreService.delete_document("fileSearchStores/s/documents/d") is True
    assert gemini.GeminiStoreService.delete_store("fileSearchStores/s") is True


def test_failures_are_reported(monkeypatch):
    monkeypatch.setattr(gemini, "_get_client", lambda: _client(Exception("503 UNAVAILABLE")))
    assert gemini.GeminiStoreService.delete_document("fileSearchStores/s/documents/d") is False
    assert gemini.GeminiStoreService.delete_store("fileSearchStores/s") is False


def test_only_sources_gone_from_gemini_may_be_deleted(monkeypatch):
    from app.tenants import sources
    kept = {"fileSearchStores/s/documents/b2"}
    monkeypatch.setattr(gemini.GeminiStoreService, "delete_document", staticmethod(lambda name: name not in kept))
    rows = [
        {"id": 1, "gemini_document_names": ["fileSearchStores/s/documents/a1"]},
        {"id": 2, "gemini_document_names": ["fileSearchStores/s/documents/b1", "fileSearchStores/s/documents/b2"]},
        {"id": 3, "gemini_document_names": []},                                  # never learned
    ]
    assert sources._delete_documents(rows, "test") == [1, 3]
