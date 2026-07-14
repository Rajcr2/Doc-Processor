import os, json, time
from textwrap import dedent
from openai import OpenAI

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
MODEL = "llama3.1:8b"

LIMIT = 15000  # Character limit 

# --- PROMPTS ---
Prompt_DIRECT = dedent("""\
    You are a legal contract analyst.

    Summarize the following contract in 100–150 words.

    The summary should naturally highlight:
    - The purpose of the agreement.
    - The key obligations of each party.
    - Any notable risks or penalties mentioned in the contract.

    Keep the summary specific to the contract and avoid generic legal language that could apply to any agreement. Do not include information that is not supported by the contract.

    Respond with ONLY the summary.

    Contract: {text}
    """)

Prompt_MAP = dedent("""\
    Review this section of a legal contract.

    Identify any information related to:
    - The purpose of the agreement.
    - Responsibilities or obligations of either party.
    - Risks, penalties, or important legal conditions.

    If these are not present, summarize the key information contained in this section.

    Capture all important points from this section while avoiding unnecessary repetition.

    Respond with concise notes, not a final contract summary.

    Section: {text}
    """)

Prompt_REDUCE = dedent("""\
    Combine the following section notes into ONE coherent summary of 100–150 words.

    The summary should naturally highlight:
    - The purpose of the agreement.
    - The key obligations of each party.
    - Any notable risks or penalties mentioned in the contract.

    Avoid repetition and avoid generic legal statements. Base the summary only on the information provided in the notes.
               
    Return ONLY the final summary.

    Do not include introductions such as "Here is the summary", "Combined summary", "In summary" or any headings other than contract texts.

    Section Notes: {notes}
    """)

def ask(prompt):
    res = client.chat.completions.create(model=MODEL, messages=[{"role": "user", "content": prompt}], temperature=0)
    return res.choices[0].message.content.strip()

def summarize(pages, prefix, cid):
    full_text = "\n\n".join(p.get("text", "") for p in pages)
    
    # Direct Summary
    if len(full_text) <= LIMIT: 
        print(f"\r{prefix} Summarizing (Direct) → {cid}... ", end="", flush=True)
        ans = ask(Prompt_DIRECT.format(text=full_text))
        print("✓ Done")
        return ans

    # Page-by-Page Summary
    groups, cur = [], ""
    for p in pages:
        txt = p.get("text", "")
        if len(cur) + len(txt) > LIMIT and cur:
            groups.append(cur.strip()); cur = ""
        cur += "\n" + txt
    if cur: groups.append(cur.strip())

    # Map Phase (Page-by-Page) Tracking
    notes = []
    total_groups = len(groups)
    for idx, g in enumerate(groups, 1):
        print(f"\r{prefix} Summarizing (Map {idx}/{total_groups}) → {cid}... ", end="", flush=True)
        notes.append(ask(Prompt_MAP.format(text=g)))

    # Reduced Prompt Phase Tracking
    print(f"\r{prefix} Summarizing (Reducing) → {cid}...       ", end="", flush=True)
    ans = ask(Prompt_REDUCE.format(notes="\n\n".join(f"- {n}" for n in notes)))
    print("✓ Done")
    
    return ans

def main():
    contracts = json.load(open("normalised_contracts.json", "r", encoding="utf-8"))
    
    res = []
    if os.path.exists("summaries.json"):
        try:
            res = json.load(open("summaries.json", "r", encoding="utf-8"))
        except json.JSONDecodeError:
            print("summaries.json is corrupted. Starting fresh.")
            
    done_ids = {r["contract_id"] for r in res}

    for i, c in enumerate(contracts, 1):
        cid = c["contract_id"]
        if cid in done_ids: continue
        
        # Progress Indicator 
        prefix = f"[{i}/{len(contracts)}]"
        res.append({"contract_id": cid, "summary": summarize(c.get("pages", []), prefix, cid)})
        
        json.dump(res, open("summaries.json", "w", encoding="utf-8"), indent=2)

    print(f"\n✓ DONE!")

if __name__ == "__main__":
    main()