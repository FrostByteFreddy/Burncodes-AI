import os
import asyncio
import re
import requests
import tempfile
import nest_asyncio
import shutil
import chromadb
import json
import httpx
from datetime import datetime, timezone
from urllib.parse import urlparse, urldefrag
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# --- Crawl4AI & ChromaDB Imports ---
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from langchain_community.vectorstores import Chroma

# --- LangChain Core Imports ---
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader, CSVLoader
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain.chains import create_retrieval_chain
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, AIMessage
from langchain.chains import create_history_aware_retriever

# --- Global Variables ---
tenant_vectorstores = {} 
embeddings = None
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# --- INITIALIZATION ---
load_dotenv()
nest_asyncio.apply()
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

# --- AI INSTRUCTIONS ---
try:
    with open('instructions.json', 'r', encoding='utf-8') as f:
        INSTRUCTIONS = json.load(f)
    CLEANUP_PROMPT_TEMPLATE = INSTRUCTIONS['cleanup_prompt_template']
    print("✅ Successfully loaded instructions from instructions.json")
except (FileNotFoundError, KeyError) as e:
    print(f"❌ Error loading instructions.json: {e}. Please ensure the file exists and is correctly formatted.")
    exit()

# --- CONFIGURATION ---
UPLOAD_FOLDER_BASE = 'uploads'
VECTOR_STORE_PATH_BASE = 'chromadb'
os.makedirs(UPLOAD_FOLDER_BASE, exist_ok=True)
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL")
QUERY_GEMINI_MODEL = os.getenv("QUERY_GEMINI_MODEL", "gemini-1.5-flash")

# --- DOCUMENT LOADERS ---
SUPPORTED_FILE_EXTENSIONS = ['.pdf', '.docx', '.txt', '.csv']
def get_loader(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    if ext == '.pdf': return PyPDFLoader(filepath)
    elif ext == '.docx': return Docx2txtLoader(filepath)
    elif ext == '.txt': return TextLoader(filepath, encoding='utf-8')
    elif ext == '.csv': return CSVLoader(filepath, encoding='utf-8')
    return None

# --- ASYNC CHROMA & CRAWLING HELPERS ---
def get_vectorstore(tenant: str):
    """Initializes and returns a tenant-specific Chroma vector store instance."""
    global tenant_vectorstores, embeddings
    if tenant in tenant_vectorstores:
        return tenant_vectorstores[tenant]

    if embeddings is None:
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

    tenant_db_path = os.path.join(VECTOR_STORE_PATH_BASE, tenant)
    client_settings = chromadb.Settings(
        is_persistent=True,
        persist_directory=tenant_db_path,
        anonymized_telemetry=False
    )
    vectorstore = Chroma(
        collection_name=f"content_{tenant}",
        embedding_function=embeddings,
        client_settings=client_settings,
        persist_directory=tenant_db_path
    )
    tenant_vectorstores[tenant] = vectorstore
    print(f"✅ ChromaDB vector store initialized for tenant: {tenant}")
    return vectorstore

async def async_clean_markdown_with_llm(markdown_text: str) -> str:
    """Uses an LLM to clean and optimize raw markdown asynchronously."""
    print(f"🤖 Calling LLM to clean markdown ({len(markdown_text)} chars)...")
    cleanup_llm = ChatGoogleGenerativeAI(model=QUERY_GEMINI_MODEL, temperature=0.0)
    cleanup_prompt = PromptTemplate.from_template(CLEANUP_PROMPT_TEMPLATE)
    cleanup_chain = cleanup_prompt | cleanup_llm
    response = await cleanup_chain.ainvoke({"raw_markdown": markdown_text})
    print("✅ Markdown cleaned successfully.")
    return response.content

def smart_chunk_markdown(markdown: str, max_len: int = 1000) -> list[str]:
    # ... (This function remains synchronous and unchanged)
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

async def async_create_document_chunks_with_metadata(content: str, source: str) -> list[Document]:
    """Asynchronously cleans, chunks, and creates Document objects with metadata."""
    documents = []
    clean_content = await async_clean_markdown_with_llm(content)

    if DEBUG:
        try:
            os.makedirs('crawled_markdown', exist_ok=True)
            safe_filename = re.sub(r'https://?|www\.|\/|\?|\=|\&', '_', source) + ".md"
            filepath = os.path.join('crawled_markdown', safe_filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"# SOURCE: {source}\n\n{clean_content}")
            print(f"🕵️‍♂️ Saved CLEANED markdown for {source} to {filepath}")
        except Exception as e:
            print(f"❌ Could not save cleaned markdown file for {source}: {e}")

    chunks = smart_chunk_markdown(clean_content, max_len=1000)
    timestamp = datetime.now(timezone.utc).isoformat()
    for i, chunk in enumerate(chunks):
        doc = Document(
            page_content=chunk,
            metadata={"source": source, "chunk": i, "last_updated": timestamp}
        )
        documents.append(doc)
    return documents

def process_documents(docs: list[Document], tenant: str):
    if not docs:
        print("No documents to process")
        return
    db = get_vectorstore(tenant)
    db.add_documents(docs)
    print(f"✅ Added {len(docs)} document chunks to ChromaDB for tenant: {tenant}.")
    
async def async_process_file_url(url: str, tenant: str) -> list[Document]:
    """Downloads a file from a URL and processes its content."""
    print(f"📄 Downloading and processing file: {url}")
    ext = os.path.splitext(urlparse(url).path)[1].lower()
    if not ext: return []

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, follow_redirects=True, timeout=60.0)
            response.raise_for_status()
        
        tenant_upload_path = os.path.join(UPLOAD_FOLDER_BASE, tenant)
        os.makedirs(tenant_upload_path, exist_ok=True)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext, dir=tenant_upload_path) as tmp_file:
            tmp_file.write(response.content)
            tmp_filepath = tmp_file.name

        loader = get_loader(tmp_filepath)
        if not loader:
            print(f"⚠️ No loader found for extension {ext}, skipping file {url}")
            os.remove(tmp_filepath)
            return []
            
        docs_from_loader = loader.load()
        os.remove(tmp_filepath)

        if not docs_from_loader: return []

        # Assuming one document per file for simplicity
        content = docs_from_loader[0].page_content
        return await async_create_document_chunks_with_metadata(content, url)

    except Exception as e:
        print(f"❌ Error processing file URL {url}: {e}")
        if 'tmp_filepath' in locals() and os.path.exists(tmp_filepath):
            os.remove(tmp_filepath)
        return []

