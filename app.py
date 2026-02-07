# Unified Mission Control + Memory System Dashboard
# FastAPI + FastHTML - Single consolidated dashboard

from fasthtml.common import *
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse
import json
import asyncio
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
import re
import secrets
from starlette.middleware.sessions import SessionMiddleware

# ==================== CONFIG ====================
WORKSPACE = Path("/home/ubuntu/.openclaw/workspace")
GTD_DIR = Path("/home/ubuntu/obsidian-notes/GTD")
OBSIDIAN_DIR = Path("/home/ubuntu/obsidian-notes")
ACTIVITIES_FILE = WORKSPACE / "mission-control" / "activities.jsonl"
MENTIONS_FILE = WORKSPACE / "mission-control" / "mentions.json"
MEMORY_DIR = WORKSPACE / "memory"
MEMORY_SYSTEM_DIR = WORKSPACE / "memory-system"
OPENCLAW_CONFIG = Path.home() / ".openclaw" / "openclaw.json"
SESSIONS_DIR = Path.home() / ".openclaw" / "agents" / "main" / "sessions"

SECRET_KEY = os.environ.get("SESSION_SECRET", secrets.token_hex(32))

# Add memory system to path
sys.path.insert(0, str(MEMORY_SYSTEM_DIR))

# ==================== MODERN STYLES ====================
MODERN_STYLES = """
:root {
    --bg-primary: #0a0a0f;
    --bg-secondary: #12121a;
    --bg-card: rgba(20, 20, 30, 0.6);
    --border: rgba(255, 255, 255, 0.08);
    --text-primary: #ffffff;
    --text-secondary: rgba(255, 255, 255, 0.6);
    --text-muted: rgba(255, 255, 255, 0.4);
    --accent: #3b82f6;
    --accent-glow: rgba(59, 130, 246, 0.3);
    --success: #10b981;
    --warning: #f59e0b;
    --error: #ef4444;
    --info: #00d4ff;
    --memory: #a855f7;
    --gradient-1: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    --gradient-2: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    --gradient-3: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
    --gradient-memory: linear-gradient(135deg, #a855f7 0%, #6366f1 100%);
}

* { box-sizing: border-box; }

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: var(--bg-primary);
    color: var(--text-primary);
    margin: 0;
    min-height: 100vh;
    line-height: 1.6;
}

.glass {
    background: var(--bg-card);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid var(--border);
    border-radius: 16px;
}

.glass-hover:hover {
    background: rgba(30, 30, 45, 0.8);
    border-color: rgba(255, 255, 255, 0.15);
    transform: translateY(-2px);
    transition: all 0.3s ease;
}

.nav-item {
    padding: 10px 18px;
    border-radius: 12px;
    color: var(--text-secondary);
    text-decoration: none;
    transition: all 0.2s ease;
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 500;
}

.nav-item:hover, .nav-item.active {
    background: rgba(59, 130, 246, 0.15);
    color: var(--accent);
}

.nav-item.active {
    box-shadow: 0 0 20px var(--accent-glow);
}

.nav-section {
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: var(--text-muted);
    margin: 16px 0 8px 12px;
}

.stat-card {
    padding: 24px;
    border-radius: 20px;
    position: relative;
    overflow: hidden;
}

.stat-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: var(--gradient-1);
}

.activity-item {
    padding: 16px 20px;
    margin-bottom: 12px;
    border-radius: 12px;
    border-left: 3px solid transparent;
    transition: all 0.2s ease;
}

.activity-item:hover {
    background: rgba(255, 255, 255, 0.03);
}

.activity-item.status-completed { border-left-color: var(--success); }
.activity-item.status-in_progress { border-left-color: var(--warning); }
.activity-item.status-error { border-left-color: var(--error); }

.timestamp {
    font-family: 'SF Mono', Monaco, monospace;
    font-size: 0.75rem;
    color: var(--text-muted);
}

.search-input {
    width: 100%;
    padding: 14px 20px;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid var(--border);
    border-radius: 12px;
    color: var(--text-primary);
    font-size: 1rem;
    transition: all 0.2s ease;
}

.search-input:focus {
    outline: none;
    border-color: var(--accent);
    box-shadow: 0 0 0 3px var(--accent-glow);
}

.btn-primary {
    padding: 12px 24px;
    background: var(--gradient-1);
    border: none;
    border-radius: 12px;
    color: white;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
}

.btn-primary:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 30px var(--accent-glow);
}

.btn-secondary {
    padding: 10px 18px;
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid var(--border);
    border-radius: 12px;
    color: var(--text-primary);
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
}

.btn-secondary:hover {
    background: rgba(255, 255, 255, 0.15);
}

.source-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.badge-activity { background: rgba(59, 130, 246, 0.15); color: #60a5fa; }
.badge-session { background: rgba(16, 185, 129, 0.15); color: #34d399; }
.badge-cron { background: rgba(245, 158, 11, 0.15); color: #fbbf24; }
.badge-message { background: rgba(139, 92, 246, 0.15); color: #a78bfa; }
.badge-gtd { background: rgba(236, 72, 153, 0.15); color: #f472b6; }
.badge-memory { background: rgba(168, 85, 247, 0.15); color: #c084fc; }

.memory-card {
    padding: 20px;
    margin-bottom: 12px;
    border-radius: 12px;
    border-left: 4px solid var(--memory);
    background: rgba(168, 85, 247, 0.08);
}

.confidence-high { color: var(--success); }
.confidence-medium { color: var(--warning); }
.confidence-low { color: var(--error); }

.live-indicator {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 12px;
    background: rgba(16, 185, 129, 0.15);
    border-radius: 20px;
    font-size: 0.8rem;
    color: var(--success);
}

.pulse {
    width: 8px;
    height: 8px;
    background: var(--success);
    border-radius: 50%;
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.5; transform: scale(1.2); }
}

.empty-state {
    text-align: center;
    padding: 60px 20px;
    color: var(--text-muted);
}

.scroll-container {
    max-height: 600px;
    overflow-y: auto;
    padding-right: 8px;
}

.scroll-container::-webkit-scrollbar {
    width: 6px;
}

.scroll-container::-webkit-scrollbar-track {
    background: transparent;
}

.scroll-container::-webkit-scrollbar-thumb {
    background: var(--border);
    border-radius: 3px;
}

.cursor-pointer { cursor: pointer; }

.tabs {
    display: flex;
    gap: 8px;
    margin-bottom: 24px;
    border-bottom: 1px solid var(--border);
    padding-bottom: 12px;
}

.tab {
    padding: 10px 20px;
    border-radius: 8px;
    color: var(--text-secondary);
    text-decoration: none;
    transition: all 0.2s ease;
}

.tab:hover, .tab.active {
    background: rgba(59, 130, 246, 0.15);
    color: var(--accent);
}

.tab.active {
    font-weight: 600;
}

/* Kanban Styles */
.kanban-board {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 16px;
    min-height: 500px;
}

.kanban-column {
    background: rgba(10, 10, 15, 0.6);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 16px;
    min-height: 400px;
}

.kanban-column-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 2px solid var(--border);
}

.kanban-column-title {
    font-weight: 600;
    font-size: 0.95rem;
    display: flex;
    align-items: center;
    gap: 8px;
}

.kanban-column-count {
    background: rgba(255, 255, 255, 0.1);
    padding: 4px 10px;
    border-radius: 12px;
    font-size: 0.8rem;
    font-weight: 600;
}

.kanban-card {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 14px;
    margin-bottom: 10px;
    cursor: grab;
    transition: all 0.2s ease;
}

.kanban-card:hover {
    background: rgba(255, 255, 255, 0.06);
    border-color: rgba(255, 255, 255, 0.12);
    transform: translateY(-2px);
}

.kanban-card.dragging {
    opacity: 0.5;
    cursor: grabbing;
}

.kanban-card-title {
    font-weight: 500;
    font-size: 0.95rem;
    margin-bottom: 8px;
    line-height: 1.4;
}

.kanban-card-meta {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
}

.kanban-card-agent {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 3px 8px;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 500;
}

.agent-lead { background: rgba(59, 130, 246, 0.2); color: #60a5fa; }
.agent-research { background: rgba(16, 185, 129, 0.2); color: #34d399; }
.agent-writing { background: rgba(236, 72, 153, 0.2); color: #f472b6; }
.agent-product-owner { background: rgba(139, 92, 246, 0.2); color: #a78bfa; }

.kanban-card-tag {
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 0.7rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.kanban-card-project {
    font-size: 0.75rem;
    color: var(--text-muted);
    margin-top: 8px;
}

.column-todo { border-top: 3px solid #64748b; }
.column-in_progress { border-top: 3px solid #f59e0b; }
.column-review { border-top: 3px solid #8b5cf6; }
.column-done { border-top: 3px solid #10b981; }
.column-blocked { border-top: 3px solid #ef4444; }

.column-todo .kanban-column-header { border-bottom-color: #64748b; }
.column-in_progress .kanban-column-header { border-bottom-color: #f59e0b; }
.column-review .kanban-column-header { border-bottom-color: #8b5cf6; }
.column-done .kanban-column-header { border-bottom-color: #10b981; }
.column-blocked .kanban-column-header { border-bottom-color: #ef4444; }
"""

