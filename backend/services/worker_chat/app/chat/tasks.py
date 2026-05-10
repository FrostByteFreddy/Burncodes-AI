"""
worker_chat/app/chat/tasks.py

Chat task using the Gemini API (google-genai SDK) with the File Search tool.
Replaces the LangChain/ChromaDB retrieval chain entirely.

Key changes:
- Single generate_content() call handles retrieval + generation atomically
- Conversation history passed natively (no LangChain message wrappers)
- Token usage read from response.usage_metadata (no callback needed)
- Fine-tune rules injected directly into the system instruction
- Citations extracted from grounding_metadata and returned to the frontend
"""
import os
from celery import shared_task
from google import genai

from app.database.supabase_client import supabase
from app.billing.services import BillingService
from app.logging_config import error_logger
from app.prompts import FINE_TUNE_RULE_PROMPTS

CHAT_GEMINI_MODEL = os.getenv("CHAT_GEMINI_MODEL", "gemini-3.1-flash-lite-preview")

_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
    return _client


def _build_contents(chat_history_json: list, query: str) -> list:
    """
    Converts the chat history + current query into the google-genai contents format:
    [{"role": "user"|"model", "parts": [{"text": "..."}]}, ...]
    """
    contents = []
    for msg in chat_history_json:
        role = "user" if msg["type"] == "human" else "model"
        contents.append({"role": role, "parts": [{"text": msg["content"]}]})
    # Gemini requires the last message to be from "user"
    contents.append({"role": "user", "parts": [{"text": query}]})
    return contents


def _build_system_instruction(tenant_config: dict, fine_tune_rules: list) -> str:
    """
    Assembles the full system instruction from the tenant's RAG prompt template,
    persona, and fine-tune rules.
    """
    translation_target = tenant_config.get("translation_target", "en")
    fine_tune_prompt_template = FINE_TUNE_RULE_PROMPTS.get(
        translation_target, FINE_TUNE_RULE_PROMPTS["en"]
    )
    fine_tune_instructions = "\n".join([
        fine_tune_prompt_template.format(
            trigger=rule["trigger"], instruction=rule["instruction"]
        )
        for rule in fine_tune_rules
    ])

    system_text = (
        tenant_config.get("rag_prompt_template", "")
        .replace("{persona}", tenant_config.get("system_persona", ""))
        .replace("{fine_tune_instructions}", fine_tune_instructions)
    )
    return system_text


def _extract_citations(response) -> list[dict]:
    """
    Pulls grounding metadata from the Gemini response.
    Returns a list of citation dicts with title, page_number, and snippet.
    """
    citations = []
    try:
        grounding = response.candidates[0].grounding_metadata
        if not grounding:
            return citations
        for chunk in grounding.grounding_chunks:
            ctx = getattr(chunk, "retrieved_context", None)
            if not ctx:
                continue
            citations.append({
                "title": getattr(ctx, "title", None),
                "page_number": getattr(ctx, "page_number", None),
                "snippet": (getattr(ctx, "text", None) or "")[:200] or None,
            })
    except (AttributeError, IndexError):
        pass
    return citations


@shared_task(bind=True, queue="chat")
def chat_task(self, tenant_id, query, chat_history_json, conversation_id, user_id=None):
    """
    Celery task to handle a chat turn using Gemini with the File Search tool.

    Returns:
        {
            "answer": str,
            "chat_history": [...],   # updated history including this turn
            "citations": [...],      # grounding sources used by the model
        }
    """
    try:
        client = _get_client()

        # --- Fetch tenant config ---
        tenant_response = (
            supabase.table("tenants")
            .select("*")
            .eq("id", str(tenant_id))
            .single()
            .execute()
        )
        if not tenant_response.data:
            raise Exception(f"Tenant '{tenant_id}' not found")
        tenant_config = tenant_response.data

        # --- Fetch fine-tune rules ---
        fine_tune_response = (
            supabase.table("tenant_fine_tune")
            .select("*")
            .eq("tenant_id", str(tenant_id))
            .execute()
        )
        fine_tune_rules = fine_tune_response.data or []

        # --- Build system instruction ---
        system_instruction = _build_system_instruction(tenant_config, fine_tune_rules)

        # --- Build tool config ---
        # Only attach file_search if the tenant has an indexed store
        tools = []
        store_name = tenant_config.get("gemini_file_store_name")
        if store_name:
            tools = [{"file_search": {"file_search_store_names": [store_name]}}]
        else:
            error_logger.info(
                "chat_task: no File Search store for tenant %s — answering from base knowledge",
                tenant_id,
            )

        # --- Build contents (conversation history + current query) ---
        # Strip leading model messages — Gemini requires first message to be "user"
        history = list(chat_history_json)
        while history and history[0].get("type") != "human":
            history.pop(0)

        contents = _build_contents(history, query)

        # --- Generate ---
        response = client.models.generate_content(
            model=CHAT_GEMINI_MODEL,
            contents=contents,
            config={
                "system_instruction": system_instruction,
                "tools": tools,
            },
        )

        ai_message = response.text

        # --- Token usage ---
        usage = getattr(response, "usage_metadata", None)
        if usage:
            input_tokens = getattr(usage, "prompt_token_count", 0) or 0
            output_tokens = getattr(usage, "candidates_token_count", 0) or 0
        else:
            # Fallback estimation
            input_tokens = len(query + str(chat_history_json)) // 4
            output_tokens = len(ai_message) // 4
            error_logger.warning("chat_task: usage_metadata unavailable for tenant %s — estimating", tenant_id)

        # --- Citations ---
        citations = _extract_citations(response)

        # --- Billing ---
        cost = 0.0
        if user_id:
            cost = BillingService.deduct_cost(user_id, CHAT_GEMINI_MODEL, input_tokens, output_tokens)

        # --- Log to DB ---
        try:
            supabase.table("chat_logs").insert({
                "tenant_id": tenant_id,
                "conversation_id": conversation_id,
                "user_message": query,
                "ai_message": ai_message,
                "model_used": CHAT_GEMINI_MODEL,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost_chf": cost,
            }).execute()
        except Exception as db_error:
            error_logger.error(
                "chat_task: DB log failed for tenant %s: %s", tenant_id, db_error, exc_info=True
            )

        # --- Build updated history ---
        updated_history = list(chat_history_json) + [
            {"type": "human", "content": query},
            {"type": "ai", "content": ai_message},
        ]

        return {
            "answer": ai_message,
            "chat_history": updated_history,
            "citations": citations,
        }

    except Exception as e:
        error_logger.error("chat_task: error for tenant %s: %s", tenant_id, e, exc_info=True)
        raise
