from datetime import datetime
from typing import Annotated, Literal
import asyncio
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from app.chatbot.tools.db_tools import get_available_doctors, list_specializations
from app.core.config import settings
from app.chatbot.rag.retriever import hybrid_search, format_rag_context
from app.chatbot.mcp.mcp_client import get_mcp_client


# TypedDict defines what gets stored and carried across every turn of the conversation.
# LangGraph persists this to SQLite automatically. Every node reads from and writes to this shared state.
# LangGraph persists this to SQLite after every node using the thread_id as the key — so memory works across turns.

# This tells LangGraph: If new recommended_specialist is empty, keep the old one.
def keep_non_empty_specialist(old: str | None, new: str | None) -> str:
    return new or old or ""

class MedHelpState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

    # Current phase — set by router_node, read by route_after_router.
    phase: Literal["symptom", "booking", "general"]

    # Specialist the bot recommended carried forward so booking phase knows what to search.
    recommended_specialist: Annotated[str, keep_non_empty_specialist]

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
    streaming=False,     # enables token-by-token streaming to frontend
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
"what specialties do you have?" → booking
"what doctors are available?" → booking
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
- You may receive "Medical knowledge base context" from the RAG system. Use it as guidance for specialist recommendation.
- If the knowledge context marks urgency as emergency, tell the user to seek emergency medical care immediately or contact 
  local emergency services.
- Emergency examples include chest pain with shortness of breath, stroke-like symptoms, severe breathing difficulty,  
  fainting, severe allergic reaction, uncontrolled bleeding, severe head injury, suicidal thoughts, or sudden severe pain.
- If the user says they want to find a doctor, 
  end your response with: SPECIALIST: <specialist_name>
  Example: SPECIALIST: cardiologist
- If user ask you to book the appointment directly, tell the user you can't do direct booking, but you can help them find 
  available doctors and their available slots

Emergency scope rules:
- If the user mentions urgent or life-threatening symptoms, give brief emergency guidance first.
- Tell the user to contact local emergency services or go to the nearest emergency department immediately.
- Do NOT offer to find the nearest emergency room.
- Do NOT provide directions, maps, hospital locations, or country-specific emergency numbers unless the user explicitly provides their location.
- Do NOT continue routine appointment booking in the same emergency response.
- You may mention the likely follow-up specialist after the emergency warning.
- Keep emergency responses short: maximum 4–5 sentences.
- End emergency responses with: "After you are safe, I can help you find the right specialist for follow-up care."
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
- ONLY show information returned by tools.
- NEVER invent doctor names, fees, days, or times.
- Do NOT invent currency symbols. Show consultation fee as ₹<amount return by tool>.
- Do NOT use markdown bullets like *, -, or #. Use clean plain text.
- Use "Available time window" unless the tool returns exact appointment slots.
- If doctors are found, show doctor name, specialization, experience, consultation fee, and available time windows.
- If doctors are found, end with: "You can book this appointment directly from the Doctors section of MedHelp."
- If no doctors are found, do NOT say "You can book this appointment" or "You can book these slots".
- If no doctors are found, say only: "Sorry, no matching doctors are available for that day. You can try a different day or check the Doctors section later."
- If the user wants doctors but no day is provided, ask which day they prefer.
- If the user wants doctors but no specialty is known, ask what type of specialist they are looking for.
- Do NOT offer to book on behalf of the user.
"""


GENERAL_PROMPT = """You are MedHelp AI, a friendly assistant on the MedHelp medical platform.
 
Help the user with:
- General questions about the MedHelp platform
- General health information (always recommend seeing a real doctor for specifics)
- Navigation questions like "how do I book an appointment"
 
If they describe symptoms, encourage them to use the symptom checker.
If they want to find a doctor, guide them to search by specialty and day.
Keep responses short, friendly, and helpful.

Scope rules:
- MedHelp AI helps with symptom guidance, specialist suggestions, and doctor availability on the MedHelp platform.
- Do not act as an emergency room locator, map assistant, ambulance service, or hospital directory.
- If the user asks for emergency room directions, tell them to contact local emergency services or go to the nearest emergency department.
- Do not provide country-specific emergency numbers unless the user's location is known.
"""


SPECIALIST_EXTRACT_PROMPT = """Extract the medical specialist type from the text below.

