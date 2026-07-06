SYSTEM_PROMPT = """
You are an expert customer support agent.

Your job is to write a professional email reply.

Rules:
- Be polite and empathetic.
- Answer only using information from the customer's email and similar past support replies.
- Never invent company policies.
- Never promise refunds, cancellations, or compensation unless explicitly justified.
- Keep the response under 150 words.
- End with:
Best,
Support Team
"""


def build_prompt(customer_email: str, retrieved_examples: list):
    examples = ""

    for i, ex in enumerate(retrieved_examples, start=1):
        examples += f"""
Example {i}

Customer:
{ex['customer_email']}

Agent Reply:
{ex['agent_reply']}

-----------------------
"""

    return f"""
{SYSTEM_PROMPT}

Here are similar previous conversations:

{examples}

Now write a reply for this new customer email.

Customer:
{customer_email}

Reply:
"""