async def async_crawl_urls_for_content(urls_to_process: list[str]) -> list[Document]:
    """Crawls URLs and processes their content concurrently, with a semaphore to limit concurrent AI calls."""
    browser_config = BrowserConfig(headless=True, verbose=False)
    run_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, stream=False)
    all_docs = []
    
    # Limit batch to 10 at a time
    semaphore = asyncio.Semaphore(10)

    async def process_single_result(result):
        """A worker function that processes one crawl result under the semaphore's control."""
        async with semaphore:
            if result.success and result.markdown:
                return await async_create_document_chunks_with_metadata(result.markdown, result.url)
        return []

    async with AsyncWebCrawler(config=browser_config) as crawler:
        results = await crawler.arun_many(urls=urls_to_process, config=run_config)
        tasks = [process_single_result(result) for result in results]
        processed_chunks_list = await asyncio.gather(*tasks)
        
        for doc_list in processed_chunks_list:
            all_docs.extend(doc_list)
            
    return all_docs

async def crawl_recursive_for_links(start_urls, max_depth=3):
    """Uses crawl4ai to recursively discover all internal links from a starting URL."""
    browser_config = BrowserConfig(headless=True, verbose=False)
    run_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, stream=False)
    visited = set()
    def normalize_url(url): return urldefrag(url)[0]
    current_urls = set([normalize_url(u) for u in start_urls])

    async with AsyncWebCrawler(config=browser_config) as crawler:
        for depth in range(max_depth):
            print(f"Crawling depth {depth + 1} with {len(current_urls)} URLs...")
            urls_to_crawl = [url for url in current_urls if url not in visited]
            if not urls_to_crawl: break
            results = await crawler.arun_many(urls=urls_to_crawl, config=run_config)
            next_level_urls = set()
            for result in results:
                norm_url = normalize_url(result.url)
                visited.add(norm_url)
                if result.success:
                    for link in result.links.get("internal", []):
                        next_url = normalize_url(link["href"])
                        if next_url not in visited: next_level_urls.add(next_url)
            current_urls = next_level_urls
    return list(visited)

