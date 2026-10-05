# SwasthiQ AI Scheduling Agent

A deterministic, fault-tolerant conversational agent for Sunrise Clinic, featuring a FastAPI backend and a React/Tailwind frontend.

## API Contract
The backend exposes a single stateless endpoint for the agent interaction.

**`POST /agent/run`**
* **Request:** `AgentRequest`
  * `conversation_id` (str): Unique identifier for the session.
  * `today` (str): Contextual date (YYYY-MM-DD).
  * `turns` (List[str]): The sequential list of user inputs.
* **Response:** `AgentResponse`
  * `conversation_id` (str)
  * `tool_calls` (List[dict]): Sequential list of tools the AI executed.
  * `terminal_state` (Enum): `booked`, `cancelled`, `rescheduled`, `escalated`, `refused`, or `abandoned`.
  * `escalation_reason` (Enum | null): Matches strict schema reasons (e.g., `clinical_urgent`).
  * `patient_id` (str | null)
  * `appointment_id` (str | null)
  * `reply` (str): The final AI message.
  * `metrics` (dict): Token count, latency, and turn count.

## Data Consistency on Update
To ensure zero cross-contamination and guarantee atomic state evaluation across automated tests, this architecture uses **Request-Scoped Ephemeral Databases**:
1. **Isolation:** On every `POST /agent/run`, `create_fresh_db()` spins up a completely isolated, in-memory SQLite connection (`:memory:`).
2. **Seeding:** It immediately seeds the schema and hydrates the state from the read-only `clinic.json` file.
3. **Execution:** The `TOOL_MAP` executes Python functions (`book_appointment`, `cancel_appointment`) using standard SQL `UPDATE` and `INSERT` transactions against this isolated connection. 
4. **Resolution:** Once the final LLM turn resolves, the JSON response is serialized, and the connection is destroyed. 
This guarantees that concurrent evaluation runs will never face race conditions, stale reads, or database locks.

## Setup
See `/backend` and `/frontend` directories for standard local installation steps.