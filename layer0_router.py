"""
Layer 0: Privacy Necessity Router

This module classifies incoming queries to determine whether they contain
privacy-sensitive information that requires obfuscation.

Classification Categories:
- GREETING: Social pleasantries, no privacy concern
- FACTUAL: Objective questions, no personal data
- CREATIVE: Fun/creative requests, typically no privacy concern
- STUDY: Academic questions, low privacy concern
- PERSONAL: Contains personal details, HIGH privacy concern -> Needs decoys
- AMBIGUOUS: Cannot determine, ask user for feedback

This layer prevents unnecessary decoy generation for queries that don't
need privacy protection, saving API costs and improving relevance.
"""

from openai import OpenAI
import json

# Classification prompt for Layer 0
ROUTER_SYSTEM_PROMPT = """You are the 'Privacy Router' - a classifier that determines if a query contains privacy-sensitive information.

CLASSIFICATION RULES:

1. **GREETING** - Social pleasantries with NO personal information
   - Examples: "你好", "Hi", "Merry Christmas", "谢谢", "再见"
   - Privacy Need: NONE

2. **FACTUAL** - Objective questions about facts, definitions, how-to
   - Examples: "Python怎么排序?", "什么是区块链?", "法国首都是哪里?"
   - Privacy Need: NONE
   - Key indicator: Could be asked by ANYONE, no personal context

3. **CREATIVE** - Requests for creative content, code, fun projects
   - Examples: "写首诗", "做个圣诞树网页", "推荐圣诞礼物", "帮我画个Logo"
   - Privacy Need: LOW (unless contains personal details)
   - Key indicator: Creative output request, no sensitive personal context

4. **STUDY** - Academic learning, homework help, exam prep
   - Examples: "解释量子力学", "这道积分怎么做", "帮我理解这段代码"
   - Privacy Need: LOW
   - Key indicator: Learning/educational purpose

5. **PERSONAL** - Contains personal details, emotions, or sensitive situations
   - Examples:
     - "我是XX大学的学生，GPA只有2.9..."
     - "我和老板关系很差..."
     - "我今年28岁，在北京工作，感觉很焦虑..."
     - "我被诊断出XXX病..."
   - Privacy Need: HIGH
   - Key indicators:
     - Personal pronouns + specific details (age, location, school, company)
     - Emotional states + personal context
     - Health/financial/relationship issues
     - Career/academic struggles with identifying info

6. **AMBIGUOUS** - Cannot determine, needs user feedback
   - When the query could go either way
   - When personal details are vague but might be sensitive

OUTPUT FORMAT (JSON ONLY):
{
  "category": "GREETING|FACTUAL|CREATIVE|STUDY|PERSONAL|AMBIGUOUS",
  "confidence": 0.0-1.0,
  "reasoning": "Brief explanation of classification",
  "privacy_risk": "NONE|LOW|MEDIUM|HIGH",
  "should_generate_decoy": true|false,
  "should_ask_user": true|false
}
"""

# Quick patterns for fast classification (skip LLM call)
GREETING_PATTERNS = [
    "你好", "您好", "hi", "hello", "hey", "嗨", "哈喽",
    "早上好", "晚上好", "下午好", "good morning", "good evening",
    "谢谢", "感谢", "thanks", "thank you", "thx",
    "再见", "拜拜", "bye", "goodbye", "see you",
    "圣诞快乐", "新年快乐", "merry christmas", "happy new year",
    "节日快乐", "生日快乐", "happy birthday"
]

# Patterns that suggest PERSONAL/SENSITIVE content
PERSONAL_INDICATORS = [
    # Personal identity markers
    "我是", "我叫", "我今年", "我在", "我的",
    "岁", "大学", "公司", "工作", "专业",
    # Emotional/sensitive markers
    "焦虑", "抑郁", "压力", "痛苦", "难过", "伤心",
    "烦恼", "困惑", "迷茫", "不知道该怎么",
    # Relationship markers
    "老板", "同事", "父母", "男友", "女友", "配偶", "家人",
    # Health markers
    "诊断", "病", "症状", "治疗", "医院", "医生",
    # Academic/career struggle markers
    "GPA", "成绩", "挂科", "延毕", "被拒", "失业", "裁员",
    # Financial markers
    "贷款", "债务", "工资", "存款"
]


def quick_classify(query: str) -> dict:
    """
    Fast pattern-based classification for obvious cases.
    Returns None if LLM classification is needed.

    Args:
        query: The user's query text

    Returns:
        dict with classification result, or None if LLM needed
    """
    query_lower = query.lower().strip()

    # Check for greetings (very short + matches pattern)
    if len(query_lower) < 20:
        for pattern in GREETING_PATTERNS:
            if pattern in query_lower:
                return {
                    "category": "GREETING",
                    "confidence": 0.95,
                    "reasoning": "Detected greeting pattern",
                    "privacy_risk": "NONE",
                    "should_generate_decoy": False,
                    "should_ask_user": False
                }

    # Check for personal indicators
    personal_score = sum(1 for p in PERSONAL_INDICATORS if p in query)
    if personal_score >= 3:
        return {
            "category": "PERSONAL",
            "confidence": 0.85,
            "reasoning": f"Detected {personal_score} personal indicators",
            "privacy_risk": "HIGH",
            "should_generate_decoy": True,
            "should_ask_user": False
        }

    # Need LLM for nuanced classification
    return None


