from celery import shared_task
from app.database.supabase_client import supabase
from app.data_processing.processor import get_vectorstore
from app.logging_config import error_logger
from app.billing.services import BillingService
import os

# --- LangChain Core Imports ---
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.retrieval import create_retrieval_chain
from langchain.chains.history_aware_retriever import create_history_aware_retriever

from langchain_core.prompts import ChatPromptTemplate, PromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from app.prompts import REPHRASE_PROMPTS, FINE_TUNE_RULE_PROMPTS

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")

@shared_task(bind=True)
def chat_task(self, tenant_id, query, chat_history_json, conversation_id, user_id=None):
    """
    Celery task to handle the chat logic synchronously.
    """
    try:
        
        # --- Init client ---
        embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
        answer_llm = ChatGoogleGenerativeAI(model=GEMINI_MODEL, temperature=0.2, convert_system_message_to_human=True)
        query_rewrite_llm = ChatGoogleGenerativeAI(model=GEMINI_MODEL, temperature=0, convert_system_message_to_human=True)

        # --- Get Tenant Info ---
        tenant_response = supabase.table('tenants').select("*").eq('id', str(tenant_id)).single().execute()
        if not tenant_response.data:
            raise Exception(f"Tenant '{tenant_id}' not found")
        tenant_config = tenant_response.data

        # --- Get Fine-Tuning Rules ---
        fine_tune_response = supabase.table('tenant_fine_tune').select("*").eq('tenant_id', str(tenant_id)).execute()
        fine_tune_rules = fine_tune_response.data or []

        # Determine the language for translation, defaulting to 'en'
        translation_target = tenant_config.get('translation_target', 'en')
        print(f"📄 Using translation_target: {translation_target}")

        # --- Construct Fine-Tuning Instructions String ---
        fine_tune_prompt_template = FINE_TUNE_RULE_PROMPTS.get(translation_target, FINE_TUNE_RULE_PROMPTS['en'])
        fine_tune_instructions = "\n".join([
            fine_tune_prompt_template.format(trigger=rule['trigger'], instruction=rule['instruction'])
            for rule in fine_tune_rules
        ])

        # --- Get Vector Store ---
        db = get_vectorstore(tenant_id, embeddings)
        if db._collection.count() == 0:
            raise Exception(f"No documents have been processed for tenant '{tenant_id}'.")

        # --- Build Chains ---
        chat_history = [HumanMessage(content=msg['content']) if msg['type'] == 'human' else AIMessage(content=msg['content']) for msg in chat_history_json]

        # Select the rephrase prompt based on the translation target
        rephrase_prompt_tuple = REPHRASE_PROMPTS.get(translation_target, REPHRASE_PROMPTS['en'])
        history_aware_prompt = ChatPromptTemplate.from_messages([
            rephrase_prompt_tuple,
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
        ])

        # --- Use a single, efficient MMR retriever ---
        retriever = db.as_retriever(
            search_type="mmr",
            search_kwargs={'k': 5, 'fetch_k': 15} 
        )
        
        history_aware_retriever_chain = create_history_aware_retriever(
            query_rewrite_llm, 
            retriever, # Use the single MMR retriever
            history_aware_prompt
        )

        rag_prompt_template = PromptTemplate.from_template(tenant_config['rag_prompt_template'])
        final_rag_prompt = rag_prompt_template.partial(
            persona=tenant_config.get('system_persona', ''),
            fine_tune_instructions=fine_tune_instructions,
        )

        document_chain = create_stuff_documents_chain(answer_llm, final_rag_prompt)
        conversational_rag_chain = create_retrieval_chain(history_aware_retriever_chain, document_chain)

        # --- Invoke Chain ---
        response = conversational_rag_chain.invoke({"chat_history": chat_history, "input": query})
        ai_message = response["answer"]

        # --- Calculate Usage and Deduct Cost ---
        # Note: LangChain Google provider might not expose token usage directly in the response object easily
        # depending on the version. If response doesn't have it, we might need to estimate or use a callback.
        # For now, let's try to get it if available, or estimate.
        # Actually, ChatGoogleGenerativeAI usually returns usage_metadata in the AIMessage if available.
        # But here response["answer"] is a string because create_stuff_documents_chain returns string output by default?
        # Wait, create_retrieval_chain returns a dict. 'answer' key is the string result.
        # To get usage we might need to access the raw generation info or use a callback handler.
        # For simplicity in this MVP, let's estimate tokens using a simple heuristic or a tokenizer if available.
        # A simple estimation: 1 token ~= 4 chars.
        
        input_text = query + str(chat_history_json) + str(fine_tune_instructions) # Rough approximation of input
        # Better: use the actual prompt sent. But that's hard to get from the chain result directly without callbacks.
        
        # Let's use a simple character count estimation for now as a fallback
        input_tokens_est = len(input_text) // 4
        output_tokens_est = len(ai_message) // 4
        
        cost = 0.0
        if user_id:
             cost = BillingService.deduct_cost(user_id, GEMINI_MODEL, input_tokens_est, output_tokens_est)

        # --- Log Chat to Database ---
        try:
            supabase.table('chat_logs').insert({
                'tenant_id': tenant_id,
                'conversation_id': conversation_id,
                'user_message': query,
                'ai_message': ai_message,
                'model_used': GEMINI_MODEL,
                'input_tokens': input_tokens_est,
                'output_tokens': output_tokens_est,
                'cost_chf': cost
            }).execute()
        except Exception as db_error:
            error_logger.error(f"Database Error in chat_task for tenant {tenant_id}: {db_error}", exc_info=True)

        # --- Format Response ---
        updated_history = chat_history + [HumanMessage(content=query), AIMessage(content=ai_message)]
        updated_history_json = [{"type": "human" if isinstance(msg, HumanMessage) else "ai", "content": msg.content} for msg in updated_history]

        return {"answer": ai_message, "chat_history": updated_history_json}

    except Exception as e:
        error_logger.error(f"Error in chat task for tenant {tenant_id}: {e}", exc_info=True)
        raise
