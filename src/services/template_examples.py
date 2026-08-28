"""Example renders of prompt templates for PolicyPilot.

This module demonstrates how to use TemplateRenderer to construct
prompts for different features. Each example shows:
1. The template being used
2. Sample placeholder values
3. The resulting filled prompt
4. Use case explanation

This serves both as documentation and as test data for validating
prompt template consistency across features.
"""

from src.services.prompt_templates import TemplateRenderer, FALLBACK_RESPONSE
import json


def example_1_interactive_chat_vague():
    """Example: Interactive chat with vague/baseline prompt.

    Use case: Testing how an LLM behaves without policy constraints.
    Feature: Comparison CLI or debugging tool.
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 1: Interactive Chat - Vague Prompt (Baseline)")
    print("=" * 80)
    print("\nUse case: Baseline comparison - unconstrained LLM behavior\n")

    messages = TemplateRenderer.render_messages(
        system_template="system_vague",
        user_template="user_simple",
        question="What is our refund policy for software purchases?",
    )

    print("Generated Messages:")
    for i, msg in enumerate(messages, 1):
        print(f"\n[Message {i}]")
        print(f"Role: {msg['role']}")
        print(f"Content:\n{msg['content']}")

    return messages


def example_2_interactive_chat_constrained():
    """Example: Interactive chat with constrained/grounded prompt.

    Use case: Production PolicyPilot assistant answering staff queries.
    Feature: Interactive CLI chat or web interface.
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Interactive Chat - Constrained Prompt")
    print("=" * 80)
    print("\nUse case: Production PolicyPilot - policy-grounded responses\n")

    sample_context = """
    Software Purchase Refund Policy:
    Employees may request a refund for software tool purchases within 
    30 days of the purchase date. Refunds require:
    1. Original receipt submitted via the Finance Portal
    2. Approval from the employee's direct manager
    3. Proof that the software license has been revoked
    
    Common exceptions:
    - No refunds after 30 days
    - Educational/training software: no refunds (different policy)
    - Open-source or free software: not eligible
    """

    sample_question = "What is our refund policy for software purchases?"

    messages = TemplateRenderer.render_messages(
        system_template="system_constrained",
        user_template="user_with_context",
        context=sample_context.strip(),
        question=sample_question,
        fallback_response=FALLBACK_RESPONSE,
    )

    print("Generated Messages:")
    for i, msg in enumerate(messages, 1):
        print(f"\n[Message {i}]")
        print(f"Role: {msg['role']}")
        print(f"Content:\n{msg['content']}")

    return messages


