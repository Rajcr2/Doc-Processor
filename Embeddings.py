import json
import chromadb
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter

INPUT_FILE = "normalised_contracts.json"
CHUNK_SIZE = 1500
CHUNK_OVERLAP = 200

splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    separators=["\n\n", "\n", ". ", " ", ""]
)

def main():

    print("→ Loading contracts...")
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        contracts = json.load(f)

    print("→ Loading embedding model...")
    model = SentenceTransformer("all-MiniLM-L6-v2")

    print("→ Initializing ChromaDB...")
    client = chromadb.PersistentClient(path="./CUAD_chroma_db")
    collection = client.get_or_create_collection("contract_chunks")

    print(f"→ Existing vectors: {collection.count()}")

    data = collection.get()
    processed = {m["contract_id"] for m in data["metadatas"]} if data["metadatas"] else set()

    total = len(contracts)

    for idx, contract in enumerate(contracts, start=1):
        contract_id = contract["contract_id"]
        if contract_id in processed:
            print(f"[{idx}/{total}] SKIP → {contract_id}")
            continue

        full_text = "\n\n".join(page["text"] for page in contract.get("pages", []))
        chunks = splitter.split_text(full_text)

        print(f"\n[{idx}/{total}] Embedding → {contract_id}")
        print(f"    Chunks: {len(chunks)}")

        embeddings = model.encode(chunks, show_progress_bar=False)

        collection.upsert(
            ids=[f"{contract_id}__chunk_{i}" for i in range(len(chunks))],
            embeddings=[e.tolist() for e in embeddings],
            documents=chunks,
            metadatas=[{"contract_id": contract_id, "chunk_index": i} for i in range(len(chunks))]
        )

        print(f"    ✓ Stored {len(chunks)} chunks")
        print(f"    Total vectors: {collection.count()}")

    print("\n✓ Embedding complete")
    print(f"Contracts processed : {total}")
    print(f"Total vectors stored: {collection.count()}")


if __name__ == "__main__":
    main()
