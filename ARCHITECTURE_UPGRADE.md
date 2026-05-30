# Project Silence - Architecture Upgrade V2.0

> Legacy design note: This historical planning document predates the current Fortress architecture and does not describe the current Fortress production, safety, compliance, or medical posture. Use `README.md` and `docs/` as the canonical public documentation.

## 🎯 Objectives
This document outlines the roadmap to fix the "Privacy Isolation Bug" and implement the "Semantic Router" and "Quality Feedback Loop" features.

**Core Goals:**
1.  **Fix Isolation Bug:** Create a public "Global Square" so users can actually see each other's decoys (anonymously).
2.  **Layer 0 (Router):** Stop generating decoys for simple factual questions (e.g., "What is aspirin?").
3.  **Quality Loop:** Only publish decoys/summaries from conversations that users mark as "Helpful".

---

## 🏗️ Phase 1: Database Refactoring ( The "Global Square" )

**Problem:** Currently, RLS locks all data per user. User B cannot search User A's decoys.
**Solution:** Separate "Private Chat" from "Public Decoys".

### 1. New Table: `global_decoys`
Create a new table strictly for public consumption.

| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | uuid | Primary Key |
| `content` | text | The obfuscated decoy message |
| `summary` | text | AI-generated summary of the solution (New!) |
| `topics` | text[] | Array of keywords/tags |
| `embedding` | vector | For semantic search |
| `created_at` | timestamp | Creation time |
| **NO user_id** | - | **CRITICAL:** Do not link to specific users to ensure anonymity. |

### 2. RLS Policies for `global_decoys`
- **SELECT**: `true` (Enable for ALL authenticated users).
- **INSERT**: `auth.role() = 'authenticated'` (Allow system to write).
- **UPDATE**: `auth.role() = 'authenticated'` (Allow system to update summary).

---

## 🧠 Phase 2: Layer 0 - Semantic Router ( The "Traffic Cop" )

**Logic:** Optimize UX and cost by distinguishing between "Simple Facts" and "Complex Scenarios".

### New Module: `layer0_router.py`
Implement a fast LLM call (e.g., gpt-4o-mini) to classify the user query.

* **Input:** User Query
* **Prompt:** "Classify this query as 'FACTUAL' (simple knowledge) or 'EXPERIENTIAL' (personal/complex). Return only label."
* **Logic Flow:**
    * **Case A: FACTUAL** -> Skip matching. Skip Decoy generation. Just Chat.
    * **Case B: EXPERIENTIAL** -> Execute full pipeline (Layer 1 Matching -> Layer 2 Obfuscation -> Layer 4 Decoy Generation).

---

## 🔄 Phase 3: The Quality & Feedback Loop

**Logic:** Don't publish everything. Only publish high-quality, solved problems. Replace raw chats with AI summaries.

### 1. UI Changes (Sidebar)
Add a "Session Feedback" control in `app.py`:
* Button: "End Chat & Rate"
* Options: "👍 This helped" / "👎 Not helpful"

### 2. Workflow Logic
1.  **During Chat:**
    * Decoy is generated in the background but **NOT** inserted into `global_decoys` yet (or inserted with `status='pending'`).
2.  **User Clicks "👎 Not helpful":**
    * Discard/Delete the pending decoy.
    * Do not generate summary.
3.  **User Clicks "👍 This helped":**
    * **Trigger Summary Agent:** Send chat history to LLM.
    * **Prompt:** "Summarize the user's medical concern and the provided solution in 3 sentences. Keep it anonymous."
    * **Publish:** Insert the **Decoy Query** + **Summary** into the public `global_decoys` table.

---

## 🚀 Execution Plan for AI Assistant

**Step 1:** Run SQL to create `global_decoys` and set RLS policies.
**Step 2:** Create `layer0_router.py` and integrate it into the main `app.py` loop.
**Step 3:** Update `layer4_decoy_factory.py` to support "Summary Generation".
**Step 4:** Update `app.py` UI to include the Feedback/Voting mechanism.
**Step 5:** Update `layer1_matching.py` to search `global_decoys` and return `summary` instead of raw messages.
