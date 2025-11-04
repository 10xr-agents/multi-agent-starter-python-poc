# Multi-Agent Voice Interaction System (POC)

A production-ready LiveKit-based voice AI system featuring two coordinated agents:
- **Business Agent**: Primary speaker handling business discussions and orchestration
- **Technical Agent**: Specialist providing technical input on-demand only

## Features

✅ **Selective Agent Activation**: Technical Agent only speaks when explicitly needed  
✅ **Shared Context**: Both agents access full conversation history  
✅ **Natural Handoffs**: Smooth transitions with verbal cues  
✅ **LLM-Driven Coordination**: Business Agent intelligently decides when to delegate  
✅ **Production-Ready**: Built on LiveKit's official starter template  

## Quick Start

### 1. Install Dependencies
```bash
uv sync
```

### 2. Configure Environment
```bash
cp .env.example .env.local
# Edit .env.local with your API keys
```

Get your API keys:
- **LiveKit**: [cloud.livekit.io](https://cloud.livekit.io/)
- **OpenAI**: [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
- **Deepgram**: [console.deepgram.com](https://console.deepgram.com/)
- **Cartesia**: [play.cartesia.ai/keys](https://play.cartesia.ai/keys)

### 3. Download Models
```bash
uv run src/agent.py download-files
```

### 4. Run the Agent

**Test in Terminal:**
```bash
uv run src/agent.py console
```

**Run for Frontend/Telephony:**
```bash
uv run src/agent.py dev
```

**Production:**
```bash
uv run src/agent.py start
```

## How It Works

### Conversation Flow Example
```
User: "How much would it cost to build a mobile app?"
Business Agent: "Great question! For a mobile app, costs typically..."

User: "What technology stack would you recommend?"
Business Agent: "That's a technical question. Let me bring in our Technical Specialist."
[SWITCHES TO TECHNICAL AGENT]

Technical Agent: "Technical Agent here. For mobile development, I'd recommend..."
[Technical Agent uses return_to_business_agent tool]
Technical Agent: "I'll hand this back to the Business Agent now."
[SWITCHES BACK TO BUSINESS AGENT]

Business Agent: "Thanks for that insight. Now, regarding your budget and timeline..."
```

### Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                      LiveKit Room                            │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   User       │◄──►│  Business    │◄──►│  Technical   │  │
│  │  (Human)     │    │   Agent      │    │   Agent      │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│                             │                     │          │
│                      (Primary Speaker)    (On-demand)        │
└─────────────────────────────────────────────────────────────┘
```

### Agent Behavior

**Business Agent:**
- Leads all conversations by default
- Handles: pricing, timelines, requirements, general questions
- Delegates: technical architecture, implementation, tech stack questions
- Uses `delegate_to_technical_agent` tool for handoffs

**Technical Agent:**
- Only speaks when explicitly delegated
- Provides: technical specifications, architecture insights, implementation details
- Uses `return_to_business_agent` tool to return control
- Does NOT respond to every user message

## Testing

Run the evaluation suite:
```bash
uv run pytest
```

Tests validate:
- Business Agent greeting behavior
- Business question handling (no delegation)
- Technical question delegation
- Technical Agent response quality
- Safety and refusal behavior

## Customization

### Change Agent Voices

Update the `voice` parameter in `TTS` initialization:
```python
# Browse voices at play.cartesia.ai
tts=cartesia.TTS(
    voice="your-voice-id-here",
    model="sonic-3"
)
```

### Adjust Agent Personalities

Modify the `instructions` parameter in each Agent's `__init__`:
```python
class BusinessAgent(Agent):
    def __init__(self, shared_context: ChatContext = None) -> None:
        super().__init__(
            instructions="Your custom instructions here...",
            # ...
        )
```

### Add Custom Tools

Use the `@function_tool` decorator:
```python
from livekit.agents import function_tool, RunContext

@function_tool
async def lookup_pricing(self, context: RunContext, product: str):
    """Look up pricing for a specific product."""
    # Your implementation
    return f"Price for {product}: $99/month"
```

## Frontend Integration

Use with any LiveKit-compatible frontend:

- **React**: [agent-starter-react](https://github.com/livekit-examples/agent-starter-react)
- **iOS/macOS**: [agent-starter-swift](https://github.com/livekit-examples/agent-starter-swift)
- **Flutter**: [agent-starter-flutter](https://github.com/livekit-examples/agent-starter-flutter)
- **React Native**: [voice-assistant-react-native](https://github.com/livekit-examples/voice-assistant-react-native)

Or enable telephony: [Telephony Guide](https://docs.livekit.io/agents/start/telephony/)

## Troubleshooting

### Technical Agent responds too often
**Solution**: Strengthen the "wait for delegation" instruction in Technical Agent's instructions.

### Agents talk over each other
**Solution**: Ensure only one `AgentSession` exists and `update_agent()` is used correctly.

### Context not shared between agents
**Solution**: Always pass `shared_context=self.session.chat_ctx` during agent transitions.

### High latency in responses
**Solution**: Ensure models are prewarmed in the `prewarm()` function.

## License

MIT License - See LICENSE file for details

## Support

- **Documentation**: [docs.livekit.io](https://docs.livekit.io)
- **Discord**: [livekit.io/discord](https://livekit.io/discord)
- **GitHub**: [github.com/livekit](https://github.com/livekit)