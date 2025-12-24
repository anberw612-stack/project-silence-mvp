# Confuser Project: Web App Expansion (Streamlit + SQLite)

## 1. Goal
Convert the current CLI script into a **Web-based Chat Application** using `Streamlit`.
Enable "Cross-User Knowledge Sharing" where users can see confused versions of past conversations from a real database.

## 2. Tech Stack
- **Frontend:** `streamlit` (Chat interface).
- **Database:** `sqlite3` (Built-in Python library) to store chat history permanently.
- **Existing Logic:** Reuse `layer1_matching.py` and `layer2_confuser.py`.

## 3. Implementation Steps

### Step 1: Database Setup (`database_manager.py`)
Create a new file `database_manager.py` to handle SQLite operations.
- **Function `init_db()`**: Create a table `conversations` with columns:
  - `id` (Primary Key)
  - `original_query` (Text, the user's raw input)
  - `ai_response` (Text, the answer DeepSeek gave)
  - `timestamp`
- **Function `save_conversation(query, response)`**: Insert new chat logs.
- **Function `get_all_queries()`**: Return all stored queries for Layer 1 matching.
- **Function `get_response_by_query(query_text)`**: Retrieve the specific AI response associated with a query.

### Step 2: The Web App (`app.py`)
Create `app.py` to replace `main.py` as the entry point.

**UI Layout:**
1. **Sidebar:**
   - Input field for API Key (Password type).
   - "Debug Mode" checkbox (to show original/confused comparison).
2. **Main Area (Chat Interface):**
   - Use `st.chat_message` to display chat history.
   - Use `st.chat_input` for user input.

**Logic Flow (The "User Loop"):**
1. User enters `query`.
2. **Layer 1 Check:** Load all queries from `database_manager`. Find the most similar one using `layer1_matching`.
3. **If Match Found (Simulating User B seeing User A's data):**
   - Retrieve User A's `original_query` and `ai_response` from DB.
   - **Layer 2 Action:** Call `layer2_confuser.perturb_text` to anonymize User A's `original_query`.
   - **Display:** Show an "💡 Insight form a Peer" box:
     - "Someone else asked: [Confused Query]"
     - "AI Answered: [Original AI Response]" (Note: In a full prod, response implies context, but for MVP keep response as is or confuse it too if sensitive).
4. **Normal Chat:**
   - Send current user's `query` to DeepSeek (standard chat).
   - Display answer.
   - **Save:** Call `database_manager.save_conversation` to store *this* user's data for future users.

### Step 3: Dependencies
- Update `requirements.txt` to include `streamlit`.
- Install new requirements.

## 4. Execution Command
After coding, tell the user to run: `streamlit run app.py`