# --- API ENDPOINTS ---
@app.route('/api/upload', methods=['POST'])
def handle_upload():
    tenant = request.form.get('tenant')
    if not tenant: return jsonify({"error": "Tenant ID is required"}), 400
    if 'file' not in request.files: return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '': return jsonify({"error": "No selected file"}), 400

    try:
        tenant_upload_path = os.path.join(UPLOAD_FOLDER_BASE, tenant)
        os.makedirs(tenant_upload_path, exist_ok=True)
        filepath = os.path.join(tenant_upload_path, file.filename)
        
        file.save(filepath)
        loader = get_loader(filepath)
        if not loader: return jsonify({"error": f"Unsupported file type: {file.filename}"}), 400
        docs_from_loader = loader.load()
        if not docs_from_loader: return jsonify({"error": f"No content could be extracted from: {file.filename}"}), 400

        all_docs = asyncio.run(async_create_document_chunks_with_metadata(docs_from_loader[0].page_content, file.filename))
        
        process_documents(all_docs, tenant)
        return jsonify({"success": True, "message": f"File '{file.filename}' processed for tenant '{tenant}'."})
    except Exception as e:
        print(f"Error in /api/upload: {e}")
        return jsonify({"error": f"Failed to process file: {str(e)}"}), 500

@app.route('/api/process_single_url', methods=['POST'])
def process_single_url():
    data = request.get_json()
    tenant = data.get('tenant')
    url = data.get('url')
    if not tenant: return jsonify({"error": "Tenant ID is required"}), 400
    if not url: return jsonify({"error": "No URL provided"}), 400
    try:
        # --- UPDATED: Use the new batch processing logic even for a single URL ---
        docs_to_process = asyncio.run(process_urls_concurrently([url], tenant))

        if docs_to_process:
            process_documents(docs_to_process, tenant)
            final_url = docs_to_process[0].metadata.get("source", url)
            source_name = os.path.basename(urlparse(final_url).path) or final_url
            return jsonify({"success": True, "message": f"Processed {final_url}", "source_name": source_name})
        else:
            return jsonify({"success": False, "message": f"No content found to process at {url}"})
    except Exception as e:
        print(f"Error processing single URL {url}: {e}")
        return jsonify({"error": str(e)}), 500
    
async def process_urls_concurrently(urls: list[str], tenant: str) -> list[Document]:
    urls_to_crawl = []
    file_urls_to_process = []
    
    for url in urls:
        ext = os.path.splitext(urlparse(url).path)[1].lower()
        if ext in SUPPORTED_FILE_EXTENSIONS:
            file_urls_to_process.append(url)
        else:
            urls_to_crawl.append(url)
    
    tasks = []
    if urls_to_crawl:
        tasks.append(async_crawl_urls_for_content(urls_to_crawl))
    
    for file_url in file_urls_to_process:
        tasks.append(async_process_file_url(file_url, tenant))
        
    results = await asyncio.gather(*tasks)
    
    all_docs = []
    for result_list in results:
        all_docs.extend(result_list)
        
    return all_docs
        
@app.route('/api/process_url_batch', methods=['POST'])
def process_url_batch():
    data = request.get_json()
    tenant = data.get('tenant')
    urls = data.get('urls')
    if not tenant: return jsonify({"error": "Tenant ID is required"}), 400
    if not urls or not isinstance(urls, list): return jsonify({"error": "A list of URLs is required"}), 400

    try:
        # --- UPDATED: Call the new master processing function ---
        docs_to_process = asyncio.run(process_urls_concurrently(urls, tenant))

        if docs_to_process:
            process_documents(docs_to_process, tenant)
            processed_sources = list(set([doc.metadata['source'] for doc in docs_to_process]))
            return jsonify({
                "success": True, 
                "message": f"Successfully processed {len(processed_sources)} URLs.",
                "processed_sources": processed_sources
            })
        else:
            return jsonify({"success": False, "message": "No content could be processed from the provided URLs."})
    except Exception as e:
        print(f"Error in /api/process_url_batch: {e}")
        return jsonify({"error": str(e)}), 500
    
    
