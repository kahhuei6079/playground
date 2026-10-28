# Decisions

Record approved, durable choices here. Do not record in-flight task state.

## Architecture
- Graph: PM → plan approval → Designer → Developer → QA → release approval.
- QA failures route back to Developer until `AGENT_OFFICE_MAX_RETRIES` is reached.
- Agents share one local Ollama model and differ by soul, memory, and task context.
- File writes are limited to `workspace/<thread_id>/`.
