"""
tests/test_task_names.py

Verifies that the task name strings hardcoded in the API's _TaskProxy
instances exactly match the @shared_task registrations in each worker.

This is a pure static analysis test — it parses the worker source files
with ast.parse() and extracts all @shared_task decorated function names,
then checks them against the strings in the API's tasks/__init__.py.

WHY THIS EXISTS:
  The API dispatches Celery tasks by string name (via celery.send_task).
  If a task is renamed in a worker but the API stub is not updated,
  tasks silently go to a dead queue. This test catches that class of
  regression at CI time, before deployment.
"""

import ast
import re
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────

REPO_ROOT   = Path(__file__).parent.parent.parent  # SwiftAnswer/
SERVICES    = REPO_ROOT / "backend" / "services"
API_TASKS   = SERVICES / "api" / "app" / "data_processing" / "tasks" / "__init__.py"

WORKER_TASK_FILES = [
    SERVICES / "worker_fast"  / "app" / "data_processing" / "tasks" / "__init__.py",
    SERVICES / "worker_fast"  / "app" / "data_processing" / "tasks" / "maintenance_tasks.py",
    SERVICES / "worker_heavy" / "app" / "data_processing" / "tasks" / "crawl_tasks.py",
    SERVICES / "worker_chat"  / "app" / "chat" / "tasks.py",
]


# ── Helpers ─────────────────────────────────────────────────────────────────

def _extract_shared_task_names(path: Path) -> set[str]:
    """
    Parse a Python source file and return the fully-qualified Celery task
    names for every @shared_task decorated function.

    Celery uses `module.function_name` as the default task name when no
    explicit `name=` kwarg is given, where `module` is the dotted import
    path of the module containing the function.
    """
    source = path.read_text()
    tree   = ast.parse(source, filename=str(path))

    # Derive module dotted path from filesystem location relative to services/<svc>/
    # e.g.  services/worker_fast/app/data_processing/tasks/__init__.py
    #     → app.data_processing.tasks
    try:
        # Walk up to find the service root (directory that contains celery_worker.py)
        parts = path.parts
        svc_dir = None
        for i, p in enumerate(parts):
            if p in ("worker_fast", "worker_heavy", "worker_chat"):
                svc_dir = Path(*parts[: i + 1])
                break
        if svc_dir is None:
            raise ValueError(f"Cannot determine service root for {path}")

        rel = path.relative_to(svc_dir)
        # Convert path to dotted module name
        mod_parts = list(rel.with_suffix("").parts)
        if mod_parts[-1] == "__init__":
            mod_parts = mod_parts[:-1]
        module_name = ".".join(mod_parts)
    except Exception:
        module_name = path.stem

    names = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        for decorator in node.decorator_list:
            # Match bare `@shared_task` or `@shared_task(...)` with any kwargs
            is_shared_task = False
            explicit_name  = None

            if isinstance(decorator, ast.Name) and decorator.id == "shared_task":
                is_shared_task = True
            elif isinstance(decorator, ast.Call):
                func = decorator.func
                if (isinstance(func, ast.Name) and func.id == "shared_task") or \
                   (isinstance(func, ast.Attribute) and func.attr == "shared_task"):
                    is_shared_task = True
                    # Look for name= kwarg
                    for kw in decorator.keywords:
                        if kw.arg == "name" and isinstance(kw.value, ast.Constant):
                            explicit_name = kw.value.value

            if is_shared_task:
                task_name = explicit_name if explicit_name else f"{module_name}.{node.name}"
                names.add(task_name)

    return names


def _extract_proxy_names(path: Path) -> set[str]:
    """
    Parse the API tasks/__init__.py and return the task name strings
    passed to _TaskProxy(). Works by regex-matching the string arguments.
    """
    source = path.read_text()
    # Pattern: _TaskProxy('app.some.module.task_name', ...)
    return set(re.findall(r"_TaskProxy\(['\"]([^'\"]+)['\"]", source))


# ── Test ─────────────────────────────────────────────────────────────────────

def test_task_proxy_names_match_worker_registrations():
    """
    All task name strings in the API's _TaskProxy instances must match
    a @shared_task decorated function registered in a worker.
    """
    # Collect all task names registered in all workers
    registered: set[str] = set()
    for task_file in WORKER_TASK_FILES:
        if task_file.exists():
            registered |= _extract_shared_task_names(task_file)

    assert registered, (
        "No @shared_task names were found in any worker file. "
        "Check WORKER_TASK_FILES paths."
    )

    # Collect the names the API expects to dispatch
    proxy_names = _extract_proxy_names(API_TASKS)
    assert proxy_names, (
        f"No _TaskProxy names were found in {API_TASKS}. "
        "Check that the file exists and uses the _TaskProxy pattern."
    )

    # Every proxy name must exist in the registered set
    missing = proxy_names - registered
    assert not missing, (
        f"The following task names are referenced in the API's _TaskProxy "
        f"but are NOT registered by any @shared_task in the workers:\n"
        + "\n".join(f"  ✗  {n}" for n in sorted(missing))
        + "\n\nEither rename the task in the worker or update the API stub."
    )
