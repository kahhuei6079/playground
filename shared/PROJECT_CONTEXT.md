# Project Context

## What this office is
A local multi-agent software office that turns a human task into a plan, a design spec, a prototype in `workspace/<thread>/`, and a QA report.

## Technology
- Orchestration: LangGraph
- Models: Ollama (`AGENT_OFFICE_MODEL`, default `qwen3.5:9b`)
- Persistence: SQLite checkpoints in `data/checkpoints.sqlite`
- Memory: Markdown files in `agents/` and `shared/`

## Engineering principles
- Follow existing project conventions.
- Keep prototypes runnable and small.
- Protect credentials and personal information.
- Tests and acceptance criteria come before polish.