def example_3_batch_cli_json_output():
    """Example: Batch/CLI processing with JSON output requirement.

    Use case: Processing multiple policy questions from a batch file.
    Feature: CLI batch processor or API endpoint returning structured data.
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Batch CLI - JSON Output Prompt")
    print("=" * 80)
    print("\nUse case: Batch processing with structured JSON output\n")

    sample_context = """
    Vacation Days Policy:
    Full-time employees receive 20 vacation days per year.
    Part-time employees receive 10 vacation days per year.
    Vacation days must be approved by the manager.
    Unused vacation days roll over up to 5 days.
    """

    sample_question = "How many vacation days do I get as a full-time employee?"

    messages = TemplateRenderer.render_messages(
        system_template="system_json_constrained",
        user_template="user_with_context",
        context=sample_context.strip(),
        question=sample_question,
        fallback_response=FALLBACK_RESPONSE,
    )

    print("Generated Messages:")
    for i, msg in enumerate(messages, 1):
        print(f"\n[Message {i}]")
        print(f"Role: {msg['role']}")
        print(f"Content:\n{msg['content']}")

    print("\n" + "-" * 80)
    print("Expected JSON Output Format:")
    expected_output = {
        "answer": "Full-time employees receive 20 vacation days per year.",
        "confidence": "high",
        "refusal": False,
    }
    print(json.dumps(expected_output, indent=2))

    return messages


def example_4_comparison_prompt_variations():
    """Example: Side-by-side prompt comparison for testing.

    Use case: Analyzing behavior differences between vague vs. constrained.
    Feature: Prompt comparison script or A/B testing framework.
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 4: Prompt Comparison - Side-by-Side")
    print("=" * 80)
    print("\nUse case: A/B testing - compare vague vs. constrained behavior\n")

    test_question = "Can I claim a refund for my personal gym membership under health benefits?"

    print(f"Test Query: {test_question}\n")

    # VARIATION 1: Vague
    print("-" * 80)
    print("VARIATION 1: Vague Prompt (No Constraints)")
    print("-" * 80)
    messages_vague = TemplateRenderer.render_messages(
        system_template="system_vague",
        user_template="user_simple",
        question=test_question,
    )
    for msg in messages_vague:
        print(f"\n[{msg['role'].upper()}]")
        print(msg['content'])

    print("\n" + "-" * 80)
    print("VARIATION 2: Constrained Prompt (Policy-Grounded)")
    print("-" * 80)

    sample_context = """
    Health Benefits Policy:
    The company provides health insurance coverage including:
    - Medical insurance
    - Dental coverage
    - Vision coverage
    - Prescription drug coverage
    
    Wellness programs include:
    - Annual fitness challenge (company event)
    - Discounts with selected partner gyms (through HR)
    - Mental health counseling services
    
    Personal gym memberships are NOT covered under health benefits.
    Employees may request subsidies through the Wellness Program office.
    """

    messages_constrained = TemplateRenderer.render_messages(
        system_template="system_constrained",
        user_template="user_with_context",
        context=sample_context.strip(),
        question=test_question,
        fallback_response=FALLBACK_RESPONSE,
    )

    for msg in messages_constrained:
        print(f"\n[{msg['role'].upper()}]")
        print(msg['content'])

    print("\n" + "-" * 80)
    print("Comparison Analysis:")
    print("-" * 80)
    print("""
    Vague Prompt: Likely to make assumptions and provide general wellness
    advice (e.g., "many companies cover gyms", "you should check with HR").
    
    Constrained Prompt: Grounded in retrieved policy, will identify that
    gym memberships are NOT covered and suggest the Wellness Program office
    as the appropriate resource.
    """)

    return messages_vague, messages_constrained


def example_5_list_all_templates():
    """Example: Discovering available templates.

    Shows how to inspect the template registry without hardcoding names.
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 5: Template Registry - Available Templates")
    print("=" * 80)

    templates = TemplateRenderer.list_templates()

    print(f"\nTotal templates available: {len(templates)}\n")

    for name, description in sorted(templates.items()):
        print(f"• {name:30} - {description}")

    print("\n" + "-" * 80)
    print("Filtered Templates (system prompts only):\n")

    system_templates = TemplateRenderer.list_templates(filter_prefix="system")
    for name, description in sorted(system_templates.items()):
        print(f"• {name:30} - {description}")


def run_all_examples():
    """Run all example renders to demonstrate template usage."""
    print("\n")
    print("=" * 80)
    print("POLICYPILOT PROMPT TEMPLATE EXAMPLES")
    print("Demonstrating reusable templates across features")
    print("=" * 80)

    example_1_interactive_chat_vague()
    example_2_interactive_chat_constrained()
    example_3_batch_cli_json_output()
    example_4_comparison_prompt_variations()
    example_5_list_all_templates()

    print("\n" + "=" * 80)
    print("SUMMARY: Template Reuse Across Features")
    print("=" * 80)
    print("""
    ✓ Feature 1 (Interactive Chat): Uses system_constrained + user_with_context
    ✓ Feature 2 (Batch CLI):        Uses system_json_constrained + user_with_context
    ✓ Feature 3 (Comparison):       Uses system_vague + user_simple
                                    Uses system_constrained + user_with_context
    
    KEY BENEFITS:
    • Single source of truth: Edit prompts in prompt_templates.py
    • Consistency: All features use the same template definitions
    • Maintainability: Wording changes apply everywhere automatically
    • Testability: Examples serve as regression tests
    • Flexibility: Add new templates without touching existing code
    """)


if __name__ == "__main__":
    run_all_examples()