# ==================== AUTH ====================

def get_gateway_token() -> Optional[str]:
    try:
        if OPENCLAW_CONFIG.exists():
            with open(OPENCLAW_CONFIG, 'r') as f:
                content = f.read()
                content = re.sub(r',(\s*[}\]])', r'\1', content)
                config = json.loads(content)
                return config.get('gateway', {}).get('auth', {}).get('token')
    except Exception:
        pass
    return None

def verify_token(token: str) -> bool:
    expected = get_gateway_token()
    if not expected:
        return False
    return secrets.compare_digest(token.strip(), expected.strip())

def is_authenticated(request: Request) -> bool:
    token = request.session.get('auth_token')
    return token is not None and verify_token(token)

# ==================== MEMORY SYSTEM DATA ACCESS ====================

def get_memory_store():
    """Lazy load memory store"""
    try:
        from memory_core.lance_store import LanceMemoryStore
        return LanceMemoryStore()
    except Exception as e:
        print(f"Error loading memory store: {e}")
        return None

def load_memories(limit: int = 50, memory_type: str = None) -> List[Dict]:
    """Load memories from the AI memory system"""
    store = get_memory_store()
    if not store:
        return []
    
    try:
        result = []
        
        # Get from personal table
        if memory_type in [None, "personal"]:
            personal_df = store.personal_table.to_pandas()
            for _, row in personal_df.iterrows():
                mem_dict = row.to_dict()
                mem_dict['_source'] = 'memory'
                mem_dict['memory_type'] = 'personal'
                mem_dict['_timestamp'] = mem_dict.get('created_at', 0)
                result.append(mem_dict)
        
        # Get from document table
        if memory_type in [None, "document"]:
            doc_df = store.document_table.to_pandas()
            for _, row in doc_df.iterrows():
                mem_dict = row.to_dict()
                mem_dict['_source'] = 'memory'
                mem_dict['memory_type'] = 'document'
                mem_dict['_timestamp'] = mem_dict.get('created_at', 0)
                result.append(mem_dict)
        
        # Sort by timestamp
        result.sort(key=lambda x: x.get('_timestamp', 0), reverse=True)
        return result[:limit]
    except Exception as e:
        print(f"Error loading memories: {e}")
        return []

def load_pending_memories() -> List[Dict]:
    """Load pending memories awaiting approval"""
    store = get_memory_store()
    if not store:
        return []
    
    try:
        return store.get_pending_memories()
    except Exception as e:
        print(f"Error loading pending memories: {e}")
        return []

def search_memories(query: str, k: int = 10) -> List[Dict]:
    """Search memories using vector similarity"""
    store = get_memory_store()
    if not store:
        return []
    
    try:
        results = store.search_memories(query, k=k, min_confidence=0.5)
        return [mem.__dict__ if hasattr(mem, '__dict__') else mem for mem in results]
    except Exception as e:
        print(f"Error searching memories: {e}")
        return []

def get_memory_stats() -> Dict:
    """Get memory system statistics"""
    store = get_memory_store()
    if not store:
        return {'total': 0, 'personal': 0, 'document': 0, 'pending': 0}
    
    try:
        stats = store.get_stats()
        pending = len(store.get_pending_memories())
        stats['pending'] = pending
        return stats
    except Exception as e:
        print(f"Error getting memory stats: {e}")
        return {'total': 0, 'personal': 0, 'document': 0, 'pending': 0}

# ==================== MISSION CONTROL DATA ACCESS ====================

def load_activities(limit: int = 100) -> List[Dict]:
    activities = []
    if ACTIVITIES_FILE.exists():
        with open(ACTIVITIES_FILE, 'r') as f:
            lines = f.readlines()
        for line in reversed(lines[-limit:]):
            line = line.strip()
            if line:
                try:
                    act = json.loads(line)
                    act['_source'] = 'activity'
                    act['_timestamp'] = act.get('timestamp', 0)
                    activities.append(act)
                except json.JSONDecodeError:
                    continue
    return activities

