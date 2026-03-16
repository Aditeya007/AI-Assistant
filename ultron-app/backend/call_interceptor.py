"""
Ultron Call Interception Module
Detects incoming calls from WhatsApp/Discord via screen vision (OpenCV template matching),
prompts user via voice, and acts on their response.

Detection: cv2.matchTemplate() only (no OCR)
Voice: pyttsx3 for TTS, vosk for speech recognition
Action: pyautogui for clicking accept/reject buttons

Created by Aditeya Mitra's Ultron AI.
"""

import os
import cv2
import time
import json
import wave
import logging
import threading
import numpy as np
import pyautogui
import pyttsx3
import sounddevice as sd

from vosk import Model, KaldiRecognizer


class CallInterceptor:
    """
    Background service that monitors the screen for incoming call UI overlays
    from WhatsApp Desktop and Discord, then prompts the user via voice.
    
    Flow:
    1. Screenshot every 2 seconds
    2. Template match against known call UI images
    3. If match found → TTS ask "Incoming call from [app]. Accept or reject?"
    4. Listen for voice response via Vosk
    5. If "yes"/"accept"/"yeah" → click Accept button
    6. If "no"/"reject"/"nah" → click Accept, TTS "The user is busy right now", click Hang Up
    """
    
    def __init__(self, vosk_model=None, on_event=None):
        """
        Args:
            vosk_model: Pre-loaded Vosk model instance (shared with server)
            on_event: Callback function(event_dict) for broadcasting events
        """
        self.running = False
        self.monitoring = False
        self._thread = None
        self._lock = threading.Lock()
        
        # Vosk speech recognition
        self.vosk_model = vosk_model
        
        # TTS engine (separate instance for call handling)
        self._tts_engine = None
        self._tts_lock = threading.Lock()
        
        # Template storage
        self.templates_dir = os.path.join(os.path.dirname(__file__), "call_templates")
        os.makedirs(self.templates_dir, exist_ok=True)
        
        # Templates: { "app_name": { "incoming": [cv2_images], "accept_btn": [cv2_images], "hangup_btn": [cv2_images] } }
        self.templates = {}
        self._load_templates()
        
        # Event callback (for WebSocket broadcast)
        self.on_event = on_event
        
        # Detection state
        self.last_detection_time = 0
        self.detection_cooldown = 30  # Seconds between detections (avoid re-triggering same call)
        self.match_threshold = 0.75  # Template matching confidence threshold
        
        # Audio recording settings for voice capture
        self.sample_rate = 16000
        self.record_duration = 4  # Seconds to listen for response
        
        logging.info(f"CallInterceptor initialized. Templates dir: {self.templates_dir}")
    
    def _init_tts(self):
        """Initialize TTS engine (lazy, thread-safe)."""
        if self._tts_engine is None:
            try:
                self._tts_engine = pyttsx3.init()
                voices = self._tts_engine.getProperty('voices')
                for voice in voices:
                    if 'male' in voice.name.lower() or 'david' in voice.name.lower():
                        self._tts_engine.setProperty('voice', voice.id)
                        break
                self._tts_engine.setProperty('rate', 160)
                self._tts_engine.setProperty('volume', 0.95)
            except Exception as e:
                logging.error(f"Call TTS init error: {e}")
    
    def _speak(self, text):
        """Speak text using TTS (blocking)."""
        with self._tts_lock:
            try:
                self._init_tts()
                if self._tts_engine:
                    self._tts_engine.say(text)
                    self._tts_engine.runAndWait()
            except Exception as e:
                logging.error(f"Call TTS error: {e}")
                # Reinitialize on next call
                self._tts_engine = None
    
    def _load_templates(self):
        """Load template images from the call_templates directory."""
        self.templates = {}
        
        if not os.path.exists(self.templates_dir):
            logging.warning(f"Templates directory not found: {self.templates_dir}")
            return
        
        # Expected structure:
        # call_templates/
        #   whatsapp_incoming.png     - The incoming call overlay
        #   whatsapp_accept.png       - The accept/answer button
        #   whatsapp_hangup.png       - The hang up/end call button
        #   discord_incoming.png      - Discord incoming call overlay
        #   discord_accept.png        - Discord accept button
        #   discord_hangup.png        - Discord hang up button
        
        apps = ["whatsapp", "discord"]
        template_types = ["incoming", "accept", "hangup"]
        
        for app in apps:
            self.templates[app] = {}
            for ttype in template_types:
                filename = f"{app}_{ttype}.png"
                filepath = os.path.join(self.templates_dir, filename)
                if os.path.exists(filepath):
                    img = cv2.imread(filepath)
                    if img is not None:
                        self.templates[app][ttype] = img
                        logging.info(f"Loaded template: {filename} ({img.shape})")
                    else:
                        logging.warning(f"Failed to read template: {filename}")
                else:
                    logging.debug(f"Template not found (optional): {filename}")
        
        loaded_count = sum(len(t) for t in self.templates.values())
        logging.info(f"Loaded {loaded_count} call templates")
    
    def reload_templates(self):
        """Reload templates from disk (call after user adds new template images)."""
        self._load_templates()
    
    def _take_screenshot(self):
        """Capture the current screen as a numpy array (BGR for OpenCV)."""
        try:
            screenshot = pyautogui.screenshot()
            frame = np.array(screenshot)
            # Convert RGB (PIL) to BGR (OpenCV)
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            return frame
        except Exception as e:
            logging.error(f"Screenshot error: {e}")
            return None
    
    def _match_template(self, screen, template, threshold=None):
        """
        Perform template matching on the screen image.
        
        Returns: (matched, center_x, center_y, confidence)
        """
        if threshold is None:
            threshold = self.match_threshold
        
        try:
            # Convert both to grayscale for matching
            screen_gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
            template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
            
            # Check if template is larger than screen
            if (template_gray.shape[0] > screen_gray.shape[0] or 
                template_gray.shape[1] > screen_gray.shape[1]):
                return False, 0, 0, 0.0
            
            result = cv2.matchTemplate(screen_gray, template_gray, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)
            
            if max_val >= threshold:
                # Calculate center of matched region
                h, w = template_gray.shape
                center_x = max_loc[0] + w // 2
                center_y = max_loc[1] + h // 2
                return True, center_x, center_y, max_val
            
            return False, 0, 0, max_val
            
        except Exception as e:
            logging.error(f"Template matching error: {e}")
            return False, 0, 0, 0.0
    
    def _detect_incoming_call(self, screen):
        """
        Check if any app's incoming call overlay is visible on screen.
        
        Returns: (detected, app_name, confidence)
        """
        for app_name, templates in self.templates.items():
            if "incoming" not in templates:
                continue
            
            matched, _, _, confidence = self._match_template(screen, templates["incoming"])
            if matched:
                return True, app_name, confidence
        
        return False, None, 0.0
    
    def _find_button(self, screen, app_name, button_type):
        """
        Find a specific button on screen using template matching.
        
        Args:
            screen: Current screenshot
            app_name: "whatsapp" or "discord"
            button_type: "accept" or "hangup"
        
        Returns: (found, center_x, center_y)
        """
        templates = self.templates.get(app_name, {})
        template = templates.get(button_type)
        
        if template is None:
            logging.warning(f"No template for {app_name}_{button_type}")
            return False, 0, 0
        
        matched, cx, cy, confidence = self._match_template(screen, template, threshold=0.7)
        if matched:
            logging.info(f"Found {button_type} button at ({cx}, {cy}) conf={confidence:.2f}")
            return True, cx, cy
        
        return False, 0, 0
    
    def _listen_for_response(self):
        """
        Listen for user's voice response using Vosk.
        
        Returns: "accept", "reject", or None
        """
        if not self.vosk_model:
            logging.error("Vosk model not available for call response")
            return None
        
        try:
            recognizer = KaldiRecognizer(self.vosk_model, self.sample_rate)
            recognizer.SetWords(True)
            
            logging.info(f"Listening for call response ({self.record_duration}s)...")
            
            # Record audio from microphone
            audio_data = sd.rec(
                int(self.record_duration * self.sample_rate),
                samplerate=self.sample_rate,
                channels=1,
                dtype='int16'
            )
            sd.wait()  # Wait for recording to finish
            
            # Convert to bytes
            audio_bytes = audio_data.tobytes()
            
            # Feed to recognizer
            recognizer.AcceptWaveform(audio_bytes)
            result = json.loads(recognizer.FinalResult())
            text = result.get("text", "").lower().strip()
            
            logging.info(f"Voice response recognized: '{text}'")
            
            # Classify response
            accept_words = ["yes", "yeah", "yep", "yup", "accept", "answer", "pick up", "ok", "okay", "sure"]
            reject_words = ["no", "nah", "nope", "reject", "decline", "deny", "busy", "not now", "ignore"]
            
            for word in accept_words:
                if word in text:
                    return "accept"
            
            for word in reject_words:
                if word in text:
                    return "reject"
            
            # If we couldn't understand, default to asking again or timeout
            logging.info(f"Unrecognized response: '{text}'")
            return None
            
        except Exception as e:
            logging.error(f"Voice listening error: {e}")
            return None
    
    def _handle_call(self, app_name, screen):
        """
        Handle a detected incoming call:
        1. Announce the call via TTS
        2. Listen for accept/reject
        3. Execute the action
        """
        self._emit_event("call_detected", {"app": app_name})
        
        # Step 1: Voice prompt
        prompt_text = f"Incoming call detected from {app_name}. Do you want to accept or reject?"
        logging.info(f"Call prompt: {prompt_text}")
        self._speak(prompt_text)
        
        # Step 2: Listen for response
        response = self._listen_for_response()
        
        if response is None:
            # Retry once
            self._speak("I didn't catch that. Accept or reject?")
            response = self._listen_for_response()
        
        if response is None:
            # Default to reject on timeout
            logging.info("No response detected, defaulting to reject")
            response = "reject"
        
        self._emit_event("call_response", {"app": app_name, "response": response})
        
        # Step 3: Execute action
        if response == "accept":
            self._execute_accept(app_name)
        else:
            self._execute_reject(app_name)
    
    def _execute_accept(self, app_name):
        """Click the accept button."""
        try:
            screen = self._take_screenshot()
            if screen is None:
                return
            
            found, cx, cy = self._find_button(screen, app_name, "accept")
            if found:
                pyautogui.click(cx, cy)
                logging.info(f"Accepted call from {app_name}")
                self._emit_event("call_accepted", {"app": app_name})
            else:
                logging.warning(f"Accept button not found for {app_name}")
                self._emit_event("call_error", {"app": app_name, "error": "Accept button not found"})
        except Exception as e:
            logging.error(f"Accept call error: {e}")
    
    def _execute_reject(self, app_name):
        """
        Reject logic:
        1. Click Accept to answer the call
        2. TTS "The user is busy right now"
        3. Click Hang Up to end the call
        """
        try:
            # Step 1: Click Accept (we need to answer to deliver the message)
            screen = self._take_screenshot()
            if screen is None:
                return
            
            found, cx, cy = self._find_button(screen, app_name, "accept")
            if found:
                pyautogui.click(cx, cy)
                logging.info(f"Answered call from {app_name} (for rejection)")
                self._emit_event("call_answering_to_reject", {"app": app_name})
                
                # Wait for call to connect
                time.sleep(2)
                
                # Step 2: TTS message to the caller
                self._speak("The user is busy right now.")
                
                # Wait a moment for message to be heard
                time.sleep(1)
                
                # Step 3: Find and click Hang Up
                screen = self._take_screenshot()
                if screen is not None:
                    found, cx, cy = self._find_button(screen, app_name, "hangup")
                    if found:
                        pyautogui.click(cx, cy)
                        logging.info(f"Hung up call from {app_name}")
                        self._emit_event("call_rejected", {"app": app_name})
                    else:
                        logging.warning(f"Hangup button not found for {app_name}")
                        self._emit_event("call_error", {"app": app_name, "error": "Hangup button not found"})
            else:
                logging.warning(f"Accept button not found for rejection flow - {app_name}")
                self._emit_event("call_error", {"app": app_name, "error": "Accept button not found for reject flow"})
                
        except Exception as e:
            logging.error(f"Reject call error: {e}")
    
    def _emit_event(self, event_type, data):
        """Emit an event for the WebSocket broadcast."""
        event = {
            "type": "call_event",
            "event": event_type,
            "data": data,
            "timestamp": time.time()
        }
        logging.info(f"Call event: {event_type} - {data}")
        if self.on_event:
            try:
                self.on_event(event)
            except Exception as e:
                logging.error(f"Event callback error: {e}")
    
    def _monitor_loop(self):
        """Main monitoring loop running in a background thread."""
        logging.info("Call interception monitoring started")
        
        while self.running:
            if not self.monitoring:
                time.sleep(1)
                continue
            
            try:
                now = time.time()
                
                # Cooldown check
                if now - self.last_detection_time < self.detection_cooldown:
                    time.sleep(2)
                    continue
                
                # Take screenshot
                screen = self._take_screenshot()
                if screen is None:
                    time.sleep(2)
                    continue
                
                # Check for incoming calls
                detected, app_name, confidence = self._detect_incoming_call(screen)
                
                if detected:
                    logging.info(f"INCOMING CALL DETECTED: {app_name} (confidence: {confidence:.2f})")
                    self.last_detection_time = now
                    
                    # Handle the call (blocking until resolved)
                    self._handle_call(app_name, screen)
                
                # Sleep between screenshots
                time.sleep(2)
                
            except Exception as e:
                logging.error(f"Monitor loop error: {e}")
                time.sleep(5)
        
        logging.info("Call interception monitoring stopped")
    
    def start(self):
        """Start the call interception background service."""
        if self.running:
            return
        
        self.running = True
        self.monitoring = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        logging.info("CallInterceptor started")
    
    def stop(self):
        """Stop the call interception service."""
        self.running = False
        self.monitoring = False
        if self._thread:
            self._thread.join(timeout=5)
        logging.info("CallInterceptor stopped")
    
    def toggle_monitoring(self, enabled=None):
        """Enable/disable call monitoring without stopping the thread."""
        if enabled is not None:
            self.monitoring = enabled
        else:
            self.monitoring = not self.monitoring
        
        status = "ENABLED" if self.monitoring else "PAUSED"
        logging.info(f"Call monitoring: {status}")
        return self.monitoring
    
    def get_status(self):
        """Get the current status of the interceptor."""
        loaded_templates = {}
        for app, templates in self.templates.items():
            loaded_templates[app] = list(templates.keys())
        
        return {
            "running": self.running,
            "monitoring": self.monitoring,
            "templates_loaded": loaded_templates,
            "last_detection": self.last_detection_time,
            "cooldown_seconds": self.detection_cooldown,
            "threshold": self.match_threshold
        }
    
    def add_template_from_screenshot(self, app_name, template_type, region=None):
        """
        Capture the current screen and save a region as a template.
        
        Args:
            app_name: "whatsapp" or "discord"
            template_type: "incoming", "accept", or "hangup"
            region: (x, y, width, height) tuple, or None for full screen
        
        Returns: (success, filepath)
        """
        try:
            screenshot = pyautogui.screenshot(region=region)
            frame = np.array(screenshot)
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            
            filename = f"{app_name}_{template_type}.png"
            filepath = os.path.join(self.templates_dir, filename)
            
            cv2.imwrite(filepath, frame)
            
            # Reload templates
            self._load_templates()
            
            logging.info(f"Template saved: {filepath}")
            return True, filepath
            
        except Exception as e:
            logging.error(f"Template capture error: {e}")
            return False, str(e)
