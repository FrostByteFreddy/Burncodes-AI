import os
import re
import time
import random
import chromadb
from uuid import UUID
from supabase import Client
from app.database.supabase_client import supabase


# --- LangChain Core Imports ---
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader, CSVLoader
from langchain_community.document_loaders.base import BaseLoader
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.documents import Document
from icalendar import Calendar
from typing import List
from app.models.database import TenantFineTune


# --- CONFIGURATION ---
SUPPORTED_FILE_EXTENSIONS = ['.pdf', '.docx', '.txt', '.csv', '.ics']

# In-memory cache to store initialized vector stores (On god I hope this does not break my 4gb limit lol)
# vectorstore_cache = {}

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
    
    # If Vectorstore is already in cache, return it
    # if tenant_id in vectorstore_cache:
    #     print(f"✅ Returning cached ChromaDB instance for tenant: {tenant_id}")
    #     return vectorstore_cache[tenant_id]
    
    tenant_id_str = str(tenant_id)
    vector_store_path_base = os.getenv('CRAWL4_AI_BASE_DIRECTORY')
    if not vector_store_path_base:
        raise ValueError("CRAWL4_AI_BASE_DIRECTORY environment variable not set.")

    tenant_db_path = os.path.join(vector_store_path_base, tenant_id_str)

    # Ensure the directory exists
    os.makedirs(tenant_db_path, exist_ok=True)

    client = chromadb.PersistentClient(path=tenant_db_path)

    vectorstore = Chroma(
        client=client,
        collection_name=f"content_gemini_{tenant_id_str}",
        embedding_function=embeddings,
    )
    
    # Cache the vectorstore for future use
    # vectorstore_cache[tenant_id] = vectorstore
    
    print(f"✅ ChromaDB vector store initialized for tenant: {tenant_id_str}")
    return vectorstore

def process_documents(docs: list[Document], tenant_id: UUID, embeddings: Embeddings, supabase_client: Client = supabase):
    if not docs:
        print("No documents to process")
        return

    source_ids = list(set(doc.metadata['source_id'] for doc in docs if 'source_id' in doc.metadata))

    try:
        db = get_vectorstore(tenant_id, embeddings)
        
        max_retries = 5
        for attempt in range(max_retries):
            try:
                db.add_documents(docs)
                break  # Success, exit loop
            except Exception as e:
                if "readonly database" in str(e) and attempt < max_retries - 1:
                    time.sleep(random.uniform(0.5, 2.0))  # Wait before retrying
                    continue
                raise e
            
        print(f"✅ Added {len(docs)} document chunks to ChromaDB for tenant: {tenant_id}.")

        if source_ids:
            supabase_client.table('tenant_sources').update({"status": "COMPLETED"}).in_('id', source_ids).execute()
            print(f"✅ Marked sources {source_ids} as COMPLETED.")

    except Exception as e:
        print(f"❌ Error processing documents for tenant {tenant_id}: {e}")
        if source_ids:
            supabase_client.table('tenant_sources').update({"status": "ERROR"}).in_('id', source_ids).execute()
            print(f"🔥 Marked sources {source_ids} as ERROR.")

def process_fine_tune_rules(rules: List[TenantFineTune], tenant_id: UUID, embeddings: Embeddings, supabase_client: Client = supabase):
    """
    Processes fine-tuning rules, creates documents, and adds them to the vector store.
    Returns the vector IDs of the newly created documents.
    """
    if not rules:
        print("No fine-tune rules to process.")
        return []

    docs = [
        Document(
            page_content=f"Trigger: {rule.trigger}\nInstruction: {rule.instruction}",
            metadata={"rule_id": str(rule.id), "tenant_id": str(tenant_id)}
        ) for rule in rules
    ]

    try:
        db = get_vectorstore(tenant_id, embeddings)
        # Assuming `add_documents` returns the IDs of the added documents.
        # This might need to be adjusted based on the actual return value of `db.add_documents`.
        # According to LangChain docs, the `add_documents` method in Chroma returns a list of IDs.
        vector_ids = db.add_documents(docs)
        print(f"✅ Added {len(docs)} fine-tune rule vectors to ChromaDB for tenant: {tenant_id}.")
        return vector_ids
    except Exception as e:
        print(f"❌ Error processing fine-tune rules for tenant {tenant_id}: {e}")
        # Optionally, handle the error more gracefully
        return []

def delete_fine_tune_vectors(vector_ids: List[str], tenant_id: UUID, embeddings: Embeddings):
    """
    Deletes fine-tuning rule vectors from the vector store based on their IDs.
    """
    if not vector_ids:
        print("No vector IDs provided for deletion.")
        return

    try:
        db = get_vectorstore(tenant_id, embeddings)
        db.delete(ids=vector_ids)
        print(f"✅ Deleted {len(vector_ids)} fine-tune rule vectors from ChromaDB for tenant: {tenant_id}.")
    except Exception as e:
        print(f"❌ Error deleting fine-tune vectors for tenant {tenant_id}: {e}")
