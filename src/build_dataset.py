import json
import os
from pathlib import Path

INTENTS = [
    {
        "intent": "refund_request",
        "topic": "refund request",
        "customer_templates": [
            "Hi, I was charged for an item that arrived broken. I'd like a refund.",
            "Hello, my order came damaged and I'd like my money back.",
            "Hi support, the product stopped working after two days. Please process a refund.",
            "Hello, I want a refund because the item never worked properly.",
        ],
        "agent_templates": [
            "Hi {name},\n\nI'm sorry about the issue with your order. We can help with a refund. Please reply with your order number so we can look it up and start the process.\n\nBest,\nSupport Team",
            "Hi {name},\n\nSorry to hear the item arrived broken. Please send your order ID and we'll review the case and guide you through the refund steps.\n\nBest,\nSupport Team",
            "Hi {name},\n\nI understand the frustration here. Please share your order number so we can verify the purchase and proceed with the refund request.\n\nBest,\nSupport Team",
            "Hi {name},\n\nWe are sorry the product did not work as expected. Please send your order details and we will check the refund eligibility right away.\n\nBest,\nSupport Team",
        ],
        "required_points": ["apologize", "request order number", "mention refund process"],
        "forbidden_points": ["guarantee immediate refund", "blame the customer"],
    },
    {
        "intent": "shipping_delay",
        "topic": "shipping delay",
        "customer_templates": [
            "Hi, my order was supposed to arrive last week but it's still not here. Can you check?",
            "Hello, the tracking hasn't updated in days and my package is late.",
            "Hi support, my shipment is delayed and I need an update.",
            "Hello, my delivery is past the expected date. Please help.",
        ],
        "agent_templates": [
            "Hi {name},\n\nSorry for the delay. Please send your order number and we'll check the latest tracking status and next steps for you.\n\nBest,\nSupport Team",
            "Hi {name},\n\nI understand the package is delayed. Share your order ID and we'll review the shipment status and update you shortly.\n\nBest,\nSupport Team",
            "Hi {name},\n\nApologies for the inconvenience. Please provide your order number so we can look into the tracking details and assist further.\n\nBest,\nSupport Team",
            "Hi {name},\n\nThanks for reaching out. We'll be happy to investigate the delay once you send your order details.\n\nBest,\nSupport Team",
        ],
        "required_points": ["acknowledge delay", "request order number", "promise to check tracking"],
        "forbidden_points": ["promise exact delivery date", "blame shipping carrier"],
    },
    {
        "intent": "password_reset",
        "topic": "password reset",
        "customer_templates": [
            "Hello, I can't log in after resetting my password.",
            "Hi, the login page says my password is incorrect even though I changed it.",
            "Hello support, I'm locked out of my account after a password change.",
            "Hi, I need help getting back into my account.",
        ],
        "agent_templates": [
            "Hi {name},\n\nSorry you're having trouble logging in. Please try the Forgot Password option first. If that does not work, reply with the email address on the account and we'll investigate.\n\nBest,\nSupport Team",
            "Hi {name},\n\nWe can help with that. Please use the password reset link, and if the issue continues, send the email linked to your account.\n\nBest,\nSupport Team",
            "Hi {name},\n\nThanks for letting us know. Please try resetting your password again and let us know the email address associated with the account if you still cannot sign in.\n\nBest,\nSupport Team",
            "Hi {name},\n\nSorry about the login issue. Please use the Forgot Password flow and share the account email if you need further help.\n\nBest,\nSupport Team",
        ],
        "required_points": ["acknowledge login issue", "suggest forgot password", "ask for account email"],
        "forbidden_points": ["ask for password", "request sensitive credentials"],
    },
    {
        "intent": "order_cancellation",
        "topic": "order cancellation",
        "customer_templates": [
            "Hi, I placed the wrong order and need to cancel it.",
            "Hello, can you stop my order before it ships?",
            "Hi support, I want to cancel my recent order.",
            "Hello, I changed my mind and want to cancel the purchase.",
        ],
        "agent_templates": [
            "Hi {name},\n\nSorry about that. Please send your order number and we'll check whether cancellation is still possible.\n\nBest,\nSupport Team",
            "Hi {name},\n\nWe can take a look. Share your order ID and we'll confirm the cancellation status for you.\n\nBest,\nSupport Team",
            "Hi {name},\n\nThanks for reaching out. Please provide your order number so we can review the request and next steps.\n\nBest,\nSupport Team",
            "Hi {name},\n\nI understand. Send your order details and we will check if the order can still be canceled.\n\nBest,\nSupport Team",
        ],
        "required_points": ["acknowledge cancellation request", "request order number", "state cancellation depends on status"],
        "forbidden_points": ["promise cancellation without checking", "mention refund without context"],
    },
    {
        "intent": "subscription_billing",
        "topic": "subscription billing",
        "customer_templates": [
            "Hi, I was charged for a subscription I thought I canceled.",
            "Hello, I don't recognize this monthly charge.",
            "Hi support, please explain the recent billing on my account.",
            "Hello, I want help with an unexpected subscription charge.",
        ],
        "agent_templates": [
            "Hi {name},\n\nSorry for the confusion. Please send the email on the account and the charge date, and we'll look into the billing details for you.\n\nBest,\nSupport Team",
            "Hi {name},\n\nThanks for reaching out. Share the account email and the billing date so we can investigate the subscription charge.\n\nBest,\nSupport Team",
            "Hi {name},\n\nWe can help with that. Please reply with the email tied to the subscription and we'll check the recent payment activity.\n\nBest,\nSupport Team",
            "Hi {name},\n\nSorry about the unexpected charge. Send your account email and we'll review the subscription status and billing history.\n\nBest,\nSupport Team",
        ],
        "required_points": ["acknowledge billing issue", "request account email", "offer to investigate charge"],
        "forbidden_points": ["confirm fraud", "promise immediate refund"],
    },
    {
        "intent": "feature_request",
        "topic": "feature request",
        "customer_templates": [
            "Hi, could you add dark mode to the app?",
            "Hello, I would love an export to CSV feature.",
            "Hi support, can you add recurring reminders?",
            "Hello, please consider adding multi-language support.",
        ],
        "agent_templates": [
            "Hi {name},\n\nThanks for the suggestion. I've shared your request with the team, and we appreciate you taking the time to send feedback.\n\nBest,\nSupport Team",
            "Hi {name},\n\nWe appreciate the idea. We'll pass this along to the product team for review.\n\nBest,\nSupport Team",
            "Hi {name},\n\nThank you for the thoughtful feedback. I've logged your request so it can be considered for future updates.\n\nBest,\nSupport Team",
            "Hi {name},\n\nThanks for suggesting this feature. We'll share it with the team and keep it in mind for future planning.\n\nBest,\nSupport Team",
        ],
        "required_points": ["thank the user", "acknowledge request", "say it will be shared with product team"],
        "forbidden_points": ["promise implementation", "give timeline"],
    },
    {
        "intent": "bug_report",
        "topic": "bug report",
        "customer_templates": [
            "Hi, the app crashes when I upload a file.",
            "Hello, the checkout button doesn't work.",
            "Hi support, I see an error when I try to save changes.",
            "Hello, the page freezes whenever I click submit.",
        ],
        "agent_templates": [
            "Hi {name},\n\nSorry for the trouble. Please send the steps to reproduce the issue, your device/browser, and a screenshot if possible so we can investigate.\n\nBest,\nSupport Team",
            "Hi {name},\n\nThanks for reporting this bug. If you can share the steps you took and any error message, we'll look into it.\n\nBest,\nSupport Team",
            "Hi {name},\n\nWe appreciate the report. Please include the browser or device you used and the steps that led to the crash.\n\nBest,\nSupport Team",
            "Hi {name},\n\nSorry about that. Send us the repro steps and any screenshots, and we'll pass this to the team for debugging.\n\nBest,\nSupport Team",
        ],
        "required_points": ["apologize", "ask for repro steps", "ask for device/browser"],
        "forbidden_points": ["blame user", "claim fixed already"],
    },
    {
        "intent": "account_locked",
        "topic": "account locked",
        "customer_templates": [
            "Hi, my account got locked after too many failed logins.",
            "Hello, I can't access my account because it says locked.",
            "Hi support, my account is blocked and I need access again.",
            "Hello, I'm locked out after multiple login attempts.",
        ],
        "agent_templates": [
            "Hi {name},\n\nSorry about the lockout. Please confirm the email on the account and we'll review the security lock and next steps.\n\nBest,\nSupport Team",
            "Hi {name},\n\nThanks for reaching out. Send the account email and we'll help check the lock status and recovery options.\n\nBest,\nSupport Team",
            "Hi {name},\n\nWe can help with that. Please share the email tied to the account so we can investigate the lock.\n\nBest,\nSupport Team",
            "Hi {name},\n\nSorry you're locked out. Reply with the account email and we'll look into restoring access.\n\nBest,\nSupport Team",
        ],
        "required_points": ["acknowledge lockout", "request account email", "mention security review"],
        "forbidden_points": ["ask for password", "promise immediate unlock"],
    },
]


NAMES = ["Alex", "Jamie", "Taylor", "Jordan"]
EMAIL_PREFIXES = ["email", "ticket", "case", "message"]


def build_dataset():
    rows = []
    idx = 1

    for intent_group in INTENTS:
        for variant in range(4):
            name = NAMES[variant % len(NAMES)]
            customer_email = intent_group["customer_templates"][variant]
            agent_reply = intent_group["agent_templates"][variant].format(name=name)

            row = {
                "id": f"email_{idx:03d}",
                "intent": intent_group["intent"],
                "topic": intent_group["topic"],
                "customer_email": customer_email,
                "agent_reply": agent_reply,
                "required_points": intent_group["required_points"],
                "forbidden_points": intent_group["forbidden_points"],
            }
            rows.append(row)
            idx += 1

    return rows


def save_dataset(rows):
    os.makedirs("data", exist_ok=True)
    out_path = Path("data/dataset.jsonl")

    with out_path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"Saved {len(rows)} email pairs to {out_path}")


if __name__ == "__main__":
    rows = build_dataset()
    save_dataset(rows)