"""
Wake Word Listener Service
Continuously listens for "Hey Ultron", "Jarvis" wake words
Uses Vosk for offline, free wake word detection
"""
import asyncio
import threading
import logging
from vosk import Model, KaldiRecognizer
import pyaudio
import json

class WakeWordListener:
    """Background service for wake word detection"""
    
    def __init__(self, wake_words=None, callback=None):
        self.wake_words = wake_words or ["hey ultron", "jarvis", "ultron"]
        self.callback = callback
        self.is_listening = False
        self.audio_stream = None
        self.recognizer = None
        self.thread = None
        
    def start(self, vosk_model):
        """Start listening for wake words in background"""
        if self.is_listening:
            logging.warning("Wake word listener already running")
            return
            
        self.is_listening = True
        self.thread = threading.Thread(target=self._listen_loop, args=(vosk_model,), daemon=True)
        self.thread.start()
        logging.info(f"Wake word listener started. Listening for: {', '.join(self.wake_words)}")
        
    def stop(self):
        """Stop wake word listening"""
        self.is_listening = False
        if self.audio_stream:
            self.audio_stream.stop_stream()
            self.audio_stream.close()
        logging.info("Wake word listener stopped")
        
    def _listen_loop(self, vosk_model):
        """Main listening loop (runs in background thread)"""
        try:
            # Initialize audio
            p = pyaudio.PyAudio()
            self.audio_stream = p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=4000
            )
            
            # Initialize recognizer
            self.recognizer = KaldiRecognizer(vosk_model, 16000)
            self.recognizer.SetWords(False)  # Don't need word timestamps
            
            logging.info("Wake word detection active...")
            
            while self.is_listening:
                try:
                    data = self.audio_stream.read(4000, exception_on_overflow=False)
                    
                    if self.recognizer.AcceptWaveform(data):
                        result = json.loads(self.recognizer.Result())
                        text = result.get("text", "").lower().strip()
                        
                        # Check if any wake word was detected
                        for wake_word in self.wake_words:
                            if wake_word in text:
                                logging.info(f"Wake word detected: '{wake_word}' in '{text}'")
                                if self.callback:
                                    # Call callback in async context
                                    asyncio.run_coroutine_threadsafe(
                                        self.callback(wake_word, text),
                                        asyncio.get_event_loop()
                                    )
                                break
                                
                except Exception as e:
                    if self.is_listening:  # Only log if we're still supposed to be listening
                        logging.debug(f"Audio processing error: {e}")
                        
        except Exception as e:
            logging.error(f"Wake word listener error: {e}")
        finally:
            if self.audio_stream:
                self.audio_stream.stop_stream()
                self.audio_stream.close()
            p.terminate()
