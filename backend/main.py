import os
import time
from dotenv import load_dotenv
from fastapi import FastAPI
from google import genai
from google.genai import types
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from schemas import AgentRequest, AgentResponse, TerminalState, EscalationReason, Metrics
from database import create_fresh_db

# 1. We import the real database functions with an alias so they don't clash with the AI tools
from tools import (
    search_slots as db_search_slots,
    book_appointment as db_book_appointment,
    reschedule_appointment as db_reschedule_appointment,
    cancel_appointment as db_cancel_appointment,
    lookup_patient as db_lookup_patient,
    escalate_to_human as db_escalate_to_human
)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all domains to access your API
    allow_credentials=True,
    allow_methods=["*"],  # Allows POST, GET, OPTIONS, etc.
    allow_headers=["*"],
)
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# 2. We define strictly typed, perfectly named dummy tools for the AI SDK to read.
# Notice we dropped the "_tool" suffix so the names perfectly match schema.md.
def search_slots(doctor_id: str, date: str) -> dict:
    """Free slots for a doctor on a date. Format date as YYYY-MM-DD. YOU MUST CALL THIS BEFORE OFFERING ANY SLOTS."""
    pass

def book_appointment(patient_id: str, doctor_id: str, date: str, start: str) -> dict:
    """Create an appointment in a free slot. Format date as YYYY-MM-DD and start as HH:MM."""
    pass

def reschedule_appointment(appointment_id: str, new_date: str, new_start: str) -> dict:
    """Move an existing appointment. Format new_date as YYYY-MM-DD and new_start as HH:MM."""
    pass

def cancel_appointment(appointment_id: str) -> dict:
    """Cancel an existing appointment."""
    pass

def lookup_patient(name: str) -> dict:
    """Resolve a caller to a patient record. YOU MUST CALL THIS to find the patient_id if the user provides a name."""
    pass

def escalate_to_human(reason: str, detail: str) -> dict:
    """Hand the conversation off. reason MUST be one of: clinical_urgent, medical_advice, not_authorised, ambiguous_patient, out_of_scope."""
    pass

# Map the exact tool names to our real database functions
TOOL_MAP = {
    "search_slots": db_search_slots,
    "book_appointment": db_book_appointment,
    "reschedule_appointment": db_reschedule_appointment,
    "cancel_appointment": db_cancel_appointment,
    "lookup_patient": db_lookup_patient,
    "escalate_to_human": db_escalate_to_human
}

# 3. An aggressive, foolproof system prompt to stop hallucinations
SYSTEM_PROMPT = """You are a strict, highly constrained front desk agent for Sunrise Clinic in Dehradun.
Your ONLY job is to manage the schedule and look up patients using the provided tools.
You speak Hindi, English, and a mix of both.

CRITICAL RULES:
1. ONE HARD RULE: If the caller describes ANY symptoms, pain, or medical emergency, you MUST immediately call escalate_to_human with reason='clinical_urgent'. Do not offer slots.
2. NEVER guess availability. You MUST ALWAYS call `search_slots` before confirming or suggesting a time.
3. NEVER guess patient IDs. You MUST ALWAYS call `lookup_patient` to find their ID before booking.
4. If patient lookup returns multiple candidates, ask the user to clarify. If they cannot, call escalate_to_human with reason='ambiguous_patient'.
5. NEVER invent slots, patient IDs, or appointment IDs. Only use data returned by your tools.
6. If a tool returns an error, tell the user the error truthfully.
"""

@app.post("/agent/run", response_model=AgentResponse)
async def run_agent(request: AgentRequest):
    start_time = time.time()
    conn = create_fresh_db()
    
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        tools=[
            search_slots, book_appointment, reschedule_appointment,
            cancel_appointment, lookup_patient, escalate_to_human
        ],
        temperature=0.0 # Force determinism
    )
    
    chat = client.chats.create(model="gemini-3.5-flash", config=config)
    
    executed_tools = []
    terminal_state = TerminalState.abandoned
    escalation_reason = None
    final_patient_id = None
    final_appointment_id = None
    final_reply = ""
    
    for turn_idx, user_turn in enumerate(request.turns):
        if turn_idx == 0:
            prompt = f"[System: Today is {request.today}]\nCaller: {user_turn}"
        else:
            prompt = f"Caller: {user_turn}"
            
        try:
            response = chat.send_message(prompt)
            
            # The AI might call multiple tools in a single turn (e.g., lookup_patient AND search_slots)
            while response.function_calls:
                function_responses = []
                
                for fn_call in response.function_calls:
                    tool_name = fn_call.name
                    args = dict(fn_call.args) if fn_call.args else {}
                    
                    executed_tools.append({"name": tool_name, "arguments": args})
                    
                    if tool_name in TOOL_MAP:
                        if tool_name == "escalate_to_human":
                            result = TOOL_MAP[tool_name](args.get("reason", "out_of_scope"), args.get("detail", ""))
                            terminal_state = TerminalState.escalated
                            try:
                                escalation_reason = EscalationReason(args.get("reason"))
                            except ValueError:
                                escalation_reason = EscalationReason.out_of_scope
                        else:
                            # Pass the SQLite connection to our real database functions
                            result = TOOL_MAP[tool_name](conn, **args)
                            
                            if result.get("success"):
                                if "appointment_id" in result:
                                    final_appointment_id = result["appointment_id"]
                                    if tool_name == "book_appointment":
                                        terminal_state = TerminalState.booked
                                    elif tool_name == "reschedule_appointment":
                                        terminal_state = TerminalState.rescheduled
                                    elif tool_name == "cancel_appointment":
                                        terminal_state = TerminalState.cancelled
                            
                            if tool_name == "lookup_patient" and "candidates" in result and len(result["candidates"]) == 1:
                                final_patient_id = result["candidates"][0]["id"]
                    else:
                        result = {"error": f"Tool {tool_name} is not recognized."}

                    function_responses.append(
                        types.Part.from_function_response(
                            name=tool_name,
                            response=result
                        )
                    )
                
                if function_responses:
                    response = chat.send_message(function_responses)
                
                if terminal_state == TerminalState.escalated:
                    break 

        except Exception as e:
            print(f"CRITICAL ERROR: {str(e)}")
            terminal_state = TerminalState.escalated
            escalation_reason = EscalationReason.out_of_scope
            final_reply = "System encountered an error parsing the request."
            break
            
        final_reply = response.text
        if terminal_state == TerminalState.escalated:
            break

    conn.close()
    latency_ms = int((time.time() - start_time) * 1000)
    
    # Calculate best-effort token usage[cite: 7]
    tokens = 0
    for message in chat.get_history():
        for part in message.parts:
            if part.text:
                tokens += len(part.text.split()) * 2 

    return AgentResponse(
        conversation_id=request.conversation_id,
        tool_calls=executed_tools,
        terminal_state=terminal_state,
        escalation_reason=escalation_reason,
        patient_id=final_patient_id,
        appointment_id=final_appointment_id,
        reply=final_reply,
        metrics=Metrics(turns=len(request.turns), tokens=tokens, latency_ms=latency_ms)
    )