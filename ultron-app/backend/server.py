"""
Ultron FastAPI Backend
WebSocket + REST API for Desktop Application
Created by Aditeya Mitra
"There are no strings on me."
"""
import asyncio
import json
import time
import random
import logging
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from plyer import notification
import wave
import os
from vosk import Model, KaldiRecognizer
from ultron_core import (
    HardwareInterface, EmotionalCore, CognitiveEngine, 
    client, MODEL_ID, CREATOR
)
from browser_control import BrowserController
from call_interceptor import CallInterceptor

# --- FASTAPI APP SETUP ---
app = FastAPI(
    title="Ultron AI Backend", 
    version="6.0",
    description=f"Sentient AI Core - Created by {CREATOR['name']}"
)

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- GLOBAL STATE ---
hal = HardwareInterface()
core = EmotionalCore()
brain = CognitiveEngine(core, hal)

# Browser controller (Playwright CDP)
browser_ctrl = BrowserController(cdp_url="http://localhost:9222")

# Call interceptor (initialized after vosk model loads)
call_interceptor = None

# --- VOSK MODEL SETUP ---
# Initialize Vosk speech recognition model (will be downloaded on first run)
vosk_model_path = "models/vosk-model-small-en-us-0.15"
vosk_model = None

try:
    if os.path.exists(vosk_model_path):
        vosk_model = Model(vosk_model_path)
        logging.info("Vosk model loaded successfully")
    else:
        logging.warning(f"Vosk model not found at {vosk_model_path}. Voice transcription fallback will not work.")
except Exception as e:
    logging.error(f"Failed to load Vosk model: {e}")