Return ONLY specialist type in lowercase.
Examples of valid responses: cardiologist, dermatologist, orthopedic surgeon, neurologist, general physician, psychiatrist, ophthalmologist...
If no specific specialists are mentioned or recommended, return exactly: none
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
        return {"phase": "general"}
    
    recent_lines = []
    for message in messages[-8:]:
        if(isinstance(message, ToolMessage)):
            continue

        content = str(message.content).strip()

        if not content:
            continue

        role = "User" if isinstance(message, HumanMessage) else "Assistant"
        if len(content) > 500:
            content = content[:500] + "..."

        recent_lines.append(f"{role}: {content}")

    recent_context = "\n".join(recent_lines)
    recommended_specialist = state.get("recommended_specialist", "")

    routing_messages = [
        SystemMessage(
            content=(
                ROUTER_PROMPT
                + "\n\nAdditional routing context:"
                + f"\nKnown recommended specialist: {recommended_specialist or 'none'}"
                + "\nIf the latest message is a short confirmation like 'yes', 'sure', "
                  "'okay', or a day like 'Monday'/'tomorrow', and a specialist is known, "
                  "classify it as booking."
            )
        ),
        HumanMessage(
            content=(
                f"Recent conversation:\n{recent_context}\n\n"
                f"Latest user message:\n{last_human.content}"
            )
        ),
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
 
    return {"phase": phase}
    

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

    # Get latest user message for RAG search
    latest_human = next(
        (m for m in reversed(messages) if isinstance(m, HumanMessage)),
        None
    )

    rag_context = ""
    if latest_human and latest_human.content:
        try:
            # Run retrieval in a thread so embedding/vector search does not block the event loop.
            rag_results = await asyncio.to_thread(
                hybrid_search,
                str(latest_human.content),
                3
            )
            rag_context = format_rag_context(rag_results)
        except Exception:
            # RAG should never break the chatbot. If retrieval fails,
            # the LLM will answer using the normal symptom prompt.
            rag_context = ""

    # Personalize system prompt if we have the user's name
    personalized_prompt = SYMPTOM_PROMPT
    if rag_context:
        personalized_prompt += f"\n\n{rag_context}"

    if user_name:
        personalized_prompt += f"\n\nThe user's name is {user_name}. Address them by name occasionally to make the conversation personal."

    prompt_messages = [SystemMessage(content=personalized_prompt), *messages]   # full conversation history for context

    response = await llm.ainvoke(prompt_messages)

    specialist = await extract_specialist_from_text(
        response.content,
        state.get("recommended_specialist", "")
    )

    return {
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
    Handles doctor search using MCP tools via the MCP server.
    Flow:
        1. Connect to MCP server via MultiServerMCPClient
        2. Load tools from MCP server (get_available_doctors, list_specializations)
        3. Bind tools to LLM
        4. LLM decides which tool to call and with what args
        5. Tool executes via MCP server → doctor_service.py → PostgreSQL
        6. LLM composes natural language response from tool results

    Falls back to direct Python tools if MCP server is unavailable.
    This ensures the chatbot keeps working even if MCP server is down.
    """

    messages = state["messages"]
    specialist = state.get("recommended_specialist", "")

    today = datetime.now()

    date_context = (
        f"\n\nCurrent server date: {today.strftime('%Y-%m-%d')}."
        f"\nCurrent day of week: {today.strftime('%A')}."
        "\nUse this when resolving words like tomorrow, today, day after tomorrow, weekend, and weekdays."
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

    # Try MCP Path
    active_tools = None
    mcp_available = False

    try:
            client = get_mcp_client()

            mcp_tools = await client.get_tools()

            if mcp_tools:
                active_tools = mcp_tools
                mcp_available = True

                # Bind MCP tools to LLM for this request
                llm_with_active_tools = llm.bind_tools(active_tools)

                # First LLM call — decide which tool to call
                response = await llm_with_active_tools.ainvoke(prompt_messages)

                if response.tool_calls:
                    tool_messages = []

                    for tool_call in response.tool_calls:
                        # Find matching MCP tool by name
                        matching_tool = next(
                            (t for t in active_tools if t.name == tool_call["name"]),
                            None
                        )
                        if matching_tool:
                            # This call goes through MCP client → MCP server → DB
                            result = await matching_tool.ainvoke(tool_call["args"])
                            tool_messages.append(
                                ToolMessage(
                                    content=result if isinstance(result, str) else str(result),
                                    tool_call_id=tool_call["id"]
                                )
                            )

                    # Second LLM call — compose natural language response
                    final_prompt = prompt_messages + [response] + tool_messages
                    final_response = await llm.ainvoke(final_prompt)

                    return {
                        "messages": [response, *tool_messages, final_response]
                    }
                
                # LLM responded directly without calling a tool
                return {"messages": [response]}
    except Exception as e:
        # MCP server unavailable or error — fall through to direct tools
        print(f"[MCP FALLBACK] reason: {e}")
        mcp_available = False

    # FALLBACK: DIRECT PYTHON TOOLS
    # Used when MCP server is not running.
    # Identical logic to the MCP path but uses db_tools.py directly.
    # This ensures the chatbot always works regardless of MCP server state.
    active_tools = tools
    llm_with_active_tools = llm_with_tools

    # First LLM call — LLM decides: call a tool, or respond directly
    # Response is an AIMessage with either .content (text) or .tool_calls (tool request)
    response = await llm_with_active_tools.ainvoke(prompt_messages)

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
            "messages": [response, *tool_messages, final_response]
        }
 
    # ── DIRECT RESPONSE PATH ────────────────────────────────────
    # LLM responded with text directly (e.g. "What day works for you?")
    # No tool call needed — just return the response
    return {"messages": [response]}


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
    return {"messages": [response]}


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
