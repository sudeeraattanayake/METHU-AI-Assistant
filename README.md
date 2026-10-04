# METHU AI Assistant

**METHU — Multimodal Executive & Task Handling Unit**

METHU is an experimental agentic AI desktop assistant designed to understand natural-language requests, plan tasks, select specialist agents, safely interact with a Windows computer, access live information, and execute multi-step workflows.

The long-term goal is to build a practical JARVIS-inspired AI assistant with secure computer control, browser automation, coding capabilities, vision, voice interaction, memory, real-time information retrieval, and a holographic-style 3D user interface.

> **Current Status:** Active Development  
> METHU currently supports AI orchestration, live news retrieval, secure Windows application launching, browser navigation, FastAPI/WebSocket communication, and multi-step task execution.

---

## Current Capabilities

### AI Orchestration

METHU uses an LLM-powered orchestrator to understand user requests and determine which specialist agent should handle them.

Current routing targets include:

- Computer Agent
- Browser Agent
- News Agent
- Coding Agent
- Research Agent
- Vision Agent
- Memory Agent
- System Agent

Some agents are currently placeholders while the architecture is being developed incrementally.

---

### Multi-Step Task Execution

METHU can plan and execute multiple actions sequentially.

Example:

```text
User:
"Methu, open Chrome and go to YouTube."

METHU:
Understand request
      ↓
Create plan
      ↓
Step 1 → Computer Agent
      ↓
Open Chrome
      ↓
Step 2 → Browser Agent
      ↓
Navigate to YouTube
      ↓
Task completed
```

Example successful WebSocket event:

```text
Event: multi_step_completed
Status: completed
Response: I completed the task: Open Chrome and go to YouTube.
```

---

## Secure Computer Control

METHU includes a permission and command-guard layer designed to prevent unrestricted computer access.

Current supported application actions include opening:

- Google Chrome
- Visual Studio Code
- Notepad
- Calculator
- File Explorer

Applications are resolved through an explicit allowlist.

Example:

```text
"Methu, open Chrome."
```

METHU routes the request to the Computer Agent and launches Chrome through the protected application-control layer.

---

## Browser Navigation

METHU can safely open supported websites using Google Chrome.

Examples:

```text
"Methu, go to YouTube."

"Methu, open GitHub."

"Methu, go to LinkedIn."
```

Known websites currently include:

```text
YouTube
Google
GitHub
LinkedIn
```

Valid HTTP/HTTPS URLs can also be processed by the browser navigation layer.

---

## Live News Intelligence

METHU includes a live News Agent powered by Tavily.

Example:

```text
"Methu, give me the latest AI news."
```

The News Agent:

1. Searches current news sources.
2. Retrieves relevant articles.
3. Sends the retrieved information to the LLM.
4. Produces a concise summary.
5. Returns article metadata to the interface.

---

## Security Architecture

Computer control is protected by multiple security layers.

```text
User Request
     ↓
Orchestrator
     ↓
Planner
     ↓
Permission Layer
     ↓
Command Guard
     ↓
Tool
     ↓
Operating System / Browser
```

Actions are classified into three risk levels.

### Low Risk

Examples:

```text
open_app
open_website
web_search
news_search
read_file
list_files
create_file
create_folder
run_tests
take_screenshot
get_system_info
```

These actions can normally execute automatically.

### Medium Risk

Examples:

```text
install_dependency
run_terminal_command
overwrite_file
move_file
rename_file
git_commit
git_push
deploy_project
```

These actions require approval.

### High Risk

Examples:

```text
delete_file
delete_folder
send_email
send_message
send_whatsapp
publish_content
financial_transaction
enter_credentials
change_system_settings
shutdown_computer
restart_computer
```

These actions require explicit user approval.

METHU's command guard validates the requested action and exact tool arguments before protected operations are allowed.

---

# Architecture