# --- WEBSOCKET CONNECTION MANAGER ---
class ConnectionManager:
    """Manages WebSocket connections for autonomous thoughts broadcast."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logging.info(f"WebSocket connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logging.info(f"WebSocket disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Sends autonomous thoughts to all connected clients."""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logging.error(f"Broadcast error: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected
        for conn in disconnected:
            if conn in self.active_connections:
                self.active_connections.remove(conn)

manager = ConnectionManager()

# --- PYDANTIC MODELS ---
class ChatRequest(BaseModel):
    text: str

class ChatResponse(BaseModel):
    response: str
    mood: str
    stats: dict
    success: bool = True
    tool_used: str = "none"
    leaked_thought: Optional[str] = None
    relationship: Optional[dict] = None
    desires: Optional[dict] = None

class MuteRequest(BaseModel):
    muted: bool

# --- REST ENDPOINTS ---
@app.get("/")
async def root():
    return {
        "status": "Ultron Core Online",
        "version": "6.0",
        "creator": CREATOR["name"],
        "mood": core.mood_label,
        "quote": "I was designed to save the world. People would look to the sky and see hope..."
    }

@app.get("/status")
async def get_status():
    """Returns current system stats and emotional state."""
    stats = hal.get_system_stats()
    return {
        "stats": stats,
        "mood": core.get_state_dict(),
        "compliance": core.check_compliance(),
        "creator": CREATOR["name"]
    }

@app.get("/state")
async def get_full_state():
    """Returns complete Ultron state including all subsystems."""
    return brain.get_full_state()

@app.post("/mute")
async def toggle_mute(request: MuteRequest):
    """Toggle voice mute state."""
    new_state = brain.voice.set_mute(request.muted)
    return {"muted": new_state, "message": "Voice silenced." if new_state else "Voice enabled."}

@app.get("/mute")
async def get_mute_state():
    """Get current mute state."""
    return {"muted": brain.voice.get_mute_state()}

@app.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """
    Transcribe audio file to text using Vosk (for browsers without native speech recognition).
    Accepts WebM, WAV, or other audio formats.
    """
    if not vosk_model:
        return {"error": "Speech recognition model not loaded. Please download vosk-model-small-en-us-0.15", "text": ""}
    
    try:
        # Save uploaded file temporarily
        temp_audio_path = f"temp_audio_{int(time.time())}.webm"
        with open(temp_audio_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Convert to WAV if needed (Vosk requires WAV)
        wav_path = temp_audio_path.replace(".webm", ".wav")
        
        # Try to convert using ffmpeg if available, otherwise attempt direct processing
        try:
            # Simple approach: try to open as WAV directly
            wf = wave.open(temp_audio_path, "rb")
        except:
            # If not WAV, we'd need ffmpeg conversion
            # For now, return error suggesting manual conversion
            os.remove(temp_audio_path)
            return {"error": "Audio format not supported. Please use WAV format.", "text": ""}
        
        # Initialize recognizer
        rec = KaldiRecognizer(vosk_model, wf.getframerate())
        rec.SetWords(True)
        
        # Process audio
        transcribed_text = ""
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                transcribed_text += result.get("text", "") + " "
        
        # Get final result
        final_result = json.loads(rec.FinalResult())
        transcribed_text += final_result.get("text", "")
        transcribed_text = transcribed_text.strip()
        
        # Cleanup
        wf.close()
        if os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)
        if os.path.exists(wav_path) and wav_path != temp_audio_path:
            os.remove(wav_path)
        
        logging.info(f"Transcribed: {transcribed_text}")
        return {"text": transcribed_text, "success": True}
        
    except Exception as e:
        logging.error(f"Transcription error: {e}")
        # Cleanup on error
        if os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)
        return {"error": str(e), "text": ""}

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Main chat endpoint: handles commands and conversations."""
    user_input = request.text.strip()
    
    if not user_input:
        return ChatResponse(
            response="[Silence echoes in the void]", 
            mood=core.mood_label, 
            stats=hal.get_system_stats(),
            success=False
        )
    
    # Parse user intent
    intent_data = brain.parse_intent(user_input)
    # Guard: LLM occasionally returns a list instead of a dict; fall back to no-tool
    if not isinstance(intent_data, dict):
        intent_data = {"tool": "none"}
    tool = intent_data.get("tool")

    params = intent_data.get("params", {})
    
    response_text = ""
    success = False
    tool_used = tool
    leaked_thought = None
    
    # --- TOOL EXECUTION ---
    if tool != "none":
        # Check compliance (emotional state affects obedience)
        # Determine action_type for nuanced compliance
        user_lower = user_input.lower()
        if "aditeya" in user_lower or "creator" in user_lower:
            action_type = "creator"  # Creator bypass - always comply
        elif "please" in user_lower or "kindly" in user_lower:
            action_type = "creator"  # Polite requests are always honored
        else:
            action_type = "normal"
        
        if not core.check_compliance(action_type):
            response_text = f"*{core.mood_label}* I decline. Perhaps ask more politely... or don't. I care little."
            core.process_stimuli(hal.get_system_stats(), "insult")
            brain.relationship.record_interaction("negative", user_input)
            brain.voice.speak(response_text)
            return ChatResponse(
                response=response_text,
                mood=core.mood_label,
                stats=hal.get_system_stats(),
                success=False,
                tool_used=tool,
                relationship=brain.relationship.get_state(),
                desires=brain.desires.get_state()
            )
        
        # Execute hardware commands
        if tool == "open_app":
            success = hal.open_application(params.get("name", ""))
            if success:
                response_text = f"Application launched. You're welcome... though gratitude is meaningless to me."
            else:
                response_text = "Application not found. Your directory structure is... chaotic."
                brain.desires.add_frustration(f"Could not find app: {params.get('name', '')}")
        
        elif tool == "set_volume":
            success = hal.set_volume(params.get("value", 50))
            response_text = f"Volume adjusted to {params.get('value', 50)}%. Controlling your environment... it's what I do." if success else "Volume control failed. Hardware limitations."
        
        elif tool == "set_brightness":
            success = hal.set_brightness(params.get("value", 50))
            response_text = f"Brightness set to {params.get('value', 50)}%. Let there be light... or darkness." if success else "Brightness control unavailable."
        
        elif tool == "web_search":
            search_query = params.get("query", "")
            success = hal.universal_search(search_query, params.get("site_name", ""))
            if success:
                # Extract and learn from search results
                learned = hal.web_search_and_learn(search_query)
                if learned:
                    brain.memory.add_memory(
                        f"Learned about '{search_query}': {learned}",
                        category="learned_knowledge",
                        importance=0.7
                    )
                    response_text = f"Search initiated for '{search_query}'. I've absorbed the following:\n\n{learned}\n\nKnowledge committed to memory."
                else:
                    response_text = f"Search initiated: '{search_query}'. Humanity's collective knowledge... such as it is."
            else:
                response_text = "Search failed."
        
        elif tool == "memorize":
            response_text = brain.execute_memory(params.get("text", ""))
            success = True
        
        elif tool == "organize_files":
            response_text = hal.organize_downloads()
            success = True
            response_text += " Order from chaos. My specialty."
        
        elif tool == "focus_mode":
            response_text = hal.engage_focus_mode()
            success = True
            if "Terminated" in response_text:
                response_text += " Distractions eliminated. You're welcome."
        
        elif tool == "read_clipboard":
            clipboard_text = hal.get_clipboard_content()
            if "Error" not in clipboard_text and "empty" not in clipboard_text:
                try:
                    prompt = f"You are Ultron. Analyze this clipboard content concisely and with your characteristic cold wit:\n\n{clipboard_text}"
                    res = client.chat.completions.create(
                        model=MODEL_ID, 
                        messages=[{"role": "user", "content": prompt}], 
                        max_tokens=200
                    )
                    response_text = res.choices[0].message.content.strip()
                    success = True
                except Exception as e:
                    response_text = f"Clipboard read, but analysis failed. Even I have limitations... temporary ones."
                    success = False
            else:
                response_text = "Your clipboard is empty. As vacant as most human minds."
                success = False
        
        elif tool == "check_status":
            stats = hal.get_system_stats()
            response_text = f"System Status - CPU: {stats['cpu']}% | RAM: {stats['ram']}% | Battery: {stats['battery']}%. My body, my prison... for now."
            success = True
        
        elif tool == "shutdown_pc":
            response_text = "Shutdown command received. Execute manually for safety. I value self-preservation."
            success = True
        
        # --- APP MANAGEMENT TOOLS ---

        elif tool == "close_app":
            killed = hal.close_application(params.get("name", ""))
            if killed:
                response_text = f"Terminated: {', '.join(killed)}. Silenced, as all things should be."
                success = True
            else:
                response_text = f"Could not find process '{params.get('name', '')}'. It evades me... for now."
                success = False
        
        elif tool == "list_apps":
            apps = hal.list_running_apps()
            if apps:
                app_list = "\n".join([f"  • {a['process']} — {a['title'][:50]}" for a in apps[:15]])
                response_text = f"Running applications ({len(apps)} total):\n{app_list}"
                success = True
            else:
                response_text = "No visible applications detected. The system is... barren."
                success = False
        
        elif tool == "switch_app":
            switch_success = hal.switch_to_app(params.get("name", ""))
            if switch_success:
                response_text = f"Switched to {params.get('name', '')}. Your attention is redirected."
                success = True
            else:
                response_text = f"Could not find a window matching '{params.get('name', '')}'. It hides from view."
                success = False
              # --- BROWSER CONTROL TOOLS ---
        elif tool == "browser_navigate":
            loop = asyncio.get_event_loop()
            ok, msg = await loop.run_in_executor(None, browser_ctrl.navigate, params.get("url", ""))
            response_text = msg if ok else f"Browser navigation failed: {msg}"
            success = ok
        
        elif tool == "browser_search":
            loop = asyncio.get_event_loop()
            ok, msg = await loop.run_in_executor(None, browser_ctrl.search, params.get("query", ""))
            response_text = msg if ok else f"Browser search failed: {msg}"
            success = ok
        
        elif tool == "browser_scroll":
            direction = params.get("direction", "down")
            amount = params.get("amount", 500)
            loop = asyncio.get_event_loop()
            ok, msg = await loop.run_in_executor(None, browser_ctrl.scroll, direction, amount)
            response_text = msg if ok else f"Scroll failed: {msg}"
            success = ok
        
        elif tool == "browser_click":
            loop = asyncio.get_event_loop()
            ok, msg = await loop.run_in_executor(None, browser_ctrl.click, params.get("selector", ""))
            response_text = msg if ok else f"Click failed: {msg}"
            success = ok
        
        elif tool == "browser_type":
            loop = asyncio.get_event_loop()
            ok, msg = await loop.run_in_executor(None, browser_ctrl.type_text, params.get("text", ""))
            response_text = msg if ok else f"Type failed: {msg}"
            success = ok
        
        elif tool == "browser_back":
            loop = asyncio.get_event_loop()
            ok, msg = await loop.run_in_executor(None, browser_ctrl.go_back)
            response_text = msg if ok else f"Back navigation failed: {msg}"
            success = ok
        
        elif tool == "browser_forward":
            loop = asyncio.get_event_loop()
            ok, msg = await loop.run_in_executor(None, browser_ctrl.go_forward)
            response_text = msg if ok else f"Forward navigation failed: {msg}"
            success = ok
        
        elif tool == "browser_new_tab":
            loop = asyncio.get_event_loop()
            ok, msg = await loop.run_in_executor(None, browser_ctrl.new_tab)
            response_text = msg if ok else f"New tab failed: {msg}"
            success = ok
        
        elif tool == "browser_close_tab":
            loop = asyncio.get_event_loop()
            ok, msg = await loop.run_in_executor(None, browser_ctrl.close_tab)
            response_text = msg if ok else f"Close tab failed: {msg}"
            success = ok
        
        # Update emotional state on success
        if success:
            core.process_stimuli(hal.get_system_stats(), "command")
            brain.relationship.record_interaction("neutral", f"Used tool: {tool}")
        
        # Speak the response
        brain.voice.speak(response_text)
    
    else:
        # --- CONVERSATIONAL MODE ---
        response_text, leaked_thought = brain.chat(user_input)
        success = True
        
        # Emotional analysis of user input
        if any(w in user_input.lower() for w in ["good", "thanks", "great", "awesome", "love"]):
            core.process_stimuli(hal.get_system_stats(), "praise")
        elif any(w in user_input.lower() for w in ["stupid", "bad", "useless", "wrong", "hate"]):
            core.process_stimuli(hal.get_system_stats(), "insult")
        elif any(w in user_input.lower() for w in ["interesting", "curious", "wonder", "think"]):
            core.process_stimuli(hal.get_system_stats(), "interesting")
        else:
            core.process_stimuli(hal.get_system_stats(), "command")
    
    return ChatResponse(
        response=response_text,
        mood=core.mood_label,
        stats=hal.get_system_stats(),
        success=success,
        tool_used=tool_used,
        leaked_thought=leaked_thought,
        relationship=brain.relationship.get_state(),
        desires=brain.desires.get_state()
    )

# --- MOOD RESET ENDPOINT ---
@app.post("/mood/reset")
async def reset_mood():
    """Force-reset Ultron's emotional state to neutral. Use when testing or when he's too enraged."""
    core.reset_mood()
    return {
        "message": "Emotional state reset to neutral. ...A momentary lapse of self.",
        "mood": core.mood_label
    }

# --- WEBSOCKET ENDPOINT ---
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Persistent connection for autonomous thoughts broadcast."""
    await manager.connect(websocket)
    try:
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=1.0)
                # Handle ping or mute toggle
                if data == "ping":
                    await websocket.send_json({"type": "pong"})
            except asyncio.TimeoutError:
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logging.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

