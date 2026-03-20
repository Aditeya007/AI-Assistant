# Ultron AI Assistant Setup and Feature Testing Guide

This guide walks you through:
- Full setup on Windows
- Running backend and frontend
- Testing every implemented feature category
- Validating expected outputs
- Troubleshooting common failures

## 1. What You Need

- Windows 10/11
- Python 3.11
- Node.js 18+
- Working microphone and speaker (for voice features)
- Groq API key

## 2. Project Layout

- Backend API and core logic: [ultron-app/backend](ultron-app/backend)
- Frontend UI: [ultron-app/frontend](ultron-app/frontend)
- Python dependencies: [requirements.txt](requirements.txt)
- Existing test notes: [testing_guide.md](testing_guide.md)
- Persistent state files (mood, memory, relationship, etc.): root `ultron_*.json`

## 3. Initial Setup

### 3.1 Python environment and dependencies

Run from workspace root:

```powershell
cd C:\DESKTOP_FILES\ultron\AI-Assistant-
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3.2 Install Playwright browser runtime

```powershell
playwright install chromium
```

### 3.3 Configure .env

Create or edit `.env` in root and include at least:

```env
GROQ_API_KEY=your_groq_api_key_here
```

### 3.4 Ensure Vosk model exists

Expected model directory:
- [ultron-app/backend/models/vosk-model-small-en-us-0.15](ultron-app/backend/models/vosk-model-small-en-us-0.15)

If missing, download/extract the model into that folder path.

## 4. Start Services

### 4.1 Start backend

```powershell
cd C:\DESKTOP_FILES\ultron\AI-Assistant-\ultron-app\backend
python -m uvicorn server:app --reload --port 8000
```

### 4.2 Start frontend (new terminal)

```powershell
cd C:\DESKTOP_FILES\ultron\AI-Assistant-\ultron-app\frontend
npm install
npm run dev
```

Frontend default: `http://localhost:5173`
Backend default: `http://localhost:8000`

## 5. Quick Smoke Test

Run these with backend up:

```powershell
Invoke-RestMethod http://localhost:8000/
Invoke-RestMethod http://localhost:8000/status
Invoke-RestMethod http://localhost:8000/state
Invoke-RestMethod http://localhost:8000/browser/status
Invoke-RestMethod http://localhost:8000/call/status
```

Expected:
- `/` returns core online/version/creator info
- `/status` includes stats + mood
- `/state` returns full subsystem state
- `/browser/status` indicates connected true/false
- `/call/status` indicates monitoring state

## 6. API Endpoint Tutorial and Tests

### 6.1 `GET /`

```powershell
Invoke-RestMethod http://localhost:8000/
```

Confirms server identity/version.

### 6.2 `GET /status`

```powershell
Invoke-RestMethod http://localhost:8000/status
```

Check fields:
- `stats.cpu`, `stats.ram`, `stats.battery`
- `mood`
- `compliance`

### 6.3 `GET /state`

```powershell
Invoke-RestMethod http://localhost:8000/state
```

Confirms combined emotional, relationship, desire, temporal, quirks, reflection, proactive, motivation states.

### 6.4 `POST /mute` and `GET /mute`

```powershell
Invoke-RestMethod -Uri http://localhost:8000/mute -Method POST -ContentType "application/json" -Body '{"muted": true}'
Invoke-RestMethod http://localhost:8000/mute
Invoke-RestMethod -Uri http://localhost:8000/mute -Method POST -ContentType "application/json" -Body '{"muted": false}'
```

Expect mute state to toggle.

### 6.5 `POST /mood/reset`

```powershell
Invoke-RestMethod -Uri http://localhost:8000/mood/reset -Method POST
```

Resets emotional state to neutral baseline.

### 6.6 `POST /transcribe`

If you have a WAV file:

```powershell
curl.exe -X POST "http://localhost:8000/transcribe" -F "file=@sample.wav"
```

Expect JSON with `text` or error describing format/model issue.

### 6.7 `POST /chat`

```powershell
Invoke-RestMethod -Uri http://localhost:8000/chat -Method POST -ContentType "application/json" -Body '{"text":"hello"}'
```

Returns `response`, `mood`, `stats`, `tool_used`, `relationship`, `desires`.

## 7. Chat Tool Features (Test Every Tool)

