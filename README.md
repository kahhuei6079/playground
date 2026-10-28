# Agent Office

Local multi-agent office: **PM → Designer → Developer → QA**, orchestrated by LangGraph and powered by Ollama.

Each agent has a `SOUL.md` (identity) and `MEMORY.md` (private notes). Shared project facts live in `shared/`. Workflow state is a LangGraph checkpoint, not a markdown file.

Human approval is required after the plan and before release. QA failures loop back to the Developer until the retry limit. Any agent can escalate scope problems back to PM, Designer, or Developer (per their JSON `escalation` field); the office UI animates those return walks the same as forward handoffs.

## Setup

```bash
cd ~/playground
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
ollama list
```

Default model: `qwen3.5:9b`. Override with `AGENT_OFFICE_MODEL`.

## Per-agent models

Edit `models.yaml` to route each role to a different backend:

- **`ollama`** — local models (`base_url` defaults to `http://localhost:11434`)
- **`openai`** — any OpenAI-compatible HTTP API (`base_url` + `api_key_env`)

Example (see `models.example.yaml`):

```yaml
agents:
  developer:
    provider: openai
    model: gpt-4o-mini
    base_url: https://api.openai.com/v1
    api_key_env: OPENAI_API_KEY
```

Set API keys in the environment (see `.env.example`), not in YAML. Restart the UI after changing `models.yaml`.

The dashboard shows each agent’s configured model on its card.

## Usage

Live dashboard (shows which agent is working):

```bash
python main.py ui
```

Then open http://127.0.0.1:8000

CLI:

```bash
python main.py run "Build a tiny local payment checkout mock"
```

The run pauses after the PM plan. Approve or reject:

```bash
python main.py approve THREAD_ID
python main.py reject THREAD_ID --feedback "Keep it to one page"
```

When QA finishes, the graph pauses again for release:

```bash
python main.py release THREAD_ID
python main.py status THREAD_ID --full
```

Prototype files are written to `workspace/<thread_id>/`.

## Layout

```
agents/<role>/{SOUL.md,MEMORY.md}
shared/{PRINCIPLES.md,PROJECT_CONTEXT.md,DECISIONS.md,TASK_BOARD.md}
data/checkpoints.sqlite
workspace/<thread_id>/
```
