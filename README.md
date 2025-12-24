# Confuser MVP (LLM-Powered)

A privacy-preserving query matching system that uses semantic similarity and **AI-powered intelligent text perturbation** to protect user identity while maintaining query meaning.

## 🏗️ Architecture

The Confuser MVP consists of three layers:

### Layer 1: Semantic Matching Engine (`layer1_matching.py`)
- Uses `sentence-transformers` with the `all-MiniLM-L6-v2` model
- Finds semantically similar queries from a mock database
- Returns matches only if similarity score ≥ 0.3

### Layer 2: LLM-Powered Confuser Module (`layer2_confuser.py`)
- **AI-powered privacy perturbation using DeepSeek API**
- Intelligently replaces identifying information while preserving meaning:
  - **Locations**: Replaced with plausible alternatives
  - **Roles/Professions**: Replaced with related positions
  - **Ages/Dates**: Replaced with similar values
  - **Emotions/Problems**: Preserved intact
- Much smarter than rule-based replacements

### Layer 3: User Bridge (`main.py`)
- Interactive CLI interface
- Securely collects DeepSeek API key (using `getpass`)
- Integrates semantic matching and LLM-based privacy perturbation
- Displays both protected and original views (for debugging)

## 🚀 Setup Instructions

### 1. Get Your DeepSeek API Key

1. Visit [https://platform.deepseek.com/](https://platform.deepseek.com/)
2. Sign up for an account
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key (you'll need it when running the system)

**Note**: DeepSeek offers free credits for new users, making it cost-effective for testing.

### 2. Create Virtual Environment

```bash
python3 -m venv venv
```

### 3. Activate Virtual Environment

**macOS/Linux:**
```bash
source venv/bin/activate
```

**Windows:**
```bash
venv\Scripts\activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

**Note:** The first run will download the `all-MiniLM-L6-v2` model (~80MB). This is a one-time download.

## 📖 Usage

### Run the Interactive System

```bash
python main.py
```

**On first run, you'll be prompted for your API key:**
```
=== CONFUSER MVP SYSTEM (LLM-Powered) ===

🔑 DeepSeek API Configuration
--------------------------------------------------
This version uses DeepSeek AI for intelligent privacy protection.
You need a DeepSeek API key to use this feature.

Get your API key at: https://platform.deepseek.com/

Enter your DeepSeek API key (or press ENTER to skip): [input hidden]
✅ API key received!
```

**Example interaction:**
```
🔍 Enter your query: I am a software engineer in Seattle

--------------------------------------------------

🔎 Searching for similar queries...
✅ Found a similar peer query (similarity: 64.50%)

🤖 Applying AI-powered privacy protection...

🛡️  PROTECTED VIEW (Privacy-Preserved by AI):
   I am a 31-year-old backend developer in Austin feeling burnt out.

   [Text successfully transformed by LLM]

🔓 ORIGINAL VIEW (Debug - Would not be shown to users):
   I am a 28yo software engineer in Seattle feeling burnt out.

--------------------------------------------------
```

Type `exit` to quit the application.

### Run Verification Tests

**Note**: The original verification script (`verify_mvp.py`) was designed for the mock version and won't work with the LLM version. Manual testing is required.

## 📁 Project Structure

```
Confuser_MVP/
├── README.md                      # This file
├── requirements.txt               # Python dependencies (includes openai)
├── main.py                        # Main CLI interface (Layer 3)
├── layer1_matching.py             # Semantic matching engine
├── layer2_confuser.py             # LLM-powered privacy perturbation
├── verify_mvp.py                  # Legacy tests (for mock version)
├── CONFUSER_SPEC.md              # Original MVP specification
├── CONFUSER_LLM_UPGRADE.md       # LLM upgrade specification
└── venv/                          # Virtual environment
```

## 🔍 How It Works

1. **API Key Collection**: System securely collects your DeepSeek API key
2. **User Input**: You enter a query through the CLI
3. **Semantic Search**: Layer 1 finds the most similar query from the mock database
4. **AI Privacy Protection**: Layer 2 sends the match to DeepSeek API with a specialized prompt
5. **Intelligent Transformation**: The LLM intelligently replaces identifying details while preserving meaning
6. **Display**: Both the protected and original views are shown (in production, only protected view would be shown)

## 🎯 Mock Database Queries

The system currently includes 5 diverse mock queries:
1. "I am a 28yo software engineer in Seattle feeling burnt out."
2. "My iPhone battery drains too fast after update."
3. "How do I make authentic carbonara?"
4. "I hate my boss in New York, he is too demanding."
5. "Best hiking trails near Denver?"

## 🤖 LLM System Prompt

The DeepSeek API is instructed with:

```
You are the 'Confuser' privacy module.
Input: A user's personal query.
Task: Rewrite the query to protect privacy while maintaining semantic meaning.
Rules:
- Replace specific Locations with plausible alternatives (e.g., Seattle -> Austin).
- Replace specific Ages/Dates with plausible alternatives (e.g., 28 -> 31).
- Replace specific Professions with related roles (e.g., Engineer -> Developer).
- KEEP the core problem/emotion intact (e.g., "burnt out", "stress").
- OUTPUT ONLY THE TRANSFORMED TEXT. NO EXPLANATIONS.
```

## 🔧 Configuration

- **Similarity Threshold**: Adjust in `SemanticMatcher.__init__()` (default: 0.3)
- **Mock Database**: Update `MOCK_DB` in `layer1_matching.py`
- **LLM Model**: Change `model="deepseek-chat"` in `layer2_confuser.py` if needed
- **API Endpoint**: Modify `base_url` parameter in `perturb_text()` for different providers

## ⚠️ Important Notes

- **API Key Required**: This version requires a valid DeepSeek API key
- **Costs**: DeepSeek offers free credits; check their pricing for production use
- **Privacy**: Your API key is never stored; you enter it each session
- **Network Required**: The LLM calls require internet connectivity
- In production, the "Original View" would not be shown to users
- The system demonstrates intelligent, context-aware privacy preservation

## 🐛 Troubleshooting

**Issue**: "No API key provided" error  
**Solution**: Make sure to enter your DeepSeek API key when prompted

**Issue**: "LLM API Error: Authentication failed"  
**Solution**: Verify your API key is correct and active on the DeepSeek platform

**Issue**: "LLM API Error: Connection error"  
**Solution**: Check your internet connection and firewall settings

**Issue**: Model download fails  
**Solution**: Check your internet connection; the sentence-transformer model downloads on first run

**Issue**: Low similarity scores  
**Solution**: The mock database is small; try queries similar to the 5 mock entries

**Issue**: API timeout  
**Solution**: DeepSeek API might be slow; wait a moment and try again

## 🆚 Comparison: Mock vs LLM Version

| Feature | Mock Version | LLM Version |
|---------|--------------|-------------|
| **Privacy Logic** | Rule-based dictionaries | AI-powered intelligent replacement |
| **Flexibility** | Fixed replacements only | Context-aware transformations |
| **API Key** | Not required | DeepSeek API key required |
| **Cost** | Free | Free credits available, then paid |
| **Internet** | Optional (only for model download) | Required for each query |
| **Intelligence** | Low (simple string replacement) | High (understands context) |

## 📝 License

This is an MVP demonstration project.
