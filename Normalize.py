import fitz, os, json

CONTRACTS_DIR = "contracts"
OUTPUT_FILE = "normalised_contracts.json"
TEXT_BLOCK = 0 

def extract_pages(path):
    doc = fitz.open(path)
    pages = []

    for i, page in enumerate(doc):
        blocks = page.get_text("blocks")

        paragraphs = []
        for b in blocks:
            if b[6] != TEXT_BLOCK:
                continue
            text = b[4].strip().replace("\n", " ")
            if text and not text.lower().startswith("source:"):
                paragraphs.append(text)

        page_text = "\n\n".join(paragraphs)
        if page_text:
            pages.append({"page_number": i + 1, "text": page_text})

    return pages


def main():
    if not os.path.exists(CONTRACTS_DIR):
        print(f"Directory '{CONTRACTS_DIR}' not found.")
        return

    contracts = []
    for filename in os.listdir(CONTRACTS_DIR):
        if not filename.lower().endswith(".pdf"):
            continue

        path = os.path.join(CONTRACTS_DIR, filename)
        contracts.append({
            "contract_id": filename.replace(".pdf", ""),
            "pages": extract_pages(path)
        })

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(contracts, f, indent=2)

    print(f"✓ {len(contracts)} contracts → {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
