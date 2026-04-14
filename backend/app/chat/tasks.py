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

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.callbacks import BaseCallbackHandler
from app.prompts import REPHRASE_PROMPTS, FINE_TUNE_RULE_PROMPTS

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")

# --- Shared LLM Clients (reused across Celery tasks) ---
_embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
_answer_llm = ChatGoogleGenerativeAI(model=GEMINI_MODEL, temperature=0.2, convert_system_message_to_human=True)
_query_rewrite_llm = ChatGoogleGenerativeAI(model=GEMINI_MODEL, temperature=0, convert_system_message_to_human=True)


class TokenUsageCallback(BaseCallbackHandler):
    """Callback handler that captures token usage from LLM responses."""
    def __init__(self):
        self.input_tokens = 0
        self.output_tokens = 0

    def on_llm_end(self, response, **kwargs):
        """Accumulate token usage from each LLM generation."""
        for generations in response.generations:
            for gen in generations:
                usage = getattr(gen, 'generation_info', {}) or {}
                usage_metadata = usage.get('usage_metadata', {})
                self.input_tokens += usage_metadata.get('prompt_token_count', 0)
                self.output_tokens += usage_metadata.get('candidates_token_count', 0)

@shared_task(bind=True)
def chat_task(self, tenant_id, query, chat_history_json, conversation_id, user_id=None):
    """
    Celery task to handle the chat logic synchronously.
    """
    try:
        
        # --- Per-task token callback (not shared) ---
        token_cb = TokenUsageCallback()
        embeddings = _embeddings
        answer_llm = _answer_llm.with_config(callbacks=[token_cb])
        query_rewrite_llm = _query_rewrite_llm.with_config(callbacks=[token_cb])

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
        error_logger.debug("Using translation_target: %s for tenant %s", translation_target, tenant_id)

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

        # Strip leading AIMessages (e.g. the intro greeting) — Gemini requires
        # the first message after a SystemMessage to be a HumanMessage.
        while chat_history and isinstance(chat_history[0], AIMessage):
            chat_history.pop(0)

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

        # --- Build the answer prompt WITH chat history ---
        # The tenant's rag_prompt_template becomes the system instruction,
        # then we inject the full chat history so the LLM has conversational context.
        rag_system_template = tenant_config['rag_prompt_template']
        # Partially fill in the persona and fine-tune instructions
        rag_system_text = rag_system_template.replace(
            '{persona}', tenant_config.get('system_persona', '')
        ).replace(
            '{fine_tune_instructions}', fine_tune_instructions
        )

        final_rag_prompt = ChatPromptTemplate.from_messages([
            ("system", rag_system_text),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "Context:\n{context}\n\nQuestion: {input}"),
        ])

        document_chain = create_stuff_documents_chain(answer_llm, final_rag_prompt)
        conversational_rag_chain = create_retrieval_chain(history_aware_retriever_chain, document_chain)

        # --- Invoke Chain ---
        response = conversational_rag_chain.invoke({"chat_history": chat_history, "input": query})
        ai_message = response["answer"]

        # --- Calculate Usage and Deduct Cost ---
        # Use actual token counts from the callback handler
        input_tokens = token_cb.input_tokens
        output_tokens = token_cb.output_tokens

        # Fallback to estimation if callback didn't capture (shouldn't happen)
        if input_tokens == 0 and output_tokens == 0:
            input_text = query + str(chat_history_json) + str(fine_tune_instructions)
            input_tokens = len(input_text) // 4
            output_tokens = len(ai_message) // 4
            error_logger.warning(f"Token callback empty for tenant {tenant_id}, using estimation")
        
        cost = 0.0
        if user_id:
             cost = BillingService.deduct_cost(user_id, GEMINI_MODEL, input_tokens, output_tokens)

        # --- Log Chat to Database ---
        try:
            supabase.table('chat_logs').insert({
                'tenant_id': tenant_id,
                'conversation_id': conversation_id,
                'user_message': query,
                'ai_message': ai_message,
                'model_used': GEMINI_MODEL,
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
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
