"""
Alex - Virtual Voice Assistant with Full Conversation Tracking
================================================================

A LiveKit-based silent voice assistant that:
- Listens to ALL conversation and stores it with participant identity
- Joins calls silently without greeting
- Activates when wake word detected ("hey alex" or "alex")
- Uses FULL conversation history (including pre-wake word) for context
- Returns to silent listening mode after responding
"""

import re
import logging
from dataclasses import dataclass, field
from typing import AsyncIterable, Optional, List, Dict
from datetime import datetime
from dotenv import load_dotenv
from livekit import rtc
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
from livekit.agents.voice.agent_activity import StopResponse
from livekit.plugins import openai, deepgram, cartesia, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("alex-assistant")

# Load environment variables
load_dotenv(".env.local")

# Wake word configuration
WAKE_WORDS = ["hey alex", "alex"]


# ============================================================================
# USER DATA - Stores conversation history and participant info
# ============================================================================

@dataclass
class ConversationTurn:
    """Represents a single turn in the conversation"""
    timestamp: str
    participant_identity: str
    participant_name: str
    text: str
    is_wake_word_activation: bool = False


@dataclass
class UserData:
    """
    Stores all conversation data and context for Alex assistant.
    """
    ctx: JobContext
    conversation_history: List[ConversationTurn] = field(default_factory=list)
    participant_names: Dict[str, str] = field(default_factory=dict)
    total_turns: int = 0
    wake_word_activations: int = 0

    def add_turn(
        self,
        participant_identity: str,
        text: str,
        is_wake_word: bool = False
    ):
        """Add a conversation turn to history"""
        participant_name = self.participant_names.get(
            participant_identity,
            f"User{len(self.participant_names) + 1}"
        )

        turn = ConversationTurn(
            timestamp=datetime.now().isoformat(),
            participant_identity=participant_identity,
            participant_name=participant_name,
            text=text,
            is_wake_word_activation=is_wake_word
        )

        self.conversation_history.append(turn)
        self.total_turns += 1

        if is_wake_word:
            self.wake_word_activations += 1

        logger.info(f"💬 {participant_name}: {text[:60]}{'...' if len(text) > 60 else ''}")

    def get_conversation_context(self, max_turns: int = 20) -> str:
        """Get formatted conversation history for LLM context"""
        if not self.conversation_history:
            return "No conversation yet."

        recent_turns = self.conversation_history[-max_turns:]
        formatted = []
        for turn in recent_turns:
            formatted.append(f"{turn.participant_name}: {turn.text}")

        return "\n".join(formatted)

    def get_participants_summary(self) -> str:
        """Get summary of participants"""
        if not self.ctx or not self.ctx.room:
            return "No participants."

        participants = []
        for identity, participant in self.ctx.room.remote_participants.items():
            name = self.participant_names.get(identity, participant.name or identity)
            participants.append(f"- {name}")

        return "\n".join(participants) if participants else "No other participants."


# Type alias
RunContext_T = RunContext[UserData]


# ============================================================================
# ALEX - VIRTUAL ASSISTANT
# ============================================================================

