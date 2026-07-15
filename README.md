# Legal Contract Analysis using LLMs

AI Internship Assignment

---

## Overview

This project automates legal contract analysis using Retrieval-Augmented Generation (RAG) and Large Language Models (LLMs).

The system processes a collection of legal contracts and generates:

- **Part A:** Extraction of important legal clauses
- **Part B:** Contract summaries

The pipeline combines semantic search, vector databases, and LLM reasoning to accurately identify and summarize contract information.

---

# Project Pipeline

```
PDF Contracts
      │
      ▼
Normalize PDF Text
      │
      ▼
Page-wise JSON
      │
      ▼
Chunking
      │
      ▼
SentenceTransformer Embeddings
      │
      ▼
ChromaDB
      │
      ▼
Semantic Retrieval
      │
      ▼
LLM Chunk Selector
      │
      ▼
Clause Extraction
      │
      ▼
JSON Output
      │
      ▼
Contract Summarization
```

---

# Folder Structure

```
contracts/
│
├── *.pdf

Normalize.py
Embeddings.py
Extract_UsageT_Clauses.py
Summarize.py

normalised_contracts.json
extracted_clauses.json
summaries.json

usage_report_tracker.json
summarise_usage_report.json

chroma_db/
```

---

# Part A – Clause Extraction

The objective is to extract the following clauses from every contract.

- Termination Clause
- Confidentiality Clause
- Liability Clause

Example output

```json
{
    "contract_id": "...",
    "termination_clause": "...",
    "confidentiality_clause": "...",
    "liability_clause": "..."
}
```

---

## Step 1 – PDF Normalization

Every PDF is converted into structured JSON.

Features

- Page-wise extraction
- Removes unnecessary footer text
- Preserves page boundaries
- Stores contract_id with extracted pages

Output

```
normalised_contracts.json
```

---

## Step 2 – Embedding Generation

Contracts are split using Recursive Character Text Splitter.

Configuration

- Chunk Size : 1500
- Overlap : 200

Embeddings are generated using

```
all-MiniLM-L6-v2
```

and stored inside ChromaDB.

---

## Step 3 – Semantic Retrieval

For every clause type, a semantic query is issued.

Example queries

- termination rights
- confidentiality obligations
- limitation of liability

Top candidate chunks are retrieved from ChromaDB.

---

## Step 4 – LLM-based Chunk Selection

Instead of directly trusting semantic similarity scores, every retrieved chunk is evaluated by an LLM.

The selector decides whether a chunk actually contains the requested legal clause.

Only relevant chunks are forwarded for extraction.

This significantly reduced false **"Not Specified"** results observed during development.

---

## Step 5 – Clause Extraction

The shortlisted chunks are merged into one context block.

A second LLM extracts the clause while following strict rules.

- Preserve original legal wording
- Do not hallucinate
- Return "Not specified" only if genuinely absent

---

## Output

```json
{
    "contract_id":"...",
    "termination_clause":"...",
    "confidentiality_clause":"...",
    "liability_clause":"..."
}
```

Saved as

```
extracted_clauses.json
```

---

# Part B – Contract Summarization

Each contract is summarized into approximately **100–150 words**.

The summary includes

- Purpose of the agreement
- Responsibilities of the parties
- Major risks or penalties

---

## Direct Summarization

Contracts within the context limit are summarized directly.

---

## Map-Reduce Summarization

Larger contracts are processed using a Map-Reduce approach.

### Map Phase

Large contracts are divided into page-safe groups.

Each group is summarized independently.

### Reduce Phase

Intermediate notes are merged into a single final summary.

This avoids context window limitations while preserving important information.

---

## Output

```json
{
    "contract_id":"...",
    "summary":"..."
}
```

Saved as

```
summaries.json
```

---

# Models Used

## Embedding Model

SentenceTransformers

```
all-MiniLM-L6-v2
```

Purpose

- Semantic search
- Vector retrieval

---

## Clause Extraction

Provider

Groq API

Model

```
llama-3.3-70b-versatile
```

Used for

- Relevant chunk selection
- Clause extraction

---

## Contract Summarization

Provider

Ollama

Model

```
Qwen3.5:9B
```

Used for

- Local contract summarization

---

# Usage Tracking

The extraction pipeline records API usage.

Tracked metrics

- Total API Calls
- Prompt Tokens
- Completion Tokens
- Total Tokens

Reports are generated after processing.

```
usage_report_tracker.json
```

and

```
summarise_usage_report.json
```

---

# Technologies Used

- Python
- PyMuPDF
- ChromaDB
- SentenceTransformers
- LangChain
- Groq API
- Ollama
- OpenAI Python SDK
- python-dotenv

---

# Challenges Faced

During development, semantic retrieval occasionally returned legally similar but contextually incorrect clauses. Although these chunks had high embedding similarity, they did not contain the actual contractual obligations, leading to incorrect extractions or "Not Specified" outputs.

To address this, an intermediate LLM-based chunk selection stage was introduced. Instead of relying solely on similarity scores, the LLM evaluates retrieved chunks and selects only those that are genuinely relevant before clause extraction. This significantly improved extraction quality across the contract dataset.

---

# Future Improvements

Possible production enhancements include

- Hybrid Retrieval (Dense + BM25)
- Confidence-based retrieval
- Parallel processing
- Prompt caching
- Batch inference
- API cost optimization

---

# How to Run

### 1. Normalize PDFs

```bash
python Normalize.py
```

### 2. Generate Embeddings

```bash
python Embeddings.py
```

### 3. Extract Clauses

```bash
python Extract_UsageT_Clauses.py
```

### 4. Generate Summaries

```bash
python Summarize.py
```

---

# Author

Raj

AI Internship Assignment
