"""
The chat worker's image copies shared knowledge modules one by one. A module
it imports but doesn't copy builds fine and only fails on the server, where
every chat then dies on import (names.py, 2026-10-30).
"""
import re
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]


def test_chat_worker_image_has_every_knowledge_module_it_imports():
    code = "\n".join(p.read_text() for p in (BACKEND / "services/worker_chat/app").rglob("*.py"))
    # imports at the top of a file run when the worker starts; one inside a
    # function (contact.py's triage, used by the crawler only) doesn't
    imported = set(re.findall(r"^from app\.knowledge\.(\w+) import", code, re.MULTILINE))
    dockerfile = (BACKEND / "services/worker_chat/Dockerfile").read_text()
    copied = set(re.findall(r"COPY shared/knowledge/(\w+)\.py ", dockerfile))
    assert imported, "no knowledge imports found: check the paths"
    assert imported <= copied, f"imported but not copied into the image: {sorted(imported - copied)}"
