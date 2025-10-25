import os, sqlite3, pickle
from embedder import LightweightEmbedder

DB_PATH = "context_memory.db"

def rebuild_index(base_dir="projects"):
    texts = []
    for root, _, files in os.walk(base_dir):
        for f in files:
            if f.endswith((".py", ".js", ".html", ".md", ".txt")):
                try:
                    with open(os.path.join(root, f), "r", encoding="utf-8", errors="ignore") as fh:
                        texts.append(fh.read())
                except Exception:
                    pass
    if not texts:
        print("⚠️ No readable project files found.")
        return

    emb = LightweightEmbedder(DB_PATH)
    emb.add(texts)
    print(f"✅ Indexed {len(texts)} files into {DB_PATH}")

def search_context(query):
    emb = LightweightEmbedder(DB_PATH)
    results = emb.query(query)
    print("🔍 Top related contexts:")
    for r in results:
        print("-", r[:150].replace("\n", " "), "...")
        
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        search_context(" ".join(sys.argv[1:]))
    else:
        rebuild_index()
