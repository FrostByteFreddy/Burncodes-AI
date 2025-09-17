import os
import re
import chromadb
from uuid import UUID

# --- LangChain Core Imports ---
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader, CSVLoader
from langchain_community.document_loaders.base import BaseLoader
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.documents import Document
from icalendar import Calendar

# --- CONFIGURATION ---
VECTOR_STORE_PATH_BASE = 'chromadb'
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

def get_vectorstore(tenant_id: UUID):
    """Initializes and returns a tenant-specific Chroma vector store instance."""
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    tenant_id_str = str(tenant_id)
    tenant_db_path = os.path.join(VECTOR_STORE_PATH_BASE, tenant_id_str)

    client_settings = chromadb.Settings(
        is_persistent=True,
        persist_directory=tenant_db_path,
        anonymized_telemetry=False
    )
    vectorstore = Chroma(
        collection_name=f"content_{tenant_id_str}",
        embedding_function=embeddings,
        client_settings=client_settings,
        persist_directory=tenant_db_path
    )
    print(f"✅ ChromaDB vector store initialized for tenant: {tenant_id_str}")
    return vectorstore

def smart_chunk_markdown(markdown: str, max_len: int = 1000) -> list[str]:
    def split_by_header(md, header_pattern):
        indices = [m.start() for m in re.finditer(header_pattern, md, re.MULTILINE)]
        indices.append(len(md))
        return [md[indices[i]:indices[i+1]].strip() for i in range(len(indices)-1) if md[indices[i]:indices[i+1]].strip()]
    chunks = []
    h1_split = split_by_header(markdown, r'^# .+$')
    if not h1_split: h1_split = [markdown]
    for h1 in h1_split:
        if len(h1) > max_len:
            h2_split = split_by_header(h1, r'^## .+$')
            if not h2_split: h2_split = [h1]
            for h2 in h2_split:
                if len(h2) > max_len:
                    h3_split = split_by_header(h2, r'^### .+$')
                    if not h3_split: h3_split = [h2]
                    for h3 in h3_split:
                        if len(h3) > max_len:
                            for i in range(0, len(h3), max_len): chunks.append(h3[i:i+max_len].strip())
                        else: chunks.append(h3)
                else: chunks.append(h2)
        else: chunks.append(h1)
    final_chunks = [c for c in chunks if c and len(c) <= max_len]
    return final_chunks

def process_documents(docs: list[Document], tenant_id: UUID):
    if not docs:
        print("No documents to process")
        return
    db = get_vectorstore(tenant_id)
    db.add_documents(docs)
    print(f"✅ Added {len(docs)} document chunks to ChromaDB for tenant: {tenant_id}.")
