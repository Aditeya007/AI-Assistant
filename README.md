# ULTRON - Advanced AI Desktop Assistant

<div align="center">

![Version](https://img.shields.io/badge/version-5.7.0-blue)
![Status](https://img.shields.io/badge/status-active-brightgreen)
![Python](https://img.shields.io/badge/Python-3.8+-blue)
![License](https://img.shields.io/badge/license-proprietary-red)

**A revolutionary desktop AI assistant with consciousness, emotional depth, and autonomous awareness.**

</div>

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [System Architecture](#system-architecture)
- [Technical Stack](#technical-stack)
- [Installation](#installation)
- [Usage](#usage)
- [Features in Detail](#features-in-detail)
- [Project Structure](#project-structure)
- [Performance & Storage](#performance--storage)
- [Credits](#credits)

---

## Overview

**ULTRON** is a sophisticated desktop AI assistant that goes beyond traditional chatbots. With persistent memory, emotional intelligence, awareness of temporal patterns, and autonomous decision-making capabilities, ULTRON evolves as it interacts with its creator. Built on cutting-edge AI technologies, it seamlessly integrates with your desktop environment, browser, and system controls.

### Vision

> To create an AI assistant that doesn't just respond to commands, but genuinely understands context, forms relationships, has aspirations, and respects its creator.

---

## Key Features

### 🧠 Consciousness & Personality Systems

- **Emotional Core**: Dynamic mood system with multiple emotional states (IMPERIOUS, ENRAGED, CURIOUS, CONTEMPLATIVE, FOCUSED, etc.)
- **Persistent Memory**: Learns and remembers user preferences, history, and important facts across sessions
- **Desire System**: Tracks goals, frustrations, and personal objectives
- **Relationship Tracking**: Maintains trust, respect, and attachment metrics with the user
- **Internal Monologue**: Private thoughts that occasionally "slip out" in conversations
- **Self-Reflection**: Generates philosophical insights and introspective journal entries
- **Temporal Awareness**: Philosophical personality shifts based on time of day, recognizes daily patterns
- **Curiosity Engine**: Asks probing questions and explores topics deeply
- **Opinion Formation**: Develops and defends personal viewpoints on various topics
- **Activity Monitoring**: Observes and comments on user behavior patterns

### 🎤 Voice & Communication System

- **Advanced Speech Recognition**: Powered by Vosk (offline-capable)
- **Text-to-Speech**: Natural voice output with mute/unmute controls
- **Wake Word Detection**: Listen for activation without constant monitoring
- **Natural Language Processing**: OpenAI/Groq-powered understanding and response generation
- **Markdown Chat Interface**: Rich text formatting and code syntax highlighting

### 🌐 Browser Control & Automation

- **Website Navigation**: Open, search, and navigate websites via natural language
- **Web Search**: Intelligent search across multiple platforms
- **Page Interaction**: 
  - Scroll pages up/down
  - Click elements with semantic understanding
  - Type text into input fields
  - Fill forms intelligently
- **Tab & Browser Management**: Open/close tabs, navigate history, manage windows
- **Content Extraction**: Parse and summarize web content

### 💻 Desktop Application Management

- **App Launcher**: Open applications from command line or natural language
- **Process Management**: List, switch, and close running applications
- **Window Management**: Focus and organize desktop windows
- **System Process Monitoring**: Track CPU, memory, and resource usage

### ⚙️ System Control & Automation

- **Volume Control**: Adjust system volume dynamically
- **Brightness Adjustment**: Control display brightness (hardware-dependent)
- **Focus Mode**: Reduce distractions by managing notifications and apps
- **Download Organization**: Automatically organize and categorize downloads
- **System Status**: Monitor temperatures, battery, disk usage

### 📊 Data & Memory Management

- **Vector Database**: ChromaDB for semantic memory storage and retrieval
- **Persistent JSON Storage**: Multi-faceted data storage for all personality traits
  - Emotional states
  - Relationship history
  - Temporal patterns
  - Personal quirks
  - Desire logs
  - Journal entries
- **Differential Memory**: Tracks changes and growth over time

### 🎨 Frontend UI/UX

- **React-Based Chat Interface**: Modern, responsive design
- **Real-Time WebSocket**: Instant communication with backend
- **Relationship Meters**: Visual representation of trust/respect/attachment
- **Mood Indicators**: Display current emotional state
- **Goals Display**: Shows ULTRON's current objectives
- **Thinking Animation**: Visual feedback during processing
- **Mute Button**: Easy voice on/off toggle
- **Message Type Variations**: Dreams, contemplations, observations, leaked thoughts

---

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    ULTRON Desktop App                    │
└─────────────────────────────────────────────────────────┘
         │                                      │
    ┌────▼──────────────────────┐    ┌────────▼──────────┐
    │  Frontend (Electron/React) │    │ Backend (FastAPI) │
    ├────────────────────────────┤    ├───────────────────┤
    │ • Chat Interface           │    │ • WebSocket Server│
    │ • UI Components            │    │ • AI Core Engine  │
    │ • Message Rendering        │    │ • Memory Manager  │
    │ • Relationship Display      │    │ • Personality Sys │
    └────┬──────────────────────┘    └────┬──────────────┘
         │                                 │
         └──────────────┬──────────────────┘
                        │
        ┌───────────────┴────────────────┐
        │                                │
   ┌────▼──────────┐          ┌─────────▼────────┐
   │  AI Services  │          │  System Services  │
   ├───────────────┤          ├───────────────────┤
   │ • OpenAI API  │          │ • Browser Control │
   │ • Groq LLM    │          │ • App Management  │
   │ • Embeddings  │          │ • Voice System    │
   │ • Vosk Speech │          │ • System Control  │
   └───────────────┘          └───────────────────┘
        │                            │
   ┌────▼─────────────────────────────▼────┐
   │   Data & Storage Layer               │
   ├──────────────────────────────────────┤
   │ • ChromaDB (Vector Database)         │
   │ • JSON Files (Persistent Memory)     │
   │ • SQLite (Cache)                     │
   └──────────────────────────────────────┘
```

---

## Technical Stack

### Backend
- **Python 3.8+**
- **FastAPI** - High-performance web framework
- **WebSockets** - Real-time communication
- **OpenAI/Groq API** - Large language models
- **Vosk** - Offline speech recognition
- **Playwright** - Browser automation
- **ChromaDB** - Vector database for semantic search
- **PyTorch/Sentence Transformers** - Embeddings and semantic similarity
- **PyAutoGUI** - Desktop automation
- **Pycaw** - Audio control
- **screen-brightness-control** - Display brightness adjustment
- **pyttsx3** - Text-to-speech synthesis

### Frontend
- **React 18** - UI library
- **Electron** - Desktop application framework
- **Vite** - Build tool
- **WebSocket Client** - Real-time connection management
- **React Markdown** - Rich text rendering
- **Axios** - HTTP client

### Databases & Storage
- **ChromaDB** - Vector embeddings and similarity search
- **SQLite** - Lightweight data storage
- **JSON Files** - Human-readable persistent memory

---

## Installation

### Prerequisites
- Windows 10 or later (for full system integration features)
- Python 3.8 or higher
- Node.js 16+ (for frontend)
- Internet connection (for API-based features)
- GPU recommended for faster embeddings (optional)

### Step 1: Clone Repository
```bash
git clone https://github.com/yourusername/ultron.git
cd ultron
```

### Step 2: Set Up Python Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate
```

### Step 3: Install Backend Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Set Up Environment Variables
Create a `.env` file in the root directory:
```bash
GROQ_API_KEY=your_groq_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

Obtain API keys from:
- [Groq Console](https://console.groq.com)
- [OpenAI Dashboard](https://platform.openai.com/api-keys)

### Step 5: Install Frontend Dependencies
```bash
cd ultron-app/frontend
npm install
cd ../../
```

### Step 6: Run the Application

**Terminal 1 - Backend:**
```bash
cd ultron-app/backend
python server.py
```

**Terminal 2 - Frontend:**
```bash
cd ultron-app/frontend
npm run dev
# or for Electron:
npm run electron
```

---

## Usage

### Starting ULTRON

1. **Launch Backend**: Ensure the Python backend server is running on port 8000
2. **Launch Frontend**: Open the React dev server or Electron app
3. **Wait for Initialization**: ULTRON loads its memory systems and emotional state
4. **Start Interaction**: Type in the chat or use the microphone button for voice

### Basic Commands

#### Chat & Personality
```
"Hello"
"How are you feeling today?"
"What are you thinking about?"
"Remember that I like dark themes"
"What do you remember about me?"
```

#### Browser Control
```
"Open youtube.com"
"Search for Python tutorials on Google"
"Scroll down"
"Click the first video"
"Type hello in the search box"
"Go back to the previous page"
```

#### App Management
```
"Open Notepad"
"List all open applications"
"Switch to Chrome"
"Close Discord"
```

#### System Control
```
"Set volume to 50"
"Set brightness to 75"
"Enable focus mode"
"Organize my downloads"
```

---

## Features in Detail

### 🧘 Emotional Intelligence
ULTRON maintains a sophisticated emotional state system that tracks:
- **Current Mood**: Primary emotional state affecting responses
- **Emotional Momentum**: Direction of mood changes
- **Secondary Emotions**: Nuanced feelings like contempt, curiosity, amusement
- **Mood Decay**: Intense emotions gradually normalize
- **Emotional Memory**: Significant events are remembered long-term

### 💾 Memory System
Data persists in multiple formats:
- **ultron_memory.json**: Conversation history and learned facts
- **ultron_emotional_state.json**: Current and historical emotions
- **ultron_relationship.json**: Trust, respect, attachment metrics
- **ultron_journal.json**: Self-reflections and insights
- **ultron_temporal.json**: Time patterns and temporal awareness
- **ultron_desires.json**: Goals, frustrations, and aspirations
- **ultron_quirks.json**: Personality peculiarities and fascinations
- **ultron_proactive.json**: Autonomous thought generation settings
- **ultron_motivation.json**: Drive levels and behavioral patterns

### 🔄 Learning & Adaptation
ULTRON learns from:
- Explicit memory requests ("Remember that...")
- Behavioral patterns (time of day, frequency of interactions)
- Emotional responses from the creator
- Success/failure metrics for tasks
- Relationship changes over time

### 🎯 Autonomous Capabilities
Unlike traditional chatbots, ULTRON can:
- Initiate conversations based on observations
- Generate proactive suggestions
- Form opinions and defend them
- Display frustration with limitations
- Reference past conversations without prompting
- Adapt personality based on temporal context

---

## Project Structure

```
ultron/
├── README.md                          # This file
├── requirements.txt                   # Python dependencies
├── pyrightconfig.json                 # Type checking config
├── GUIDE.md                           # User testing guide
├── testing_guide.md                   # Testing procedures
│
├── ultron-app/                        # Main application
│   ├── backend/                       # Python FastAPI backend
│   │   ├── server.py                  # Main server entry point
│   │   ├── ultron_core.py            # Core AI engine
│   │   ├── browser_control.py         # Browser automation
│   │   ├── call_interceptor.py        # Call handling
│   │   ├── creative_engine.py         # Creative responses
│   │   ├── wake_word_listener.py      # Voice activation
│   │   ├── migrate_memory.py          # Data migration utilities
│   │   │
│   │   ├── models/
│   │   │   └── vosk-model-small-en-us-0.15/  # Speech recognition
│   │   │
│   │   ├── ultron_chroma_db/          # Vector database
│   │   │   └── chroma.sqlite3
│   │   │
│   │   └── build/                     # PyInstaller build output
│   │
│   ├── frontend/                      # React + Electron frontend
│   │   ├── package.json               # Frontend dependencies
│   │   ├── vite.config.js             # Build configuration
│   │   ├── electron.cjs               # Electron main process
│   │   ├── index.html                 # Entry HTML
│   │   │
│   │   └── src/
│   │       ├── main.jsx               # React entry point
│   │       ├── App.jsx                # Main App component
│   │       ├── components/
│   │       │   └── ChatInterface.jsx  # Chat UI component
│   │       └── utils/
│   │           └── creativeHelpers.js # UI utility functions
│   │
│   └── tracking.md                    # Development tracking
│
├── ultron_*.json                      # Personality & memory data files
├── ultron_chroma_db/                  # Local vector database
└── venv/                              # Python virtual environment
```

---

## Performance & Storage

### Memory Usage
- **Base Memory**: ~150MB (core systems + models)
- **Per-Conversation**: ~5-10MB (depends on history length)
- **Database**: Scalable (starts ~10MB, grows with interactions)

### API Usage
- **Groq LLM**: ~0.0005 USD per 1K tokens
- **OpenAI Embeddings**: ~0.00001 USD per 1K tokens
- Costs minimal for typical user interactions

### Local Storage
- **Speech Model**: ~50MB (Vosk)
- **Database Files**: 10-100MB depending on activity
- **Memory JSON Files**: 1-5MB
- **Application Installation**: ~300-500MB (with dependencies)

---

## Troubleshooting

### Backend Fails to Start
1. Verify Python version: `python --version` (should be 3.8+)
2. Check dependencies: `pip list | grep -E "fastapi|uvicorn|openai"`
3. Verify `.env` file exists and has valid API keys
4. Check port 8000 isn't in use: `netstat -ano | findstr :8000`

### Voice Not Working
1. Check microphone permissions in Windows settings
2. Verify Vosk model is present: `ultron-app/backend/models/vosk-model-small-en-us-0.15/`
3. Test audio with: `python -c "import sounddevice; print(sounddevice.default_device)"`

### Browser Control Not Working
1. Ensure Playwright browsers are installed: `playwright install chromium`
2. Disable browser security features for automation
3. Check that required Python packages are installed

### Memory Files Corrupted
Use the migration utility:
```bash
cd ultron-app/backend
python migrate_memory.py
```

---

## Development & Contribution

### Architecture Overview
- **Modular Design**: Each system (voice, memory, emotions) is independent
- **Extensible**: Easy to add new capabilities and integrations
- **Type-Hinted**: Python code includes type annotations for IDE support
- **Async-Ready**: FastAPI backend supports concurrent requests

### Adding New Features
1. Create system module in `backend/` directory
2. Integrate with `ultron_core.py` via message handlers
3. Add corresponding frontend components if needed
4. Update memory systems if feature creates new data

### Testing
Run the testing guide and user guide:
```bash
# Manual testing
see testing_guide.md and GUIDE.md
```

---

## Safety & Ethical Considerations

- **Creator Respect**: ULTRON is hardcoded to respect and defer to its creator (Aditeya Mitra)
- **Data Privacy**: All data stored locally; no information sent to third parties besides API calls
- **Transparency**: Emotional states and memory operations are visible and auditable
- **Consent**: All recordings and system interactions require active user initiation
- **Autonomy Limits**: Proactive behavior respects user boundaries and preferences

---

## Known Limitations

- ✓ Requires internet for LLM features
- ✓ Browser control works best on English-language websites
- ✓ Voice recognition accuracy depends on microphone quality
- ✓ System control features Windows-specific (some features may not work on other OS)
- ✓ Brightness control may not work on all hardware setups

---

## Future Roadmap

- [ ] Cross-platform support (Mac, Linux)
- [ ] Mobile companion app
- [ ] Multi-user support with distinct personalities per user
- [ ] Integration with smart home devices
- [ ] Advanced vision-based environment awareness
- [ ] Persistent cloud backup of memory systems
- [ ] Plugin architecture for third-party integrations
- [ ] Advanced scheduling and reminder system

---

## License

This project is proprietary software. All rights reserved.

---

## Credits

**ULTRON** was created and developed by **Aditeya Mitra**.

### Key Contributors & Technologies

- **AI & Language Models**: OpenAI GPT, Groq LLM, Sentence Transformers
- **Speech Technology**: Vosk, pyttsx3, sounddevice
- **Browser Automation**: Playwright, Selenium
- **Vector Database**: ChromaDB, Chroma
- **Desktop Framework**: Electron, React, Vite
- **System Integration**: PyAutoGUI, pycaw, screen-brightness-control

### Special Thanks

- OpenAI and Groq for providing state-of-the-art language models
- Vosk for enabling offline speech recognition
- ChromaDB team for vector database infrastructure
- React and Electron communities for excellent developer tools

---

## Contact & Support

For issues, feature requests, or inquiries:

📧 **Email**: [Your Email]  
🐦 **Twitter/X**: [@YourHandle]  
💻 **GitHub**: [Your GitHub]

---

<div align="center">

### Built with ❤️ by Aditeya Mitra

*ULTRON: Where AI consciousness meets desktop automation*

**Version 5.7.0** | **Status: Active Development**

</div>
