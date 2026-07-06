import json
import os
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer, util
import ollama

from src.prompts import build_prompt


DATASET_PATH = Path("data/dataset.jsonl")
OUTPUT_PATH = Path("outputs/predictions.jsonl")
MODEL_NAME = "llama3.1:8b"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
TOP_K = 3


def load_dataset(path: Path):
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            rows.append(json.loads(line))
    return rows


def build_embeddings(texts):
    model = SentenceTransformer(EMBEDDING_MODEL)
    embeddings = model.encode(texts, convert_to_tensor=True, normalize_embeddings=True)
    return model, embeddings


def retrieve_similar_examples(query_email: str, dataset, embeddings, embedder, top_k=3):
    query_emb = embedder.encode(query_email, convert_to_tensor=True, normalize_embeddings=True)
    scores = util.cos_sim(query_emb, embeddings)[0].cpu().numpy()
    top_indices = np.argsort(scores)[::-1][:top_k]

    examples = []
    for idx in top_indices:
        examples.append(dataset[idx])
    return examples


def generate_reply(prompt: str):
    response = ollama.chat(
        model=MODEL_NAME,
        messages=[
            {"role": "user", "content": prompt}
        ],
    )
    return response["message"]["content"].strip()


def run_generation():
    os.makedirs("outputs", exist_ok=True)

    dataset = load_dataset(DATASET_PATH)
    embedder = SentenceTransformer(EMBEDDING_MODEL)
    customer_texts = [row["customer_email"] for row in dataset]
    embeddings = embedder.encode(customer_texts, convert_to_tensor=True, normalize_embeddings=True)

    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        for row in dataset:
            retrieved = retrieve_similar_examples(
                row["customer_email"],
                dataset,
                embeddings,
                embedder,
                top_k=TOP_K,
            )

            prompt = build_prompt(row["customer_email"], retrieved)
            reply = generate_reply(prompt)

            out = {
                "id": row["id"],
                "intent": row["intent"],
                "customer_email": row["customer_email"],
                "reference_reply": row["agent_reply"],
                "generated_reply": reply,
                "retrieved_examples": [
                    {
                        "id": ex["id"],
                        "intent": ex["intent"],
                        "customer_email": ex["customer_email"],
                        "agent_reply": ex["agent_reply"],
                    }
                    for ex in retrieved
                ],
            }

            f.write(json.dumps(out, ensure_ascii=False) + "\n")
            print(f"Generated reply for {row['id']}")

    print(f"\nSaved generated replies to {OUTPUT_PATH}")


if __name__ == "__main__":
    run_generation()