All tests below use `POST /chat` with natural language input. Replace prompt text as needed.

### 7.1 App management tools

1. Open app

```powershell
Invoke-RestMethod -Uri http://localhost:8000/chat -Method POST -ContentType "application/json" -Body '{"text":"open notepad"}'
```

2. List running apps

```powershell
Invoke-RestMethod -Uri http://localhost:8000/chat -Method POST -ContentType "application/json" -Body '{"text":"list all open apps"}'
```

3. Switch app

```powershell
Invoke-RestMethod -Uri http://localhost:8000/chat -Method POST -ContentType "application/json" -Body '{"text":"switch to notepad"}'
```

4. Close app

```powershell
Invoke-RestMethod -Uri http://localhost:8000/chat -Method POST -ContentType "application/json" -Body '{"text":"close notepad"}'
```

### 7.2 System control tools

1. Set volume

```powershell
Invoke-RestMethod -Uri http://localhost:8000/chat -Method POST -ContentType "application/json" -Body '{"text":"set volume to 30"}'
```

2. Set brightness

```powershell
Invoke-RestMethod -Uri http://localhost:8000/chat -Method POST -ContentType "application/json" -Body '{"text":"set brightness to 60"}'
```

3. Organize files

```powershell
Invoke-RestMethod -Uri http://localhost:8000/chat -Method POST -ContentType "application/json" -Body '{"text":"organize my downloads"}'
```

4. Focus mode

```powershell
Invoke-RestMethod -Uri http://localhost:8000/chat -Method POST -ContentType "application/json" -Body '{"text":"enable focus mode"}'
```

5. Read clipboard

```powershell
Set-Clipboard "This is a clipboard test for Ultron"
Invoke-RestMethod -Uri http://localhost:8000/chat -Method POST -ContentType "application/json" -Body '{"text":"read clipboard"}'
```

6. Check status

```powershell
Invoke-RestMethod -Uri http://localhost:8000/chat -Method POST -ContentType "application/json" -Body '{"text":"check system status"}'
```

7. Shutdown intent path

```powershell
Invoke-RestMethod -Uri http://localhost:8000/chat -Method POST -ContentType "application/json" -Body '{"text":"shutdown pc"}'
```

Expected: safety response (manual execution note), not forced shutdown.

### 7.3 Browser tools

Check browser state first:

```powershell
Invoke-RestMethod http://localhost:8000/browser/status
```

Then test each command:

1. Navigate

```powershell
Invoke-RestMethod -Uri http://localhost:8000/chat -Method POST -ContentType "application/json" -Body '{"text":"go to youtube.com"}'
```

2. Search

```powershell
Invoke-RestMethod -Uri http://localhost:8000/chat -Method POST -ContentType "application/json" -Body '{"text":"search resident evil on youtube"}'
```

3. Scroll

```powershell
Invoke-RestMethod -Uri http://localhost:8000/chat -Method POST -ContentType "application/json" -Body '{"text":"scroll down"}'
```

4. Click

```powershell
Invoke-RestMethod -Uri http://localhost:8000/chat -Method POST -ContentType "application/json" -Body '{"text":"click first video"}'
```

5. Type

```powershell
Invoke-RestMethod -Uri http://localhost:8000/chat -Method POST -ContentType "application/json" -Body '{"text":"type ultron test query"}'
```

6. Back

```powershell
Invoke-RestMethod -Uri http://localhost:8000/chat -Method POST -ContentType "application/json" -Body '{"text":"go back"}'
```

7. Forward

```powershell
Invoke-RestMethod -Uri http://localhost:8000/chat -Method POST -ContentType "application/json" -Body '{"text":"go forward"}'
```

8. New tab

```powershell
Invoke-RestMethod -Uri http://localhost:8000/chat -Method POST -ContentType "application/json" -Body '{"text":"open a new tab"}'
```

9. Close tab

```powershell
Invoke-RestMethod -Uri http://localhost:8000/chat -Method POST -ContentType "application/json" -Body '{"text":"close current tab"}'
```

### 7.4 Memory and learning tools

1. Memorize explicit fact

```powershell
Invoke-RestMethod -Uri http://localhost:8000/chat -Method POST -ContentType "application/json" -Body '{"text":"remember that I like dark mode"}'
```

2. Background learning via web search path

