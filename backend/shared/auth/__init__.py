# backend/shared/auth/__init__.py
# Explicit package marker.
#
# Without this file, Python treats `auth/` as an implicit namespace package.
# Implicit namespace packages work in CPython 3.3+ but can cause subtle issues:
#   - Some import tools (PyCharm, mypy, pylint) don't handle them consistently
#   - `pkgutil.extend_path` and `pkg_resources` behave differently
#   - Some older WSGI/Celery configurations may fail to find the module
#
# Explicit is better than implicit (PEP 20).