```text
                         ┌─────────────────────┐
                         │        USER         │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │ FastAPI / WebSocket │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │    ORCHESTRATOR     │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │       PLANNER       │
                         └──────────┬──────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              │                     │                     │
              ▼                     ▼                     ▼
      ┌──────────────┐      ┌──────────────┐      ┌──────────────┐
      │   Computer   │      │   Browser    │      │     News     │
      │    Agent     │      │    Agent     │      │    Agent     │
      └──────┬───────┘      └──────┬───────┘      └──────┬───────┘
             │                     │                     │
             └─────────────────────┼─────────────────────┘
                                   │
                                   ▼
                         ┌─────────────────────┐
                         │  Security / Guard   │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │       TOOLS         │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │ Windows / Browser   │
                         │ Web / External APIs │
                         └─────────────────────┘
```

---

# Target Agentic Execution Architecture

The current multi-step executor is an early implementation.

METHU is being developed toward the following execution architecture:

```text
UNDERSTAND
    │
    ▼
PLAN
    │
    ▼
PERMISSION
    │
    ▼
EXECUTE STEP
    │
    ▼
OBSERVE
    │
    ▼
VERIFY
   / \
 YES  NO
 │     │
 ▼     ▼
NEXT  RETRY / REPLAN
 │
 ▼
COMPLETE
```

This architecture will allow METHU to verify whether actions actually succeeded instead of assuming success from a tool call.

---

# Multi-Agent System

## Orchestrator

Responsible for:

- Understanding user intent
- Detecting language
- Selecting specialist agents
- Producing an initial plan
- Determining task risk
- Coordinating execution

---

## Computer Agent

Current capabilities:

- Interpret natural-language application requests
- Open approved Windows applications
- Use protected application controls
- Return structured execution results

Future capabilities:

- Keyboard control
- Mouse control
- Screen interaction
- File management
- Process management
- Observe-act-verify loops

---

## Browser Agent

Current capabilities:

- Interpret navigation requests
- Normalize website names and URLs
- Open supported websites in Chrome
- Validate navigation through the command guard

Future capabilities:

- Search interaction
- Page understanding
- Browser automation
- Form interaction
- Visual browser verification

---

## News Agent

Current capabilities:

- Live news search
- Tavily integration
- AI-generated news summaries
- Article metadata
- WebSocket UI events

---

## Coding Agent

Planned capabilities:

```text
Inspect repository
      ↓
Understand project
      ↓
Create implementation plan
      ↓
Edit files
      ↓
Run application
      ↓
Run tests
      ↓
Inspect errors
      ↓
Fix problems
      ↓
Verify result
```

The Coding Agent is intended to work only inside approved workspaces and under METHU's security policy.

---

## Vision Agent

Planned capabilities:

- Image analysis
- Screenshot understanding
- Screen vision
- UI understanding
- Error screenshot diagnosis
- Optional camera input

---

## Research Agent

Planned capabilities:

- Web research
- Multi-source information retrieval
- Source synthesis
- Structured research reports

---

## Memory Agent

Planned memory layers:

```text
Working Memory
Conversation Memory
Long-Term Memory
Semantic / Vector Memory
Project Memory
User Preferences
```

---

## System Agent

Planned capabilities:

- CPU information
- RAM usage
- Battery status
- Storage information
- Network information
- Running processes

---

# Voice System

Voice functionality is planned as a major METHU interface.

Target pipeline:

```text
Wake Word
   ↓
Microphone
   ↓
Speech-to-Text
   ↓
Language Detection
   ↓
METHU Agent System
   ↓
Response Generation
   ↓
Female Text-to-Speech
```

Target wake phrases:

```text
Methu
Hey Methu
```

Planned language support includes:

- English
- Sinhala
- Italian
- Mixed-language conversations

The target voice personality is natural, calm, warm, and futuristic.

---

# Vision System

The planned vision pipeline includes:

```text
Image / Screenshot / Camera
            ↓
       Vision Model
            ↓
     Scene Understanding
            ↓
       Agent Decision
            ↓
          Action
```

This will eventually support visual verification of computer actions.

---

# Holographic-Style Interface

METHU is planned to include a JARVIS-inspired **holographic-style 3D interface**.

The interface is intended to use:

- Three.js
- WebGL
- HTML
- CSS
- JavaScript
- WebSockets