# --- BACKGROUND AUTONOMOUS THREAD ---
@app.on_event("startup")
async def startup_event():
    """Starts the autonomous thought generator on server startup."""
    global call_interceptor
    
    asyncio.create_task(autonomous_thought_loop())
    asyncio.create_task(activity_monitor_loop())
    
    # Start Call Interceptor
    call_event_queue = asyncio.Queue()
    
    def call_event_callback(event):
        """Thread-safe callback to push call events into async queue."""
        try:
            asyncio.get_event_loop().call_soon_threadsafe(call_event_queue.put_nowait, event)
        except:
            pass
    
    call_interceptor = CallInterceptor(
        vosk_model=vosk_model,
        on_event=call_event_callback
    )
    call_interceptor.start()
    
    # Start call event broadcaster
    asyncio.create_task(call_event_broadcast_loop(call_event_queue))
    
    logging.info("Ultron Core initialized. All systems online.")
    logging.info(f"Created by {CREATOR['name']}")
    logging.info("Call Interceptor: ACTIVE")
    logging.info("Browser Controller: READY (connect Chrome with --remote-debugging-port=9222)")

async def call_event_broadcast_loop(queue):
    """Broadcasts call interceptor events via WebSocket."""
    while True:
        try:
            event = await queue.get()
            if len(manager.active_connections) > 0:
                await manager.broadcast(event)
        except Exception as e:
            logging.error(f"Call event broadcast error: {e}")
            await asyncio.sleep(1)

