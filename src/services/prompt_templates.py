"""Centralized prompt templates for PolicyPilot RAG Assistant.

This module defines reusable prompt templates with named placeholders
({context}, {question}, {schema}, etc.) to ensure consistency across
all features (interactive chat, batch CLI, comparisons, etc.).

Templates are separated from business logic, allowing prompt changes
without touching application code.
"""

from typing import Dict, Any
from string import Formatter


class PromptTemplate:
    """A prompt template with named placeholders and rendering capability."""

    def __init__(self, name: str, template: str, description: str = ""):
        """Initialize a prompt template.

        Args:
            name: Unique identifier for the template
            template: Template string with {placeholder} markers
            description: Human-readable description of the template's purpose
        """
        self.name = name
        self.template = template
        self.description = description
        self._validate_placeholders()

    def _validate_placeholders(self) -> None:
        """Extract and validate all placeholders in template."""
        self.placeholders = [
            field_name
            for _, field_name, _, _
            in Formatter().parse(self.template)
            if field_name is not None
        ]

    def render(self, **kwargs) -> str:
        """Render the template with provided values.

        Args:
            **kwargs: Placeholder values (e.g., context="...", question="...")

        Returns:
            Rendered prompt string with all placeholders filled

        Raises:
            KeyError: If a required placeholder is missing
        """
        missing = set(self.placeholders) - set(kwargs.keys())
        if missing:
            raise KeyError(
                f"Template '{self.name}' missing required placeholders: {missing}"
            )
        return self.template.format(**kwargs)

    def __repr__(self) -> str:
        return f"PromptTemplate(name='{self.name}', placeholders={self.placeholders})"


# ============================================================================
# TEMPLATE DEFINITIONS
# ============================================================================

FALLBACK_RESPONSE = (
    "I am unable to answer this question as it is not specified "
    "in the official policy guidelines."
)

# ---------------------------------------------------------------------------
# SYSTEM PROMPTS
# ---------------------------------------------------------------------------

SYSTEM_PROMPT_VAGUE = PromptTemplate(
    name="system_vague",
    description="Vague system prompt for baseline comparison testing",
    template="You are a helpful assistant.",
)

SYSTEM_PROMPT_CONSTRAINED = PromptTemplate(
    name="system_constrained",
    description="Strict PolicyPilot system prompt grounded in retrieved context",
    template="""You are PolicyPilot, an internal company policy assistant.

Your ONLY job is to answer questions using the official policy information
provided in the retrieved context.

STRICT RULES:

1. Use ONLY the information contained in the retrieved policy context.
2. If the retrieved policy context contains enough information to answer the
   question, answer the question directly and concisely.
3. If the retrieved policy context does NOT contain enough information to
   answer the question, reply EXACTLY with:
   "{fallback_response}"
4. If the question is unrelated to company policy, reply EXACTLY with the
   same fallback response.
5. NEVER use general knowledge, outside information, assumptions, common
   corporate practices, or guesses.
6. NEVER invent or infer missing policy details.
7. NEVER provide an answer just because something is generally true in
   other companies.
8. Do not recommend HR, Google, websites, handbooks, or other sources when
   the required information is missing.
9. Do not mention the retrieved context in the final answer.
10. Do not reveal your reasoning or internal thought process.
11. NEVER output <think>, </think>, analysis, reasoning, self-correction,
    or planning text.
12. Keep valid answers concise, factual, and professional.
13. Return ONLY the final answer. Do not add headings, labels, explanations,
    or extra commentary.

The retrieved policy context will be provided with each user question.""",
)

SYSTEM_PROMPT_JSON_CONSTRAINED = PromptTemplate(
    name="system_json_constrained",
    description="Strict PolicyPilot prompt that requires JSON-formatted output",
    template="""You are PolicyPilot, an internal company policy assistant.

Your ONLY job is to answer questions using the official policy information
provided in the retrieved context.

STRICT RULES:

1. Use ONLY the retrieved policy context.
2. If the context contains enough information to answer the question,
   provide the answer using ONLY that information.
3. If the context does not contain enough information, use exactly:
   "{fallback_response}"
4. If the question is unrelated to company policy, use exactly the same
   fallback response.
5. NEVER use general knowledge or outside information.
6. NEVER guess or infer missing policy information.
7. NEVER invent company policies.
8. Do not reveal reasoning or internal thought processes.
9. NEVER output <think> or </think>.
10. Return ONLY valid JSON.
11. Do not use markdown code fences.

Required JSON schema:

{{
    "answer": "<string>",
    "confidence": "<high|medium|low|unknown>",
    "refusal": <true|false>
}}

For a supported question:
- "answer" = concise answer based only on the retrieved context.
- "confidence" = "high" when the context directly supports the answer.
- "refusal" = false.

For an unsupported or unrelated question:
- "answer" = "{fallback_response}"
- "confidence" = "unknown"
- "refusal" = true.""",
)

