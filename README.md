# Alex - Virtual Voice Assistant

A LiveKit-based silent voice assistant that joins calls as a passive listener and only responds when directly prompted with a wake word.

## 🎯 Overview

**Alex** is a virtual assistant that:
- ✅ Joins calls silently without greeting or interruption
- ✅ Listens passively to all conversations
- ✅ Activates only when prompted with wake word ("hey alex" or "alex")
- ✅ Provides helpful, concise responses
- ✅ Automatically returns to silent listening mode after responding
- ✅ Maintains conversation context throughout the call

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
uv sync
```

### 2. Configure Environment

```bash
cp .env.example .env.local
# Edit .env.local with your API keys
```

Required API keys:
- **LiveKit**: [cloud.livekit.io](https://cloud.livekit.io/)
- **OpenAI**: [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
- **Deepgram**: [console.deepgram.com](https://console.deepgram.com/)
- **Cartesia**: [play.cartesia.ai/keys](https://play.cartesia.ai/keys)

### 3. Download Models

```bash
uv run src/agent.py download-files
```

### 4. Run Alex

**Test in Terminal:**
```bash
uv run src/agent.py console
```

**Development Mode:**
```bash
uv run src/agent.py dev
```

**Production:**
```bash
uv run src/agent.py start
```

---

## 💡 How Alex Works

### Silent Listening Mode (Default)

When Alex joins a call:
1. **No greeting** - Alex doesn't announce their presence
2. **Passive listening** - All speech is transcribed but not processed
3. **No responses** - Alex stays completely silent
4. **Context aware** - Maintains memory of the conversation

### Wake Word Activation

Alex responds when hearing:
- **"Hey Alex"** - Primary wake word
- **"Alex"** - Alternative wake word

### Response & Reset

After activation:
1. Alex processes only the query **after** the wake word
2. Generates and speaks a helpful response
3. **Automatically returns to silent mode**
4. Waits for next wake word prompt

---

## 🎬 Example Usage

### Example 1: Basic Assistance

```
[Call in progress with multiple participants]

Participant A: "So I think we should use PostgreSQL for this."
Participant B: "Yeah, that makes sense."

User: "Hey Alex, what do you think about using PostgreSQL?"

Alex: "PostgreSQL is an excellent choice for this use case. It's highly reliable, 
       supports advanced features like JSON columns and full-text search, and has 
       strong ACID compliance. It's particularly well-suited for applications 
       requiring complex queries and data integrity."

[Alex returns to silent mode]

Participant A: "Great, let's go with that then."
[Alex stays silent - no wake word]
```

### Example 2: Context Awareness

```
[Earlier in the call]
Participant: "We're building a mobile app for customer bookings."

[Later in the call]
User: "Alex, what tech stack would you recommend?"

Alex: "For your customer booking mobile app, I'd recommend React Native for 
       cross-platform development, Node.js with Express for the backend, and 
       PostgreSQL for the database. This stack gives you code reusability across 
       iOS and Android while maintaining strong performance and scalability."

[Alex remembers the earlier context about the mobile booking app]
```

---

## 🔧 Technical Architecture

### Wake Word Detection System

```
User Speech → Deepgram STT → stt_node() Filter
                                    ↓
                        ┌───────────┴───────────┐
                        │                       │
                   Wake Word?              Wake Word?
                      NO                       YES
                        │                       │
                    Discard              Extract query
                  (Stay Silent)          after wake word
                                              ↓
                                         Process query
                                              ↓
                                        Generate response
                                              ↓
                                      Return to silent mode
```

### State Management

Alex operates in three states:

1. **SILENT** (Default)
   - Transcribing speech but not processing
   - Looking for wake word
   - No responses generated

2. **ACTIVE** (Wake word detected)
   - Processing current utterance
   - Extracting query after wake word
   - Preparing to respond

3. **RESPONDING** (Generating output)
   - LLM generating response
   - TTS speaking response
   - Will reset to SILENT after completion

---

## 🛠️ Alex's Capabilities

### Core Expertise

✅ **Technical Guidance**
- Technology stack recommendations
- Architecture patterns and best practices
- Integration approaches
- Performance and scalability advice

✅ **Business & Strategy**
- Project planning and timelines
- Resource allocation
- Risk assessment
- ROI analysis

✅ **Problem Solving**
- Debugging assistance
- Alternative approaches
- Trade-off analysis
- Best practice recommendations

### Available Tools

#### 1. Remember Participant Name
```python
@function_tool
async def remember_participant_name(self, context: RunContext, name: str):
    """Remember participant names for personalized interaction"""
```

#### 2. Take Notes
```python
@function_tool
async def take_note(self, context: RunContext, note: str):
    """Take notes about important information during the call"""
```

---

## ⚙️ Configuration

### Wake Words

Modify wake words in `agent.py`:
```python
WAKE_WORDS = ["hey alex", "alex"]  # Primary and alternative
```

You can add more variations:
```python
WAKE_WORDS = ["hey alex", "alex", "okay alex", "hi alex"]
```

### Response Style

Adjust Alex's personality by modifying the `instructions` parameter in the code.

### Voice Characteristics

Change Alex's voice by browsing voices at [play.cartesia.ai](https://play.cartesia.ai)

---

## 📊 Logging & Debugging

### Log Events

```
🤖 Alex joined the call in silent listening mode
⏳ Waiting for wake words: hey alex, alex
🔍 Cleaned transcript: 'hey alex what is the weather today'
🎯 Wake word detected: 'hey alex'
💬 Processing query: 'what is the weather today'
🗣️ Generating response...
✅ Response completed - returning to silent mode
```

---

## 🔍 Troubleshooting

### Issue: Wake word not detected

**Solutions**:
- Check logs for "🔍 Cleaned transcript:" to see what's heard
- Verify wake word matches exactly (case-insensitive)
- Try speaking wake word more clearly
- Check microphone is working

### Issue: Alex doesn't return to silent mode

**Solutions**:
- Check `on_user_turn_completed` is resetting `wake_word_detected`
- Verify END_OF_SPEECH event is being detected
- Review logs for "✅ Response completed - returning to silent mode"

---

## 🚀 Production Deployment

### Deploy to LiveKit Cloud

```bash
lk cloud auth
lk agent create
lk agent deploy
```

### Docker Deployment

```bash
docker build -t alex-assistant .
docker run -d --env-file .env.local alex-assistant
```

---

## 📝 License

MIT License - See LICENSE file for details