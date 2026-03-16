# 🤖 Ultron AI — Feature Testing Guide

> **All tests assume you are inside** `ultron-app/backend/` as the working directory.  
> The Vosk model (`vosk-model-small-en-us-0.15`) is already present and the path has been fixed in `server.py`.

---

## 🔧 Prerequisites (Do These First!)

### 1. Install Python Dependencies

```powershell
cd c:\DESKTOP_FILES\ultron\AI-Assistant-
pip install -r requirements.txt
```

### 2. Install Playwright Browsers

```powershell
playwright install chromium
```

### 3. Set Up Your `.env` File

Copy the example and fill in your **Groq API key**:

```powershell
copy .env.example .env
```

Open `.env` and set:
```
GROQ_API_KEY=your_groq_key_here
```

### 4. Verify Vosk Model Is Present

```powershell
dir models\
```

You should see **`vosk-model-small-en-us-0.15`** listed. If it's missing, download it:

```powershell
# Download the small English model (~40 MB)
Invoke-WebRequest -Uri "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip" -OutFile "vosk-model-small-en-us-0.15.zip"
Expand-Archive -Path "vosk-model-small-en-us-0.15.zip" -DestinationPath "models\"
Remove-Item "vosk-model-small-en-us-0.15.zip"
```

> [!IMPORTANT]
> The model path in `server.py` has already been corrected from the broken `vosk-model-en-us-0.22-lgraph` path to `models/vosk-model-small-en-us-0.15`.

### 5. Launch Chrome With Remote Debugging (For Browser Control)

Close all existing Chrome windows first, then run:

```powershell
Start-Process "chrome.exe" "--remote-debugging-port=9222"
```

> [!TIP]
> To make this permanent, right-click Chrome shortcut → Properties → add `--remote-debugging-port=9222` to the Target field.

### 6. Start the Backend Server

```powershell
cd c:\DESKTOP_FILES\ultron\AI-Assistant-\ultron-app\backend
python -m uvicorn server:app --reload --port 8000
```

Watch for these lines in the console confirming everything loaded:
```
Vosk model loaded successfully
Call Interceptor: ACTIVE
Browser Controller: READY (connect Chrome with --remote-debugging-port=9222)
```

---

## 🧪 Feature 1: App Management (Close / List / Switch)

These are tested via the `/chat` endpoint.

### Test A — List Running Apps

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/chat" -Method POST `
  -ContentType "application/json" `
  -Body '{"text": "list all open apps"}'
```

**Expected:** A bullet list of running processes and their window titles.

---

### Test B — Switch To a Running App

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/chat" -Method POST `
  -ContentType "application/json" `
  -Body '{"text": "switch to notepad"}'
```

**Expected:** Notepad window comes to the foreground. Response confirms the switch.

---

### Test C — Close an App

> [!CAUTION]
> This actually terminates the process. Make sure you have saved data first.

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/chat" -Method POST `
  -ContentType "application/json" `
  -Body '{"text": "close notepad"}'
```

**Expected:** Notepad closes. Response: `"Terminated: notepad.exe..."`

---

## 🌐 Feature 2: Browser Control (Playwright + CDP)

> **Requirement:** Chrome must be running with `--remote-debugging-port=9222` (see Prerequisite 5).

### Test A — Check Browser Connection

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/browser/status" -Method GET
```

**Expected:** `{"connected": true, "title": "New Tab", "url": "..."}`  
If you see `connected: false`, Chrome isn't running with the debug port.

---

### Test B — Navigate to a URL (via Chat)

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/chat" -Method POST `
  -ContentType "application/json" `
  -Body '{"text": "open youtube.com in the browser"}'
```

**Expected:** Chrome navigates to YouTube. Response confirms the page title.

---

### Test C — Search the Web via Browser

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/chat" -Method POST `
  -ContentType "application/json" `
  -Body '{"text": "search for latest AI news in browser"}'
```

**Expected:** Chrome opens Google search results for "latest AI news".

---

### Test D — Scroll the Page

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/chat" -Method POST `
  -ContentType "application/json" `
  -Body '{"text": "scroll down in the browser"}'
```

**Expected:** The page scrolls down 500px.

---

### Test E — Open / Close Tabs

