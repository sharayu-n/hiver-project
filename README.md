# 📧 AI Email Suggested Response System

An end-to-end AI-powered email response suggestion system built for the **Hiver Open Challenge**.

The system generates customer support email replies using **Retrieval-Augmented Generation (RAG)** over a synthetic support email dataset and evaluates each generated response using a custom rule-based accuracy framework.

---

# Problem Statement

Customer support teams repeatedly answer similar emails every day. Instead of generating replies without context, this project retrieves similar historical conversations and uses them to ground an LLM when drafting a response.

The project also includes an evaluation system that measures how useful and accurate each generated response is.

---

# Approach

The project consists of three main components:

1. Dataset Generation
2. AI Response Generation
3. Response Evaluation

---

# 1. Dataset

The challenge allows using synthetic, public, or hand-authored data.

For this project I created a **synthetic customer-support dataset** consisting of **32 historical email-response pairs** covering common support scenarios.

Supported intents include:

- Refund requests
- Shipping delays
- Password reset
- Order cancellation
- Subscription billing
- Feature requests
- Bug reports
- Account lockout

Each record contains:

```json
{
  "id": "email_001",
  "intent": "refund_request",
  "customer_email": "...",
  "agent_reply": "...",
  "required_points": [
    "...",
    "..."
  ],
  "forbidden_points": [
    "..."
  ]
}
```

### Why this dataset?

The goal was to simulate the type of repetitive support conversations commonly seen in shared inboxes.

In addition to email/reply pairs, every example contains:

- required information that should appear in a correct response
- forbidden claims that should never be made

These annotations make automatic evaluation significantly more meaningful than comparing text alone.

---

# 2. AI Response Generation

The response generator uses a Retrieval-Augmented Generation (RAG) pipeline.

Instead of asking an LLM to answer from scratch, the system first retrieves similar historical conversations before generating a reply.

Pipeline:

```
Incoming Email
        │
        ▼
Sentence Transformer Embeddings
        │
        ▼
Cosine Similarity Search
        │
        ▼
Top-3 Similar Historical Emails
        │
        ▼
Prompt Construction
        │
        ▼
Ollama (Llama 3.1 8B)
        │
        ▼
Suggested Response
```

### Why Retrieval-Augmented Generation?

Support emails often repeat similar issues.

Retrieval grounds the LLM using historical examples, producing replies that are more consistent than zero-shot prompting while remaining much simpler than fine-tuning.

---

# 3. Accuracy / Evaluation

This is the primary focus of the project.

## Why exact match is not appropriate

Two support emails may communicate exactly the same information using different wording.

Traditional NLP metrics like BLEU or ROUGE would incorrectly penalize good responses simply because the wording differs.

Instead, this project evaluates whether the generated response satisfies the business objective.

---

## Evaluation Metrics

Each response receives a weighted score based on:

| Metric | Weight |
|---------|--------|
| Required point coverage | 55% |
| Groundedness (avoid forbidden claims) | 25% |
| Tone & professionalism | 10% |
| Formatting | 5% |
| Brevity | 5% |

### Required Point Coverage

Checks whether important information requested for that support scenario is present.

Examples:

- apologize
- ask for order number
- suggest password reset
- request account email

---

### Groundedness

Ensures the model avoids unsupported claims such as:

- guaranteeing refunds
- asking for passwords
- promising implementation dates
- claiming issues are already fixed

---

### Tone

Rewards polite and professional language.

---

### Formatting

Checks for a proper customer-support email structure.

---

### Brevity

Encourages concise responses suitable for support agents.

---

## Per-response Output

Every generated email produces:

- individual metric scores
- overall score
- matched required points
- missing required points
- forbidden rule violations
- explanation

---

## Overall System Score

The evaluator also computes aggregate statistics across the entire dataset.

Example output:

```json
{
  "num_examples": 32,
  "overall_score": 77.86,
  "avg_coverage": 64.58,
  "avg_groundedness": 93.75,
  "avg_tone": 89.06,
  "avg_format": 100.0,
  "avg_brevity": 100.0
}
```

---

# Repository Structure

```
hiver-project/
│
├── data/
│   └── dataset.jsonl
│
├── outputs/
│   ├── predictions.jsonl
│   ├── scores.jsonl
│   └── summary.json
│
├── src/
│   ├── build_dataset.py
│   ├── generate.py
│   ├── evaluate.py
│   ├── prompts.py
│   └── utils.py
│
├── run.py
├── requirements.txt
└── README.md
```

---

# How to Run

Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies

```bash
pip install -r requirements.txt
```

Start Ollama

```bash
ollama serve
```

Download the model

```bash
ollama pull llama3.1:8b
```

Generate the dataset

```bash
python src/build_dataset.py
```

Generate responses

```bash
python -m src.generate
```

Evaluate responses

```bash
python -m src.evaluate
```

Or run the complete pipeline

```bash
python run.py
```

---

# Technologies Used

- Python
- Ollama
- Llama 3.1 8B
- Sentence Transformers
- scikit-learn
- NumPy

---

# Trade-offs

### Advantages

- Fully local inference
- Retrieval improves consistency
- Evaluation is explainable
- Simple end-to-end pipeline

### Limitations

- Synthetic dataset is relatively small
- Rule-based evaluation cannot fully capture human judgment
- Retrieval uses cosine similarity only (no reranking)

---

# Future Improvements

- Larger and more diverse datasets
- Multi-turn email threads
- Hybrid lexical + semantic retrieval
- LLM-as-a-Judge evaluation
- Better hallucination detection

---

# AI Tools Used

AI tools were used to assist with:

- brainstorming the overall architecture
- generating boilerplate code
- refining prompts
- improving documentation

The project design, integration, testing, and final implementation were completed by the author.

---

# Deliverables

✅ Dataset generation script

✅ Retrieval-Augmented email response generator

✅ Automated evaluation system

✅ Per-response scores

✅ Overall evaluation summary

✅ End-to-end runnable pipeline