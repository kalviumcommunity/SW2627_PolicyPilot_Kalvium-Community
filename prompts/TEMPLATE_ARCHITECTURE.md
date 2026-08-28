# Prompt Template Refactoring - Architecture & Usage Guide

## Overview

PolicyPilot's prompts have been refactored from **scattered, duplicate definitions** into a **centralized, reusable template system**. This ensures consistency across all features and makes prompt maintenance trivial.

### Problem Solved

**Before:**
- Prompt definitions scattered across multiple files (`prompt_service.py`, `response_service.py`, etc.)
- Same prompt definitions duplicated with slight variations
- Wording changes required editing multiple copies
- Hard to track which features use which prompts
- Easy to introduce inconsistencies

**After:**
- All templates in a single module: `src/services/prompt_templates.py`
- One source of truth for each prompt
- Rendering happens via a clean API: `TemplateRenderer`
- Templates are reused across features
- Changes in one place apply everywhere

---

## Architecture

### Three New Modules

#### 1. **`src/services/prompt_templates.py`** — Template Definitions
Defines all prompts as reusable `PromptTemplate` objects with named placeholders:

```python
template = PromptTemplate(
    name="system_constrained",
    template="You are PolicyPilot...\n{fallback_response}",
    description="Strict policy-grounded assistant"
)
```

**Key Classes:**
- `PromptTemplate`: Stores a template with placeholders and a `render()` method
- `TemplateRenderer`: Static API for rendering templates safely

#### 2. **`src/services/prompt_service.py`** — Feature Integration (Refactored)
Simplified to delegate to `TemplateRenderer`:

```python
def get_constrained_prompt(user_query: str, context: str = ""):
    return TemplateRenderer.render_messages(
        system_template="system_constrained",
        user_template="user_with_context",
        context=context,
        question=user_query,
        fallback_response=FALLBACK_RESPONSE,
    )
```

#### 3. **`src/services/response_service.py`** — Feature Integration (Refactored)
Also simplified to use templates:

```python
messages = TemplateRenderer.render_messages(
    system_template="system_constrained",
    user_template="user_with_context",
    context=context_text,
    question=query,
    fallback_response=FALLBACK_RESPONSE,
)
```

#### 4. **`src/services/template_examples.py`** — Examples & Documentation
Runnable examples showing:
- Interactive chat with vague vs. constrained prompts
- Batch/CLI JSON output mode
- A/B comparison of prompt variations
- Template registry inspection

Run examples:
```bash
python src/services/template_examples.py
```

---

## Template Registry

All templates are registered in `TEMPLATE_REGISTRY`:

| Template Name | Type | Purpose |
|---|---|---|
| `system_vague` | System | Baseline comparison (unconstrained) |
| `system_constrained` | System | Production PolicyPilot (grounded) |
| `system_json_constrained` | System | JSON output mode |
| `user_simple` | User | Just the question |
| `user_with_context` | User | Question + retrieved policy context |
| `messages_constrained` | Full | System + user combined (for display) |
| `messages_json` | Full | System + user for JSON mode |

---

## Placeholders & Usage

### Named Placeholders

Templates use named placeholders:
- `{context}` — Retrieved policy context
- `{question}` — User's query
- `{fallback_response}` — Fallback message for unsupported queries

### Rendering API

#### Single Template
```python
system_prompt = TemplateRenderer.render(
    'system_constrained',
    fallback_response="I cannot answer..."
)
```

#### Message Pair (OpenAI format)
```python
messages = TemplateRenderer.render_messages(
    system_template='system_constrained',
    user_template='user_with_context',
    context='Our refund policy is...',
    question='What is the refund policy?',
    fallback_response="I cannot answer..."
)

# Result:
# [
#   {"role": "system", "content": "..."},
#   {"role": "user", "content": "..."}
# ]
```

#### List Available Templates
```python
templates = TemplateRenderer.list_templates()
# or filter:
system_templates = TemplateRenderer.list_templates(filter_prefix="system")
```

---

## How Templates Are Reused Across Features

### Feature 1: Interactive Chat
- Uses: `system_constrained` + `user_with_context`
- Location: `prompt_service.get_constrained_prompt()`
- Output: User-friendly answers