```powershell
# Open new tab
Invoke-RestMethod -Uri "http://localhost:8000/chat" -Method POST `
  -ContentType "application/json" `
  -Body '{"text": "open a new browser tab"}'

# Close current tab
Invoke-RestMethod -Uri "http://localhost:8000/chat" -Method POST `
  -ContentType "application/json" `
  -Body '{"text": "close the current tab"}'
```

---

## 📞 Feature 3: Call Interception (OpenCV + Vosk + pyttsx3)

> [!NOTE]
> The call interceptor uses **OpenCV template matching** (no OCR). You must provide screenshot templates of the call UI for WhatsApp/Discord.

### Step 1 — Check Interceptor Status

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/call/status" -Method GET
```

**Expected output:**
```json
{
  "running": true,
  "monitoring": true,
  "templates_loaded": {"whatsapp": [], "discord": []},
  ...
}
```

If `monitoring: false`, enable it:

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/call/toggle" -Method POST
```

---

### Step 2 — Capture Call UI Templates

You need to capture screenshots of the **incoming call overlay**, **accept button**, and **hang up button** for each app. The simplest way is to:

1. Have a friend call you on **WhatsApp Desktop** or **Discord**
2. While the call overlay is visible, run this in a Python shell:

```python
import pyautogui, cv2, numpy as np

# Full screen capture (crop the call UI regions manually in paint)
screenshot = pyautogui.screenshot()
screenshot.save("call_templates/whatsapp_incoming.png")  # Crop to just the overlay!
```

> [!TIP]
> Crop precisely to just the notification banner. The template match confidence needs to be ≥ 0.75.  
> Files to create in `backend/call_templates/`:  
> - `whatsapp_incoming.png` — The call popup/overlay  
> - `whatsapp_accept.png` — The green accept button  
> - `whatsapp_hangup.png` — The red end-call button  
> - `discord_incoming.png`, `discord_accept.png`, `discord_hangup.png`

### Step 3 — Reload Templates After Adding Images

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/call/reload-templates" -Method POST
```

**Expected:** Status shows the templates are now loaded in `templates_loaded`.

---

### Step 4 — Simulate a Live Call Test

1. Have someone call you on WhatsApp Desktop or Discord
2. The interceptor will automatically:
   - Detect the call overlay (screenshots every 2s)
   - **Speak via pyttsx3**: *"Incoming call detected from whatsapp. Do you want to accept or reject?"*
   - **Listen for your voice** (4 seconds) using **Vosk** for offline speech recognition
   - If you say **"yes" / "accept" / "yeah"** — it clicks the accept button
   - If you say **"no" / "reject" / "busy"** — it picks up, says *"The user is busy right now"*, then hangs up

---

## 🎙️ Feature 4: Wake Word Detection (Vosk)

The wake word listener is part of `wake_word_listener.py` and uses the same Vosk model.

### Test — Verify Wake Words Are Recognized

With the server running, say one of these out loud near your microphone:
- **"Hey Ultron"**
- **"Jarvis"**
- **"Ultron"**

**Expected:** Server logs should show:
```
Wake word detected: 'hey ultron' in 'hey ultron what time is it'
```

---

## 🔊 Vosk Model — Confirming Correct Setup

The project uses **Vosk for all speech-to-text (STT)** across three components:

| Component | Vosk Usage |
|---|---|
| `server.py` | `/transcribe` endpoint — converts WAV audio to text |
| `call_interceptor.py` | Listens for "accept"/"reject" during call prompts |
| `wake_word_listener.py` | Detects "Hey Ultron", "Jarvis" wake words |

**TTS (Text-To-Speech)** uses `pyttsx3` (not Vosk — Vosk is STT only).

**Model path (already fixed in `server.py`):**
```python
vosk_model_path = "models/vosk-model-small-en-us-0.15"
```

---

## ✅ Quick Health Check

Run all at once after starting the server to confirm everything is working:

```powershell
# 1. Server is up
Invoke-RestMethod http://localhost:8000/

# 2. Browser control ready
Invoke-RestMethod http://localhost:8000/browser/status

# 3. Call interceptor active
Invoke-RestMethod http://localhost:8000/call/status

# 4. Basic chat works
Invoke-RestMethod -Uri "http://localhost:8000/chat" -Method POST `
  -ContentType "application/json" `
  -Body '{"text": "hello"}'
```
