"""
shared/gemini_store/service.py

Central service for all Gemini File Search Store operations.
Used by every worker (fast, heavy, chat) and the API service.

One store per tenant — created lazily on first source upload.
Embedding model is fixed at store creation time (gemini-embedding-2).
"""
import os
import io
import time
import tempfile
from pathlib import Path

from google import genai

from app.database.supabase_client import supabase
from app.logging_config import error_logger

# File extensions treated as directly-indexable documents (downloaded & uploaded as-is)
INDEXABLE_FILE_EXTENSIONS: set[str] = {
    ".pdf", ".docx", ".doc", ".txt", ".md",
    ".png", ".jpg", ".jpeg", ".gif", ".webp",
}

# Extensions we explicitly reject (not supported by File Search)
UNSUPPORTED_EXTENSIONS: set[str] = {
    ".xlsx", ".xls", ".pptx", ".ppt", ".csv", ".ics", ".zip",
}

_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
    return _client


class GeminiStoreService:
    """Manages per-tenant Gemini File Search Stores."""

    # -----------------------------------------------------------------------
    # Store lifecycle
    # -----------------------------------------------------------------------

    @staticmethod
    def get_or_create_store(tenant_id: str) -> str:
        """
        Returns the store name for a tenant.
        Creates it with gemini-embedding-2 if it doesn't exist yet.
        Persists the store name to tenants.gemini_file_store_name.
        """
        row = (
            supabase.table("tenants")
            .select("gemini_file_store_name")
            .eq("id", tenant_id)
            .single()
            .execute()
        )
        store_name: str | None = (row.data or {}).get("gemini_file_store_name")

        if not store_name:
            error_logger.info("Creating new File Search store for tenant %s", tenant_id)
            client = _get_client()
            store = client.file_search_stores.create(
                config={
                    "display_name": f"tenant-{tenant_id}",
                    "embedding_model": "models/gemini-embedding-2",
                }
            )
            store_name = store.name
            supabase.table("tenants").update(
                {"gemini_file_store_name": store_name}
            ).eq("id", tenant_id).execute()
            error_logger.info("Created store %s for tenant %s", store_name, tenant_id)

        return store_name

    @staticmethod
    def delete_store(store_name: str) -> None:
        """
        Deletes the entire store and all contained documents.
        Called when a tenant is deleted.
        """
        try:
            client = _get_client()
            client.file_search_stores.delete(
                name=store_name, config={"force": True}
            )
            error_logger.info("Deleted File Search store %s", store_name)
        except Exception as e:
            error_logger.error("Failed to delete store %s: %s", store_name, e, exc_info=True)

    # -----------------------------------------------------------------------
    # Document upload
    # -----------------------------------------------------------------------

    @staticmethod
    def upload_file(
        store_name: str,
        file_path: str,
        display_name: str,
        metadata: dict | None = None,
    ) -> str:
        """
        Uploads a local file path to the store and polls until indexed.
        Returns the gemini_document_name used for later deletion.

        Args:
            store_name: Gemini store resource name.
            file_path:  Absolute path to the file on disk.
            display_name: Human-readable label (filename or URL).
            metadata: Optional dict of key→string_value pairs.
        """
        client = _get_client()
        config: dict = {"display_name": display_name}
        if metadata:
            config["custom_metadata"] = [
                {"key": k, "string_value": str(v)} for k, v in metadata.items()
            ]

        error_logger.info("Uploading %s to store %s", display_name, store_name)
        operation = client.file_search_stores.upload_to_file_search_store(
            file_search_store_name=store_name,
            file=file_path,
            config=config,
        )

        # Poll until Gemini finishes chunking + embedding
        while not operation.done:
            time.sleep(3)
            operation = client.operations.get(operation)

        # Extract the document resource name from the completed operation
        doc_name = GeminiStoreService._extract_doc_name(operation, store_name, display_name)
        error_logger.info("Indexed %s → %s", display_name, doc_name)
        return doc_name

    @staticmethod
    def upload_text(
        store_name: str,
        text: str,
        display_name: str,
        metadata: dict | None = None,
    ) -> str:
        """
        Uploads plain text content (e.g., crawled markdown) to the store.
        Writes to a temp .txt file so the SDK correctly detects MIME type.
        """
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", suffix=".txt", delete=False
        ) as f:
            f.write(text)
            tmp_path = f.name
        try:
            return GeminiStoreService.upload_file(
                store_name=store_name,
                file_path=tmp_path,
                display_name=display_name,
                metadata=metadata,
            )
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    @staticmethod
    def upload_bytes(
        store_name: str,
        content: bytes,
        filename: str,
        display_name: str,
        metadata: dict | None = None,
    ) -> str:
        """
        Uploads raw bytes (e.g., a downloaded PDF) to the store.
        Writes to a temp file using the original file's extension.
        """
        suffix = Path(filename).suffix or ".bin"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
            f.write(content)
            tmp_path = f.name
        try:
            return GeminiStoreService.upload_file(
                store_name=store_name,
                file_path=tmp_path,
                display_name=display_name,
                metadata=metadata,
            )
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    # -----------------------------------------------------------------------
    # Document deletion
    # -----------------------------------------------------------------------

    @staticmethod
    def delete_document(gemini_document_name: str) -> None:
        """
        Deletes a specific document from its store.
        Called when a user deletes a source.
        """
        try:
            client = _get_client()
            client.file_search_stores.documents.delete(name=gemini_document_name)
            error_logger.info("Deleted document %s", gemini_document_name)
        except Exception as e:
            error_logger.error(
                "Failed to delete document %s: %s", gemini_document_name, e, exc_info=True
            )

    # -----------------------------------------------------------------------
    # Internal helpers
    # -----------------------------------------------------------------------

    @staticmethod
    def _extract_doc_name(operation, store_name: str, display_name: str) -> str:
        """
        Extracts the document resource name from a completed upload operation.
        Falls back to listing the store if metadata isn't directly accessible.
        """
        # Try the most likely attribute paths from the SDK
        for attr_path in [
            ("response", "document_name"),        # UploadToFileSearchStoreResponse.document_name
            ("metadata", "document_resource_name"),
            ("response", "name"),                  # fallback in case the SDK changes
        ]:
            obj = operation
            try:
                for attr in attr_path:
                    obj = getattr(obj, attr)
                if obj and isinstance(obj, str):
                    return obj
            except AttributeError:
                continue

        # Last resort: scan the operation name itself for the document ID
        # operation.name format: "operations/fileSearchStores/xxx/documents/yyy/..."
        op_name = getattr(operation, "name", "") or ""
        if "documents/" in op_name:
            # Extract fileSearchStores/.../documents/... prefix
            idx = op_name.find("documents/")
            end = op_name.find("/", idx + len("documents/"))
            doc_fragment = op_name[: end if end != -1 else None]
            if store_name in doc_fragment:
                return doc_fragment

        error_logger.warning(
            "Could not extract document name from operation for %s — "
            "deletion of this source will not be possible. Operation: %s",
            display_name,
            vars(operation),
        )
        return ""
