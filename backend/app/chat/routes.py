import asyncio
from flask import Blueprint, request, jsonify
from app.database.supabase_client import supabase
from app.data_processing.processor import get_vectorstore
import os

# --- LangChain Core Imports ---
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain.chains import create_retrieval_chain
from langchain_core.messages import HumanMessage, AIMessage
from langchain.chains import create_history_aware_retriever

chat_bp = Blueprint('chat', __name__)

GEMINI_MODEL = os.getenv("GEMINI_MODEL")
QUERY_GEMINI_MODEL = os.getenv("QUERY_GEMINI_MODEL", "gemini-1.5-flash")

@chat_bp.route('/<uuid:tenant_id>', methods=['POST'])
def handle_chat(tenant_id):
    data = request.get_json()
    query = data.get('query')
    chat_history_json = data.get('chat_history', [])

    if not query:
        return jsonify({"error": "No query provided"}), 400

    try:
        # Since Flask runs in a thread, we need to manage the asyncio event loop manually.
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(async_chat_logic(tenant_id, query, chat_history_json))
        loop.close()
        return jsonify(result)
    except Exception as e:
        # Ensure the loop is closed on error as well
        if 'loop' in locals() and not loop.is_closed():
            loop.close()
        print(f"Error in /api/chat/{tenant_id}: {e}")
        return jsonify({"error": str(e)}), 500

async def async_chat_logic(tenant_id, query, chat_history_json):
    # Fetch tenant configuration from the database
    tenant_response = supabase.table('tenants').select("*, tenant_fine_tune(*)").eq('id', str(tenant_id)).single().execute()

    if not tenant_response.data:
        # This won't be caught by the top-level try-except in handle_chat, so handle appropriately
        # For simplicity, we'll let it raise, but in a real app, you might return a specific dict
        raise Exception(f"Tenant '{tenant_id}' not found")

    tenant_config = tenant_response.data

    # Check if the tenant has any processed documents
    db = get_vectorstore(tenant_id)
    if db._collection.count() == 0:
        raise Exception(f"No documents have been processed for tenant '{tenant_id}'.")

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

    # Format fine-tuning rules from the database
    fine_tune_rules = tenant_config.get('tenant_fine_tune', [])
    formatted_fine_tune_rules = ""
    if fine_tune_rules:
        rule_strings = [f"- When the user's question is about '{rule['trigger']}', you must follow this instruction: '{rule['instruction']}'" for rule in fine_tune_rules]
        formatted_fine_tune_rules = "\n".join(rule_strings)

    rag_prompt_template = PromptTemplate.from_template(tenant_config['rag_prompt_template'])
    final_rag_prompt = rag_prompt_template.partial(
        persona=tenant_config.get('system_persona', ''),
        fine_tune_instructions=formatted_fine_tune_rules
    )

    document_chain = create_stuff_documents_chain(answer_llm, final_rag_prompt)
    conversational_rag_chain = create_retrieval_chain(history_aware_retriever_chain, document_chain)

    # Use ainvoke for the async version of the chain
    response = await conversational_rag_chain.ainvoke({"chat_history": chat_history, "input": query})

    updated_history = chat_history + [HumanMessage(content=query), AIMessage(content=response["answer"])]
    updated_history_json = [{"type": "human" if isinstance(msg, HumanMessage) else "ai", "content": msg.content} for msg in updated_history]

    return {"answer": response["answer"], "chat_history": updated_history_json}

@chat_bp.route('/<uuid:tenant_id>/intro', methods=['GET'])
def get_intro_message(tenant_id):
    try:
        tenant = supabase.table('tenants').select("intro_message").eq('id', str(tenant_id)).single().execute()
        if not tenant.data:
            return jsonify({"error": f"Tenant '{tenant_id}' not found"}), 404
        return jsonify({"intro_message": tenant.data['intro_message']})
    except Exception as e:
        print(f"Error in /api/chat/{tenant_id}/intro: {e}")
        return jsonify({"error": "An internal error occurred"}), 500