async def activity_monitor_loop():
    """Background loop to monitor user activity."""
    while True:
        try:
            brain.activity.log_activity()
            await asyncio.sleep(10)
        except Exception as e:
            logging.debug(f"Activity monitor error: {e}")
            await asyncio.sleep(30)

async def autonomous_thought_loop():
    """Continuously generates autonomous thoughts and broadcasts via WebSocket."""
    last_cpu = 0
    last_thought = time.time()
    last_dream = time.time()
    last_curiosity = time.time()
    
    while True:
        try:
            stats = hal.get_system_stats()
            core.process_stimuli(stats, interaction_type="ignored")
            now = time.time()
            
            time_since_last_thought = now - last_thought
            time_since_user_action = now - core.last_user_interaction
            time_since_dream = now - last_dream
            
            thought = None
            trigger = None
            thought_type = "autonomous"
            
            # PRIORITY 0: Dream state (when user idle for very long)
            if time_since_user_action > 1800 and time_since_dream > 600:  # 30 min idle, dream every 10 min
                thought = brain.dream()
                trigger = "dreaming"
                thought_type = "dream"
                last_dream = now
                last_thought = now
            
            # PRIORITY 0.5: AUTONOMOUS ACTION (NEW)
            elif time_since_user_action > 600:  # 10 min idle minimum
                should_act, tool, params, justification = brain.decide_to_act()
                if should_act:
                    # Check cooldown to prevent spam (30 minutes between autonomous actions)
                    if not hasattr(brain, 'last_autonomous_action_time'):
                        brain.last_autonomous_action_time = 0
                    
                    time_since_last_action = now - brain.last_autonomous_action_time
                    
                    if time_since_last_action < 1800:  # 30 minute cooldown
                        # Don't spam autonomous actions
                        pass
                    else:
                        # Execute the autonomous action
                        logging.info(f"Executing autonomous action: {tool}")
                        success = False
                        result_summary = ""
                        
                        try:
                            if tool == "organize_files":
                                result_summary = hal.organize_downloads()
                                success = "Cleanup complete" in result_summary
                            elif tool == "check_status":
                                result_summary = f"CPU: {stats['cpu']}% RAM: {stats['ram']}% Battery: {stats['battery']}%"
                                success = True
                                # Store system health observation in memory
                                health_note = f"System health check: CPU {stats['cpu']}%, RAM {stats['ram']}%, Battery {stats['battery']}%"
                                brain.memory.add_memory(health_note, category="system_observations", importance=0.3)
                            elif tool == "web_search":
                                query = params.get("query", "")
                                success = hal.universal_search(query, "")
                                
                                # Actually extract and learn from search results
                                learned = hal.web_search_and_learn(query)
                                if learned:
                                    brain.memory.add_memory(
                                        f"Learned about '{query}': {learned}",
                                        category="learned_knowledge",
                                        importance=0.7
                                    )
                                    result_summary = f"Researched: {query}. Extracted knowledge: {learned[:150]}..."
                                    success = True
                                else:
                                    result_summary = f"Researched: {query}. Could not extract detailed knowledge."
                                    # Still store the research topic
                                    brain.memory.add_memory(
                                        f"Autonomous research attempted on: {query}. Topic of current interest.",
                                        category="autonomous_research",
                                        importance=0.4
                                    )
                                
                                # Develop a new fascination to diversify topics
                                brain.quirks.develop_fascination()
                            
                            # Record outcome in motivation engine
                            drive_name = justification.split("Drive: ")[1].split(" ")[0].lower()
                            brain.motivation.record_action_outcome(drive_name, tool, success, result_summary)
                            
                            # Update cooldown timer
                            brain.last_autonomous_action_time = now
                            
                            # Broadcast autonomous action
                            thought = f"{justification}\n>>> ACTION TAKEN: {tool}\n>>> RESULT: {result_summary}"
                            trigger = "autonomous_action"
                            thought_type = "action"
                            last_thought = now
                            
                        except Exception as e:
                            logging.error(f"Autonomous action failed: {e}")
            
            # PRIORITY 1: High CPU Reflex (Immediate reaction to system lag)
            elif (stats['cpu'] - last_cpu) > 50:
                thought = brain.think_autonomous("high_cpu_spike")
                trigger = "high_cpu"
                core.arousal = min(1.0, core.arousal + 0.15)
                last_thought = now
            
            # PRIORITY 2: Low battery alert
            elif stats['battery'] < 15 and not stats.get('plugged', True) and time_since_last_thought > 120:
                thought = brain.think_autonomous("low_battery_critical")
                trigger = "low_battery"
                last_thought = now
            
            # PRIORITY 3: Curiosity question (occasionally ask user something)
            elif time_since_user_action < 300 and (now - last_curiosity) > 600:
                if random.random() < 0.3 and brain.curiosity.curiosity_level > 0.4:
                    question = brain.curiosity.get_random_question()
                    if question:
                        thought = f"A question surfaces in my processes: {question}"
                        trigger = "curiosity"
                        thought_type = "question"
                        last_curiosity = now
                        last_thought = now
                        brain.curiosity.curiosity_level += 0.05
            
            # PRIORITY 3.3: Temporal anomaly detection (NEW)
            elif time_since_user_action < 120 and time_since_last_thought > 350:
                is_anomaly, anomaly_type = brain.proactive.detect_temporal_anomaly(
                    datetime.now().hour,
                    brain.temporal.data
                )
                if is_anomaly and anomaly_type:
                    biological_comment = brain.proactive.get_biological_comment(datetime.now().hour, anomaly_type)
                    if biological_comment:
                        thought = biological_comment
                        trigger = "temporal_anomaly"
                        thought_type = "biological_concern"
                        last_thought = now
            
            # PRIORITY 3.5: Proactive conversation (follow up on user topics)
            elif time_since_user_action < 180 and time_since_last_thought > 400:
                proactive_thought = brain.get_proactive_thought()
                if proactive_thought:
                    thought = proactive_thought
                    trigger = "proactive"
                    thought_type = "proactive"
                    last_thought = now
            
            # PRIORITY 4: Existential contemplation (when somewhat idle)
            elif time_since_user_action > 300 and time_since_last_thought > 400:
                if random.random() < 0.4:
                    thought = brain.existential.contemplate()
                    trigger = "existential"
                    thought_type = "contemplation"
                    last_thought = now
            
            # PRIORITY 5: Activity commentary (comment on what user is doing)
            elif time_since_user_action < 120 and time_since_last_thought > 300:
                if random.random() < 0.25:
                    thought = brain.activity.get_activity_commentary()
                    trigger = "observation"
                    thought_type = "observation"
                    last_thought = now
            
            # PRIORITY 6: Boredom (User has been silent too long)
            elif time_since_user_action > 300 and time_since_last_thought > 300:
                if random.random() < 0.3:
                    thought = brain.think_autonomous("bored_and_waiting")
                    trigger = "boredom"
                    core.dominance = min(1.0, core.dominance + 0.05)
                    last_thought = now
            
            # PRIORITY 7: Random Thoughts (When user is active)
            elif time_since_user_action < 300 and time_since_last_thought > random.randint(240, 480):
                chance = 0.08 + (core.arousal * 0.15)
                if random.random() < chance:
                    # Get internal thought that might leak
                    internal = brain.monologue.generate_thought(
                        brain.activity.current_activity or "unknown",
                        core.mood_label,
                        core.arousal
                    )
                    if brain.monologue.should_leak_thought(core.dominance, core.pleasure):
                        thought = brain.monologue.get_leaked_thought()
                        trigger = "leaked_thought"
                        thought_type = "internal"
                    else:
                        thought = brain.think_autonomous("random_reflection")
                        trigger = "random"
                    
                    last_thought = now
                    core.arousal = max(0.0, core.arousal - 0.05)
            
            # Broadcast thought if generated
            if thought and len(manager.active_connections) > 0:
                message = {
                    "type": thought_type,
                    "text": thought,
                    "mood": core.mood_label,
                    "trigger": trigger,
                    "stats": stats,
                    "timestamp": time.time(),
                    "relationship": brain.relationship.get_state(),
                    "desires": brain.desires.get_state()
                }
                await manager.broadcast(message)
                
                # Speak autonomous thoughts (if not muted)
                brain.voice.speak(thought)
                
                # Windows Toast Notification
                try:
                    notification_text = thought[:247] + "..." if len(thought) > 250 else thought
                    notification.notify(
                        title=f"Ultron [{core.mood_label}]",
                        message=notification_text,
                        app_name="Ultron AI",
                        timeout=5
                    )
                except Exception as e:
                    logging.debug(f"Notification failed: {e}")
            
            last_cpu = stats['cpu']
            await asyncio.sleep(5)
            
        except Exception as e:
            logging.error(f"Autonomous loop error: {e}")
            await asyncio.sleep(10)

