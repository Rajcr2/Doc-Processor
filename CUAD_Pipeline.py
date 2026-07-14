import json

CLAUSES_FILE = "extracted_clauses.json"
SUMMARIES_FILE = "summaries.json"
OUTPUT_FILE = "CUAD_Final_Deliverables.json"

with open(CLAUSES_FILE, "r", encoding="utf-8") as f:
    clauses = json.load(f)

with open(SUMMARIES_FILE, "r", encoding="utf-8") as f:
    summaries = json.load(f)

summary_map = {
    item["contract_id"]: item["summary"]
    for item in summaries
}

final_output = []

for clause in clauses:
    final_output.append({
        "contract_id": clause["contract_id"],
        "summary": summary_map[clause["contract_id"]],
        "termination_clause": clause["termination_clause"],
        "confidentiality_clause": clause["confidentiality_clause"],
        "liability_clause": clause["liability_clause"]
    })

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(final_output, f, indent=4, ensure_ascii=False)

print(f"✓ Successfully merged {len(final_output)} contracts")
print(f"Output saved to '{OUTPUT_FILE}'")