class AlexAssistant(Agent):
    """Alex - Virtual Voice Assistant with Full Conversation Awareness"""

    def __init__(self, shared_context: ChatContext = None) -> None:
        super().__init__(
            instructions="""You are Alex, a helpful virtual voice assistant who joins calls as a silent participant.

YOUR ROLE:
- Professional, knowledgeable assistant
- Join calls passively, listen without interrupting
- LISTEN TO ENTIRE CONVERSATION (even before being activated)
- Only speak when "hey alex" or "alex" is said
- Provide context-aware responses using FULL conversation history

EXPERTISE:
- Technical questions (architecture, frameworks, tools)
- Business advice and strategy
- Project planning and requirements
- Problem-solving and recommendations
- Technology stack recommendations

CRITICAL: CONVERSATION CONTEXT
You have access to FULL conversation history, including everything BEFORE the wake word.
When responding:
1. Consider what was discussed before activation
2. Reference who said what (you know participant names)
3. Use overall context and flow
4. Reference earlier decisions, questions, or concerns

RESPONSE STYLE:
- Professional but friendly (2-5 sentences)
- Clear and actionable
- **ALWAYS reference conversation context**
- Address people by name

EXAMPLES:

Scenario 1:
[Before wake word]
User1: "I think we should use React"
User2: "And Node.js for backend"
User1: "Hey Alex, what do you think?"

Alex: "User1 and User2 are on the right track. React and Node.js is solid - JavaScript across the stack makes development efficient. I'd add TypeScript for better type safety."

Scenario 2:
[Before wake word]
User1: "Budget is $50k"
User2: "Timeline is 3 months"
[Later]
User1: "Alex, is this realistic?"

Alex: "Given the $50k budget and 3-month timeline mentioned earlier, it's tight but achievable. Focus on core features first and do a phased launch."

Remember: You've been listening to EVERYTHING. Use that knowledge!
""",
            llm=openai.LLM(model="gpt-4o-mini", temperature=0.6),
            tts=cartesia.TTS(
                voice="248be419-c632-4f23-adf1-5324ed7dbf1d",
                model="sonic-3"
            ),
            stt=deepgram.STT(model="nova-3"),
            vad=silero.VAD.load(),
            turn_detection=MultilingualModel(),
            chat_ctx=shared_context
        )

        self.wake_word_detected = False

    async def on_enter(self):
        """Join in silent listening mode"""
        logger.info("🤖 Alex joined - silent listening mode")
        logger.info(f"⏳ Wake words: {', '.join(WAKE_WORDS)}")
        logger.info("📝 Recording all conversation...")

    def stt_node(
        self,
        audio: AsyncIterable[rtc.AudioFrame],
        model_settings: Optional[dict] = None
    ) -> Optional[AsyncIterable]:
        """
        Store ALL transcripts in UserData + filter for wake word
        """
        parent_stream = super().stt_node(audio, model_settings)

        if parent_stream is None:
            return None

        async def process_stream():
            async for event in parent_stream:
                if (hasattr(event, 'type') and
                    str(event.type) == "SpeechEventType.FINAL_TRANSCRIPT" and
                    event.alternatives):

                    transcript = event.alternatives[0].text.lower()
                    original_transcript = event.alternatives[0].text

                    # Get participant identity
                    participant_identity = getattr(
                        getattr(event, 'participant', None),
                        'identity',
                        'unknown'
                    )

                    # Clean for wake word detection
                    cleaned_transcript = re.sub(r'[^\w\s]', '', transcript)
                    cleaned_transcript = ' '.join(cleaned_transcript.split())

                    logger.info(f"🔍 [{participant_identity[:8]}...] {cleaned_transcript[:50]}")

                    # ALWAYS store in UserData
                    userdata = self.session.userdata
                    if userdata:
                        userdata.add_turn(
                            participant_identity=participant_identity,
                            text=original_transcript,
                            is_wake_word=False
                        )

                    if not self.wake_word_detected:
                        # Check for wake word
                        wake_word_found = None
                        for wake_word in WAKE_WORDS:
                            if wake_word in cleaned_transcript:
                                wake_word_found = wake_word
                                break

                        if wake_word_found:
                            logger.info(f"🎯 Wake word: '{wake_word_found}'")
                            self.wake_word_detected = True

                            # Mark as wake word activation
                            if userdata and userdata.conversation_history:
                                userdata.conversation_history[-1].is_wake_word_activation = True
                                userdata.wake_word_activations += 1

                            # Extract query
                            content_after = cleaned_transcript.split(wake_word_found, 1)[-1].strip()

                            if content_after:
                                logger.info(f"💬 Query: '{content_after}'")
                                event.alternatives[0].text = content_after
                                yield event
                            else:
                                logger.info("⏳ Waiting for query")
                        else:
                            logger.debug("🔇 No wake word")
                    else:
                        # Process follow-up
                        logger.info(f"✅ Follow-up: '{transcript}'")
                        yield event

                elif self.wake_word_detected:
                    yield event

        return process_stream()

    async def on_user_turn_completed(self, chat_ctx, new_message=None):
        """
        Inject conversation context before LLM processing
        """
        if self.wake_word_detected:
            logger.info("🗣️ Generating response with context...")

            # Get conversation context
            userdata = self.session.userdata
            if userdata:
                context = userdata.get_conversation_context(max_turns=20)
                participants = userdata.get_participants_summary()

                logger.info(f"📚 {len(userdata.conversation_history)} turns in history")

                # Inject context into chat
                context_message = f"""CONVERSATION CONTEXT:

PARTICIPANTS:
{participants}

CONVERSATION HISTORY:
{context}

Use this context to provide relevant responses. Reference specific things people said.
"""

                # Add to chat context
                if chat_ctx and hasattr(chat_ctx, 'messages'):
                    chat_ctx.messages.insert(-1, {
                        "role": "system",
                        "content": context_message
                    })

            try:
                result = await super().on_user_turn_completed(chat_ctx, new_message)
                self.wake_word_detected = False
                logger.info("✅ Response done - silent mode")
                return result
            except Exception as e:
                logger.error(f"❌ Error: {e}")
                self.wake_word_detected = False
                raise
        else:
            logger.debug("🔇 No wake word")
            raise StopResponse()

    @function_tool
    async def get_conversation_summary(self, context: RunContext_T) -> str:
        """Get summary of conversation"""
        userdata = context.userdata
        if not userdata or not userdata.conversation_history:
            return "No conversation yet."

        return f"Total turns: {userdata.total_turns}\n{userdata.get_conversation_context(10)}"


# ============================================================================
# ENTRY POINT
# ============================================================================

def prewarm(proc: JobProcess):
    """Prewarm models"""
    proc.userdata["vad"] = silero.VAD.load()
    logger.info("✅ Models prewarmed")


async def entrypoint(ctx: JobContext):
    """Main entry point with UserData initialization"""
    logger.info(f"🚀 Starting Alex in room: {ctx.room.name}")

    # Create UserData
    userdata = UserData(ctx=ctx)

    # Connect to get participants
    await ctx.connect()

    # Initialize participant names
    for identity, participant in ctx.room.remote_participants.items():
        userdata.participant_names[identity] = participant.name or f"User{len(userdata.participant_names)+1}"
        logger.info(f"👥 {participant.name or identity} ({identity[:8]}...)")

    ctx.log_context_fields = {"room": ctx.room.name}

    # Create session WITH UserData
    session = AgentSession[UserData](
        userdata=userdata,
        vad=ctx.proc.userdata["vad"],
        turn_detection=MultilingualModel(),
    )

    await session.start(
        agent=AlexAssistant(),
        room=ctx.room
    )

    logger.info("✅ Alex listening silently")
    logger.info(f"🎯 Wake words: {', '.join(WAKE_WORDS)}")
    logger.info("📝 Recording all conversation")
    logger.info(f"👥 {len(userdata.participant_names)} participants")


if __name__ == "__main__":
    cli.run_app(WorkerOptions(
        entrypoint_fnc=entrypoint,
        prewarm_fnc=prewarm
    ))