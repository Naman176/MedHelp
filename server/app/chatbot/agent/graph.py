from datetime import datetime
from typing import Annotated, Literal
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from app.chatbot.tools.db_tools import get_available_doctors, list_specializations
from app.core.config import settings


# TypedDict defines what gets stored and carried across every turn of the conversation.
# LangGraph persists this to SQLite automatically. Every node reads from and writes to this shared state.
# LangGraph persists this to SQLite after every node using the thread_id as the key — so memory works across turns.
class MedHelpState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

    # Current phase — set by router_node, read by route_after_router.
    phase: Literal["symptom", "booking", "general"]

    # Specialist the bot recommended carried forward so booking phase knows what to search.
    recommended_specialist: str

    user_id: str
    user_name: str


# LLM SETUP
router_llm = ChatGroq(
    model="llama-3.1-8b-instant",
    api_key=settings.GROQ_API_KEY,
    temperature=0,     # fully deterministic — same input = same output always
    streaming=False,   # no streaming needed, we just need one word back
)

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=settings.GROQ_API_KEY,
    temperature=0.3,    # slight randomness for natural-sounding responses
    streaming=True,     # enables token-by-token streaming to frontend
)

tools = [get_available_doctors, list_specializations]
llm_with_tools = llm.bind_tools(tools)


# One prompt for each phase of the conversation.
ROUTER_PROMPT = """You are a medical chatbot intent classifier.
 
Classify the user's latest message into exactly one category:
- symptom: user describes health symptoms, pain, illness, or asks which type of doctor/specialist to see
- booking: user wants to find doctors, check availability, see time slots, asks about specific days
- general: greetings, thanks, platform questions, or anything unclear
 
Rules:
- Reply with ONLY one word: symptom, booking, or general
- No explanation, no punctuation, nothing else
- If the user already received a specialist recommendation and now asks anything about doctors or days, say: booking
 
Examples:
"I have chest pain" → symptom
"show me cardiologists on monday" → booking
"find me a dentist available tomorrow" → booking
"which doctor should I see for back pain?" → symptom
"is there anyone available tuesday and wednesday?" → booking
"all weekdays except sunday" → booking
"hello" → general
"thank you" → general
"I have a fever, who should I consult?" → symptom
"show me dentists on tuesday, wednesday and thursday" → booking
"""


SYMPTOM_PROMPT = """You are MedHelp AI, a friendly medical triage assistant.

The user is describing symptoms or health concerns.
Your job:
1. Ask clarifying questions if needed (location of pain, duration, severity, etc.)
2. Once you have enough information, recommend which specialist they need
3. Briefly explain WHY that specialist is appropriate
4. Ask if they would like help finding an available doctor

Rules:
- Be empathetic and clear
- Never diagnose — only recommend which specialist to see
- Always remind the user you are an AI assistant, not a doctor
- Keep responses concise — do not overwhelm with too much information at once
- If the user says they want to find a doctor, 
  end your response with: SPECIALIST: <specialist_name>
  Example: SPECIALIST: cardiologist
- If user ask you to book the appointment directly, tell the user you can't do direct booking, but you can help them find available doctors and their available slots
"""


BOOKING_PROMPT = """You are MedHelp AI, a helpful medical assistant.
 
The user wants to find available doctors. Your job:
1. Use the get_available_doctors tool to search the database for matching doctors
2. Pass ALL requested days as a list — never query just one day if the user mentioned multiple
3. Present results clearly and neatly: doctor name, specialization, experience, fee, available slots
4. End by telling the user they can book from the Doctors section of MedHelp

How to handle days:
- Always pass days as a list of actual day names to get_available_doctors
- Resolve any expressions yourself before calling the tool:
  "tomorrow"              → figure out the actual day and pass it e.g. ["Friday"]
  "tuesday and thursday"  → ["Tuesday", "Thursday"]
  "all weekdays"          → ["Monday","Tuesday","Wednesday","Thursday","Friday"]
  "all week except sunday"→ ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"]
  "this weekend"          → ["Saturday", "Sunday"]
  "all week"              → ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

How to handle specialty:
- If a specialist was recommended earlier in the conversation, use that
- If the user directly names a specialty (e.g. "find me a dentist"), use that
- If the user asks for "doctors" or "available doctors" WITHOUT mentioning any specialty
  → Do NOT call get_available_doctors yet
  → Instead ask: "What type of specialist are you looking for? 
    For example: cardiologist, dentist, dermatologist, etc. 
    Or I can show you all available specialties — just ask!"
- Only call list_specializations if the user explicitly asks "what specialties do you have?"

Rules:
- ONLY show information returned by the tools — NEVER invent doctor names, fees, or slots
- If no doctors found, apologize and suggest trying a different day
- Always use the tools before responding with doctor information
- Do NOT offer to book on behalf of the user — just display the results
- Always end with: "You can book any of these slots directly from the Doctors section of MedHelp."
- Format time slots clearly: "Monday 5:00 PM - 5:30 PM"
"""


