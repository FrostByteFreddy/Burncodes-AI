import os
import re
import chromadb
from uuid import UUID
from flask import current_app
from supabase import Client
from app.database.supabase_client import supabase


# --- LangChain Core Imports ---
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader, CSVLoader
from langchain_community.document_loaders.base import BaseLoader
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.documents import Document
from icalendar import Calendar

# --- CONFIGURATION ---
SUPPORTED_FILE_EXTENSIONS = ['.pdf', '.docx', '.txt', '.csv', '.ics']

# --- DOCUMENT LOADERS ---
class ICSExtensionLoader(BaseLoader):
    """A simple loader for .ics files."""
    def __init__(self, file_path: str):
        self.file_path = file_path

    def load(self) -> list[Document]:
        with open(self.file_path, 'rb') as f:
            calendar = Calendar.from_ical(f.read())

        content = ""
        for component in calendar.walk():
            if component.name == "VEVENT":
                summary = component.get('summary')
                description = component.get('description')
                start_time = component.get('dtstart').dt if component.get('dtstart') else 'N/A'
                end_time = component.get('dtend').dt if component.get('dtend') else 'N/A'
                location = component.get('location')

                content += f"Event: {summary}\n"
                if description:
                    content += f"Description: {description}\n"
                content += f"Start: {start_time}\n"
                content += f"End: {end_time}\n"
                if location:
                    content += f"Location: {location}\n"
                content += "---\n"

        return [Document(page_content=content)]

def get_loader(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    if ext == '.pdf': return PyPDFLoader(filepath)
    elif ext == '.docx': return Docx2txtLoader(filepath)
    elif ext == '.txt': return TextLoader(filepath, encoding='utf-8')
    elif ext == '.csv': return CSVLoader(filepath, encoding='utf-8')
    elif ext == '.ics': return ICSExtensionLoader(filepath)
    return None

from langchain_core.embeddings import Embeddings

def get_vectorstore(tenant_id: UUID, embeddings: Embeddings):
    """Initializes and returns a tenant-specific Chroma vector store instance."""
    tenant_id_str = str(tenant_id)
    vector_store_path_base = current_app.config['CRAWL4_AI_BASE_DIRECTORY']
    tenant_db_path = os.path.join(vector_store_path_base, tenant_id_str)

    # Using the recommended persistent client approach
    persistent_client = chromadb.PersistentClient(path=tenant_db_path)

    vectorstore = Chroma(
        client=persistent_client,
        collection_name=f"content_gemini_{tenant_id_str}",
        embedding_function=embeddings,
    )
    print(f"✅ ChromaDB vector store initialized for tenant: {tenant_id_str}")
    return vectorstore

def process_documents(docs: list[Document], tenant_id: UUID, embeddings: Embeddings, supabase_client: Client = supabase):
    if not docs:
        print("No documents to process")
        return

    source_ids = list(set(doc.metadata['source_id'] for doc in docs if 'source_id' in doc.metadata))

    try:
        db = get_vectorstore(tenant_id, embeddings)
        db.add_documents(docs)
        print(f"✅ Added {len(docs)} document chunks to ChromaDB for tenant: {tenant_id}.")

        if source_ids:
            supabase_client.table('tenant_sources').update({"status": "COMPLETED"}).in_('id', source_ids).execute()
            print(f"✅ Marked sources {source_ids} as COMPLETED.")

    except Exception as e:
        print(f"❌ Error processing documents for tenant {tenant_id}: {e}")
        if source_ids:
            supabase_client.table('tenant_sources').update({"status": "ERROR"}).in_('id', source_ids).execute()
            print(f"🔥 Marked sources {source_ids} as ERROR.")
