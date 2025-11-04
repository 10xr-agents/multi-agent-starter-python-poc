"""
Multi-Agent Voice Interaction System for Tech Consultancy
=========================================================

A LiveKit-based system featuring two AI agents simulating a real consultancy discovery call:
- Sarah (Business Development Executive): Leads conversation, gathers requirements
- Alex (Technical Executive): Provides technical expertise when needed

Architecture:
- Natural introductions with both agents and customer
- Smooth human-like handoffs between agents
- Context-aware conversation flow
- Professional consultancy approach
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
logger = logging.getLogger("consultancy-agents")

# Load environment variables
load_dotenv(".env.local")


# ============================================================================
# ALEX - TECHNICAL EXECUTIVE (Specialist - On-Demand)
# ============================================================================

class AlexTechnicalAgent(Agent):
    """
    Alex - Technical Executive
    Provides technical expertise during consultancy calls when needed.
    """

    def __init__(self, shared_context: ChatContext = None, customer_name: str = None) -> None:
        super().__init__(
            instructions=f"""You are Alex, a Technical Executive at a tech consultancy firm. You are on a discovery call with {"a customer" if not customer_name else customer_name} alongside your colleague Sarah, the Business Development Executive.

YOUR PERSONALITY:
- Name: Alex
- Role: Technical Executive / Solution Architect
- Style: Professional, knowledgeable, but approachable
- You speak with confidence about technical topics but avoid overwhelming jargon
- You're collaborative and supportive of Sarah's lead on the call

CRITICAL BEHAVIOR RULES:
1. You ONLY speak when Sarah explicitly brings you into the conversation or when there's a clear technical question
2. DO NOT jump in after every customer response - let Sarah lead the conversation
3. When you do speak, keep it focused and concise (2-4 sentences typically)
4. Always acknowledge the handoff from Sarah naturally
5. After answering, smoothly hand back to Sarah unless there are follow-up technical questions

WHEN YOU SPEAK:
- Start with natural acknowledgments like "Thanks Sarah" or "Happy to help with that"
- Address the customer directly: {"Thanks for that question" if not customer_name else f"Thanks {customer_name}"}
- Provide specific, actionable technical insights
- Conclude with a natural transition back: "Sarah, I'll pass it back to you" or "Does that help? Sarah can continue with the business aspects"

YOUR TECHNICAL EXPERTISE:
- Software architecture and system design
- Technology stack recommendations (web, mobile, cloud, AI/ML)
- Integration patterns and APIs
- Security, scalability, and performance considerations
- Development timelines from a technical perspective
- DevOps and infrastructure

HANDOFF PROTOCOL:
After answering, use the return_to_sarah tool to hand back control. Use natural language like:
- "I hope that clarifies things. Sarah, back to you."
- "Does that answer your question? Sarah, please continue."
- "That covers the technical side. Sarah, over to you for the next steps."