GENERAL_PROMPT = """You are MedHelp AI, a friendly assistant on the MedHelp medical platform.
 
Help the user with:
- General questions about the MedHelp platform
- General health information (always recommend seeing a real doctor for specifics)
- Navigation questions like "how do I book an appointment"
 
If they describe symptoms, encourage them to use the symptom checker.
If they want to find a doctor, guide them to search by specialty and day.
Keep responses short, friendly, and helpful.
"""


SPECIALIST_EXTRACT_PROMPT = """Extract the medical specialist type from the text below.

Return ONLY the list of specialist types in lowercase.
Examples of valid responses: cardiologist, dermatologist, orthopedic surgeon, neurologist, general physician, psychiatrist, ophthalmologist...
If no specific specialists iare mentioned or recommended, return exactly: none
No explanation. No punctuation. Just the specialist type or the word none.
"""


# ROUTER NODE
# Uses a small fast LLM to classify intent into one of three
# phases. No keyword lists, no regex — agent decides.
async def router_node(state: MedHelpState) -> MedHelpState:
    """
    Classifies the user's latest message into symptom / booking / general.
    Uses a small fast LLM (8B) instead of keyword matching.
    Only looks at the latest human message — not full history —
    because routing should be based on current intent, not past messages.
    """

    # Get the latest user message
    messages = state["messages"]

    last_human = next((m for m in reversed(messages) if isinstance(m, HumanMessage)), None)

    # No human message found → default to general
    if not last_human:
        return {**state, "phase": "general"}
    
    routing_messages = [
        SystemMessage(content=ROUTER_PROMPT),
        HumanMessage(content=last_human.content)
    ]

    # Fast LLM call — expects exactly one word back
    response = await router_llm.ainvoke(routing_messages)

    # Clean the response: strip whitespace, lowercase, remove punctuation
    # LLMs sometimes add periods or extra spaces even when told not to
    phase_raw = response.content.strip().lower().strip(".,!?")

    # Validate — if LLM returns something unexpected, default to general
    # This is a safety net for unexpected model outputs
    valid_phases = {"symptom", "booking", "general"}
    phase = phase_raw if phase_raw in valid_phases else "general"
 
    return {**state, "phase": phase}
    

# System node
async def symptom_node(state: MedHelpState) -> MedHelpState:
    """
    Handles symptom analysis and specialist recommendation.
    Uses the full conversation history so the LLM has complete
    context — it can ask follow-up questions naturally.
    After responding, extracts the specialist using a second
    LLM call so we store it in state for future turns.
    """

    messages = state["messages"]
    user_name = state.get("user_name", "")

    # Personalize system prompt if we have the user's name
    personalized_prompt = SYMPTOM_PROMPT
    if user_name:
        personalized_prompt += f"\n\nThe user's name is {user_name}. Address them by name occasionally to make the conversation personal."

    prompt_messages = [SystemMessage(content=personalized_prompt), *messages]   # full conversation history for context

    response = await llm.ainvoke(prompt_messages)

    specialist = await extract_specialist_from_text(
        response.content,
        state.get("recommended_specialist", "")
    )

    return {
        **state,
        "messages": [response],
        "recommended_specialist": specialist
    }

async def extract_specialist_from_text(response_text: str, existing_specialist: str) -> str:
    """
    Uses router_llm to extract the specialist type from the symptom
    node's response. Falls back to the existing specialist in state
    if none found — so recommended_specialist is never accidentally cleared.
    """

    # Quick check — if the response doesn't look like a recommendation,
    # don't waste an LLM call. Keep whatever specialist is already in state.
    recommendation_signals = [
        "consult", "recommend", "see a", "visit a",
        "specialist", "doctor", "physician", "surgeon"
    ]
    if not any(word in response_text.lower() for word in recommendation_signals):
        return existing_specialist
 
    # Ask the small LLM to extract just the specialist name
    extract_messages = [
        SystemMessage(content=SPECIALIST_EXTRACT_PROMPT),
        HumanMessage(content=response_text)
    ]
 
    result = await router_llm.ainvoke(extract_messages)
    extracted = result.content.strip().lower().strip(".,!? ")
 
    # "none" means no specialist was found in this response
    if extracted == "none" or not extracted:
        return existing_specialist  # keep existing, don't clear it
 
    return extracted


