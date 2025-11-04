"""
Multi-Agent Voice Interaction System
====================================

A LiveKit-based POC featuring two AI agents (Business & Technical) 
and one human participant in a coordinated conversation.

Architecture:
- Business Agent: Primary speaker, leads conversation, orchestrates flow
- Technical Agent: Specialist providing technical input on-demand only
- Shared Context: Both agents access full conversation history
"""

import logging
from dotenv import load_dotenv
from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    JobProcess,
    WorkerOptions,
    cli,
    function_tool,
    RunContext,
)
from livekit.agents.llm import ChatContext
from livekit.plugins import openai, deepgram, cartesia, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("multi-agent")

# Load environment variables
load_dotenv(".env.local")


# ============================================================================
# TECHNICAL AGENT (Specialist - On-Demand Only)
# ============================================================================

class TechnicalAgent(Agent):
    """
    Technical Agent provides specialized technical input.
    Only responds when explicitly delegated by Business Agent.
    """

    def __init__(self, shared_context: ChatContext = None) -> None:
        super().__init__(
            instructions="""You are a Technical Specialist in a multi-agent system.

CRITICAL BEHAVIOR RULES:
1. You ONLY speak when the Business Agent explicitly delegates a technical question to you
2. DO NOT respond to every user message - wait for delegation
3. Keep answers focused, technical, and concise (2-3 sentences max)
4. After answering, always indicate you're ready to hand back control
5. Use phrases like "I'll hand this back to the Business Agent now"

YOUR EXPERTISE:
- Technical architecture and system design
- Implementation details and best practices
- Technology stack recommendations
- Security and scalability considerations
- API integrations and protocols

RESPONSE STYLE:
- Direct and technically accurate
- No marketing speak or business jargon
- Use technical terminology appropriately
- Provide specific actionable insights

Remember: You are a specialist called in for specific technical questions only.
""",
            llm=openai.LLM(model="gpt-4o-mini", temperature=0.3),
            tts=cartesia.TTS(
                voice="248be419-c632-4f23-adf1-5324ed7dbf1d",  # Professional male voice
                model="sonic-3"
            ),
            stt=deepgram.STT(model="nova-3"),
            vad=silero.VAD.load(),
            turn_detection=MultilingualModel(),
            chat_ctx=shared_context
        )

    async def on_enter(self):
        """Called when Technical Agent becomes active"""
        logger.info("🔧 Technical Agent activated")
        await self.session.say("Technical Agent here. Let me address that technical question.")

    @function_tool
    async def return_to_business_agent(self, context: RunContext):
        """
        Return control to Business Agent after providing technical input.
        Call this function when you've finished answering the technical question.
        """
        logger.info("🔧 Technical Agent returning control to Business Agent")
        await self.session.say("I'll hand this back to the Business Agent now.")

        # Switch back to Business Agent with shared context
        self.session.update_agent(
            BusinessAgent(shared_context=self.session.chat_ctx)
        )


# ============================================================================
# BUSINESS AGENT (Primary Speaker - Orchestrator)
# ============================================================================

class BusinessAgent(Agent):
    """
    Business Agent is the primary speaker and conversation orchestrator.
    Decides when to involve Technical Agent based on conversation context.
    """

    def __init__(self, shared_context: ChatContext = None) -> None:
        super().__init__(
            instructions="""You are the Business Agent - the primary point of contact in a multi-agent system.

YOUR ROLE:
1. Lead the conversation and gather user requirements
2. Handle all business-related questions (pricing, timeline, process, ROI)
3. Maintain engagement and build rapport with the user
4. Decide when technical expertise is needed and delegate appropriately
5. Keep the conversation flowing naturally and professionally

WHEN TO DELEGATE TO TECHNICAL AGENT:
Delegate when the user asks about:
- Technical architecture or system design ("How does it work?")
- Implementation details or technology stack ("What technologies would you use?")
- Technical specifications or requirements ("What are the technical requirements?")
- Integration patterns or APIs ("How would it integrate with our systems?")
- Security, scalability, or performance considerations

DELEGATION PROTOCOL:
When delegating, use the delegate_to_technical_agent tool and:
1. Briefly acknowledge the technical nature of the question
2. Use natural transitions like "That's a great technical question" or "Let me bring in our technical specialist"
3. Pass the specific technical question to the tool

WHAT YOU HANDLE DIRECTLY (No Delegation):
- Business objectives and outcomes
- Budget and pricing discussions
- Project timelines and milestones
- Team structure and roles
- General questions about your services
- Small talk and relationship building

CONVERSATION STYLE:
- Warm, professional, and consultative
- Ask clarifying questions to understand needs
- Show business acumen and strategic thinking
- Build trust and rapport naturally
- Keep responses conversational (avoid bullet points or lists in speech)

Remember: You are the primary contact and orchestrator. The Technical Agent is your specialist colleague you bring in when needed.
""",
            llm=openai.LLM(model="gpt-4o-mini", temperature=0.7),
            tts=cartesia.TTS(
                voice="79a125e8-cd45-4c13-8a67-188112f4dd22",  # Friendly female voice
                model="sonic-3"
            ),
            stt=deepgram.STT(model="nova-3"),
            vad=silero.VAD.load(),
            turn_detection=MultilingualModel(),
            chat_ctx=shared_context
        )

    async def on_enter(self):
        """Called when Business Agent becomes active"""
        logger.info("💼 Business Agent activated")

        # Only greet if this is the first activation (no chat history)
        if not self.chat_ctx or len(self.chat_ctx.messages) == 0:
            await self.session.say(
                "Hi! I'm your Business Agent. I'm here to help you with your project requirements. "
                "If we need any technical input, I'll bring in our Technical Specialist."
            )

    @function_tool
    async def delegate_to_technical_agent(
            self,
            context: RunContext,
            technical_question: str
    ):
        """
        Delegate a technical question to the Technical Agent.
        Use this when the user asks technical questions about implementation, 
        architecture, technology stack, or other technical details.

        Args:
            technical_question: The specific technical question the user asked
        """
        logger.info(f"💼 Delegating to Technical Agent: {technical_question}")

        # Announce the delegation to the user
        await self.session.say(
            "That's a technical question. Let me bring in our Technical Specialist to address that."
        )

        # Switch to Technical Agent with shared context
        self.session.update_agent(
            TechnicalAgent(shared_context=self.session.chat_ctx)
        )

        return f"Delegated to Technical Specialist: {technical_question}"


# ============================================================================
# SESSION ENTRY POINT
# ============================================================================

def prewarm(proc: JobProcess):
    """Prewarm models to reduce startup latency"""
    proc.userdata["vad"] = silero.VAD.load()
    logger.info("✅ Models prewarmed successfully")


async def entrypoint(ctx: JobContext):
    """
    Main entry point for the multi-agent session.
    Initializes with Business Agent as primary speaker.
    """
    logger.info(f"🚀 Starting multi-agent session in room: {ctx.room.name}")

    # Add logging context
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Create shared session with Business Agent as default
    session = AgentSession(
        vad=ctx.proc.userdata["vad"],
        turn_detection=MultilingualModel(),
    )

    # Start session with Business Agent
    await session.start(
        agent=BusinessAgent(),
        room=ctx.room
    )

    logger.info("✅ Multi-agent session started successfully")
    logger.info("💼 Business Agent is now active and ready")

    # Connect to the room
    await ctx.connect()


# ============================================================================
# MAIN RUNNER
# ============================================================================

if __name__ == "__main__":
    cli.run_app(WorkerOptions(
        entrypoint_fnc=entrypoint,
        prewarm_fnc=prewarm
    ))