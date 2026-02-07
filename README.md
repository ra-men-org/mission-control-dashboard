# 🦊 Mission Control Dashboard

FastAPI + FastHTML dashboard for OpenClaw. Local-only, Tailscale-accessible.

## Views

1. **📊 Activity Feed** — Real-time log of every OpenClaw action
2. **📅 Calendar** — Scheduled tasks with weekly overview  
3. **🗂️ Kanban Board** — Agent task board with columns (Todo, In Progress, Review, Done, Blocked)
4. **🧠 Memories** — AI memory system browser with search and approval
5. **🔍 Global Search** — Search across memories, GTD files, and tasks
6. **📈 Stats** — System overview with counts

## Quick Start

```bash
cd ~/.openclaw/workspace/mission-control-dashboard
./start.sh
```

Then open: http://localhost:8080

## Access via Tailscale

Since it binds to `0.0.0.0`, you can access from any Tailscale-connected device:

```
http://<ubuntu-hostname>:8080
```

## Data Sources

- **Activities**: `~/.openclaw/workspace/mission-control/activities.jsonl`
- **Cron Jobs**: Pulled from `openclaw cron list`
- **GTD**: `~/obsidian-notes/GTD/`
- **Memories**: `~/.openclaw/workspace/memory/`

## Files

- `app.py` — Main FastHTML application
- `start.sh` — Convenience startup script
- `requirements.txt` — Python dependencies