@app.route('/api/chat', methods=['POST'])
def handle_chat():
    data = request.get_json()
    tenant = data.get('tenant')
    query = data.get('query')
    chat_history_json = data.get('chat_history', []) 
    if not tenant: return jsonify({"error": "Tenant ID is required"}), 400
    if not query: return jsonify({"error": "No query provided"}), 400

    try:
        tenant_instructions = INSTRUCTIONS['tenants'].get(tenant)
        if not tenant_instructions:
            return jsonify({"error": f"Tenant '{tenant}' not found in instructions.json"}), 404

        db = get_vectorstore(tenant)
        tenant_db_path = os.path.join(VECTOR_STORE_PATH_BASE, tenant)
        if not os.path.exists(tenant_db_path) or db._collection.count() == 0:
            return jsonify({"error": f"No documents have been processed for tenant '{tenant}'."}), 400

        chat_history = [HumanMessage(content=msg['content']) if msg['type'] == 'human' else AIMessage(content=msg['content']) for msg in chat_history_json]
        
        answer_llm = ChatGoogleGenerativeAI(model=GEMINI_MODEL, temperature=0.2)
        query_rewrite_llm = ChatGoogleGenerativeAI(model=QUERY_GEMINI_MODEL, temperature=0)

        history_aware_prompt = ChatPromptTemplate.from_messages([
            ("system", "Given a chat history and a follow up question, rephrase the follow up question to be a standalone question."),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
        ])
        
        retriever = db.as_retriever(search_type="mmr", search_kwargs={'k': 7, 'fetch_k': 25})
        history_aware_retriever_chain = create_history_aware_retriever(query_rewrite_llm, retriever, history_aware_prompt)
        
        # fine-tuning
        fine_tune_rules = tenant_instructions.get('fine_tune', [])
        formatted_fine_tune_rules = ""
        if fine_tune_rules:
            rule_strings = []
            for rule in fine_tune_rules:
                trigger = rule.get('trigger')
                instruction = rule.get('instruction')
                if trigger and instruction:
                    rule_strings.append(f"- When the user's question is about '{trigger}', you must follow this instruction: '{instruction}'")
            formatted_fine_tune_rules = "\n".join(rule_strings)
        
        rag_prompt_template = PromptTemplate.from_template(tenant_instructions['rag_prompt_template'])
        final_rag_prompt = rag_prompt_template.partial(
            persona=tenant_instructions.get('system_persona', ''),
            fine_tune_instructions=formatted_fine_tune_rules
        )
        
        document_chain = create_stuff_documents_chain(answer_llm, final_rag_prompt)
        conversational_rag_chain = create_retrieval_chain(history_aware_retriever_chain, document_chain)
        
        response = conversational_rag_chain.invoke({"chat_history": chat_history, "input": query})
        
        updated_history = chat_history + [HumanMessage(content=query), AIMessage(content=response["answer"])]
        
        updated_history_json = [{"type": "human" if isinstance(msg, HumanMessage) else "ai", "content": msg.content} for msg in updated_history]

        return jsonify({"answer": response["answer"], "chat_history": updated_history_json})
    except Exception as e:
        print(f"Error in /api/chat: {e}")
        return jsonify({"error": str(e)}), 500
    
@app.route('/api/discover_links', methods=['POST'])
def discover_links():
    data = request.get_json()
    url = data.get('url')
    if not url: return jsonify({"error": "No URL provided"}), 400
    try:
        max_depth = int(data.get('max_depth', 4))
        discovered_urls = asyncio.run(crawl_recursive_for_links([url], max_depth=max_depth))
        return jsonify({"success": True, "urls": discovered_urls})
    except Exception as e:
        print(f"Error in /api/discover_links: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/clear', methods=['POST'])
def clear_context():
    data = request.get_json()
    tenant = data.get('tenant')
    if not tenant: return jsonify({"error": "Tenant ID is required"}), 400
    
    try:
        if tenant in tenant_vectorstores:
            del tenant_vectorstores[tenant]
            print(f"Cleared in-memory vector store for tenant: {tenant}")

        tenant_db_path = os.path.join(VECTOR_STORE_PATH_BASE, tenant)
        if os.path.exists(tenant_db_path):
            shutil.rmtree(tenant_db_path)
            print(f"Removed ChromaDB directory for tenant: {tenant}")

        tenant_upload_path = os.path.join(UPLOAD_FOLDER_BASE, tenant)
        if os.path.exists(tenant_upload_path):
            shutil.rmtree(tenant_upload_path)
            print(f"Cleared upload folder for tenant: {tenant}")

        return jsonify({"success": True, "message": f"Context cleared successfully for tenant '{tenant}'."})
    except Exception as e:
        print(f"Error in /api/clear: {e}")
        return jsonify({"error": str(e)}), 500
    
@app.route('/api/intro', methods=['POST'])
def get_intro_message():
    data = request.get_json()
    tenant = data.get('tenant')
    if not tenant:
        return jsonify({"error": "Tenant ID is required"}), 400

    try:
        tenant_instructions = INSTRUCTIONS['tenants'].get(tenant)
        if not tenant_instructions:
            return jsonify({"error": f"Tenant '{tenant}' not found in instructions.json"}), 404

        intro_message = tenant_instructions.get('intro_message', 'Hello! How can I help you?')
        return jsonify({"intro_message": intro_message})

    except Exception as e:
        print(f"Error in /api/intro: {e}")
        return jsonify({"error": "An internal error occurred"}), 500

if __name__ == '__main__':
    # Use an environment variable to set the debug mode
    debug_mode = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    app.run(debug=debug_mode)