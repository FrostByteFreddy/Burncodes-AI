from celery import shared_task
from app.database.supabase_client import supabase
from app.data_processing.processor import get_vectorstore
from app.logging_config import error_logger
import os

# --- LangChain Core Imports ---
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain.chains import create_retrieval_chain
from langchain_core.messages import HumanMessage, AIMessage
from langchain.chains import create_history_aware_retriever
from app.prompts import REPHRASE_PROMPTS, FINE_TUNE_RULE_PROMPTS

GEMINI_MODEL = os.getenv("GEMINI_MODEL")
QUERY_GEMINI_MODEL = os.getenv("QUERY_GEMINI_MODEL", "gemini-1.5-flash")

@shared_task(bind=True)
def chat_task(self, tenant_id, query, chat_history_json, conversation_id):
    """
    Celery task to handle the chat logic synchronously.
    """
    try:
        # --- Create embeddings ---
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

        # --- Get Tenant Info ---
        tenant_response = supabase.table('tenants').select("*, tenant_fine_tune(*)").eq('id', str(tenant_id)).single().execute()
        if not tenant_response.data:
            raise Exception(f"Tenant '{tenant_id}' not found")
        tenant_config = tenant_response.data

        # Determine the language for translation, defaulting to 'en'
        translation_target = tenant_config.get('translation_target', 'en')
        print(f"📄 Using translation_target: {translation_target}")

        # --- Get Vector Store ---
        db = get_vectorstore(tenant_id, embeddings)
        if db._collection.count() == 0:
            raise Exception(f"No documents have been processed for tenant '{tenant_id}'.")

        # --- Build Chains ---
        chat_history = [HumanMessage(content=msg['content']) if msg['type'] == 'human' else AIMessage(content=msg['content']) for msg in chat_history_json]

        answer_llm = ChatGoogleGenerativeAI(model=GEMINI_MODEL, temperature=0.2)
        query_rewrite_llm = ChatGoogleGenerativeAI(model=QUERY_GEMINI_MODEL, temperature=0)

        # Select the rephrase prompt based on the translation target
        rephrase_prompt_tuple = REPHRASE_PROMPTS.get(translation_target, REPHRASE_PROMPTS['en'])
        history_aware_prompt = ChatPromptTemplate.from_messages([
            rephrase_prompt_tuple,
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
        ])

        retriever = db.as_retriever(search_type="mmr", search_kwargs={'k': 7, 'fetch_k': 25})
        history_aware_retriever_chain = create_history_aware_retriever(query_rewrite_llm, retriever, history_aware_prompt)

        fine_tune_rules = tenant_config.get('tenant_fine_tune', [])
        formatted_fine_tune_rules = ""
        if fine_tune_rules:
            # Select the fine-tune rule prompt based on the translation target
            rule_template = FINE_TUNE_RULE_PROMPTS.get(translation_target, FINE_TUNE_RULE_PROMPTS['en'])
            rule_strings = [rule_template.format(trigger=rule['trigger'], instruction=rule['instruction']) for rule in fine_tune_rules]
            formatted_fine_tune_rules = "\n".join(rule_strings)

        rag_prompt_template = PromptTemplate.from_template(tenant_config['rag_prompt_template'])
        final_rag_prompt = rag_prompt_template.partial(
            persona=tenant_config.get('system_persona', ''),
            fine_tune_instructions=formatted_fine_tune_rules
        )

        document_chain = create_stuff_documents_chain(answer_llm, final_rag_prompt)
        conversational_rag_chain = create_retrieval_chain(history_aware_retriever_chain, document_chain)

        # --- Invoke Chain ---
        response = conversational_rag_chain.invoke({"chat_history": chat_history, "input": query})
        ai_message = response["answer"]

        # --- Log Chat to Database ---
        try:
            supabase.table('chat_logs').insert({
                'tenant_id': tenant_id,
                'conversation_id': conversation_id,
                'user_message': query,
                'ai_message': ai_message
            }).execute()
        except Exception as db_error:
            error_logger.error(f"Database Error in chat_task for tenant {tenant_id}: {db_error}", exc_info=True)
            # Decide if you want to raise the exception or just log it and continue
            # For now, we'll just log it.

        # --- Format Response ---
        updated_history = chat_history + [HumanMessage(content=query), AIMessage(content=ai_message)]
        updated_history_json = [{"type": "human" if isinstance(msg, HumanMessage) else "ai", "content": msg.content} for msg in updated_history]

        return {"answer": ai_message, "chat_history": updated_history_json}

    except Exception as e:
        error_logger.error(f"Error in chat task for tenant {tenant_id}: {e}", exc_info=True)
        raise
