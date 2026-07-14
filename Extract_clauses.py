import os
import json
from textwrap import dedent
import chromadb
from sentence_transformers import SentenceTransformer
from openai import OpenAI

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
MODEL = "llama3.1:8b"

OUTPUT_FILE = "extracted_clauses.json"

INITIAL_RETRIEVAL_K = 12  # chunks retrieved from ChromaDB per clause type

QUERIES = {
    "termination_clause": "termination conditions, termination rights, termination notice, cancellation of agreement",
    "confidentiality_clause": "confidentiality, confidentiality clause, confidential information, confidential information obligations, confidential information shall not disclose, non-disclosure agreement, nondisclosure, proprietary information, trade secrets, confidential data, disclosure restrictions",
    "liability_clause": "limitation of liability clause, consequential damages, indemnification obligations, warranty disclaimer",
}

# One call evaluates ALL retrieved chunks at once instead of one call per chunk
SELECTOR_PROMPT = dedent("""\
    You are a STRICT legal relevance evaluator.

    Below are numbered excerpts retrieved from a contract. For each one, decide whether it is
    DIRECTLY useful to extract the {clause_type} — meaning it contains actual legal terms,
    obligations, or rights related to it. Reject table-of-contents lines, generic headings,
    or unrelated text. Be strict. Do NOT guess.

    Target Clause Type: {clause_type}

    Excerpts:
    {numbered_chunks}

    Respond ONLY with valid JSON listing the numbers of the relevant excerpts, e.g. {{"relevant": [2, 5]}}.
    If none are relevant, return {{"relevant": []}}.
    """)

EXTRACTOR_PROMPT = dedent("""\
    You are an expert legal contract analyst.
    Below are excerpts selected as relevant to the requested clause. Extract the clause using
    ONLY the provided text.

    Rules:
    - Use the contract's own wording as closely as possible.
    - Do not infer or invent information that is not present.
    - If the clause is genuinely absent, return exactly: "Not specified"
    - Return ONLY valid JSON. No markdown, no explanations.
    - CRITICAL: The "Reference Examples" below are templates. You MUST extract from the "Selected Legal Context" provided at the very bottom. Do NOT copy text from the examples.

    --- REFERENCE EXAMPLES ---
    Example 1 (Termination):
    Target Clause Type: termination_clause
    Selected Legal Context: "[1] The term of this Agreement shall commence on the Effective Date. [2] Either Party may terminate the Project and all commitments and obligations with respect thereto upon thirty (30) days written notice to the other Party."
    Output:
    {{"termination_clause": "Either Party may terminate the Project and all commitments and obligations with respect thereto upon thirty (30) days written notice to the other Party."}}

    Example 2 (Confidentiality):
    Target Clause Type: confidentiality_clause
    Selected Legal Context: "[1] The receiving Party shall hold all such Information in confidence with the same degree of care with which it protects its own confidential Information. [2] Neither Party shall disclose Information under this Agreement without express consent."
    Output:
    {{"confidentiality_clause": "The receiving Party shall hold all such Information in confidence with the same degree of care with which it protects its own confidential Information. Neither Party shall disclose Information under this Agreement without express consent."}}

    Example 3 (Not Found):
    Target Clause Type: liability_clause
    Selected Legal Context: "[1] The receiving Party shall hold all such Information in confidence. [2] Invoices must be paid within 30 days of receipt."
    Output:
    {{"liability_clause": "Not specified"}}
    -------------------------

    EXTRACT ACTUAL DETAILS FROM THE FOLLOWING :-
                          
    Target Clause Type: {clause_type}

    Selected Legal Context:
    {context}
    """)

def retrieve_chunks(collection, embedder, contract_id, query_text):
    query_embedding = embedder.encode(query_text).tolist()
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=INITIAL_RETRIEVAL_K,
        where={"contract_id": contract_id}
    )
    return results["documents"][0] if results["documents"] else []

def select_relevant_chunks(clause_type, chunks):
    if not chunks:
        return []

    # PROMPT BATCHING - Evaluates all retrieved chunks in a single LLM call instead of sending one API request per chunk.
    numbered = "\n\n".join(f"[{i+1}] {chunk}" for i, chunk in enumerate(chunks))
    prompt = SELECTOR_PROMPT.format(clause_type=clause_type, numbered_chunks=numbered)

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.0,
        )
        raw = response.choices[0].message.content.strip()
        parsed = json.loads(raw)
        indices = parsed.get("relevant", [])
        return [chunks[i - 1] for i in indices if 1 <= i <= len(chunks)]
    except Exception as e:
        print(f"        [Selector] API error: {e}")
        return []

def generate_clause(clause_type, selected_chunks):
    if not selected_chunks:
        return "Not specified"

    context = "\n\n---\n\n".join(selected_chunks)
    prompt = EXTRACTOR_PROMPT.format(clause_type=clause_type, context=context)

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.0,
        )
        raw = response.choices[0].message.content.strip()
        parsed = json.loads(raw)
        return parsed.get(clause_type, "Not specified")
    except Exception as e:
        print(f"        [Generator] Execution error: {e}")
        return "Extraction failed"

def extract_clauses(collection, embedder, contract_id):
    extracted = {}

    for clause_type, query_text in QUERIES.items():
        retrieved = retrieve_chunks(collection, embedder, contract_id, query_text)
        selected = select_relevant_chunks(clause_type, retrieved)
        value = generate_clause(clause_type, selected)

        print(f"      {clause_type}: retrieved {len(retrieved)}, selected {len(selected)} -> {value[:60]}")
        extracted[clause_type] = value

    return extracted

def load_existing_results():
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("Output file corrupted — starting fresh.")
    return []

def main():
    print("→ Loading embedding model...")
    embedder = SentenceTransformer("all-MiniLM-L6-v2")

    print("→ Connecting to ChromaDB...")
    collection = chromadb.PersistentClient(path="./CUAD_chroma_db").get_or_create_collection("contract_chunks")

    all_contract_ids = sorted({m["contract_id"] for m in collection.get()["metadatas"]})

    results = load_existing_results()
    done_ids = {r["contract_id"] for r in results}

    if done_ids:
        print(f"Resuming — {len(done_ids)} contracts already done.\n")

    total = len(all_contract_ids)

    for idx, contract_id in enumerate(all_contract_ids, start=1):
        if contract_id in done_ids:
            print(f"[{idx}/{total}] SKIP → {contract_id}")
            continue

        print(f"\n[{idx}/{total}] Extracting → {contract_id}")

        clauses = extract_clauses(collection, embedder, contract_id)
        results.append({"contract_id": contract_id, **clauses})

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)

    print(f"\n✓ DONE — {len(results)} contracts saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