### Feature 2: Batch/CLI Processing
- Uses: `system_json_constrained` + `user_with_context`
- Location: Can use `compare_prompts.py` or create CLI tool
- Output: Structured JSON responses

### Feature 3: Prompt Comparison
- Uses: Both vague and constrained templates
- Location: `prompt_service.py`, `compare_prompts.py`
- Output: Side-by-side comparison showing differences

### Feature 4: Response Service (Production)
- Uses: `system_constrained` + `user_with_context`
- Location: `response_service.py`
- Output: Grounded, policy-only answers with fallback handling

---

## Adding a New Template

1. Define the template in `prompt_templates.py`:
```python
SYSTEM_PROMPT_CUSTOM = PromptTemplate(
    name="system_custom",
    description="Custom purpose",
    template="Your prompt with {placeholder} markers"
)
```

2. Register it:
```python
TEMPLATE_REGISTRY["system_custom"] = SYSTEM_PROMPT_CUSTOM
```

3. Use it:
```python
TemplateRenderer.render("system_custom", placeholder="value")
```

**No changes needed** to existing code—new templates are immediately available.

---

## Validation & Error Handling

The template system automatically validates:
- **Missing placeholders** — Raises `KeyError` with helpful message
- **Unknown templates** — Raises `KeyError` with list of available templates
- **Placeholder mismatch** — Clear error: `"Template 'system_constrained' missing required placeholders: {'fallback_response'}"`

Example:
```python
try:
    prompt = TemplateRenderer.render("system_constrained")
except KeyError as e:
    print(f"Error: {e}")
    # Error: Template 'system_constrained' missing required placeholders: {'fallback_response'}
```

---

## Testing

All prompt templates are exercised by the example renders:

```bash
# Run examples and verify output
python src/services/template_examples.py

# Check that prompt_service.py functions work
python -c "from src.services.prompt_service import get_constrained_prompt; print(get_constrained_prompt('test', 'context'))"

# Verify response_service.py still works
python src/main.py
```

---

## Maintenance & Future Changes

### To update a prompt:
**Before:** Edit multiple copies across files ❌
**After:** Edit one template in `prompt_templates.py` ✅

Example: Update fallback response
```python
# src/services/prompt_templates.py
FALLBACK_RESPONSE = "Updated message..."

# Automatically applies everywhere:
# - prompt_service.py (comparison, interactive)
# - response_service.py (production)
# - Any new features
```

### To add a new feature using templates:
```python
from src.services.prompt_templates import TemplateRenderer

# In your feature code:
messages = TemplateRenderer.render_messages(
    system_template="system_constrained",
    user_template="user_with_context",
    context=retrieved_policy,
    question=user_query,
    fallback_response=FALLBACK_RESPONSE,
)
```

---

## Benefits

✅ **Single Source of Truth** — All prompts defined once  
✅ **Consistency** — All features use identical prompt structures  
✅ **Maintainability** — Change once, apply everywhere  
✅ **Testability** — Examples serve as regression tests  
✅ **Flexibility** — Add templates without touching existing code  
✅ **Safety** — Validation prevents missing placeholders  
✅ **Clarity** — Template names describe purpose (`system_constrained`, `user_with_context`)  
✅ **Reusability** — New features automatically benefit from centralized templates  

---

## Files Changed

| File | Change | Impact |
|---|---|---|
| `src/services/prompt_templates.py` | **NEW** | Central template definitions |
| `src/services/prompt_service.py` | **REFACTORED** | Now uses `TemplateRenderer` |
| `src/services/response_service.py` | **REFACTORED** | Now uses `TemplateRenderer` |
| `src/services/template_examples.py` | **NEW** | Runnable examples & documentation |

---

## Next Steps

1. **Extend templates** — Add new templates as features grow
2. **Document usage** — Add examples to each feature's docstring
3. **Monitor consistency** — When adding features, use `TemplateRenderer`
4. **Benchmark** — Compare prompt costs/latency across variations in `template_examples.py`

---

## Questions?

Refer to:
- Template definitions: `src/services/prompt_templates.py`
- Usage examples: `src/services/template_examples.py`
- Feature integration: `src/services/prompt_service.py`, `response_service.py`