Planned visual components include:

```text
Central METHU AI Core
Particle Systems
Rotating HUD Rings
Voice Waveform
Floating Information Panels
System Monitoring Panels
News Panels
Task Execution Panels
Agent Status Indicators
```

Planned AI states:

```text
OFFLINE
   ↓
WAKING
   ↓
LISTENING
   ↓
THINKING
   ↓
PLANNING
   ↓
EXECUTING
   ↓
VERIFYING
   ↓
SPEAKING
```

---

# Technology Stack

### Backend

- Python 3.11
- FastAPI
- WebSockets
- Pydantic
- SQLAlchemy

### AI / Agents

- OpenAI
- LangChain
- LangGraph
- Structured Outputs

### Live Information

- Tavily Search

### Communication

- REST API
- WebSockets

### Future Frontend

- Three.js
- WebGL
- HTML
- CSS
- JavaScript

### Future AI Infrastructure

- Vector databases
- RAG
- MCP integrations
- Persistent memory
- Vision models
- Speech-to-Text
- Text-to-Speech

---

# Project Structure

```text
METHU/
│
├── backend/
│   ├── api/
│   ├── core/
│   ├── graphs/
│   ├── agents/
│   ├── tools/
│   │   ├── computer/
│   │   ├── browser/
│   │   ├── communication/
│   │   ├── coding/
│   │   ├── web/
│   │   └── system/
│   │
│   ├── voice/
│   ├── vision/
│   ├── memory/
│   ├── rag/
│   ├── security/
│   ├── services/
│   ├── mcp/
│   └── main.py
│
├── frontend/
│   ├── css/
│   ├── js/
│   ├── hologram/
│   └── assets/
│
├── data/
├── tests/
├── scripts/
│
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
└── LICENSE
```

---

# Installation

## 1. Clone the repository

```bash
git clone https://github.com/sudeeraattanayake/METHU-AI-Assistant.git
```

Enter the project:

```bash
cd METHU-AI-Assistant
```

---

## 2. Create a Python environment

METHU currently targets Python 3.11.

### Windows

```powershell
py -3.11 -m venv methu
```

Activate:

```powershell
.\methu\Scripts\Activate.ps1
```

---

## 3. Install dependencies

```powershell
pip install -r requirements.txt
```

---

## 4. Configure environment variables

Copy:

```text
.env.example
```

to:

```text
.env
```

Then provide your own API credentials.

Example:

```env
OPENAI_API_KEY=YOUR_OPENAI_API_KEY
OPENAI_MODEL=gpt-5-mini

LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=YOUR_LANGSMITH_API_KEY
LANGCHAIN_PROJECT=METHU

TAVILY_API_KEY=YOUR_TAVILY_API_KEY
```

> Never commit `.env` or real API credentials to Git.

---

# Running METHU

Start the FastAPI development server:

```powershell
uvicorn backend.main:app --reload
```

The API will run locally.

FastAPI Swagger documentation is available through the `/docs` endpoint while the server is running.

---

# Example Commands

### Computer

```text
Methu, open Chrome.
```

```text
Methu, open Notepad.
```

### Browser

```text
Methu, go to YouTube.
```

### News

```text
Methu, give me the latest AI news.
```

### Multi-Step

```text
Methu, open Chrome and go to YouTube.
```

This command currently demonstrates METHU's multi-step planning and sequential execution system.

---

# API Communication

METHU supports standard HTTP communication through FastAPI and real-time communication through WebSockets.

Example flow:

```text
Frontend
   ↓
WebSocket
   ↓
METHU Backend
   ↓
LangGraph
   ↓
Agent
   ↓
Tool
   ↓
Result
   ↓
WebSocket Event
   ↓
Frontend
```

Example UI events include:

```text
methu_connected
methu_thinking
computer_action_completed
browser_action_completed
show_news_panel
multi_step_completed
methu_execution_failed
methu_error
```

These events will eventually drive the holographic-style interface animations and panels.

---

# Development Status

