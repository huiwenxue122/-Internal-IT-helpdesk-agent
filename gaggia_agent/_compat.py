"""
gaggia_agent/_compat.py

Third-party library compatibility shims.

Import this module exactly once, before any langgraph / langchain import, to
avoid AttributeError crashes caused by version mismatches.

---------------------------------------------------------------------------
langchain.debug / langchain.verbose (langchain ≥ 1.0 + langchain-core 0.3.x)
---------------------------------------------------------------------------
langchain-core 0.3.x references `langchain.debug` and `langchain.verbose` in
`langchain_core.globals.get_debug()` and `get_verbose()`.  Starting with
langchain 1.0 these module-level attributes were removed as part of the
globals refactor.  When both packages are installed the mismatch raises:

    AttributeError: module 'langchain' has no attribute 'debug'

The recommended long-term fix is to upgrade langchain-core to ≥ 0.3.85 where
the back-reference was removed, or to use langchain < 1.0.  Until the
dependency tree settles, we patch the missing attributes to False (their
original default values) so the existing call-sites in langchain-core work
as before.

See: https://github.com/langchain-ai/langchain/issues/XXXX
"""

from __future__ import annotations


def apply_langchain_globals_patch() -> None:
    """
    Patch missing `debug` / `verbose` attributes on the `langchain` module.

    Safe to call multiple times (idempotent).
    """
    try:
        import langchain as _lc  # noqa: F401

        if not hasattr(_lc, "debug"):
            _lc.debug = False  # type: ignore[attr-defined]
        if not hasattr(_lc, "verbose"):
            _lc.verbose = False  # type: ignore[attr-defined]
    except ImportError:
        pass  # langchain not installed — no patch needed


# Apply automatically on import so callers only need `import gaggia_agent._compat`.
apply_langchain_globals_patch()
