"""
Layer 2: Confuser Module (LLM-Powered)

This module implements LLM-based semantic perturbation using DeepSeek API
to protect user privacy by intelligently replacing identifying information
while maintaining semantic meaning.
"""

from openai import OpenAI
import re


# System prompt for the LLM
CONFUSER_SYSTEM_PROMPT = """You are the 'Confuser' privacy module.
Input: A user's personal query.
Task: Rewrite the query to protect privacy while maintaining semantic meaning.
Rules:
- Replace specific Locations with plausible alternatives (e.g., Seattle -> Austin).
- Replace specific Ages/Dates with plausible alternatives (e.g., 28 -> 31).
- Replace specific Professions with related roles (e.g., Engineer -> Developer).
- KEEP the core problem/emotion intact (e.g., "burnt out", "stress").
- OUTPUT ONLY THE TRANSFORMED TEXT. NO EXPLANATIONS."""


def perturb_text(text, api_key, base_url="https://api.deepseek.com"):
    """
    Perturb the input text using LLM-based semantic transformation.
    
    This function uses the DeepSeek API to intelligently replace identifying
    information while preserving the semantic meaning and emotional content.
    
    Args:
        text (str): The original text to perturb
        api_key (str): DeepSeek API key
        base_url (str): API endpoint URL (default: "https://api.deepseek.com")
        
    Returns:
        str: The perturbed text with identifying information replaced
        
    Raises:
        Exception: If API call fails (propagates for error handling upstream)
        
    Example:
        >>> api_key = "your-api-key"
        >>> perturb_text("I am a 28yo software engineer in Seattle", api_key)
        "I am a 31yo backend developer in Austin feeling burnt out."
    """
    try:
        if not text:
            return text
        
        if not api_key:
            raise ValueError("API key is required for LLM-based perturbation")
        
        # Initialize OpenAI client with DeepSeek endpoint
        client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        
        # Call the API with the system prompt
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": CONFUSER_SYSTEM_PROMPT},
                {"role": "user", "content": text}
            ],
            temperature=0.7,  # Some creativity for plausible alternatives
            max_tokens=500
        )
        
        # Extract the perturbed text from the response
        perturbed = response.choices[0].message.content.strip()
        
        return perturbed
        
    except Exception as e:
        # Re-raise with more context
        raise Exception(f"LLM perturbation failed: {str(e)}")


def get_perturbation_stats(original, perturbed):
    """
    Get basic statistics about text transformation.
    
    Note: With LLM-based perturbation, we can't know exactly what categories
    were changed, so this provides a simple character/word difference metric.
    
    Args:
        original (str): Original text
        perturbed (str): Perturbed text
        
    Returns:
        dict: Basic statistics about the transformation
    """
    try:
        stats = {
            'original_length': len(original),
            'perturbed_length': len(perturbed),
            'length_difference': abs(len(perturbed) - len(original)),
            'texts_differ': original.strip() != perturbed.strip(),
            'total_changes': 1 if original.strip() != perturbed.strip() else 0
        }
        
        return stats
        
    except Exception as e:
        print(f"Error calculating perturbation stats: {e}")
        return {'total_changes': 0, 'texts_differ': False}



# System prompt for the Sanitizer
SANITIZER_SYSTEM_PROMPT = """You are a 'Response Sanitizer' for a privacy system.
Input: 
1. An AI response (which might reference specific user details).
2. The 'Obfuscated Query' (the persona we WANT the AI to be talking to).

Task: Rewrite the AI response so it contextually aligns with the 'Obfuscated Query' persona.
Rules:
- If the original response mentions attributes (like "As a surgeon..."), CHANGE them to match the Obfuscated Query (e.g., "As a teacher...").
- KEEP the core advice and sentiment exactly the same.
- Do NOT add any preamble or "Here is the sanitized version".
- OUTPUT ONLY the sanitized response text."""


def sanitize_response_consistency(original_response, obfuscated_query, api_key, base_url="https://api.deepseek.com"):
    """
    Sanitize the AI response to be consistent with the obfuscated persona.
    
    Args:
        original_response (str): The raw response from the AI
        obfuscated_query (str): The obfuscated query (defining the target persona)
        api_key (str): DeepSeek API key
        base_url (str): API endpoint URL
        
    Returns:
        str: The sanitized response
    """
    try:
        if not original_response or not obfuscated_query:
            return original_response
            
        print(f"Sanitizing response...")
            
        # Initialize OpenAI client
        client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        
        # Prepare the conversation context
        user_content = f"""
Original Response: "{original_response}"
Obfuscated Query: "{obfuscated_query}"
"""
        
        # Call the API
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": SANITIZER_SYSTEM_PROMPT},
                {"role": "user", "content": user_content}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        sanitized = response.choices[0].message.content.strip()
        return sanitized
        
    except Exception as e:
        print(f"Sanitization failed: {e}")
        return original_response
    except Exception as e:
        print(f"Sanitization failed: {e}")
        return original_response


# System prompt for Atomic Pair Perturbation
PAIR_PERTURB_SYSTEM_PROMPT = """You are a privacy masker. 
Input: A Query and a Response. 
Task: Identify sensitive entities in the Query (Name, Location, Age, Role). Replace them with consistent alternatives in BOTH the Query and the Response. 
- Ensure the context remains consistent (e.g., if "London" -> "Manchester" in Query, "London" must also be "Manchester" in Response).
- Output ONLY valid JSON: {"query": "...", "response": "..."}."""


def perturb_pair(query, response_text, api_key, base_url="https://api.deepseek.com"):
    """
    Perturb a Query/Response pair atomically to ensure entity consistency.
    
    Args:
        query (str): The original user query
        response_text (str): The original AI response
        api_key (str): DeepSeek API key
        
    Returns:
        dict: {'query': '...', 'response': '...'} with consistent obfuscation
    """
    try:
        if not query or not response_text:
            return {'query': query, 'response': response_text}
            
        # Initialize OpenAI client
        client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        
        user_content = f"Query: {query}\nResponse: {response_text}"
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": PAIR_PERTURB_SYSTEM_PROMPT},
                {"role": "user", "content": user_content}
            ],
            temperature=0.7,
            response_format={ "type": "json_object" },
            max_tokens=1000
        )
        
        import json
        result = json.loads(response.choices[0].message.content)
        return result
        
    except Exception as e:
        print(f"Pair perturbation failed: {e}")
        # Fallback to returning originals if anything fails
        return {'query': query, 'response': response_text}


# Legacy compatibility: keep the old dictionaries for reference
# These are no longer used in LLM mode but kept for documentation
LEGACY_LOCATIONS = {
    "Seattle": "Austin",
    "New York": "Chicago",
    "London": "Manchester",
    "San Francisco": "Los Angeles",
    "Denver": "Boulder"
}

LEGACY_ROLES = {
    "software engineer": "backend developer",
    "doctor": "nurse practitioner",
    "student": "researcher",
    "boss": "manager"
}

LEGACY_AGES = {
    "28": "31",
    "25": "23",
    "40": "45"
}


if __name__ == "__main__":
    # Test the confuser module
    print("\n=== Testing LLM-Powered Confuser Module ===\n")
    print("This module now requires a DeepSeek API key.")
    print("To test, run main.py with your API key.\n")
    print("System Prompt:")
    print("-" * 60)
    print(CONFUSER_SYSTEM_PROMPT)
    print("-" * 60)
    print("\nThe LLM will intelligently replace identifying information")
    print("while preserving semantic meaning and emotional content.")