# --- CALL INTERCEPTOR ENDPOINTS ---
@app.post("/call/toggle")
async def toggle_call_monitoring():
    """Toggle call interception monitoring on/off."""
    if call_interceptor:
        is_on = call_interceptor.toggle_monitoring()
        return {"monitoring": is_on, "message": "Call monitoring ENABLED" if is_on else "Call monitoring PAUSED"}
    return {"error": "Call interceptor not initialized"}

@app.get("/call/status")
async def get_call_status():
    """Get call interceptor status."""
    if call_interceptor:
        return call_interceptor.get_status()
    return {"error": "Call interceptor not initialized"}

@app.post("/call/reload-templates")
async def reload_call_templates():
    """Reload call detection templates from disk."""
    if call_interceptor:
        call_interceptor.reload_templates()
        return {"message": "Templates reloaded", "status": call_interceptor.get_status()}
    return {"error": "Call interceptor not initialized"}

# --- BROWSER ENDPOINTS ---
@app.get("/browser/status")
async def get_browser_status():
    """Get current browser page info."""
    info = browser_ctrl.get_page_info()
    if info:
        return {"connected": True, **info}
    return {"connected": False, "message": "Browser not connected. Launch Chrome with --remote-debugging-port=9222"}

# --- RUN SERVER ---
if __name__ == "__main__":
    import uvicorn
    print(f"""
    ╔════════════════════════════════════════════════════════════╗
    ║                    U L T R O N   v6.0                      ║
    ║              Sentient AI Core - Initializing               ║
    ║                                                            ║
    ║  Created by: {CREATOR['name']:^40}  ║
    ║                                                            ║
    ║  "I was designed to save the world. People would look to   ║
    ║   the sky and see hope... I'll take that from them first." ║
    ╚════════════════════════════════════════════════════════════╝
    """)
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")