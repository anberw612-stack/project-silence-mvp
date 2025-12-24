# Confuser MVP: LLM Upgrade Specification

## Task
Rewrite ONLY `layer2_confuser.py` to use a real LLM for semantic perturbation.

## Specifications for `layer2_confuser.py`
1. **Library**: Use `openai` client (standard interface for DeepSeek/OpenAI).
2. **Function Signature**: `perturb_text(text, api_key, base_url="https://api.deepseek.com")`
3. **System Prompt**:
   """
   You are the 'Confuser' privacy module.
   Input: A user's personal query.
   Task: Rewrite the query to protect privacy while maintaining semantic meaning.
   Rules:
   - Replace specific Locations with plausible alternatives (e.g., Seattle -> Austin).
   - Replace specific Ages/Dates with plausible alternatives (e.g., 28 -> 31).
   - Replace specific Professions with related roles (e.g., Engineer -> Developer).
   - KEEP the core problem/emotion intact (e.g., "burnt out", "stress").
   - OUTPUT ONLY THE TRANSFORMED TEXT. NO EXPLANATIONS.
   """
4. **Logic**:
   - Initialize `OpenAI` client with the key and base_url.
   - Call `client.chat.completions.create` (model="deepseek-chat").
   - Return the `content` from the response.

## Specifications for `main.py` (Update needed)
- Update the workflow to ask the user for their API Key at the start (use `getpass` or simple `input`).
- Pass this key to the `perturb_text` function in Layer 2.
