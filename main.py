"""
Layer 3: User Bridge - Main CLI Interface (LLM-Powered)

This is the main entry point for the Confuser MVP system with LLM integration.
It integrates Layer 1 (semantic matching) and Layer 2 (LLM-based privacy perturbation)
to provide an interactive CLI experience.
"""

from layer1_matching import SemanticMatcher
from layer2_confuser import perturb_text, get_perturbation_stats
import getpass
import sys


def print_banner():
    """Print the welcome banner for the Confuser system."""
    print("\n" + "=" * 50)
    print("=== CONFUSER MVP SYSTEM (LLM-Powered) ===")
    print("=" * 50)
    print("\nPrivacy-preserving query matching with AI")
    print("Type 'exit' to quit\n")


def print_separator():
    """Print a visual separator."""
    print("-" * 50)


def get_api_key():
    """
    Collect API key from the user securely.
    
    Returns:
        str: The API key, or None if user wants to skip
    """
    print("🔑 DeepSeek API Configuration")
    print("-" * 50)
    print("This version uses DeepSeek AI for intelligent privacy protection.")
    print("You need a DeepSeek API key to use this feature.")
    print("\nGet your API key at: https://platform.deepseek.com/")
    print("\nOptions:")
    print("  1. Enter your API key (input will be hidden)")
    print("  2. Press ENTER to skip (system will not function)")
    print()
    
    try:
        api_key = getpass.getpass("Enter your DeepSeek API key (or press ENTER to skip): ").strip()
        
        if not api_key:
            print("\n⚠️  No API key provided. The system cannot function without it.")
            return None
        
        print("✅ API key received!")
        return api_key
        
    except KeyboardInterrupt:
        print("\n\n⚠️  API key input cancelled.")
        return None


def main():
    """
    Main application loop for the Confuser MVP system with LLM integration.
    
    Workflow:
    1. Collect API key from user
    2. Initialize semantic matcher
    3. Accept user input via CLI
    4. Find semantic matches in the database
    5. Use LLM to perturb matching queries intelligently
    6. Display both protected and original views
    """
    try:
        # Print welcome banner
        print_banner()
        
        # Get API key from user
        api_key = get_api_key()
        
        if not api_key:
            print("\n❌ Cannot proceed without API key. Exiting.\n")
            return 1
        
        print_separator()
        
        # Initialize the semantic matcher (this will load the model)
        print("\n⚙️  Initializing Confuser system...")
        matcher = SemanticMatcher()
        print_separator()
        
        # Main interaction loop
        while True:
            try:
                # Get user input
                user_query = input("\n🔍 Enter your query: ").strip()
                
                # Check for exit command
                if user_query.lower() == 'exit':
                    print("\n👋 Thank you for using Confuser MVP. Goodbye!\n")
                    break
                
                # Skip empty queries
                if not user_query:
                    print("⚠️  Please enter a valid query.")
                    continue
                
                print_separator()
                
                # Layer 1: Find semantic match
                print("\n🔎 Searching for similar queries...")
                match, score = matcher.find_best_match(user_query)
                
                if match:
                    # Match found
                    print(f"✅ Found a similar peer query (similarity: {score:.2%})")
                    print()
                    
                    try:
                        # Layer 2: Use LLM to perturb the matched text
                        print("🤖 Applying AI-powered privacy protection...")
                        perturbed = perturb_text(match, api_key)
                        stats = get_perturbation_stats(match, perturbed)
                        
                        # Display results
                        print()
                        print("🛡️  PROTECTED VIEW (Privacy-Preserved by AI):")
                        print(f"   {perturbed}")
                        print()
                        
                        if stats['texts_differ']:
                            print(f"   [Text successfully transformed by LLM]")
                            print()
                        
                        print("🔓 ORIGINAL VIEW (Debug - Would not be shown to users):")
                        print(f"   {match}")
                        
                    except Exception as e:
                        print(f"\n⚠️  LLM API Error: {e}")
                        print("   Could not perturb the text. This might be due to:")
                        print("   - Invalid API key")
                        print("   - Network issues")
                        print("   - API rate limits")
                        print("\n   Original match (unperturbed):")
                        print(f"   {match}")
                
                else:
                    # No match found
                    print("❌ No similar queries found in the database.")
                    print("   (Similarity score was below threshold)")
                
                print_separator()
                
            except KeyboardInterrupt:
                print("\n\n👋 Interrupted. Goodbye!\n")
                break
            except Exception as e:
                print(f"\n⚠️  Error processing query: {e}")
                print("   Please try again.")
                print_separator()
        
    except Exception as e:
        print(f"\n❌ Fatal error initializing Confuser system: {e}")
        print("   Please check your dependencies and try again.\n")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