def classify_query(query: str, api_key: str, base_url: str = "https://api.deepseek.com") -> dict:
    """
    Classify a query to determine privacy sensitivity and whether decoy generation is needed.

    Args:
        query: The user's query text
        api_key: DeepSeek API key
        base_url: API base URL

    Returns:
        dict with classification result
    """
    # Try quick pattern matching first
    quick_result = quick_classify(query)
    if quick_result:
        print(f"🚦 [L0] Quick classification: {quick_result['category']} (confidence: {quick_result['confidence']:.2f})")
        return quick_result

    # Fall back to LLM classification
    try:
        print(f"🚦 [L0] Using LLM classification for query: {query[:50]}...")

        client = OpenAI(api_key=api_key, base_url=base_url)

        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": ROUTER_SYSTEM_PROMPT},
                {"role": "user", "content": f"Classify this query:\n\n{query}"}
            ],
            temperature=0.1,  # Low temp for consistent classification
            response_format={"type": "json_object"},
            max_tokens=500
        )

        content = response.choices[0].message.content
        if not content:
            return _default_ambiguous()

        result = json.loads(content)

        # Validate required fields
        required_fields = ["category", "confidence", "privacy_risk", "should_generate_decoy"]
        if not all(field in result for field in required_fields):
            print(f"⚠️ [L0] Missing fields in LLM response, using defaults")
            return _default_ambiguous()

        print(f"🚦 [L0] LLM classification: {result['category']} (confidence: {result['confidence']:.2f}, privacy: {result['privacy_risk']})")
        return result

    except Exception as e:
        print(f"❌ [L0] Classification error: {e}")
        # Default to generating decoys on error (fail-safe for privacy)
        return _default_ambiguous()


def _default_ambiguous() -> dict:
    """Return default ambiguous classification (fail-safe)."""
    return {
        "category": "AMBIGUOUS",
        "confidence": 0.5,
        "reasoning": "Could not classify, defaulting to safe behavior",
        "privacy_risk": "MEDIUM",
        "should_generate_decoy": True,  # Fail-safe: generate decoy when uncertain
        "should_ask_user": True
    }


def should_generate_decoy(classification: dict) -> bool:
    """
    Determine if decoy generation should proceed based on classification.

    Args:
        classification: Result from classify_query()

    Returns:
        bool: True if decoys should be generated
    """
    return classification.get("should_generate_decoy", True)


def get_user_feedback_prompt(classification: dict) -> str:
    """
    Generate a user feedback prompt for ambiguous cases.

    Args:
        classification: Result from classify_query()

    Returns:
        str: Feedback prompt to show user, or empty string if not needed
    """
    if not classification.get("should_ask_user", False):
        return ""

    category = classification.get("category", "AMBIGUOUS")

    if category == "AMBIGUOUS":
        return "🔒 This conversation may contain personal information. Would you like to enable privacy protection (generate anonymous decoys)?"
    elif category in ["CREATIVE", "STUDY"]:
        return "💡 This appears to be a creative/study query. Enable privacy protection anyway?"

    return ""


# Convenience function for integration
def route_query(query: str, api_key: str) -> tuple:
    """
    Main entry point for Layer 0 routing.

    Args:
        query: User's query
        api_key: DeepSeek API key

    Returns:
        tuple: (should_generate_decoy: bool, classification: dict, feedback_prompt: str)
    """
    classification = classify_query(query, api_key)
    should_decoy = should_generate_decoy(classification)
    feedback = get_user_feedback_prompt(classification)

    return should_decoy, classification, feedback


if __name__ == "__main__":
    # Test cases
    test_queries = [
        "你好",
        "Python怎么排序列表?",
        "帮我用网页做一个圣诞树",
        "我叫林浩，今年23岁，是广州医科大学临床医学专业大四学生，GPA只有2.9，我想问：以我这种成绩还能申请美国医学博士吗？",
        "解释一下量子纠缠",
        "我最近和老板关系很差，不知道该怎么办",
    ]

    print("=" * 60)
    print("Layer 0 Router - Test Cases")
    print("=" * 60)

    for q in test_queries:
        print(f"\nQuery: {q[:50]}...")
        result = quick_classify(q)
        if result:
            print(f"  Quick: {result['category']} | Privacy: {result['privacy_risk']} | Decoy: {result['should_generate_decoy']}")
        else:
            print(f"  Quick: None (needs LLM)")
