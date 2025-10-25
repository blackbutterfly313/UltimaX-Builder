#!/usr/bin/env python3
"""
query_and_ask.py
Usage:
  python query_and_ask.py project_name "Your question here"
It returns top-k context and then runs llama-cli with the combined prompt.
"""
import sys, sqlite3, numpy as np, os, subprocess
from sentence_transformers import SentenceTransformer

MODEL_NAME="all-MiniLM-L6-v2"
INDEX_DIR = os.path.expanduser("~/copilot/indexes")
LLAMA_BIN = os.path.expanduser("~/llama.cpp/build/bin/llama-cli")
LLAMA_MODEL = os.path.expanduser("~/models/qwen1.5/qwen1_5-1_8b-chat.Q4_K_M.gguf")

def load_db(project_name):
    p = os.path.join(INDEX_DIR, f"{project_name}.db")
    if not os.path.exists(p):
        print("index not found:", p)
        sys.exit(1)
    conn = sqlite3.connect(p)
    conn.row_factory = None
    return conn

def top_k_sim(conn, q_emb, k=5):
    cur = conn.cursor()
    # fetch all embeddings (small projects okay). For larger: implement approximate search.
    rows = cur.execute("SELECT id, filepath, text, embedding FROM chunks").fetchall()
    sims = []
    q = np.array(q_emb, dtype=np.float32)
    q = q / (np.linalg.norm(q)+1e-9)
    for row in rows:
        emb = np.frombuffer(row[3], dtype=np.float32)
        emb = emb / (np.linalg.norm(emb)+1e-9)
        score = float(np.dot(q, emb))
        sims.append((score, row[1], row[2]))
    sims.sort(reverse=True, key=lambda x: x[0])
    return sims[:k]

def make_context(sims):
    out = []
    for score, fp, text in sims:
        header = f"### Source: {os.path.basename(fp)} (score={score:.4f})\n"
        out.append(header + text)
    return "\n\n".join(out)

def call_llama(prompt, n_predict=256):
    cmd = [LLAMA_BIN, "-m", LLAMA_MODEL, "-p", prompt, "-n", str(n_predict)]
    p = subprocess.run(cmd, capture_output=True, text=True)
    print(p.stdout)
    if p.stderr:
        print("stderr:", p.stderr, file=sys.stderr)

def main():
    if len(sys.argv) < 3:
        print("Usage: python query_and_ask.py project_name \"Your question\"")
        sys.exit(1)
    project = sys.argv[1]
    question = sys.argv[2]
    model = SentenceTransformer(MODEL_NAME)
    q_emb = model.encode([question])[0]
    conn = load_db(project)
    sims = top_k_sim(conn, q_emb, k=6)
    context = make_context(sims)
    full_prompt = f"Context:\n{context}\n\nUser question:\n{question}\n\nAnswer concisely and with code examples if relevant."
    call_llama(full_prompt, n_predict=256)

if __name__ == '__main__':
    main()
