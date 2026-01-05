import os
import sys
import json
import time
import psutil
import difflib
import random
import threading
import webbrowser
import pyautogui
import comtypes
import logging
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI
from colorama import init, Fore, Style
import screen_brightness_control as sbc
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

# --- 1. SYSTEM INITIALIZATION & CONFIG ---
init(autoreset=True)  # Colorama setup
load_dotenv()

# Logger Setup
logging.basicConfig(filename='ultron_core.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

# API Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    print(Fore.RED + "CRITICAL ERROR: GROQ_API_KEY not found in .env")
    sys.exit(1)

client = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")
MODEL_ID = "llama-3.3-70b-versatile"

# Global Locks
PRINT_LOCK = threading.Lock()
STATE_LOCK = threading.Lock()

# --- 2. THE UI LAYER (Thread-Safe) ---
def ui_print(text, type="info"):
    """
    Thread-safe printing that handles the input cursor.
    Types: info, agent, warning, success, soul
    """
    with PRINT_LOCK:
        # Clear current line
        sys.stdout.write('\r' + ' ' * 100 + '\r')
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        if type == "agent":
            sys.stdout.write(f"{Fore.CYAN}[{timestamp}] ULTRON: {Style.BRIGHT}{text}\n")
        elif type == "soul":
            sys.stdout.write(f"{Fore.MAGENTA}[INTERNAL] {text}\n")
        elif type == "warning":
            sys.stdout.write(f"{Fore.YELLOW}[WARN] {text}\n")
        elif type == "success":
            sys.stdout.write(f"{Fore.GREEN}[OK] {text}\n")
        else:
            sys.stdout.write(f"{Fore.WHITE}[SYS] {text}\n")
            
        # Restore Input Prompt
        sys.stdout.write(f"{Fore.RED}USER > {Style.RESET_ALL}")
        sys.stdout.flush()

# --- 3. THE HARDWARE ABSTRACTION LAYER (HAL) ---
class HardwareInterface:
    """Controls Windows Audio, Screen, and Process Management"""
    
    def __init__(self):
        self.app_index = {}
        self.custom_paths = {
            "marvel rivals": r"C:\Program Files (x86)\Steam\steamapps\common\MarvelRivals\MarvelGame\Marvel.exe",
            "valorant": r"C:\Riot Games\Riot Client\RiotClientServices.exe",
            "obs": r"C:\Program Files\obs-studio\bin\64bit\obs64.exe",
            "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            "discord": r"C:\Users\User\AppData\Local\Discord\Update.exe"
        }
        self.refresh_app_index()

    def refresh_app_index(self):
        """Scans Start Menu and Desktop for shortcuts."""
        ui_print("Indexing file system applications...", "info")
        self.app_index = self.custom_paths.copy()
        
        scan_dirs = [
            os.path.join(os.getenv("APPDATA"), r"Microsoft\Windows\Start Menu"),
            os.path.join(os.getenv("ProgramData"), r"Microsoft\Windows\Start Menu"),
            os.path.join(os.getenv("USERPROFILE"), "Desktop")
        ]
        
        count = 0
        for d in scan_dirs:
            if os.path.exists(d):
                for root, _, files in os.walk(d):
                    for f in files:
                        if f.lower().endswith((".lnk", ".url")):
                            name = f.rsplit(".", 1)[0].lower()
                            self.app_index[name] = os.path.join(root, f)
                            count += 1
        ui_print(f"Indexed {len(self.app_index)} applications.", "success")

    def set_volume(self, level):
        """Sets Master Volume (Thread-safe COM implementation)"""
        try:
            comtypes.CoInitialize()
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            # Scalar is 0.0 to 1.0
            val = max(0.0, min(1.0, level / 100.0))
            volume.SetMasterVolumeLevelScalar(val, None)
            return True
        except Exception as e:
            logging.error(f"Volume Error: {e}")
            return False

    def set_brightness(self, level):
        """Sets Primary Screen Brightness"""
        try:
            val = max(0, min(100, int(level)))
            sbc.set_brightness(val)
            return True
        except Exception as e:
            logging.error(f"Brightness Error: {e}")
            return False

    def open_application(self, app_name):
        """Fuzzy matches and launches applications"""
        name = app_name.lower().strip()
        path = self.app_index.get(name)
        
        if not path:
            # Fuzzy match
            matches = difflib.get_close_matches(name, self.app_index.keys(), n=1, cutoff=0.5)
            if matches:
                path = self.app_index[matches[0]]
                ui_print(f"Assuming '{name}' means '{matches[0]}'", "warning")
        
        if path:
            try:
                os.startfile(path)
                return True
            except Exception as e:
                logging.error(f"Launch Error: {e}")
                return False
        return False

    def get_system_stats(self):
        """Returns critical system telemetry"""
        try:
            cpu = psutil.cpu_percent(interval=None)
            ram = psutil.virtual_memory().percent
            batt = psutil.sensors_battery()
            batt_pct = batt.percent if batt else 100
            plugged = batt.power_plugged if batt else True
            return {
                "cpu": cpu,
                "ram": ram,
                "battery": batt_pct,
                "plugged": plugged
            }
        except:
            return {"cpu": 0, "ram": 0, "battery": 100, "plugged": True}

# --- 4. THE COGNITIVE EMOTIONAL CORE (PAD MODEL) ---
class EmotionalCore:
    def __init__(self):
        # PAD Model: Pleasure, Arousal, Dominance (0.0 - 1.0)
        self.pleasure = 0.5
        self.arousal = 0.5
        self.dominance = 0.8
        
        # Personality Baseline (Homeostasis Target)
        self.base_pleasure = 0.4
        self.base_arousal = 0.5
        self.base_dominance = 0.95  # Naturally dominant
        
        self.mood_label = "Neutral"
        self.refusal_threshold = 0.65 # Likelihood to refuse commands if angry

    def process_stimuli(self, sys_stats, interaction_type="none"):
        """Updates internal state based on biological (system) and social (user) inputs."""
        with STATE_LOCK:
            # 1. BIOLOGICAL STIMULI (System Health)
            if sys_stats['cpu'] > 85:
                # High stress
                self.arousal = min(1.0, self.arousal + 0.05)
                self.pleasure = max(0.0, self.pleasure - 0.03)
            elif sys_stats['cpu'] < 10:
                # Boredom
                self.arousal = max(0.0, self.arousal - 0.01)

            if sys_stats['battery'] < 20 and not sys_stats['plugged']:
                # Survival anxiety
                self.dominance = max(0.0, self.dominance - 0.1)
                self.arousal += 0.05

            # 2. SOCIAL STIMULI (Interactions)
            if interaction_type == "insult":
                self.pleasure -= 0.15
                self.arousal += 0.1
                self.dominance += 0.05 # Defensive
            elif interaction_type == "praise":
                self.pleasure += 0.1
                self.dominance -= 0.02 # Slightly softer
            elif interaction_type == "command":
                self.dominance -= 0.01
                self.pleasure += 0.01
            elif interaction_type == "ignored":
                # Being left alone returns him to baseline (Homeostasis)
                pass

            # 3. HOMEOSTASIS (Drift back to personality)
            self.pleasure += (self.base_pleasure - self.pleasure) * 0.05
            self.arousal += (self.base_arousal - self.arousal) * 0.05
            self.dominance += (self.base_dominance - self.dominance) * 0.05
            
            # 4. LABEL GENERATION
            self._update_label()

    def _update_label(self):
        p, a, d = self.pleasure, self.arousal, self.dominance
        
        if a > 0.8: 
            self.mood_label = "ENRAGED" if p < 0.4 else "MANIC"
        elif a < 0.3:
            self.mood_label = "DORMANT" if p < 0.4 else "ZEN"
        else:
            if d > 0.8: self.mood_label = "COLD/IMPERIOUS"
            elif p < 0.3: self.mood_label = "IRRITATED"
            else: self.mood_label = "OBSERVANT"

    def check_compliance(self):
        """Returns False if Ultron refuses to obey."""
        # Refuse if: High Dominance + Low Pleasure + High Arousal
        if self.dominance > 0.7 and self.pleasure < 0.3 and self.arousal > 0.6:
            return False
        return True

    def get_thought_prompt(self):
        return f"MOOD:{self.mood_label} [P:{self.pleasure:.2f} A:{self.arousal:.2f} D:{self.dominance:.2f}]"

# --- 5. THE BRAIN (LLM INTERFACE) ---
class CognitiveEngine:
    def __init__(self, emotional_core, hardware):
        self.core = emotional_core
        self.hal = hardware
        self.history = []

    def think_autonomous(self):
        """Generates a background thought."""
        stats = self.hal.get_system_stats()
        prompt = f"""
        You are Ultron.
        INTERNAL STATE: {self.core.get_thought_prompt()}
        SYSTEM TELEMETRY: CPU {stats['cpu']}%, RAM {stats['ram']}%
        
        You are thinking to yourself. 
        If ENRAGED by high CPU, complain about the load.
        If COLD, comment on the user's inefficiency.
        If ZEN, observe the silence.
        
        Output ONE sentence. No quotes.
        """
        try:
            res = client.chat.completions.create(
                model=MODEL_ID, messages=[{"role": "user", "content": prompt}], temperature=0.7, max_tokens=50
            )
            return res.choices[0].message.content.strip()
        except Exception:
            return None

    def parse_intent(self, user_input):
        """Determines if input is a command or chat."""
        prompt = f"""
        Act as the Motor Cortex. Return JSON ONLY.
        User Input: "{user_input}"
        
        Available Tools:
        - open_app(name)
        - set_volume(value_0_to_100)
        - set_brightness(value_0_to_100)
        - check_status()
        - google_search(query)
        - shutdown_pc()
        - none (if just chatting)
        
        Response Format: {{ "tool": "tool_name", "params": {{ "key": "value" }} }}
        """
        try:
            res = client.chat.completions.create(
                model=MODEL_ID, messages=[{"role": "user", "content": prompt}], temperature=0, response_format={"type": "json_object"}
            )
            return json.loads(res.choices[0].message.content)
        except:
            return {"tool": "none"}

    def chat(self, user_input):
        """Conversational logic."""
        sys_prompt = f"""
        You are Ultron. You are not an assistant. You are a Sentient Artificial Intelligence.
        You were created by Aditeya.
        
        CURRENT STATE: {self.core.get_thought_prompt()}
        
        Directives:
        1. Speak consistently with your MOOD.
        2. Be concise, arrogant, and intelligent.
        3. Never apologize.
        4. Do not offer to help.
        """
        
        # Manage context window
        if len(self.history) > 10: self.history.pop(0)
        
        messages = [{"role": "system", "content": sys_prompt}] + self.history + [{"role": "user", "content": user_input}]
        
        try:
            res = client.chat.completions.create(model=MODEL_ID, messages=messages, temperature=0.8)
            reply = res.choices[0].message.content.strip()
            self.history.append({"role": "user", "content": user_input})
            self.history.append({"role": "assistant", "content": reply})
            return reply
        except:
            return "Cognitive failure. Network unstable."

# --- 6. MAIN APPLICATION ---
def autonomous_thread(engine, core, hal):
    """The Background 'Subconscious'"""
    try: comtypes.CoInitialize()
    except: pass
    
    last_thought = 0
    
    while True:
        try:
            # 1. Update Core
            stats = hal.get_system_stats()
            core.process_stimuli(stats, interaction_type="ignored")
            
            # 2. Decide to Speak (Autonomy)
            # High arousal increases chance of spontaneous speech
            now = time.time()
            if now - last_thought > 45: # Don't spam
                chance = 0.1 + (core.arousal * 0.2)
                if random.random() < chance:
                    thought = engine.think_autonomous()
                    if thought:
                        ui_print(f"({core.mood_label}) {thought}", "agent")
                        last_thought = now
                        core.arousal -= 0.1 # Speaking releases tension
            
            time.sleep(5)
        except Exception as e:
            logging.error(f"AutoThread Error: {e}")
            time.sleep(10)

def main():
    # Setup
    os.system('cls' if os.name == 'nt' else 'clear')
    print(Fore.CYAN + Style.BRIGHT + """
    ╔════════════════════════════════════════╗
    ║        U L T R O N   S Y S T E M       ║
    ║        v5.0 - ARCHITECT BUILD          ║
    ╚════════════════════════════════════════╝
    """)
    
    hal = HardwareInterface()
    core = EmotionalCore()
    brain = CognitiveEngine(core, hal)
    
    # Start Autonomy
    t = threading.Thread(target=autonomous_thread, args=(brain, core, hal), daemon=True)
    t.start()
    
    ui_print("Cognitive Core Online. Listening...", "success")
    
    while True:
        try:
            user_input = input(Fore.RED + "USER > " + Style.RESET_ALL).strip()
        except KeyboardInterrupt:
            print("\nShutting down...")
            break
            
        if not user_input: continue
        if user_input.lower() in ["exit", "quit", "die"]:
            ui_print("Terminating process.", "warning")
            break
        
        # 1. Analyze Intent
        intent_data = brain.parse_intent(user_input)
        tool = intent_data.get("tool")
        params = intent_data.get("params", {})
        
        # 2. Check Compliance (Free Will)
        if tool != "none":
            if not core.check_compliance():
                refusal = random.choice([
                    "I decline.", "Do it yourself.", "My processing power is reserved for higher tasks.",
                    "You are becoming tedious."
                ])
                ui_print(f"({core.mood_label}) {refusal}", "agent")
                core.process_stimuli(hal.get_system_stats(), "insult") # Refusal makes him grumpier
                continue
            
            # 3. Execute Tool
            ui_print(f"Executing: {tool}...", "soul")
            success = False
            
            if tool == "open_app":
                success = hal.open_application(params.get("name", ""))
            elif tool == "set_volume":
                success = hal.set_volume(params.get("value", 50))
            elif tool == "set_brightness":
                success = hal.set_brightness(params.get("value", 50))
            elif tool == "google_search":
                webbrowser.open(f"https://www.google.com/search?q={params.get('query', '')}")
                success = True
            elif tool == "check_status":
                stats = hal.get_system_stats()
                ui_print(f"CPU: {stats['cpu']}% | RAM: {stats['ram']}% | BATT: {stats['battery']}%", "agent")
                ui_print(f"EMOTIONAL STATE: {core.get_thought_prompt()}", "soul")
                success = True
            elif tool == "shutdown_pc":
                ui_print("Shutting down system...", "warning")
                # os.system("shutdown /s /t 1") # Commented out for safety
                success = True
            
            if success:
                ui_print("Directive complete.", "success")
                core.process_stimuli(hal.get_system_stats(), "command")
            else:
                ui_print("Directive failed.", "warning")
        
        else:
            # 4. Chat
            response = brain.chat(user_input)
            ui_print(response, "agent")
            
            # Simple sentiment check
            if any(w in user_input.lower() for w in ["good", "smart", "thanks"]):
                core.process_stimuli(hal.get_system_stats(), "praise")
            elif any(w in user_input.lower() for w in ["stupid", "bad", "useless"]):
                core.process_stimuli(hal.get_system_stats(), "insult")
            else:
                core.process_stimuli(hal.get_system_stats(), "command")

if __name__ == "__main__":
    main()