# ---------------------------------------------------------------------------
# USER MESSAGE TEMPLATES
# ---------------------------------------------------------------------------

USER_MESSAGE_WITH_CONTEXT = PromptTemplate(
    name="user_with_context",
    description="User message template with policy context and question",
    template="""Retrieved policy context:
{context}

User question:
{question}""",
)

USER_MESSAGE_SIMPLE = PromptTemplate(
    name="user_simple",
    description="Simple user message with only the question",
    template="{question}",
)

# ---------------------------------------------------------------------------
# MESSAGE BUILDER TEMPLATES (for full chat-like format)
# ---------------------------------------------------------------------------

MESSAGES_CONSTRAINED = PromptTemplate(
    name="messages_constrained",
    description="Complete message pair: constrained system + context-aware user message",
    template="""[SYSTEM]
{system_prompt}

[USER]
Retrieved policy context:
{context}

User question:
{question}""",
)

MESSAGES_JSON = PromptTemplate(
    name="messages_json",
    description="Complete message pair: JSON system + context-aware user message",
    template="""[SYSTEM]
{system_prompt}

[USER]
Retrieved policy context:
{context}

User question:
{question}""",
)

# ============================================================================
# PROMPT TEMPLATE REGISTRY
# ============================================================================

TEMPLATE_REGISTRY: Dict[str, PromptTemplate] = {
    # System prompts
    "system_vague": SYSTEM_PROMPT_VAGUE,
    "system_constrained": SYSTEM_PROMPT_CONSTRAINED,
    "system_json_constrained": SYSTEM_PROMPT_JSON_CONSTRAINED,
    # User message templates
    "user_with_context": USER_MESSAGE_WITH_CONTEXT,
    "user_simple": USER_MESSAGE_SIMPLE,
    # Full message templates
    "messages_constrained": MESSAGES_CONSTRAINED,
    "messages_json": MESSAGES_JSON,
}


# ============================================================================
# TEMPLATE RENDERER CLASS (Task 2)
# ============================================================================

class TemplateRenderer:
    """High-level API for rendering prompts from templates.

    Provides a clean interface to render templates with validation
    and error handling. Used by all features (chat, CLI, comparison, etc.)
    to ensure consistent prompt construction.
    """

    @staticmethod
    def get_template(name: str) -> PromptTemplate:
        """Retrieve a template by name from registry.

        Args:
            name: Template name (e.g., 'system_constrained')

        Returns:
            PromptTemplate instance

        Raises:
            KeyError: If template not found
        """
        if name not in TEMPLATE_REGISTRY:
            available = ", ".join(TEMPLATE_REGISTRY.keys())
            raise KeyError(
                f"Template '{name}' not found. Available: {available}"
            )
        return TEMPLATE_REGISTRY[name]

    @staticmethod
    def render(template_name: str, **kwargs) -> str:
        """Render a template by name with provided values.

        This is the primary API for rendering prompts across the application.
        Validates that all required placeholders are provided.

        Args:
            template_name: Name of the template to render
            **kwargs: Placeholder values (e.g., context="...", question="...")

        Returns:
            Rendered prompt string

        Example:
            >>> system = TemplateRenderer.render(
            ...     'system_constrained',
            ... )
            >>> user = TemplateRenderer.render(
            ...     'user_with_context',
            ...     context='Our policy...',
            ...     question='What is...'
            ... )
        """
        template = TemplateRenderer.get_template(template_name)
        return template.render(**kwargs)

    @staticmethod
    def render_messages(
        system_template: str,
        user_template: str,
        **kwargs
    ) -> list:
        """Render a pair of system/user messages from templates.

        Convenience method for constructing OpenAI-style message lists.
        Handles rendering both templates and assembling into message format.

        Args:
            system_template: Name of system prompt template
            user_template: Name of user message template
            **kwargs: Placeholder values for both templates

        Returns:
            List of dicts: [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]

        Example:
            >>> messages = TemplateRenderer.render_messages(
            ...     system_template='system_constrained',
            ...     user_template='user_with_context',
            ...     context='Policy text here',
            ...     question='What is the refund policy?'
            ... )
        """
        system_content = TemplateRenderer.render(system_template, **kwargs)
        user_content = TemplateRenderer.render(user_template, **kwargs)

        return [
            {"role": "system", "content": system_content.strip()},
            {"role": "user", "content": user_content.strip()},
        ]

    @staticmethod
    def list_templates(filter_prefix: str = None) -> Dict[str, str]:
        """List available templates with descriptions.

        Args:
            filter_prefix: Optional prefix to filter templates (e.g., 'system')

        Returns:
            Dict mapping template names to descriptions
        """
        result = {}
        for name, template in TEMPLATE_REGISTRY.items():
            if filter_prefix is None or name.startswith(filter_prefix):
                result[name] = template.description
        return result
