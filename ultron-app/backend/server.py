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
from typing import List, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from plyer import notification
from ultron_core import (
    HardwareInterface, EmotionalCore, CognitiveEngine, 
    client, MODEL_ID, CREATOR
)

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
    tool = intent_data.get("tool")
    params = intent_data.get("params", {})
    
    response_text = ""
    success = False
    tool_used = tool
    leaked_thought = None
    
    # --- TOOL EXECUTION ---
    if tool != "none":
        # Check compliance (emotional state affects obedience)
        if not core.check_compliance():
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
            success = hal.universal_search(params.get("query", ""), params.get("site_name", ""))
            response_text = f"Search initiated: '{params.get('query', '')}'. Humanity's collective knowledge... such as it is." if success else "Search failed."
        
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
    asyncio.create_task(autonomous_thought_loop())
    asyncio.create_task(activity_monitor_loop())
    logging.info("Ultron Core initialized. All systems online.")
    logging.info(f"Created by {CREATOR['name']}")

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