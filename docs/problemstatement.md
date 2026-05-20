# Problem Statement: AI-Powered Restaurant Recommendation System

## Project context

This project builds a **restaurant discovery and recommendation application** inspired by platforms like Zomato. Users often face too many choices and inconsistent filters when deciding where to eat. A typical listing page shows names, ratings, and price bands, but it does not explain *why* a place fits a specific mood, budget, or occasion.

The application combines:

- A **structured restaurant dataset** (real-world Zomato-style records)
- **Rule-based filtering** on hard constraints (location, budget, cuisine, minimum rating)
- A **Large Language Model (LLM)** to rank, explain, and present recommendations in natural language

The goal is a small end-to-end system that demonstrates how structured data and generative AI work together—not a production clone of Zomato, but a credible prototype that could be extended later (API, web UI, auth, etc.).

---

## Problem we are solving

**Finding a restaurant that matches nuanced preferences is slow and frustrating.**

Users know constraints (e.g. “Italian in Bangalore, mid budget, rating ≥ 4, good for families”) but product UIs usually return long, undifferentiated lists. Ranking is often opaque (popularity or star sort only), and there is little narrative guidance (“this fits your budget and is known for quick service”).

| Pain point | How this project addresses it |
|------------|--------------------------------|
| Information overload | Filter dataset first; show only a short ranked list |
| Opaque matching | LLM explains why each option fits stated preferences |
| Rigid filters | Optional free-text preferences (e.g. “quiet”, “kid-friendly”) via the prompt |
| Cold start on a new city | Dataset-backed suggestions instead of hallucinated venues |

---

## Objective

Design and implement an application that:

1. Accepts user preferences (location, budget, cuisine, minimum rating, and optional extras)
2. Loads and preprocesses a real-world restaurant dataset
3. Filters candidates with deterministic logic
4. Uses an LLM to rank options and generate human-like explanations
5. Displays clear, actionable results to the user

---

## Data source

**Dataset:** [ManikaSaini/zomato-restaurant-recommendation](https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation) on Hugging Face

**Fields to use (after preprocessing):** restaurant name, location/city, cuisines, approximate cost for two, aggregate rating, and any other columns needed for filtering and display.

**Preprocessing expectations:**

- Handle missing or malformed values
- Normalize location and cuisine strings for consistent filtering
- Map budget tiers (low / medium / high) to dataset cost ranges

---

## System workflow

### 1. Data ingestion

- Load the Zomato dataset from Hugging Face
- Clean and normalize relevant fields
- Keep a queryable in-memory or local store for filtering (CSV/Parquet cache optional for repeat runs)

### 2. User input

Collect:

| Input | Examples |
|-------|----------|
| Location | Delhi, Bangalore |
| Budget | low, medium, high |
| Cuisine | Italian, Chinese |
| Minimum rating | e.g. 4.0 |
| Additional preferences (optional) | family-friendly, quick service, outdoor seating |

### 3. Integration layer

- Apply hard filters on structured data (location, budget, cuisine, rating)
- Cap the candidate set passed to the LLM (e.g. top N by rating) to control token cost and latency
- Build a structured prompt: user preferences + tabular summary of candidates
- Instruct the LLM to rank, justify each pick, and avoid inventing restaurants not in the candidate list

### 4. Recommendation engine

The LLM should:

- Rank filtered restaurants against stated preferences
- Explain why each recommendation fits
- Optionally provide a short comparative summary (“best value”, “highest rated”, etc.)

### 5. Output display

Present top recommendations in a readable format:

- Restaurant name  
- Cuisine(s)  
- Rating  
- Estimated cost (for two)  
- AI-generated explanation  

Output may be CLI, notebook, or simple web UI depending on implementation choice.

---

## Success criteria

The project is successful when:

- [ ] Dataset loads reliably and filters produce sensible candidate sets for common queries
- [ ] User can specify location, budget, cuisine, and minimum rating and receive at least 3 relevant suggestions when data exists
- [ ] Every recommended restaurant exists in the filtered dataset (no fabricated venues)
- [ ] Each recommendation includes a short, preference-aware explanation
- [ ] End-to-end flow runs in reasonable time for a demo-sized candidate set

---

## Scope

**In scope**

- Dataset load, clean, filter
- Preference-based filtering and LLM-based ranking/explanation
- Minimal user-facing interface to run a query and view results
- Basic error handling (no matches, API failures, invalid input)

**Out of scope (for initial version)**

- User accounts, order placement, or live Zomato API integration
- Real-time availability, maps, or reviews ingestion
- Production-scale deployment, caching layers, or A/B testing

---

## Technical considerations

- **LLM provider:** Configurable API key (e.g. OpenAI, Anthropic, or local model); prompts should stay provider-agnostic where possible
- **Cost & latency:** Limit candidates sent to the LLM; use concise prompt templates
- **Reliability:** Prefer structured filter-then-generate over asking the LLM to search the full dataset
- **Evaluation:** Manually spot-check that names, ratings, and costs in output match the filtered data

---

## Open questions / future work

- Web UI vs CLI-first delivery
- Caching embeddings or precomputed summaries per city/cuisine
- Feedback loop (“not interested”) to refine recommendations
- Multi-language explanations for Indian metro users