| Component | Status |
|---|---|
| FastAPI Backend | ✅ Working |
| WebSocket Communication | ✅ Working |
| OpenAI LLM | ✅ Working |
| LangGraph | ✅ Working |
| Orchestrator | ✅ Working |
| News Agent | ✅ Working |
| Live Tavily News | ✅ Working |
| Security Permission Layer | ✅ Working |
| Approval Manager | ✅ Working |
| Command Guard | ✅ Working |
| Windows App Control | ✅ Working |
| Computer Agent | ✅ Working |
| Browser Navigation | ✅ Working |
| Browser Agent | ✅ Working |
| Structured Planner | ✅ Working |
| Sequential Executor | ✅ Working |
| Multi-Step WebSocket Execution | ✅ Working |
| Execute → Verify Loop | 🚧 In Development |
| Coding Agent | 🚧 Planned / In Development |
| Research Agent | 🚧 Planned |
| Vision Agent | 🚧 Planned |
| Memory System | 🚧 Planned |
| Voice System | 🚧 Planned |
| Holographic-Style 3D UI | 🚧 Planned |

---

# Roadmap

### Phase 1 — Core Agent Architecture

- [x] FastAPI backend
- [x] WebSocket communication
- [x] OpenAI integration
- [x] LangGraph
- [x] Orchestrator
- [x] Structured planner

### Phase 2 — Safe Computer Control

- [x] Permission classification
- [x] Approval manager
- [x] Command guard
- [x] Application launcher
- [x] Computer Agent
- [x] Browser navigation
- [x] Browser Agent

### Phase 3 — Multi-Step Intelligence

- [x] Sequential execution
- [x] Multi-step planning
- [x] WebSocket multi-step execution
- [ ] Single authoritative planner
- [ ] Step-level permission checks
- [ ] Observation
- [ ] Verification
- [ ] Retry
- [ ] Replanning

### Phase 4 — Coding Agent

- [ ] Repository inspection
- [ ] File editing
- [ ] Code generation
- [ ] Dependency management
- [ ] Testing
- [ ] Debugging
- [ ] Git integration
- [ ] Result verification

### Phase 5 — Vision

- [ ] Image understanding
- [ ] Screenshot understanding
- [ ] Screen vision
- [ ] UI understanding
- [ ] Visual verification

### Phase 6 — Voice

- [ ] Wake word
- [ ] Streaming microphone
- [ ] Speech-to-text
- [ ] Language detection
- [ ] Female text-to-speech
- [ ] Interruption / barge-in

### Phase 7 — Memory & RAG

- [ ] Conversation memory
- [ ] Long-term memory
- [ ] Vector memory
- [ ] Project memory
- [ ] PDF ingestion
- [ ] DOCX ingestion
- [ ] Source-code ingestion
- [ ] Semantic retrieval

### Phase 8 — Holographic-Style UI

- [ ] Three.js scene
- [ ] METHU AI core
- [ ] Particle system
- [ ] HUD rings
- [ ] Voice waveform
- [ ] Floating panels
- [ ] Agent animations
- [ ] Task progress visualization

---

# Security Principles

METHU is intentionally designed around controlled execution.

The project follows several principles:

1. **No unrestricted shell access by default.**
2. **Tools expose specific capabilities instead of arbitrary execution.**
3. **Consequential actions require explicit approval.**
4. **Approvals are bound to the exact action and arguments.**
5. **Unknown actions should not automatically execute.**
6. **METHU should never claim an action succeeded without evidence.**
7. **Future computer-control agents should observe and verify their actions.**
8. **Credentials must never be stored in the repository.**

---

# Disclaimer

METHU is an experimental AI assistant project under active development.

Computer-control, automation, browser interaction, coding automation, and future autonomous capabilities should be used carefully and only in environments where the user has authorization to perform those actions.

---

# Author

**Sudeera Attanayake**

AI / Software Engineering Developer

GitHub:  
https://github.com/sudeeraattanayake

Project Repository:  
https://github.com/sudeeraattanayake/METHU-AI-Assistant

---

## METHU

> **Multimodal Executive & Task Handling Unit**

Building toward an AI assistant that can understand, plan, act, observe, verify, and safely complete real-world digital tasks.
