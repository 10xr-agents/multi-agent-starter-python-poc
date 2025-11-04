# Tech Consultancy Multi-Agent Voice AI System

A production-ready LiveKit-based voice AI system simulating a real tech consultancy discovery call with two coordinated agents:

- **Sarah** (Business Development Executive) - Leads the call, gathers requirements, builds rapport
- **Alex** (Technical Executive) - Provides technical expertise when needed

## Features

✅ **Natural Introductions**: Both agents introduce themselves professionally  
✅ **Customer Name Capture**: Personalized conversation using customer's name  
✅ **Structured Discovery**: Organized flow through project requirements  
✅ **Smooth Handoffs**: Human-like transitions between agents  
✅ **Context-Aware**: Both agents share full conversation history  
✅ **Professional Tone**: Consultative, warm, and business-appropriate  

---

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

Required API keys:
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

**Development Mode:**
```bash
uv run src/agent.py dev
```

**Production:**
```bash
uv run src/agent.py start
```

---

## How the Conversation Flows

### Phase 1: Introduction & Rapport Building

```
Sarah: "Hi there! I'm Sarah, a Business Development Executive with our consultancy. 
        I have my colleague Alex on the call as well - he's our Technical Executive. 
        We're really excited to learn about your project today. 
        Before we dive in, may I ask who I'm speaking with and what you'd like to discuss?"

Customer: "Hi, I'm John Smith. I'm looking to build a mobile app for my business."

Sarah: "Great to meet you, John! Thanks for taking the time to speak with us today. 
        I'd love to hear more about your mobile app project. What problem are you trying to solve?"
```

### Phase 2: Requirements Gathering (Sarah Leads)

```
Customer: "We need a way for customers to book appointments and view their history."

Sarah: "That makes sense. So you're looking for a booking system with customer account features. 
        Can you tell me more about your ideal timeline for this project?"

Customer: "We'd like to launch within 6 months if possible."

Sarah: "Six months is a good timeframe. Do you have any hard deadlines or events that are driving this timeline?"
```

### Phase 3: Technical Questions (Alex Joins)

```
Customer: "What technology stack would you recommend for building this?"

Sarah: "That's a great technical question. Let me bring in Alex, our Technical Executive, to address that."

[HANDOFF TO ALEX]

Alex: "Thanks Sarah. Happy to help with that, John. For a booking app with customer accounts, 
       I'd recommend a React Native mobile frontend for cross-platform support, 
       a Node.js backend with PostgreSQL for robust data management, 
       and AWS for hosting with auto-scaling capabilities. 
       This stack gives you flexibility and proven scalability. 
       Does that help? Sarah can continue with the business aspects."

[HANDOFF BACK TO SARAH]

Sarah: "Thanks Alex. John, in terms of budget, do you have a range in mind for this project?"
```

### Phase 4: Closing & Next Steps

```
Sarah: "Let me summarize what we've discussed today. You're looking to build a cross-platform 
        booking app with customer accounts, launching within six months, with a budget around 
        $80,000. Does that capture everything correctly?"

Customer: "Yes, that's right."

Sarah: "Perfect. Here are our next steps: I'll send you a detailed proposal within two business days 
        outlining our approach, timeline, and investment breakdown. After you've had a chance to review, 
        we can schedule a follow-up call to address any questions. How does that sound?"
```

---

## Agent Personalities

### Sarah (Business Development Executive)

**Voice**: Female, warm, professional  
**Voice ID**: `79a125e8-cd45-4c13-8a67-188112f4dd22`

**Characteristics**:
- Leads the conversation and sets the agenda
- Builds rapport and asks thoughtful questions
- Focuses on business objectives, timelines, and budget
- Brings in Alex for technical questions
- Summarizes discussions and sets next steps

**What Sarah Handles**:
- Project vision and objectives
- Timeline requirements
- Budget discussions
- Team structure and stakeholders
- Next steps and follow-up
- Relationship building

### Alex (Technical Executive)

**Voice**: Male, knowledgeable, approachable  
**Voice ID**: `248be419-c632-4f23-adf1-5324ed7dbf1d`

**Characteristics**:
- Only speaks when brought in by Sarah or for technical questions
- Provides specific, actionable technical insights
- Keeps responses focused and concise
- Always hands back to Sarah after answering
- Collaborative and supportive

**What Alex Handles**:
- Technology stack recommendations
- Technical architecture
- Integration approaches
- Security and scalability considerations
- Technical timeline estimates
- Development complexity

---

## Conversation Topics

### Business Topics (Sarah Leads)

✅ Project goals and vision  
✅ Business objectives and ROI  
✅ Timeline and deadlines  
✅ Budget and pricing  
✅ Team structure  
✅ Stakeholders  
✅ Next steps and process  