def load_sessions(limit: int = 50) -> List[Dict]:
    sessions = []
    if not SESSIONS_DIR.exists():
        return sessions
    
    session_files = sorted(SESSIONS_DIR.glob("*.jsonl"), key=lambda x: x.stat().st_mtime, reverse=True)[:limit]
    
    for sf in session_files:
        try:
            with open(sf, 'r') as f:
                lines = f.readlines()
            
            if not lines:
                continue
                
            first = json.loads(lines[0])
            if first.get('type') == 'session':
                session_data = {
                    '_source': 'session',
                    '_timestamp': datetime.fromisoformat(first.get('timestamp', '').replace('Z', '+00:00')).timestamp() if first.get('timestamp') else sf.stat().st_mtime,
                    'id': first.get('id', sf.stem),
                    'timestamp': first.get('timestamp'),
                    'cwd': first.get('cwd', ''),
                    'message_count': len([l for l in lines if json.loads(l).get('type') == 'message']),
                    'preview': 'Chat session'
                }
                
                for line in lines:
                    try:
                        msg = json.loads(line)
                        if msg.get('type') == 'message' and msg.get('message', {}).get('role') == 'user':
                            content = msg['message'].get('content', [{}])[0].get('text', '')[:100]
                            session_data['preview'] = content + '...' if len(content) > 95 else content
                            break
                    except:
                        continue
                
                sessions.append(session_data)
        except Exception:
            continue
    
    return sessions

