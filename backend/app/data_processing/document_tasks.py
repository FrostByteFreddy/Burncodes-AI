import os
import asyncio
import re
import tempfile
import httpx
from datetime import datetime, timezone
from urllib.parse import urlparse, urldefrag
from uuid import UUID
import google.generativeai as genai

from celery import shared_task
from app.database.supabase_client import supabase, bucket_name
from app.data_processing.processor import get_loader, process_documents
from langchain_core.documents import Document
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_core.prompts import PromptTemplate
from app.prompts import CLEANUP_PROMPT_TEMPLATES

DEBUG = os.getenv("DEBUG", "False").lower() == "true"
QUERY_GEMINI_MODEL = os.getenv("QUERY_GEMINI_MODEL", "gemini-2.5-flash")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

async def async_process_pdf_with_gemini(filepath: str) -> str:
    """
    Uploads a PDF to Gemini, extracts text and descriptions of visual elements,
    and returns the content as Markdown.
    """
    print(f"🤖 Uploading PDF {filepath} to Gemini for processing...")
    try:
        # Upload the file
        file = await asyncio.to_thread(genai.upload_file, filepath, mime_type="application/pdf")
        
        # Wait for the file to be active
        print(f"⏳ Waiting for file {file.name} to be processed...")
        while file.state.name == "PROCESSING":
            await asyncio.sleep(2)
            file = await asyncio.to_thread(genai.get_file, file.name)
            
        if file.state.name == "FAILED":
            raise Exception("Gemini file processing failed.")

        print(f"✅ File {file.name} is active. Generating content...")

        # Generate content
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = "Extract all text from this document. If there are images, diagrams, or tables, describe them in detail in the text flow where they appear. Output the result in clean Markdown format."
        
        response = await asyncio.to_thread(model.generate_content, [file, prompt])
        
        # Cleanup: Delete the file from Gemini
        await asyncio.to_thread(genai.delete_file, file.name)
        
        return response.text
    except Exception as e:
        print(f"❌ Error processing PDF with Gemini: {e}")
        raise e

async def async_clean_and_chunk_markdown_with_llm(markdown_text: str, doc_language: str = 'en', source_id: int = None) -> str:
    """Uses an LLM to clean, optimize, and chunk raw markdown asynchronously."""
    print(f"🤖 Calling LLM to clean and chunk markdown ({len(markdown_text)} chars) with language '{doc_language}'...")

    # Select the appropriate prompt template based on the document language
    template = CLEANUP_PROMPT_TEMPLATES.get(doc_language, CLEANUP_PROMPT_TEMPLATES['en'])
    print(f"📄 Using doc_language: {doc_language}")

    cleanup_llm = ChatGoogleGenerativeAI(model=QUERY_GEMINI_MODEL, temperature=0.0, timeout=600)
    cleanup_prompt = PromptTemplate.from_template(template)
    cleanup_chain = cleanup_prompt | cleanup_llm
    response = await cleanup_chain.ainvoke({"raw_markdown": markdown_text})
    print("✅ Markdown cleaned and chunked successfully.")
    
    # Write the processed markdown to the "readme" column in tenant_sources
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, lambda: supabase.table('tenant_sources').update({"readme": response.content}).eq('id', source_id).execute())

    return response.content

async def async_create_document_chunks_with_metadata(content: str, source: str, source_id: int, tenant_id: UUID) -> list[Document]:
    """Asynchronously cleans, chunks, and creates Document objects with metadata."""
    documents = []
    loop = asyncio.get_running_loop()
    try:
        # Fetch tenant to get doc_language
        tenant_response = await loop.run_in_executor(None, lambda: supabase.table('tenants').select('doc_language').eq('id', str(tenant_id)).single().execute())
        doc_language = tenant_response.data.get('doc_language', 'en') if tenant_response.data else 'en'

        await loop.run_in_executor(None, lambda: supabase.table('tenant_sources').update({"status": "PROCESSING"}).eq('id', source_id).execute())

        # The LLM now returns a single string with chunks separated by a specific token.
        cleaned_and_chunked_content = await async_clean_and_chunk_markdown_with_llm(content, doc_language, source_id)
        chunks = [chunk.strip() for chunk in cleaned_and_chunked_content.split("---CHUNK_SEPARATOR---") if chunk.strip()]

        if DEBUG:
            try:
                os.makedirs('crawled_markdown', exist_ok=True)
                safe_filename = re.sub(r'https://?|www\.|\/|\?|\=|\&', '_', source) + ".md"
                filepath = os.path.join('crawled_markdown', safe_filename)
                # Save the raw, chunked output for inspection
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(f"# SOURCE: {source}\n\n{cleaned_and_chunked_content}")
                print(f"🕵️‍♂️ Saved CLEANED and CHUNKED markdown for {source} to {filepath}")
            except Exception as e:
                print(f"❌ Could not save cleaned markdown file for {source}: {e}")

        timestamp = datetime.now(timezone.utc).isoformat()
        for i, chunk in enumerate(chunks):
            doc = Document(
                page_content=chunk,
                metadata={"source": source, "source_id": source_id, "chunk": i, "last_updated": timestamp}
            )
            documents.append(doc)

        return documents
    except Exception as e:
        print(f"Error creating document chunks for source {source_id}: {e}")
        await loop.run_in_executor(None, lambda: supabase.table('tenant_sources').update({"status": "ERROR"}).eq('id', source_id).execute())
        return []