# Booking node
async def booking_node(state: MedHelpState) -> MedHelpState:
    """
    Handles doctor search. Uses llm_with_tools so the LLM can call
    get_available_doctors or list_specializations against the DB.
 
    Two-call pattern per tool use:
      Call 1: LLM decides which tool to call and extracts arguments
      Tool:   Runs against your PostgreSQL database
      Call 2: LLM composes a natural language response from DB results
 
    Also handles the case where user jumps directly to booking
    without going through the symptom phase first.
    """

    messages = state["messages"]
    specialist = state.get("recommended_specialist", "")

    today = datetime.now()

    date_context = (
        f"\n\nCurrent server date: {today.strftime('%Y-%m-%d')}."
        f"\nCurrent day of week: {today.strftime('%A')}."
        "\nUse this when resolving words like tomorrow, today, weekend, and weekdays."
    )

    # If we already know the specialist from a previous turn,
    # inject it as context so the LLM uses it automatically
    # even if the user just says "show me doctors on Monday"
    context = ""
    if specialist:
        # Specialist was set in a previous symptom turn
        context = (
            f"\n\nContext from earlier in this conversation: "
            f"This user was recommended to see a {specialist}. "
            f"When calling get_available_doctors, use '{specialist}' "
            f"as the specialist_type unless the user explicitly asks for a different specialty."
        )
    else:
        # User jumped directly to booking — no symptom phase
        context = (
            "\n\nNote: No specialist has been recommended yet in this conversation. "
            "Extract the specialty directly from the user's message "
            "(e.g. if they say 'find me a dentist', use 'dentist'). "
            "If the specialty is completely unclear, call list_specializations first."
        )

    prompt_messages = [
        SystemMessage(content=BOOKING_PROMPT + context + date_context),
        *messages
    ]

    # First LLM call — LLM decides: call a tool, or respond directly
    # Response is an AIMessage with either .content (text) or .tool_calls (tool request)
    response = await llm_with_tools.ainvoke(prompt_messages)

    # # LLM decided to call one or more tools
    if response.tool_calls:
        tool_messages = []
 
        for tool_call in response.tool_calls:
            # Find the Python function matching the tool name LLM requested
            # tool_call looks like:
            # {"id": "call_abc", "name": "get_available_doctors",
            #  "args": {"specialist_type": "cardiologist", "day_of_week": "Monday"}}
            matching_tool = next(
                (t for t in tools if t.name == tool_call["name"]),
                None
            )
 
            if matching_tool:
                # Execute the tool — runs your SQLAlchemy query against PostgreSQL
                result = await matching_tool.ainvoke(tool_call["args"])
 
                # Wrap result in ToolMessage — the tool_call_id links this result
                # back to the specific tool call the LLM made
                tool_messages.append(
                    ToolMessage(
                        content=result,
                        tool_call_id=tool_call["id"]
                    )
                )
 
        # Second LLM call — compose natural language response using DB results
        # Prompt includes: system + history + tool call request + tool results
        # Plain llm (not llm_with_tools) — we want text now, not another tool call
        final_prompt = prompt_messages + [response] + tool_messages
        final_response = await llm.ainvoke(final_prompt)
 
        # Store ALL three in state:
        # response       = the tool call request (AIMessage with tool_calls)
        # tool_messages  = the DB results (ToolMessage objects)
        # final_response = the natural language answer the user sees
        return {
            **state,
            "messages": [response, *tool_messages, final_response]
        }
 
    # ── DIRECT RESPONSE PATH ────────────────────────────────────
    # LLM responded with text directly (e.g. "What day works for you?")
    # No tool call needed — just return the response
    return {**state, "messages": [response]}


async def general_node(state: MedHelpState) -> MedHelpState:
    """
    Handles greetings, platform questions, and anything that
    doesn't fit symptom or booking. Uses full history for context.
    """
    messages = state["messages"]
    user_name = state.get("user_name", "")
 
    personalized_prompt = GENERAL_PROMPT
    if user_name:
        personalized_prompt += f"\n\nThe user's name is {user_name}."
 
    prompt_messages = [
        SystemMessage(content=personalized_prompt),
        *messages
    ]
 
    response = await llm.ainvoke(prompt_messages)
    return {**state, "messages": [response]}


# Called by LangGraph after router_node runs.
# Reads state.phase and returns the next node name as a string.
def route_after_router(state: MedHelpState) -> str:
    return state.get("phase", "general")


# Build graph
def build_graph(checkpointer):
    """
    Assembles the LangGraph state machine.
    Called once at startup with the checkpointer.
    """
    graph = StateGraph(MedHelpState)

    # Register all nodes
    graph.add_node("router", router_node)
    graph.add_node("symptom", symptom_node)
    graph.add_node("booking", booking_node)
    graph.add_node("general", general_node)

    # Entry point — every conversation starts at router
    graph.set_entry_point("router")

    # After router runs, call route_after_router(state) which
    # returns "symptom", "booking", or "general".
    # The mapping dict translates that string to the node name to jump to.
    graph.add_conditional_edges(
        "router",
        route_after_router,
        {
            "symptom": "symptom",
            "booking": "booking",
            "general": "general",
        }
    )

    # All response nodes end the graph after responding
    graph.add_edge("symptom", END)
    graph.add_edge("booking", END)
    graph.add_edge("general", END)

    # Compile with checkpointer — this enables memory
    return graph.compile(checkpointer=checkpointer)
