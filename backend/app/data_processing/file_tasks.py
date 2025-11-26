import os
import time
import asyncio
import tempfile
from google import genai
from uuid import UUID
from celery import shared_task
from app.database.supabase_client import supabase, bucket_name
from app.data_processing.processor import process_documents, get_loader
from app.data_processing.tasks import _get_document_chunks_from_content
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.documents import Document
from datetime import datetime, timezone

# Configure Gemini
api_key = os.getenv("GOOGLE_API_KEY")
MODEL_NAME = os.getenv("QUERY_GEMINI_MODEL", "gemini-2.5-flash")
PROMPT = "Convert this document to Markdown. Preserve all headers, tables, and structure."

if not api_key:
    print("WARNING: GOOGLE_API_KEY not found in environment variables.")
    # We can't initialize the client without an API key, but we can defer it or let it fail later.
    # The client might pick it up from env automatically if set as GOOGLE_API_KEY.
    client = None
else:
    client = genai.Client(api_key=api_key)


@shared_task(time_limit=1800)
def process_s3_file(s3_path: str, source_filename: str, source_id: int, tenant_id: UUID):
    """Celery task to process a file stored in Supabase S3 using Gemini 2.5 Flash."""
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    docs = asyncio.run(async_process_s3_file(s3_path, source_filename, source_id, tenant_id))
    process_documents(docs, tenant_id, embeddings)

async def async_process_s3_file(s3_path: str, source_filename: str, source_id: int, tenant_id: UUID) -> list[Document]:
    """
    Downloads a file from S3, uploads it to Gemini, and processes it into document chunks.
    """
    ext = os.path.splitext(source_filename)[1].lower()
    tmp_filepath = None
    loop = asyncio.get_running_loop()
    
    try:
        if not client:
             raise ValueError("Google GenAI Client not initialized. Check GOOGLE_API_KEY.")

        # 1. Download file from S3
        file_content = supabase.storage.from_(bucket_name).download(s3_path)
        if file_content is None:
            raise FileNotFoundError(f"File not found in S3 at path: {s3_path}")

        # 2. Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp_file:
            tmp_file.write(file_content)
            tmp_filepath = tmp_file.name

        # 3. Upload to Gemini and wait for processing
        print(f"--- Uploading {tmp_filepath} to Gemini ---")
        # The new client.files.upload is synchronous, so we run it in executor
        uploaded_file = await loop.run_in_executor(None, lambda: upload_and_wait_for_processing(tmp_filepath))
        
        # 4. Generate content
        print(f"--- Generating content with {MODEL_NAME} ---")
        
        # We need to run this in an executor because it's blocking
        response = await loop.run_in_executor(
            None, 
            lambda: client.models.generate_content(
                model=MODEL_NAME,
                contents=[uploaded_file, PROMPT]
            )
        )
        
        output_text = response.text
        
        # 5. Update database with full markdown
        await loop.run_in_executor(None, lambda: supabase.table('tenant_sources').update({"readme": output_text}).eq('id', source_id).execute())
        
        # 6. Create chunks
        # We can reuse _get_document_chunks_from_content but we already have the markdown.
        # _get_document_chunks_from_content handles structured data vs unstructured.
        # But here we have explicitly converted to markdown using Gemini.
        # So we should probably just chunk the markdown.
        # However, _get_document_chunks_from_content calls async_create_document_chunks_with_metadata which does cleaning.
        # Since we already have clean markdown from Gemini 2.5, maybe we don't need another cleaning step?
        # The user said: "We might use the same functions for writing the chunked markdown into the our chromadb."
        # So I should probably use `async_create_document_chunks_with_metadata` but maybe skip the cleaning part if it's already good?
        # Or just let it run. The `async_create_document_chunks_with_metadata` calls `async_clean_and_chunk_markdown_with_llm`.
        # That function does "Uses an LLM to clean, optimize, and chunk raw markdown asynchronously."
        # If Gemini 2.5 Flash already gives us good markdown, maybe we just need to chunk it?
        # But `async_clean_and_chunk_markdown_with_llm` also adds the `---CHUNK_SEPARATOR---`.
        # So we DO need to call it, or replicate that logic.
        # Let's use the existing function to maintain consistency and chunking logic.
        
        # However, `_get_document_chunks_from_content` takes `content` which is usually raw text from a loader.
        # Here `output_text` IS the content we want to chunk.
        # So we can call `async_create_document_chunks_with_metadata` directly.
        
        from app.data_processing.tasks import async_create_document_chunks_with_metadata
        
        return await async_create_document_chunks_with_metadata(output_text, source_filename, source_id, tenant_id)

    except Exception as e:
        print(f"❌ Error processing S3 file {s3_path}: {e}")
        await loop.run_in_executor(None, lambda: supabase.table('tenant_sources').update({"status": "ERROR"}).eq('id', source_id).execute())
        return []
    finally:
        # Clean up the temporary file
        if tmp_filepath and os.path.exists(tmp_filepath):
            os.remove(tmp_filepath)
        # We should also delete the file from Gemini to save space/privacy?
        # The user's script didn't do it, but it's good practice.
        # I'll leave it for now as per user script.

def upload_and_wait_for_processing(file_path):
    """Uploads the file and waits until it's ready for inference."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    # FIX: Pass the file_path string directly. Removed undefined 'media' variable.
    uploaded_file = client.files.upload(file=file_path)
    
    print(f"Uploaded: {uploaded_file.display_name} ({uploaded_file.uri})")

    print("Waiting for processing...", end="", flush=True)
    # Check state using the name property. 
    # Loops while processing; if it fails, the loop breaks and we catch it below.
    while uploaded_file.state.name == "PROCESSING":
        print(".", end="", flush=True)
        time.sleep(2)
        # FIX: Use keyword argument 'name=' for clarity and correctness with the new SDK
        uploaded_file = client.files.get(name=uploaded_file.name)

    print(f"\nState: {uploaded_file.state.name}")
    
    if uploaded_file.state.name == "FAILED":
        raise RuntimeError("File processing failed.")
        
    return uploaded_file