async def async_create_document_chunks_for_structured_data(content: str, source: str, source_id: int) -> list[Document]:
    """Asynchronously chunks and creates Document objects for structured data without LLM cleaning."""
    documents = []
    loop = asyncio.get_running_loop()
    try:
        # Note: This path skips the `async_clean_markdown_with_llm` step
        await loop.run_in_executor(None, lambda: supabase.table('tenant_sources').update({"status": "PROCESSING"}).eq('id', source_id).execute())

        # For structured data, create a single document with the entire content.
        timestamp = datetime.now(timezone.utc).isoformat()
        doc = Document(
            page_content=content,
            metadata={"source": source, "source_id": source_id, "chunk": 0, "last_updated": timestamp}
        )
        documents.append(doc)

        print(f"✅ Created 1 document for structured file {source} (source_id: {source_id})")
        return documents
    except Exception as e:
        print(f"Error creating document chunks for structured source {source_id}: {e}")
        await loop.run_in_executor(None, lambda: supabase.table('tenant_sources').update({"status": "ERROR"}).eq('id', source_id).execute())
        return []

async def _get_document_chunks_from_content(content: str, source: str, source_id: int, ext: str, tenant_id: UUID) -> list[Document]:
    """Internal helper to decide which chunking strategy to use based on file extension."""
    structured_extensions = ['.csv', '.ics']
    if ext in structured_extensions:
        # Use the direct path for structured data
        return await async_create_document_chunks_for_structured_data(content, source, source_id)
    else:
        # Use the LLM cleaning path for unstructured data
        return await async_create_document_chunks_with_metadata(content, source, source_id, tenant_id)

@shared_task
def process_s3_file(s3_path: str, source_filename: str, source_id: int, tenant_id: UUID):
    """Celery task to process a file stored in Supabase S3."""
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    docs = asyncio.run(async_process_s3_file(s3_path, source_filename, source_id, tenant_id))
    process_documents(docs, tenant_id, embeddings)

async def async_process_s3_file(s3_path: str, source_filename: str, source_id: int, tenant_id: UUID) -> list[Document]:
    """
    Downloads a file from S3, processes it into document chunks, and cleans up the temporary file.
    """
    ext = os.path.splitext(source_filename)[1].lower()
    tmp_filepath = None
    try:
        # Download file from S3
        file_content = supabase.storage.from_(bucket_name).download(s3_path)
        if file_content is None:
            raise FileNotFoundError(f"File not found in S3 at path: {s3_path}")

        # Create a temporary file to store the content
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp_file:
            tmp_file.write(file_content)
            tmp_filepath = tmp_file.name

        # --- GEMINI PDF PROCESSING ---
        if ext == '.pdf':
            try:
                content = await async_process_pdf_with_gemini(tmp_filepath)
                return await _get_document_chunks_from_content(content, source_filename, source_id, ext, tenant_id)
            except Exception as e:
                print(f"⚠️ Gemini processing failed for {source_filename}, falling back to standard loader: {e}")
                # Fallback to standard loader if Gemini fails
        
        # Get the appropriate loader for the file extension
        loader = get_loader(tmp_filepath)
        if not loader:
            print(f"⚠️ No loader found for extension {ext}, skipping file {source_filename}")
            return []

        # Load and process the document
        docs_from_loader = loader.load()
        if not docs_from_loader:
            return []

        # FIX: Join all pages instead of just taking the first one
        content = "\n\n".join([d.page_content for d in docs_from_loader])
        return await _get_document_chunks_from_content(content, source_filename, source_id, ext, tenant_id)

    except Exception as e:
        print(f"❌ Error processing S3 file {s3_path}: {e}")
        # Mark the source as errored
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, lambda: supabase.table('tenant_sources').update({"status": "ERROR"}).eq('id', source_id).execute())
        return []
    finally:
        # Clean up the temporary file
        if tmp_filepath and os.path.exists(tmp_filepath):
            os.remove(tmp_filepath)

async def async_process_file_url(url: str, tenant_id: UUID, source_id: int) -> list[Document]:
    """Downloads a file from a URL and processes its content."""
    print(f"📄 Downloading and processing file: {url}")
    ext = os.path.splitext(urlparse(url).path)[1].lower()
    if not ext: return []

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, follow_redirects=True, timeout=60.0)
            response.raise_for_status()

        tenant_upload_path = os.path.join('uploads', str(tenant_id))
        os.makedirs(tenant_upload_path, exist_ok=True)

        with tempfile.NamedTemporaryFile(delete=False, suffix=ext, dir=tenant_upload_path) as tmp_file:
            tmp_file.write(response.content)
            tmp_filepath = tmp_file.name

        # --- GEMINI PDF PROCESSING ---
        if ext == '.pdf':
            try:
                content = await async_process_pdf_with_gemini(tmp_filepath)
                os.remove(tmp_filepath)
                return await _get_document_chunks_from_content(content, url, source_id, ext, tenant_id)
            except Exception as e:
                print(f"⚠️ Gemini processing failed for {url}, falling back to standard loader: {e}")

        loader = get_loader(tmp_filepath)
        if not loader:
            print(f"⚠️ No loader found for extension {ext}, skipping file {url}")
            os.remove(tmp_filepath)
            return []

        docs_from_loader = loader.load()
        os.remove(tmp_filepath)

        if not docs_from_loader: return []

        # FIX: Join all pages
        content = "\n\n".join([d.page_content for d in docs_from_loader])
        return await _get_document_chunks_from_content(content, url, source_id, ext, tenant_id)

    except Exception as e:
        print(f"❌ Error processing file URL {url}: {e}")
        if 'tmp_filepath' in locals() and os.path.exists(tmp_filepath):
            os.remove(tmp_filepath)
        return []
