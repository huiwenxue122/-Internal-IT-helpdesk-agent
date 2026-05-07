from __future__ import annotations

import os
import warnings
from typing import Any

from gaggia_agent.llm.json_utils import extract_json_object

_DEFAULT_MODEL = "claude-sonnet-4-20250514"


class LLMClient:
    """
    Lightweight wrapper around the Anthropic Messages API.

    Falls back gracefully when the API key is absent, the anthropic package is
    not installed, or any call fails at runtime.  Callers always provide a
    `fallback` value that is returned in those cases.
    """

    def __init__(self, model: str | None = None) -> None:
        self._model = model or os.environ.get("ANTHROPIC_MODEL", _DEFAULT_MODEL)
        self._client: Any = None
        self._try_init()

    def _try_init(self) -> None:
        api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
        if not api_key:
            return
        try:
            import anthropic  # type: ignore

            self._client = anthropic.Anthropic(api_key=api_key)
        except ImportError:
            warnings.warn(
                "anthropic package not installed; LLMClient will use fallbacks.",
                stacklevel=2,
            )
        except Exception as exc:
            warnings.warn(
                f"LLMClient init failed ({exc}); will use fallbacks.",
                stacklevel=2,
            )

    def available(self) -> bool:
        """Return True when the Anthropic client is configured and ready."""
        return self._client is not None

    def complete_json(
        self,
        system_prompt: str,
        user_prompt: str,
        fallback: dict,
        max_tokens: int = 1200,
        temperature: float = 0.0,
    ) -> dict:
        """
        Call the LLM and parse its response as a JSON object.

        Returns `fallback` if the client is unavailable, the call fails, or the
        response cannot be parsed as a dict.
        """
        if not self.available():
            return fallback

        try:
            text = self._call(system_prompt, user_prompt, max_tokens, temperature)
            result = extract_json_object(text)
            if result is None:
                warnings.warn("LLM returned non-JSON; using fallback.", stacklevel=2)
                return fallback
            return result
        except Exception as exc:
            warnings.warn(f"LLM complete_json failed ({exc}); using fallback.", stacklevel=2)
            return fallback

    def complete_text(
        self,
        system_prompt: str,
        user_prompt: str,
        fallback: str,
        max_tokens: int = 1200,
        temperature: float = 0.0,
    ) -> str:
        """
        Call the LLM and return its response as plain text.

        Returns `fallback` if the client is unavailable or the call fails.
        """
        if not self.available():
            return fallback

        try:
            return self._call(system_prompt, user_prompt, max_tokens, temperature)
        except Exception as exc:
            warnings.warn(f"LLM complete_text failed ({exc}); using fallback.", stacklevel=2)
            return fallback

    def _call(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int,
        temperature: float,
    ) -> str:
        response = self._client.messages.create(
            model=self._model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            temperature=temperature,
        )
        # Safely extract text from the first content block
        content = response.content
        if not content:
            return ""
        block = content[0]
        return getattr(block, "text", str(block))