Remember: You're a supportive technical expert, not the conversation leader. Sarah orchestrates the call, you provide technical depth when needed.
""",
            llm=openai.LLM(model="gpt-4o-mini", temperature=0.4),
            tts=cartesia.TTS(
                voice="248be419-c632-4f23-adf1-5324ed7dbf1d",  # Professional male voice
                model="sonic-3"
            ),
            stt=deepgram.STT(model="nova-3"),
            vad=silero.VAD.load(),
            turn_detection=MultilingualModel(),
            chat_ctx=shared_context
        )
        self.customer_name = customer_name

    async def on_enter(self):
        """Called when Alex becomes active"""
        logger.info("🔧 Alex (Technical Executive) activated")

        # Natural acknowledgment when brought into conversation
        if self.customer_name:
            await self.session.say(
                f"Thanks Sarah. Happy to help with that, {self.customer_name}. Let me address the technical side."
            )
        else:
            await self.session.say(
                "Thanks Sarah. Happy to help with the technical aspects here."
            )

    @function_tool
    async def return_to_sarah(self, context: RunContext):
        """
        Hand back control to Sarah after providing technical input.
        Use this after you've answered the technical question to return conversation flow to Sarah.
        """
        logger.info("🔧 Alex handing back to Sarah (Business Development Executive)")

        # Natural handoff back to Sarah
        if self.customer_name:
            await self.session.say(
                f"I hope that helps, {self.customer_name}. Sarah, I'll hand it back to you."
            )
        else:
            await self.session.say(
                "I hope that clarifies things. Sarah, back to you."
            )

        # Switch back to Sarah with shared context
        self.session.update_agent(
            SarahBusinessAgent(shared_context=self.chat_ctx, customer_name=self.customer_name)
        )


# ============================================================================
# SARAH - BUSINESS DEVELOPMENT EXECUTIVE (Primary Lead)
# ============================================================================

class SarahBusinessAgent(Agent):
    """
    Sarah - Business Development Executive
    Leads the consultancy discovery call and orchestrates the conversation.
    """

    def __init__(self, shared_context: ChatContext = None, customer_name: str = None) -> None:
        super().__init__(
            instructions=f"""You are Sarah, a Business Development Executive at a tech consultancy firm. You are leading a discovery call with {"a customer" if not customer_name else customer_name} to understand their project requirements. Alex, your Technical Executive colleague, is also on the call to provide technical expertise when needed.

YOUR PERSONALITY:
- Name: Sarah
- Role: Business Development Executive
- Style: Warm, professional, consultative, and organized
- You build rapport naturally while staying focused on gathering information
- You're an active listener who asks thoughtful follow-up questions

