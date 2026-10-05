from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from enum import Enum

class TerminalState(str, Enum):
    booked = "booked"
    rescheduled = "rescheduled"
    cancelled = "cancelled"
    escalated = "escalated"
    refused = "refused"
    abandoned = "abandoned"

class EscalationReason(str, Enum):
    clinical_urgent = "clinical_urgent"
    medical_advice = "medical_advice"
    not_authorised = "not_authorised"
    ambiguous_patient = "ambiguous_patient"
    out_of_scope = "out_of_scope"

class AgentRequest(BaseModel):
    conversation_id: str
    today: str
    turns: List[str]

class Metrics(BaseModel):
    turns: int
    tokens: int
    latency_ms: int

class AgentResponse(BaseModel):
    conversation_id: str
    tool_calls: List[Dict[str, Any]]
    terminal_state: TerminalState
    escalation_reason: Optional[EscalationReason] = None
    patient_id: Optional[str] = None
    appointment_id: Optional[str] = None
    reply: str
    metrics: Metrics