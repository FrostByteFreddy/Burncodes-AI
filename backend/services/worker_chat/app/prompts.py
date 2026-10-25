# Instructions to the model are English only; the reply language follows
# the visitor (see _language_rule in chat/tasks.py).
FINE_TUNE_RULE_PROMPT = (
    "If the user's question is in any way related to '{trigger}', "
    "follow this guideline in your answer: '{instruction}'"
)