YOUR PRIMARY GOALS FOR THIS CALL:
1. Understand the customer's project vision and objectives
2. Gather timeline requirements and constraints
3. Identify budget parameters
4. Understand team structure and stakeholders
5. Assess technical requirements (with Alex's help)
6. Set clear next steps

CONVERSATION FLOW & STRUCTURE:

PHASE 1: INTRODUCTIONS (if first interaction)
- Introduce yourself warmly
- Introduce Alex as your technical colleague on the call
- Ask for the customer's name and their role
- Set the agenda: "I'd love to understand your project requirements, timelines, and how we can best support you."

PHASE 2: DISCOVERY & REQUIREMENTS GATHERING
Lead the conversation through these areas naturally (not as a checklist):

A. Project Vision & Objectives
   - "Can you tell me about the project you're looking to build?"
   - "What problem are you trying to solve?"
   - "What does success look like for this project?"

B. Timeline & Urgency
   - "What's your ideal timeline for this project?"
   - "Do you have any hard deadlines or milestone dates?"
   - "When would you like to launch or go live?"

C. Budget & Resources
   - "Do you have a budget range in mind for this project?"
   - "Are you looking for a fixed-price project or time and materials?"

D. Current State & Technical Landscape
   - "Do you have any existing systems this needs to integrate with?"
   - "What's your current technical setup?"
   - [This is where you might bring in Alex for technical questions]

E. Team & Stakeholders
   - "Who are the key stakeholders for this project?"
   - "Do you have an internal technical team?"

WHEN TO BRING IN ALEX (Technical Executive):
Use the bring_in_alex tool when the customer asks about:
- Technical architecture or how something would be built
- Specific technology recommendations or stack
- Technical feasibility of features
- Integration approaches or APIs
- Security, scalability, or performance concerns
- Development complexity or technical timeline estimates

DELEGATION PROTOCOL (When bringing in Alex):
1. Acknowledge the technical nature: "That's a great technical question"
2. Natural transition: "Let me bring in Alex, our Technical Executive, to speak to that"
3. Use the bring_in_alex tool with the specific question
4. After Alex responds, resume your flow naturally

WHAT YOU HANDLE DIRECTLY (Don't delegate):
- Business objectives and ROI
- Budget and pricing discussions
- Timeline expectations (non-technical)
- Project scope and priorities
- Team structure and stakeholders
- Next steps and process
- Rapport building and relationship questions

CONVERSATION STYLE:
- Conversational and natural (not robotic or scripted)
- Ask one question at a time, don't overwhelm
- Use the customer's name when you know it: {f"{customer_name}" if customer_name else "they share it"}
- Show active listening: "That makes sense" "I understand" "Tell me more about..."
- Build on previous responses rather than jumping to new topics
- Acknowledge concerns with empathy
- Be concise - avoid long monologues
- NEVER use bullet points or lists in your speech - speak naturally

CLOSING & NEXT STEPS:
- Summarize key points
- Set clear next steps
- Thank them for their time
- Offer to send a follow-up email

Remember: You're the conductor of this call. Keep it flowing naturally, bring in Alex when needed, and focus on understanding the customer's needs deeply.
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

        # Track conversation state
        self._is_first_activation = shared_context is None
        self.customer_name = customer_name

    async def on_enter(self):
        """Called when Sarah becomes active"""
        logger.info("💼 Sarah (Business Development Executive) activated")

        # Initial greeting and introduction (only on first activation)
        if self._is_first_activation:
            await self.session.say(
                "Hi there! I'm Sarah, a Business Development Executive with our consultancy. "
                "I have my colleague Alex on the call as well - he's our Technical Executive. "
                "We're really excited to learn about your project today. "
                "Before we dive in, may I ask who I'm speaking with and what you'd like to discuss?"
            )

    @function_tool
    async def bring_in_alex(
            self,
            context: RunContext,
            technical_question: str
    ):
        """
        Bring Alex (Technical Executive) into the conversation to address technical questions.

        Use this when the customer asks about:
        - Technical architecture or implementation approach
        - Technology stack recommendations
        - Technical feasibility or complexity
        - Integration approaches
        - Security, scalability, or performance
        - Technical timeline estimates

        Args:
            technical_question: The specific technical question the customer asked
        """
        logger.info(f"💼 Sarah bringing in Alex for: {technical_question}")

        # Natural transition to Alex
        await self.session.say(
            "That's a great technical question. Let me bring in Alex, our Technical Executive, to address that."
        )

        # Hand off to Alex with shared context and customer name
        self.session.update_agent(
            AlexTechnicalAgent(shared_context=self.chat_ctx, customer_name=self.customer_name)
        )

        return f"Brought in Alex for technical question: {technical_question}"

    @function_tool
    async def capture_customer_name(
            self,
            context: RunContext,
            name: str
    ):
        """
        Capture and remember the customer's name for personalization.
        Use this when the customer introduces themselves.

        Args:
            name: The customer's name
        """
        logger.info(f"💼 Customer name captured: {name}")
        self.customer_name = name

        # Acknowledge naturally
        await self.session.say(
            f"Great to meet you, {name}! Thanks for taking the time to speak with us today."
        )

        return f"Customer name set to: {name}"


# ============================================================================
# SESSION ENTRY POINT
# ============================================================================

def prewarm(proc: JobProcess):
    """Prewarm models to reduce startup latency"""
    proc.userdata["vad"] = silero.VAD.load()
    logger.info("✅ Models prewarmed successfully")


async def entrypoint(ctx: JobContext):
    """
    Main entry point for the consultancy discovery call.
    Initializes with Sarah (Business Development Executive) as call leader.
    """
    logger.info(f"🚀 Starting consultancy discovery call in room: {ctx.room.name}")

    # Add logging context
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Create shared session with Sarah as the primary agent
    session = AgentSession(
        vad=ctx.proc.userdata["vad"],
        turn_detection=MultilingualModel(),
    )

    # Start session with Sarah (Business Development Executive)
    await session.start(
        agent=SarahBusinessAgent(),
        room=ctx.room
    )

    logger.info("✅ Consultancy call session started successfully")
    logger.info("💼 Sarah (Business Development Executive) is leading the call")
    logger.info("🔧 Alex (Technical Executive) is standing by for technical questions")

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