def load_cron_jobs() -> List[Dict]:
    import subprocess
    try:
        result = subprocess.run(
            ["openclaw", "cron", "list", "--json"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            return json.loads(result.stdout).get("jobs", [])
    except Exception:
        pass
    return []

def search_qmd(query: str, limit: int = 10) -> List[Dict]:
    results = []
    try:
        import subprocess
        result = subprocess.run(
            ["qmd", "search", query, "--json", "-n", str(limit * 2)],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            if isinstance(data, list):
                for hit in data[:limit]:
                    results.append({
                        '_source': 'qmd',
                        'path': hit.get('file', 'unknown'),
                        'title': hit.get('title', 'Untitled'),
                        'preview': hit.get('snippet', '')[:300],
                        'score': hit.get('score', 0),
                        '_timestamp': 0
                    })
            elif isinstance(data, dict):
                for hit in data.get('hits', [])[:limit]:
                    results.append({
                        '_source': 'qmd',
                        'path': hit.get('file', hit.get('document', {}).get('path', 'unknown')),
                        'title': hit.get('title', hit.get('document', {}).get('title', 'Untitled')),
                        'preview': hit.get('snippet', hit.get('highlights', [''])[0])[:300],
                        'score': hit.get('score', 0),
                        '_timestamp': 0
                    })
    except Exception as e:
        pass
    return results

def get_upcoming_tasks() -> List[Dict]:
    jobs = load_cron_jobs()
    upcoming = []
    now = datetime.now()
    
    for job in jobs:
        schedule = job.get('schedule', {})
        kind = schedule.get('kind')
        
        if kind == 'cron':
            state = job.get('state', {})
            next_run_ms = state.get('nextRunAtMs')
            
            if next_run_ms:
                next_run = datetime.fromtimestamp(next_run_ms / 1000)
                upcoming.append({
                    'name': job.get('name', 'Unnamed'),
                    'next_run': next_run,
                    'schedule': f"Cron: {schedule.get('expr', 'Unknown')}",
                    'payload': job.get('payload', {})
                })
    
    def sort_key(x):
        nr = x.get('next_run')
        if isinstance(nr, datetime):
            return nr
        return datetime.max
    
    upcoming.sort(key=sort_key)
    return upcoming[:10]

def get_all_stats() -> Dict:
    """Get combined stats from both systems"""
    stats = {
        'activities': 0,
        'sessions': 0,
        'cron_jobs': len(load_cron_jobs()),
        'memories': 0,
        'gtd_files': 0,
    }
    
    if ACTIVITIES_FILE.exists():
        with open(ACTIVITIES_FILE, 'r') as f:
            stats['activities'] = sum(1 for _ in f if _.strip())
    
    if SESSIONS_DIR.exists():
        stats['sessions'] = len(list(SESSIONS_DIR.glob("*.jsonl")))
    
    if GTD_DIR.exists():
        stats['gtd_files'] = sum(1 for _ in GTD_DIR.rglob('*.md'))
    
    # Memory stats
    mem_stats = get_memory_stats()
    stats['memories'] = mem_stats.get('total', 0)
    stats['personal_memories'] = mem_stats.get('personal', 0)
    stats['document_memories'] = mem_stats.get('document', 0)
    stats['pending_memories'] = mem_stats.get('pending', 0)
    
    return stats

# ==================== KANBAN DATA ACCESS ====================

def parse_working_md() -> List[Dict]:
    """Parse WORKING.md to get agent task statuses"""
    working_file = WORKSPACE / "memory" / "WORKING.md"
    tasks = []
    
    if not working_file.exists():
        return tasks
    
    try:
        with open(working_file, 'r') as f:
            content = f.read()
        
        # Parse agent sections
        agents = ['Lead', 'Research', 'Writing', 'Product Owner']
        
        for agent in agents:
            agent_lower = agent.lower().replace(' ', '-')
            
            # Find the agent section
            pattern = rf'## {agent} Tasks\s*\n(.*?)(?=## |\Z)'
            match = re.search(pattern, content, re.DOTALL)
            
            if match:
                section = match.group(1)
                
                # Extract status
                status_match = re.search(r'\*\*Status:\*\*\s*(\w+)', section)
                status = status_match.group(1).lower() if status_match else 'idle'
                
                # Extract current task
                current_match = re.search(r'\*\*Current:\*\*\s*(.+?)\n', section)
                current_task = current_match.group(1).strip() if current_match else None
                
                # Extract next task
                next_match = re.search(r'\*\*Next:\*\*\s*(.+?)\n', section)
                next_task = next_match.group(1).strip() if next_match else None
                
                if current_task and current_task.lower() not in ['none', 'idle', 'n/a']:
                    tasks.append({
                        'id': f"{agent_lower}-current",
                        'title': current_task,
                        'agent': agent_lower,
                        'status': 'in_progress' if status == 'in_progress' else status,
                        'column': 'in_progress' if status == 'in_progress' else status,
                        'source': 'WORKING.md',
                        'type': 'agent-task'
                    })
                
                if next_task and next_task.lower() not in ['none', 'idle', 'n/a', 'available for assignment from gtd']:
                    tasks.append({
                        'id': f"{agent_lower}-next",
                        'title': next_task,
                        'agent': agent_lower,
                        'status': 'todo',
                        'column': 'todo',
                        'source': 'WORKING.md',
                        'type': 'agent-task'
                    })
                
                # Check for blocked section
                blocked_match = re.search(r'## Blocked\s*\n(.*?)(?=## |\Z)', content, re.DOTALL)
                if blocked_match:
                    blocked_section = blocked_match.group(1)
                    blocked_items = [line.strip('- ').strip() for line in blocked_section.split('\n') 
                                   if line.strip().startswith('- ') and line.strip() != '-']
                    
                    for item in blocked_items:
                        if item and item.lower() != '_none_':
                            tasks.append({
                                'id': f"blocked-{hash(item) % 10000}",
                                'title': item,
                                'agent': agent_lower,
                                'status': 'blocked',
                                'column': 'blocked',
                                'source': 'WORKING.md',
                                'type': 'agent-task'
                            })
    except Exception as e:
        print(f"Error parsing WORKING.md: {e}")
    
    return tasks

def parse_gtd_tasks() -> List[Dict]:
    """Parse GTD next.md for actionable tasks"""
    tasks = []
    next_file = GTD_DIR / "01-Next-Actions" / "next.md"
    
    if not next_file.exists():
        return tasks
    
    try:
        with open(next_file, 'r') as f:
            content = f.read()
        
        # Map contexts to agents
        agent_map = {
            '@research': 'research',
            '@writing': 'writing',
            '@product-owner': 'product-owner',
            '@computer': 'lead',
            '@calls': 'lead',
        }
        
        # Find tasks (both checked and unchecked)
        task_pattern = r'- \[(.)\] (.+?)(?=@|\n|$)'
        
        for match in re.finditer(task_pattern, content):
            checked = match.group(1) == 'x'
            task_text = match.group(2).strip()
            
            # Find agent tag
            agent = 'lead'  # default
            for tag, mapped_agent in agent_map.items():
                if tag in task_text.lower():
                    agent = mapped_agent
                    break
            
            # Extract project tag if present
            project_match = re.search(r'#(\w+)', task_text)
            project = project_match.group(1) if project_match else None
            
            # Clean task text
            clean_text = re.sub(r'@\w+', '', task_text)
            clean_text = re.sub(r'#\w+', '', clean_text)
            clean_text = clean_text.strip()
            
            if clean_text:
                tasks.append({
                    'id': f"gtd-{hash(task_text) % 10000}",
                    'title': clean_text,
                    'agent': agent,
                    'status': 'done' if checked else 'todo',
                    'column': 'done' if checked else 'todo',
                    'source': 'GTD',
                    'project': project,
                    'type': 'gtd-task'
                })
    except Exception as e:
        print(f"Error parsing GTD: {e}")
    
    return tasks

def load_kanban_tasks() -> Dict[str, List[Dict]]:
    """Load all tasks organized by kanban column"""
    columns = {
        'todo': [],
        'in_progress': [],
        'review': [],
        'done': [],
        'blocked': []
    }
    
    # Get tasks from WORKING.md
    working_tasks = parse_working_md()
    for task in working_tasks:
        col = task.get('column', 'todo')
        if col in columns:
            columns[col].append(task)
    
    # Get tasks from GTD
    gtd_tasks = parse_gtd_tasks()
    for task in gtd_tasks:
        col = task.get('column', 'todo')
        if col in columns:
            columns[col].append(task)
    
    # Deduplicate by title
    seen = set()
    for col in columns:
        unique = []
        for task in columns[col]:
            key = task['title'].lower()
            if key not in seen:
                seen.add(key)
                unique.append(task)
        columns[col] = unique
    
    return columns

def get_agent_emoji(agent: str) -> str:
    """Get emoji for agent type"""
    emojis = {
        'lead': '👑',
        'research': '🔬',
        'writing': '✍️',
        'product-owner': '📋',
    }
    return emojis.get(agent, '🤖')

# ==================== UI HELPERS ====================

def format_timestamp(ts) -> str:
    if not ts:
        return "Unknown"
    
    if isinstance(ts, str):
        try:
            ts = float(ts)
        except:
            return str(ts)
    
    try:
        dt = datetime.fromtimestamp(ts)
    except (ValueError, TypeError, OSError):
        return "Unknown"
    
    now = datetime.now()
    diff = now - dt
    
    if diff.days > 0:
        return f"{diff.days}d ago"
    hours = diff.seconds // 3600
    if hours > 0:
        return f"{hours}h ago"
    minutes = diff.seconds // 60
    if minutes > 0:
        return f"{minutes}m ago"
    return "Just now"

def get_confidence_class(confidence: float) -> str:
    if confidence >= 0.8:
        return "confidence-high"
    elif confidence >= 0.5:
        return "confidence-medium"
    else:
        return "confidence-low"

def nav_link(text, href, active=False):
    cls = "nav-item"
    if active:
        cls += " active"
    return A(text, href=href, cls=cls)

def layout(title, content, active_tab, request: Request):
    authed = is_authenticated(request)
    
    if not authed:
        return login_page()
    
    # Main nav sections
    mc_nav = [
        nav_link("📊 Feed", "/", active_tab == "feed"),
        nav_link("📅 Calendar", "/calendar", active_tab == "calendar"),
        nav_link("🗂️ Kanban", "/kanban", active_tab == "kanban"),
    ]
    
    memory_nav = [
        nav_link("🧠 Memories", "/memories", active_tab == "memories"),
        nav_link("⏳ Pending", "/memories/pending", active_tab == "pending"),
    ]
    
    search_nav = [
        nav_link("🔍 Search", "/search", active_tab == "search"),
        nav_link("📈 Stats", "/stats", active_tab == "stats"),
    ]
    
    return Title(title), Div(
        Style(MODERN_STYLES),
        # Header
        Div(
            Div(
                H1("🦊 Mission Control", cls="text-2xl font-bold mb-1"),
                P("Unified OpenClaw Dashboard", cls="text-sm", style="color: var(--text-muted);"),
                cls="glass p-6 mb-6"
            ),
            # Navigation
            Div(
                P("Activity", cls="nav-section"),
                *mc_nav,
                P("Memory", cls="nav-section"),
                *memory_nav,
                P("System", cls="nav-section"),
                *search_nav,
                A("🚪 Logout", href="/logout", cls="nav-item mt-6"),
                cls="glass p-4 mb-6"
            ),
            # Content
            Div(content, cls="mt-4"),
            # Footer
            Div(
                P(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}", 
                  cls="text-xs", style="color: var(--text-muted);"),
                cls="mt-8 pt-4 text-center",
                style="border-top: 1px solid var(--border);"
            ),
            cls="max-w-6xl mx-auto p-4",
            style="min-height: 100vh;"
        )
    )

def login_page():
    return Title("Login - Mission Control"), Div(
        Style(MODERN_STYLES),
        Div(
            Div(
                H1("🦊", cls="text-5xl mb-4 text-center"),
                H2("Mission Control", cls="text-2xl font-bold text-center mb-2"),
                P("Unified OpenClaw + Memory Dashboard", 
                  cls="text-center mb-6", style="color: var(--text-muted);"),
                Form(
                    Input(
                        type="password",
                        name="token",
                        placeholder="OpenClaw gateway token",
                        cls="search-input mb-4"
                    ),
                    Button(
                        "Authenticate",
                        type="submit",
                        cls="btn-primary w-full"
                    ),
                    action="/login",
                    method="post"
                ),
                P("Token: ~/.openclaw/openclaw.json → gateway.auth.token", 
                  cls="text-center mt-4 text-xs", style="color: var(--text-muted);"),
                cls="glass p-8",
                style="max-width: 400px; width: 100%;"
            ),
            cls="min-h-screen flex items-center justify-center p-4"
        )
    )

# ==================== ROUTES ====================

app = FastHTMLWithLiveReload(hdrs=(Link(rel="stylesheet", href="https://cdn.tailwindcss.com"),))
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY, max_age=3600*24*7)
rt = app.route

@rt('/login', methods=['GET'])
def login_get(request: Request):
    if is_authenticated(request):
        return RedirectResponse("/")
    return login_page()

@rt('/login', methods=['POST'])
async def login_post(request: Request):
    form = await request.form()
    token = form.get('token', '')
    
    if verify_token(token):
        request.session['auth_token'] = token
        return RedirectResponse("/", status_code=303)
    else:
        return login_page()

@rt('/logout')
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login")

@rt('/')
def feed_page(request: Request):
    items = load_activities(limit=50) + load_sessions(limit=20)
    
    def get_ts(x):
        ts = x.get('_timestamp', 0)
        return float(ts) if isinstance(ts, (int, float)) else 0
    
    items.sort(key=get_ts, reverse=True)
    
    feed_items = []
    for item in items[:50]:
        source = item.get('_source', 'unknown')
        ts = item.get('_timestamp', 0)
        
        badge_class = f"badge-{source}"
        source_label = source.upper()
        
        if source == 'activity':
            title = item.get('task', item.get('message', 'Activity'))
            agent = item.get('agent', 'Unknown')
            detail = f"@{agent}"
        elif source == 'session':
            title = item.get('preview', 'Chat session')[:60]
            detail = f"{item.get('message_count', 0)} messages"
            session_id = item.get('id', '')
        else:
            title = str(item)[:50]
            detail = ""
            session_id = ""
        
        # Make sessions clickable
        if source == 'session' and session_id:
            title_elem = A(title, href=f"/session?id={session_id}", 
                          style="text-decoration: none; color: inherit; font-weight: 500;")
        else:
            title_elem = P(title, cls="font-medium mb-1")
        
        feed_items.append(
            Div(
                Div(
                    Span(source_label, cls=f"source-badge {badge_class}"),
                    Span(format_timestamp(ts), cls="timestamp ml-auto"),
                    cls="flex justify-between items-center mb-2"
                ),
                title_elem,
                P(detail, cls="text-sm", style="color: var(--text-secondary);"),
                cls="activity-item glass"
            )
        )
    
    content = Div(
        Div(
            Div(
                H2("Activity Feed", cls="text-xl font-bold"),
                Div(
                    Span(cls="pulse"),
                    Span("Live", cls="text-sm font-medium"),
                    cls="live-indicator"
                ),
                cls="flex justify-between items-center mb-4"
            ),
            P(f"{len(items)} recent items", cls="text-sm mb-4", style="color: var(--text-muted);"),
            Div(*feed_items, cls="scroll-container"),
            cls="glass p-6"
        )
    )
    
    return layout("Activity Feed", content, "feed", request)

@rt('/session')
def view_session(request: Request, id: str = ""):
    if not id:
        return RedirectResponse("/")
    
    # Find the session file
    session_file = SESSIONS_DIR / f"{id}.jsonl"
    if not session_file.exists():
        # Try without extension
        session_file = SESSIONS_DIR / id
    
    if not session_file.exists():
        content = Div(
            Div(
                P("💬", cls="text-4xl mb-3"),
                H2("Session Not Found", cls="text-xl font-bold mb-2"),
                P(f"ID: {id}", style="color: var(--text-muted);"),
                A("← Back to Feed", href="/", cls="nav-item mt-4 inline-block"),
                cls="empty-state glass"
            )
        )
    else:
        try:
            messages = []
            with open(session_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        msg = json.loads(line)
                        if msg.get('type') == 'message':
                            role = msg.get('message', {}).get('role', 'unknown')
                            msg_content = ""
                            
                            # Extract text content
                            content_parts = msg.get('message', {}).get('content', [])
                            if isinstance(content_parts, list):
                                for part in content_parts:
                                    if isinstance(part, dict) and part.get('type') == 'text':
                                        msg_content += part.get('text', '')
                            elif isinstance(content_parts, str):
                                msg_content = content_parts
                            
                            timestamp = msg.get('timestamp', '')
                            
                            if role == 'user':
                                msg_class = "glass p-3 mb-3"
                                msg_style = "border-left: 3px solid var(--accent); margin-left: 20%;"
                                role_label = "👤 You"
                            elif role == 'assistant':
                                msg_class = "glass p-3 mb-3"
                                msg_style = "border-left: 3px solid var(--success); margin-right: 20%;"
                                role_label = "🦊 Assistant"
                            else:
                                msg_class = "glass p-3 mb-3"
                                msg_style = "border-left: 3px solid var(--text-muted);"
                                role_label = role.upper()
                            
                            # Truncate long messages
                            display_content = msg_content[:1000] + "..." if len(msg_content) > 1000 else msg_content
                            # Escape HTML
                            display_content = display_content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                            
                            messages.append(
                                Div(
                                    Div(
                                        Span(role_label, cls="text-xs font-semibold", 
                                             style="color: var(--text-secondary);"),
                                        Span(timestamp[:19] if timestamp else "", 
                                             cls="timestamp ml-auto"),
                                        cls="flex justify-between items-center mb-2"
                                    ),
                                    Pre(display_content, cls="text-sm", 
                                        style="white-space: pre-wrap; font-family: inherit; color: var(--text-primary);"),
                                    cls=msg_class,
                                    style=msg_style
                                )
                            )
                    except json.JSONDecodeError:
                        continue
            
            content = Div(
                Div(
                    A("← Back to Feed", href="/", cls="nav-item mb-4 inline-block"),
                    H2(f"Session: {id[:8]}...", cls="text-xl font-bold mb-2"),
                    P(f"{len(messages)} messages", cls="text-sm mb-4", style="color: var(--text-muted);"),
                    Div(*messages, cls="scroll-container"),
                    cls="glass p-6"
                )
            )
        except Exception as e:
            content = Div(
                Div(
                    P("⚠️", cls="text-4xl mb-3"),
                    H2("Error Loading Session", cls="text-xl font-bold mb-2"),
                    P(str(e), style="color: var(--text-muted);"),
                    A("← Back to Feed", href="/", cls="nav-item mt-4 inline-block"),
                    cls="empty-state glass"
                )
            )
    
    return layout("Session View", content, "feed", request)

@rt('/calendar')
def calendar_page(request: Request):
    upcoming = get_upcoming_tasks()
    
    if not upcoming:
        schedule_content = Div(
            Div(
                P("📅", cls="text-4xl mb-3"),
                P("No scheduled tasks.", cls="text-lg"),
                cls="empty-state"
            )
        )
    else:
        rows = []
        for task in upcoming:
            next_run = task['next_run']
            if isinstance(next_run, datetime):
                next_run_str = next_run.strftime('%Y-%m-%d %H:%M:%S')
                is_soon = (next_run - datetime.now()) < timedelta(hours=1)
            else:
                next_run_str = str(next_run)
                is_soon = False
            
            rows.append(
                Div(
                    Div(
                        H3(task['name'], cls="font-semibold"),
                        Span(task['schedule'], cls="source-badge badge-cron text-xs"),
                        cls="flex justify-between items-start mb-3"
                    ),
                    Div(
                        Span("Next: ", style="color: var(--text-muted);"),
                        Span(next_run_str, cls="font-mono ml-2", 
                             style=f"color: {'var(--error)' if is_soon else 'var(--success)'};"),
                        cls="text-sm"
                    ),
                    cls="glass p-4 mb-3 glass-hover"
                )
            )
        schedule_content = Div(*rows)
    
    content = Div(
        Div(
            H2("Upcoming Tasks", cls="text-xl font-bold mb-4"),
            schedule_content,
            cls="glass p-6"
        )
    )
    
    return layout("Calendar", content, "calendar", request)

@rt('/memories')
def memories_page(request: Request, q: str = "", type: str = ""):
    if q:
        memories = search_memories(q, k=20)
        search_info = P(f"Search: '{q}'", cls="mb-4", style="color: var(--text-muted);")
    else:
        memories = load_memories(limit=50, memory_type=type if type else None)
        search_info = Div()
    
    # Filter tabs
    tabs = Div(
        A("All", href="/memories", cls=f"tab {'active' if not type else ''}"),
        A("Personal", href="/memories?type=personal", cls=f"tab {'active' if type == 'personal' else ''}"),
        A("Document", href="/memories?type=document", cls=f"tab {'active' if type == 'document' else ''}"),
        cls="tabs"
    )
    
    if not memories:
        mem_content = Div(
            Div(
                P("🧠", cls="text-4xl mb-3"),
                P("No memories found." if not q else f"No results for '{q}'", cls="text-lg"),
                cls="empty-state"
            )
        )
    else:
        mem_cards = []
        for mem in memories:
            mem_content_text = mem.get('content', mem.get('text', 'No content'))
            mem_type = mem.get('memory_type', 'personal')
            confidence = mem.get('confidence', 0.5)
            created = mem.get('created_at', 0)
            mem_id = mem.get('id', '')
            
            conf_class = get_confidence_class(confidence)
            
            mem_cards.append(
                Div(
                    Div(
                        Span(mem_type.upper(), cls="source-badge badge-memory"),
                        Span(f"{confidence:.0%}", cls=f"timestamp ml-auto {conf_class}"),
                        cls="flex justify-between items-center mb-2"
                    ),
                    P(mem_content_text[:200] + "..." if len(mem_content_text) > 200 else mem_content_text, 
                      cls="font-medium mb-2", style="white-space: pre-wrap;"),
                    Div(
                        Span(format_timestamp(created), cls="text-xs", style="color: var(--text-muted);"),
                        cls="mb-3"
                    ),
                    # Action buttons for all memories
                    Div(
                        A("✏️ Edit", href=f"/memories/edit?id={mem_id}", 
                          cls="btn-secondary", style="text-decoration: none; margin-right: 8px; font-size: 0.8rem; padding: 6px 12px;"),
                        Form(
                            Input(type="hidden", name="id", value=mem_id),
                            Input(type="hidden", name="redirect", value="memories"),
                            Button("🗑️ Delete", type="submit", cls="btn-secondary", 
                                   style="padding: 6px 12px; font-size: 0.8rem; background: rgba(239, 68, 68, 0.2); color: var(--error);"),
                            action="/memories/delete",
                            method="post",
                            style="display: inline;"
                        ),
                        cls="flex gap-2 mt-2"
                    ),
                    cls="memory-card"
                )
            )
        
        mem_content = Div(*mem_cards, cls="scroll-container")
    
    content = Div(
        Div(
            H2("🧠 Memories", cls="text-xl font-bold mb-4"),
            Form(
                Input(type="text", name="q", value=q, placeholder="Search memories...", cls="search-input"),
                Button("🔍 Search", type="submit", cls="btn-primary mt-3"),
                action="/memories",
                method="get"
            ),
            cls="glass p-6 mb-6"
        ),
        Div(
            tabs,
            search_info,
            mem_content,
            cls="glass p-6"
        )
    )
    
    return layout("Memories", content, "memories", request)

@rt('/memories/pending')
def pending_memories_page(request: Request, message: str = ""):
    pending = load_pending_memories()
    
    message_div = Div(
        P(message, cls="mb-4 p-3 rounded-lg", style="background: rgba(16, 185, 129, 0.15); color: var(--success);"),
    ) if message else Div()
    
    if not pending:
        content = Div(
            message_div,
            Div(
                P("✅", cls="text-4xl mb-3"),
                P("No pending memories.", cls="text-lg"),
                P("All memories have been reviewed.", style="color: var(--text-muted);"),
                cls="empty-state glass"
            )
        )
    else:
        pending_cards = []
        for mem in pending:
            mem_content = mem.get('content', mem.get('text', 'No content'))
            confidence = mem.get('confidence', 0.5)
            mem_id = mem.get('id', '')
            mem_type = mem.get('memory_type', 'personal')
            
            pending_cards.append(
                Div(
                    Div(
                        Span("PENDING", cls="source-badge", style="background: rgba(245, 158, 11, 0.2); color: #fbbf24;"),
                        Span(f"{confidence:.0%}", cls="timestamp ml-auto"),
                        cls="flex justify-between items-center mb-3"
                    ),
                    P(mem_content[:300] + "..." if len(mem_content) > 300 else mem_content, 
                      cls="font-medium mb-3", style="white-space: pre-wrap;"),
                    Div(
                        Span(f"Type: {mem_type}", cls="text-xs mr-4", style="color: var(--text-muted);"),
                        cls="mb-3"
                    ),
                    # Action buttons
                    Div(
                        Form(
                            Input(type="hidden", name="id", value=mem_id),
                            Button("✅ Approve", type="submit", cls="btn-primary", style="padding: 8px 16px; font-size: 0.85rem; margin-right: 8px;"),
                            action="/memories/approve",
                            method="post",
                            style="display: inline;"
                        ),
                        A("✏️ Edit", href=f"/memories/edit?id={mem_id}", 
                          cls="btn-secondary", style="text-decoration: none; margin-right: 8px;"),
                        Form(
                            Input(type="hidden", name="id", value=mem_id),
                            Button("🗑️ Delete", type="submit", cls="btn-secondary", 
                                   style="padding: 8px 16px; font-size: 0.85rem; background: rgba(239, 68, 68, 0.2); color: var(--error);"),
                            action="/memories/delete",
                            method="post",
                            style="display: inline;"
                        ),
                        cls="flex gap-2 mt-3"
                    ),
                    cls="memory-card",
                    style="border-left-color: #f59e0b;"
                )
            )
        
        content = Div(
            message_div,
            H2(f"⏳ Pending Memories ({len(pending)})", cls="text-xl font-bold mb-4"),
            Div(*pending_cards, cls="scroll-container"),
            cls="glass p-6"
        )
    
    return layout("Pending Memories", content, "pending", request)

@rt('/memories/approve', methods=['POST'])
async def approve_memory(request: Request):
    form = await request.form()
    mem_id = form.get('id', '')
    
    store = get_memory_store()
    if store and mem_id:
        try:
            success = store.confirm_memory(mem_id)
            if success:
                return RedirectResponse("/memories/pending?message=✅+Memory+approved", status_code=303)
        except Exception as e:
            print(f"Error approving memory: {e}")
    
    return RedirectResponse("/memories/pending?message=❌+Failed+to+approve", status_code=303)

@rt('/memories/delete', methods=['POST'])
async def delete_memory_route(request: Request):
    form = await request.form()
    mem_id = form.get('id', '')
    redirect_to = form.get('redirect', 'pending')
    
    store = get_memory_store()
    if store and mem_id:
        try:
            success = store.reject_memory(mem_id)
            if success:
                redirect_path = "/memories" if redirect_to == "memories" else "/memories/pending"
                return RedirectResponse(f"{redirect_path}?message=🗑️+Memory+deleted", status_code=303)
        except Exception as e:
            print(f"Error deleting memory: {e}")
    
    redirect_path = "/memories" if redirect_to == "memories" else "/memories/pending"
    return RedirectResponse(f"{redirect_path}?message=❌+Failed+to+delete", status_code=303)

@rt('/memories/edit')
def edit_memory_page(request: Request, id: str = "", source: str = ""):
    if not id:
        return RedirectResponse("/memories")
    
    store = get_memory_store()
    if not store:
        return RedirectResponse("/memories?message=❌+Memory+store+unavailable")
    
    # Find the memory in any table
    mem = None
    mem_source = source
    
    try:
        # Check pending table first
        pending_df = store.pending_table.to_pandas()
        memory_row = pending_df[pending_df['id'] == id]
        if not memory_row.empty:
            mem = memory_row.iloc[0].to_dict()
            mem_source = "pending"
        
        # Check personal table
        if not mem:
            personal_df = store.personal_table.to_pandas()
            memory_row = personal_df[personal_df['id'] == id]
            if not memory_row.empty:
                mem = memory_row.iloc[0].to_dict()
                mem['memory_type'] = 'personal'
                mem_source = "personal"
        
        # Check document table
        if not mem:
            doc_df = store.document_table.to_pandas()
            memory_row = doc_df[doc_df['id'] == id]
            if not memory_row.empty:
                mem = memory_row.iloc[0].to_dict()
                mem['memory_type'] = 'document'
                mem_source = "document"
        
        if not mem:
            return RedirectResponse("/memories?message=❌+Memory+not+found")
        
    except Exception as e:
        print(f"Error finding memory: {e}")
        return RedirectResponse("/memories?message=❌+Error+loading+memory")
    
    back_link = "/memories/pending" if mem_source == "pending" else "/memories"
    back_text = "← Back to Pending" if mem_source == "pending" else "← Back to Memories"
    
    content = Div(
        Div(
            A(back_text, href=back_link, cls="nav-item mb-4 inline-block"),
            H2("✏️ Edit Memory", cls="text-xl font-bold mb-4"),
            
            Form(
                Input(type="hidden", name="id", value=id),
                Input(type="hidden", name="source", value=mem_source),
                
                Div(
                    P("Content:", cls="text-sm mb-2", style="color: var(--text-secondary);"),
                    Textarea(
                        mem.get('content', ''),
                        name="content",
                        rows=8,
                        cls="search-input",
                        style="font-family: inherit; min-height: 150px;"
                    ),
                    cls="mb-4"
                ),
                
                Div(
                    P("Memory Type:", cls="text-sm mb-2", style="color: var(--text-secondary);"),
                    Select(
                        Option("Personal", value="personal", selected=mem.get('memory_type') == 'personal'),
                        Option("Document", value="document", selected=mem.get('memory_type') == 'document'),
                        name="memory_type",
                        cls="search-input"
                    ),
                    cls="mb-4"
                ),
                
                Div(
                    P("Confidence:", cls="text-sm mb-2", style="color: var(--text-secondary);"),
                    Input(
                        type="number",
                        name="confidence",
                        value=str(mem.get('confidence', 0.8)),
                        min="0",
                        max="1",
                        step="0.1",
                        cls="search-input"
                    ),
                    cls="mb-4"
                ),
                
                Div(
                    Button("💾 Save Changes", type="submit", cls="btn-primary", style="margin-right: 12px;"),
                    A("Cancel", href=back_link, cls="btn-secondary", style="text-decoration: none;"),
                    cls="flex gap-3"
                ),
                
                action="/memories/update",
                method="post"
            ),
            
            cls="glass p-6"
        )
    )
    
    return layout("Edit Memory", content, "memories" if mem_source != "pending" else "pending", request)

@rt('/memories/update', methods=['POST'])
async def update_memory_route(request: Request):
    form = await request.form()
    mem_id = form.get('id', '')
    content = form.get('content', '')
    memory_type = form.get('memory_type', 'personal')
    confidence = float(form.get('confidence', 0.8))
    source = form.get('source', 'pending')
    
    store = get_memory_store()
    if store and mem_id:
        try:
            success = store.update_memory(
                mem_id,
                content=content,
                memory_type=memory_type,
                confidence=confidence
            )
            if success:
                redirect_path = "/memories" if source != "pending" else "/memories/pending"
                return RedirectResponse(f"{redirect_path}?message=💾+Memory+updated", status_code=303)
        except Exception as e:
            print(f"Error updating memory: {e}")
    
    redirect_path = "/memories" if source != "pending" else "/memories/pending"
    return RedirectResponse(f"{redirect_path}?message=❌+Failed+to+update", status_code=303)

@rt('/search')
def search_page(request: Request, q: str = ""):
    results_div = Div()
    
    if q:
        results = search_qmd(q, limit=20)
        
        if results:
            result_cards = []
            for r in results:
                result_cards.append(
                    Div(
                        Div(
                            Span("QMD", cls="source-badge badge-qmd"),
                            cls="mb-2"
                        ),
                        A(H3(r['title'], cls="font-semibold mb-1"), 
                          href=f"/view?path={r['path']}", 
                          style="text-decoration: none; color: inherit;"),
                        P(r['path'], cls="text-xs mb-2", style="color: var(--text-muted); font-family: monospace;"),
                        Pre(r['preview'], cls="text-sm p-3 rounded-lg", 
                           style="background: rgba(0,0,0,0.3); color: var(--text-secondary); overflow-x: auto;"),
                        cls="glass p-4 mb-3 glass-hover cursor-pointer"
                    )
                )
            
            results_div = Div(
                P(f"Found {len(results)} results", cls="mb-4", style="color: var(--text-muted);"),
                *result_cards
            )
        else:
            results_div = Div(
                Div(
                    P("🔍", cls="text-4xl mb-3"),
                    P(f"No results for '{q}'", cls="text-lg"),
                    cls="empty-state"
                )
            )
    
    content = Div(
        Div(
            H2("Global Search", cls="text-xl font-bold mb-4"),
            Form(
                Input(type="text", name="q", value=q, placeholder="Search documents...", cls="search-input"),
                Button("🔍 Search", type="submit", cls="btn-primary mt-3"),
                action="/search",
                method="get"
            ),
            cls="glass p-6 mb-6"
        ),
        Div(results_div, cls="glass p-6")
    )
    
    return layout("Search", content, "search", request)

@rt('/stats')
def stats_page(request: Request):
    stats = get_all_stats()
    
    stat_cards = [
        ("⚡ Activities", stats['activities'], "var(--gradient-1)"),
        ("💬 Sessions", stats['sessions'], "var(--gradient-2)"),
        ("⏰ Cron Jobs", stats['cron_jobs'], "var(--gradient-3)"),
        ("🧠 Memories", stats['memories'], "var(--gradient-memory)"),
        ("👤 Personal", stats.get('personal_memories', 0), "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)"),
        ("📄 Documents", stats.get('document_memories', 0), "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)"),
        ("⏳ Pending", stats.get('pending_memories', 0), "linear-gradient(135deg, #f59e0b 0%, #fbbf24 100%)"),
        ("📋 GTD Files", stats['gtd_files'], "linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)"),
    ]
    
    cards = []
    for label, value, gradient in stat_cards:
        cards.append(
            Div(
                P(label, cls="text-sm mb-2", style="color: var(--text-secondary);"),
                P(str(value), cls="text-3xl font-bold"),
                cls="stat-card glass",
                style=f"--gradient-1: {gradient};"
            )
        )
    
    content = Div(
        Div(
            H2("System Statistics", cls="text-xl font-bold mb-4"),
            Div(*cards, cls="grid grid-cols-2 md:grid-cols-4 gap-4"),
            cls="glass p-6"
        )
    )
    
    return layout("Statistics", content, "stats", request)

@rt('/kanban')
def kanban_page(request: Request):
    """Kanban board for agent tasks"""
    columns = load_kanban_tasks()
    
    column_config = [
        ('todo', '⏳ To Do', 'column-todo'),
        ('in_progress', '🔄 In Progress', 'column-in_progress'),
        ('review', '👀 Review', 'column-review'),
        ('done', '✅ Done', 'column-done'),
        ('blocked', '🚫 Blocked', 'column-blocked'),
    ]
    
    kanban_columns = []
    
    for col_id, col_title, col_class in column_config:
        tasks = columns.get(col_id, [])
        
        task_cards = []
        for task in tasks:
            agent = task.get('agent', 'lead')
            project = task.get('project')
            task_type = task.get('type', 'task')
            
            meta_items = [
                Span(f"{get_agent_emoji(agent)} {agent.replace('-', ' ').title()}", 
                     cls=f"kanban-card-agent agent-{agent}")
            ]
            
            if project:
                meta_items.append(Span(f"#{project}", cls="kanban-card-tag", 
                                       style="background: rgba(59, 130, 246, 0.15); color: #60a5fa;"))
            
            if task_type == 'gtd-task':
                meta_items.append(Span("GTD", cls="kanban-card-tag",
                                       style="background: rgba(16, 185, 129, 0.15); color: #34d399;"))
            
            task_cards.append(
                Div(
                    P(task['title'], cls="kanban-card-title"),
                    Div(*meta_items, cls="kanban-card-meta"),
                    cls="kanban-card",
                    draggable="true",
                    data_task_id=task['id']
                )
            )
        
        kanban_columns.append(
            Div(
                Div(
                    Span(col_title, cls="kanban-column-title"),
                    Span(str(len(tasks)), cls="kanban-column-count"),
                    cls="kanban-column-header"
                ),
                Div(*task_cards, cls="kanban-tasks", data_column=col_id),
                cls=f"kanban-column {col_class}",
                data_column=col_id
            )
        )
    
    content = Div(
        Div(
            Div(
                H2("🗂️ Agent Kanban Board", cls="text-xl font-bold"),
                P("Drag cards between columns to update status. Pulls from WORKING.md and GTD.", 
                  cls="text-sm", style="color: var(--text-muted);"),
                cls="mb-4"
            ),
            Div(*kanban_columns, cls="kanban-board"),
            cls="glass p-6"
        )
    )
    
    return layout("Kanban Board", content, "kanban", request)

@rt('/view')
def view_doc(request: Request, path: str = ""):
    if not path:
        return RedirectResponse("/search")
    
    from urllib.parse import unquote
    path = unquote(path)
    
    full_path = None
    
    if path.startswith("qmd://obsidian/"):
        rel_path = path.replace("qmd://obsidian/", "")
        try_path = OBSIDIAN_DIR / rel_path
        if try_path.exists():
            full_path = try_path
        else:
            parts = rel_path.split('/')
            current = OBSIDIAN_DIR
            for part in parts:
                found = False
                for child in current.iterdir():
                    if child.name.lower() == part.lower():
                        current = child
                        found = True
                        break
                if not found:
                    current = current / part
                    break
            full_path = current
    elif path.startswith("/"):
        full_path = Path(path)
    else:
        full_path = OBSIDIAN_DIR / path
    
    if not full_path or not full_path.exists():
        content = Div(
            Div(
                P("📄 Not Found", cls="text-2xl mb-3"),
                P(f"Path: {path}", style="color: var(--text-muted);"),
                A("← Back", href="/search", cls="nav-item mt-4 inline-block"),
                cls="empty-state glass"
            )
        )
    else:
        try:
            with open(full_path, 'r') as f:
                file_content = f.read()
            
            max_size = 50000
            if len(file_content) > max_size:
                file_content = file_content[:max_size] + "\n\n... [truncated]"
            
            file_content = file_content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            
            content = Div(
                Div(
                    A("← Back to Search", href="/search", cls="nav-item mb-4 inline-block"),
                    H2(full_path.name, cls="text-xl font-bold mb-2"),
                    Pre(file_content, cls="p-4 rounded-lg text-sm",
                       style="background: rgba(0,0,0,0.4); color: var(--text-secondary); overflow-x: auto; white-space: pre-wrap; max-height: 70vh; overflow-y: auto;"),
                    cls="glass p-6"
                )
            )
        except Exception as e:
            content = Div(
                P(f"Error: {e}", style="color: var(--error);"),
                cls="empty-state"
            )
    
    return layout("View Document", content, "search", request)

# ==================== MAIN ====================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    host = os.environ.get("HOST", "0.0.0.0")
    
    print(f"🦊 Unified Mission Control starting on http://{host}:{port}")
    print(f"   Includes: Activity Feed, Calendar, Memory System, Search, Stats")
    
    serve(host=host, port=port, reload=False)