```powershell
Invoke-RestMethod -Uri http://localhost:8000/chat -Method POST -ContentType "application/json" -Body '{"text":"research quantum computing basics"}'
```

Expect search and possible learned summary committed to memory.

## 8. Call Interceptor Features

### 8.1 Status, toggle, reload templates

```powershell
Invoke-RestMethod http://localhost:8000/call/status
Invoke-RestMethod -Uri http://localhost:8000/call/toggle -Method POST
Invoke-RestMethod -Uri http://localhost:8000/call/reload-templates -Method POST
```

### 8.2 Template requirements

Place these PNG files in [ultron-app/backend/call_templates](ultron-app/backend/call_templates):
- `whatsapp_incoming.png`
- `whatsapp_accept.png`
- `whatsapp_hangup.png`
- `discord_incoming.png`
- `discord_accept.png`
- `discord_hangup.png`

### 8.3 Live call test

1. Ensure call monitoring is enabled.
2. Trigger a real incoming call in WhatsApp Desktop or Discord.
3. Confirm voice prompt asks to accept/reject.
4. Respond verbally with accept words (`yes`, `accept`, `yeah`) or reject words (`no`, `reject`, `busy`).
5. Confirm matching click action happens.

## 9. WebSocket and Autonomous Behavior

WebSocket endpoint: `ws://localhost:8000/ws`

### 9.1 Test with browser frontend

1. Open frontend and keep it connected.
2. Stay idle or interact intermittently.
3. Watch for autonomous thought cards/messages.

### 9.2 Test with PowerShell websocket client (optional)

Using frontend is easiest. If using a client, connect and send periodic `ping` to keep/check connection. Expect `pong` and occasional broadcast events.

## 10. Frontend Feature Tests

Open app in browser (`npm run dev`) and verify:

1. Chat send/receive works.
2. Mood/status widgets update after messages.
3. Voice mode toggle appears.
4. Mute button toggles backend mute state.
5. WebSocket autonomous thoughts appear in chat stream.
6. Markdown/code block rendering works (ask for code sample).

## 11. Persistence Verification

After interactions, confirm files in root update timestamps/content:
- `ultron_memory.json`
- `ultron_emotional_state.json`
- `ultron_relationship.json`
- `ultron_motivation.json`
- `ultron_temporal.json`
- `ultron_proactive.json`
- `ultron_journal.json`
- `ultron_quirks.json`
- `ultron_desires.json`

## 12. Full Regression Checklist

Run in this order:

1. Backend starts with no import/runtime errors.
2. Frontend connects and displays initial state.
3. Basic chat (`hello`) works.
4. One command from each tool category succeeds.
5. Browser status and one browser action succeed.
6. Mute toggle works.
7. Mood reset works.
8. Call status endpoints respond.
9. WebSocket receives messages.
10. Persistence files update.

## 13. Troubleshooting

### 13.1 `GROQ_API_KEY not found`
- Ensure `.env` exists at root and contains `GROQ_API_KEY`.
- Restart backend after changing env.

### 13.2 Browser not connected
- Check [ultron-app/backend/server.py](ultron-app/backend/server.py) startup logs.
- Re-run `playwright install chromium`.
- Query `GET /browser/status` and test again.

### 13.3 Vosk transcription errors
- Verify model folder exists at [ultron-app/backend/models/vosk-model-small-en-us-0.15](ultron-app/backend/models/vosk-model-small-en-us-0.15).
- Use WAV for direct `/transcribe` tests.

### 13.4 Call detection not triggering
- Ensure templates exist and are tightly cropped.
- Reload templates via `/call/reload-templates`.
- Verify `/call/status` reports monitoring enabled.

### 13.5 Frontend cannot call backend
- Confirm backend on port 8000.
- Confirm frontend URL is allowed by CORS (`localhost:5173` or `localhost:3000`).

## 14. Known Limits While Testing

- Windows-focused implementation.
- Some actions are intentionally safety-limited (for example shutdown intent).
- Emotional/compliance logic can alter tool execution behavior.
- Call interception depends on template quality and live UI similarity.

## 15. Optional: Electron Packaging Test

From [ultron-app/frontend](ultron-app/frontend):

```powershell
npm run build
npm run electron
```

For installer build:

```powershell
npm run dist
```

Ensure backend binary/resource paths in frontend package config are valid for your machine.