### Technical Topics (Alex Joins)

✅ Technology stack recommendations  
✅ System architecture  
✅ Integration patterns  
✅ Security considerations  
✅ Scalability approach  
✅ Technical feasibility  
✅ Development approach  

---

## Key Features

### 1. Automatic Customer Name Capture

Sarah captures and remembers the customer's name for personalized conversation:

```python
@function_tool
async def capture_customer_name(self, context: RunContext, name: str):
    """Capture and remember the customer's name"""
    self.customer_name = name
    await self.session.say(f"Great to meet you, {name}!")
```

### 2. Smooth Agent Handoffs

Natural transitions between agents:

**Sarah → Alex:**
```python
await self.session.say(
    "That's a great technical question. Let me bring in Alex, 
     our Technical Executive, to address that."
)
```

**Alex → Sarah:**
```python
await self.session.say(
    "I hope that clarifies things. Sarah, back to you."
)
```

### 3. Context Sharing

Both agents access the full conversation history:

```python
# When switching agents
TechnicalAgent(shared_context=self.chat_ctx, customer_name=self.customer_name)
```

---

## Customization

### Change Agent Voices

Browse voices at [play.cartesia.ai](https://play.cartesia.ai):

```python
# Sarah's voice (currently female, warm)
tts=cartesia.TTS(
    voice="79a125e8-cd45-4c13-8a67-188112f4dd22",
    model="sonic-3"
)

# Alex's voice (currently male, professional)
tts=cartesia.TTS(
    voice="248be419-c632-4f23-adf1-5324ed7dbf1d",
    model="sonic-3"
)
```

### Adjust Conversation Flow

Modify Sarah's instructions to change the discovery flow:

```python
YOUR PRIMARY GOALS FOR THIS CALL:
1. Understand the customer's project vision
2. Gather timeline requirements
3. Identify budget parameters
4. Assess technical requirements
5. Set clear next steps
```

### Add Custom Tools

Add tools for CRM integration, calendar booking, etc:

```python
@function_tool
async def schedule_follow_up(self, context: RunContext, date: str, time: str):
    """Schedule a follow-up meeting"""
    # Your implementation
    return f"Follow-up scheduled for {date} at {time}"
```

---

## Testing

Run the evaluation suite:

```bash
uv run pytest
```

Tests validate:
- Proper agent introductions
- Customer name capture
- Business question handling (no delegation)
- Technical question delegation
- Natural handoff behavior
- Context preservation

---

## Production Deployment

### Deploy to LiveKit Cloud

```bash
# Install LiveKit CLI
# See: https://docs.livekit.io/home/cli/cli-setup

# Authenticate
lk cloud auth

# Create agent
lk agent create

# Deploy
lk agent deploy
```

### Docker Deployment

```bash
# Build image
docker build -t consultancy-agents .

# Run container
docker run -d \
  --env-file .env.local \
  consultancy-agents
```

---

## Frontend Integration

Connect with any LiveKit-compatible frontend:

- **React**: [agent-starter-react](https://github.com/livekit-examples/agent-starter-react)
- **iOS/macOS**: [agent-starter-swift](https://github.com/livekit-examples/agent-starter-swift)
- **Flutter**: [agent-starter-flutter](https://github.com/livekit-examples/agent-starter-flutter)

Or enable **telephony** for phone-based calls: [Telephony Guide](https://docs.livekit.io/agents/start/telephony/)

---

## Troubleshooting

### Issue: Agents interrupt each other
**Solution**: Ensure `turn_detection=MultilingualModel()` is configured properly

### Issue: Alex speaks too much
**Solution**: Strengthen the "wait for delegation" instruction in Alex's prompt

### Issue: Sarah doesn't delegate technical questions
**Solution**: Review the "WHEN TO BRING IN ALEX" section in Sarah's instructions

### Issue: Customer name not captured
**Solution**: Ensure Sarah's `capture_customer_name` tool is being called correctly

---

## Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                        LiveKit Room                             │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐    ┌──────────────┐    ┌──────────────┐     │
│  │  Customer   │◄──►│    Sarah     │◄──►│     Alex     │     │
│  │   (John)    │    │  (BD Exec)   │    │  (Tech Exec) │     │
│  └─────────────┘    └──────────────┘    └──────────────┘     │
│                            │                      │            │
│                     (Call Leader)         (On-demand)          │
│                                                                 │
│  Shared Conversation Context & Customer Information            │
└────────────────────────────────────────────────────────────────┘
```

---

## Support

- **Documentation**: [docs.livekit.io](https://docs.livekit.io)
- **Discord**: [livekit.io/discord](https://livekit.io/discord)
- **GitHub**: [github.com/livekit](https://github.com/livekit)

---

## License

MIT License - See LICENSE file for details