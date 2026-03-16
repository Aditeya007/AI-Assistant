"""
Creative Engine
Handles image generation, code generation, and sound synthesis
All using FREE tools and APIs
"""
import requests
import json
import logging
import numpy as np
import wave
import io
import base64
from typing import Optional

class CreativeEngine:
    """Handles creative AI tasks - images, code, sounds"""
    
    def __init__(self, gemini_client=None, model_id=None):
        self.gemini_client = gemini_client
        self.model_id = model_id
        self.hf_token = None  # Optional: Hugging Face token for higher limits
        
    async def generate_image(self, prompt: str, negative_prompt: str = "") -> dict:
        """
        Generate image using Hugging Face Inference API (FREE)
        Model: stabilityai/stable-diffusion-2-1
        """
        try:
            API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2-1"
            headers = {}
            if self.hf_token:
                headers["Authorization"] = f"Bearer {self.hf_token}"
            
            payload = {
                "inputs": prompt,
                "parameters": {
                    "negative_prompt": negative_prompt or "blurry, bad quality, distorted",
                    "num_inference_steps": 20,  # Faster generation
                }
            }
            
            response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
            
            if response.status_code == 200:
                # Convert image bytes to base64
                image_bytes = response.content
                image_base64 = base64.b64encode(image_bytes).decode('utf-8')
                
                logging.info(f"Image generated for prompt: {prompt}")
                return {
                    "success": True,
                    "image_base64": image_base64,
                    "prompt": prompt,
                    "message": "Image generated successfully"
                }
            else:
                error_msg = response.text
                logging.error(f"Image generation failed: {error_msg}")
                return {
                    "success": False,
                    "error": error_msg,
                    "message": "Image generation failed. The API might be loading. Try again in a moment."
                }
                
        except Exception as e:
            logging.error(f"Image generation error: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Image generation failed"
            }
    
    async def generate_code(self, description: str, language: str = "python") -> dict:
        """Generate code using Gemini (already free in your setup)"""
        try:
            if not self.gemini_client:
                return {
                    "success": False,
                    "error": "Gemini client not initialized",
                    "message": "Code generation unavailable"
                }
            
            # Craft a code-focused prompt
            prompt = f"""Generate clean, well-commented {language} code for the following task:

Task: {description}

Requirements:
- Include comments explaining the code
- Follow best practices for {language}
- Make it production-ready
- Include example usage if applicable

Generate ONLY the code, no explanations before or after."""

            response = self.gemini_client.chat.completions.create(
                model=self.model_id,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000
            )
            
            code = response.choices[0].message.content.strip()
            
            logging.info(f"Code generated for: {description}")
            return {
                "success": True,
                "code": code,
                "language": language,
                "description": description,
                "message": "Code generated successfully"
            }
            
        except Exception as e:
            logging.error(f"Code generation error: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Code generation failed"
            }
    
    async def generate_sound(self, description: str, duration: float = 1.0) -> dict:
        """
        Generate simple sound/tone using numpy (FREE)
        Can create beeps, notifications, alerts
        """
        try:
            sample_rate = 44100  # CD quality
            
            # Parse description to determine sound type
            desc_lower = description.lower()
            
            if "beep" in desc_lower or "notification" in desc_lower:
                # Generate a beep tone
                frequency = 800  # Hz
                t = np.linspace(0, duration, int(sample_rate * duration))
                wave_data = np.sin(2 * np.pi * frequency * t)
                # Add envelope to avoid clicks
                envelope = np.exp(-t * 3)
                wave_data = wave_data * envelope
                
            elif "alert" in desc_lower or "alarm" in desc_lower:
                # Generate an alert sound (two-tone)
                t = np.linspace(0, duration, int(sample_rate * duration))
                wave_data = (
                    np.sin(2 * np.pi * 1000 * t) * (t < duration/2) +
                    np.sin(2 * np.pi * 1200 * t) * (t >= duration/2)
                )
                
            elif "chord" in desc_lower or "music" in desc_lower:
                # Generate a major chord
                t = np.linspace(0, duration, int(sample_rate * duration))
                wave_data = (
                    np.sin(2 * np.pi * 261.63 * t) +  # C
                    np.sin(2 * np.pi * 329.63 * t) +  # E
                    np.sin(2 * np.pi * 392.00 * t)    # G
                ) / 3
                envelope = np.exp(-t * 2)
                wave_data = wave_data * envelope
                
            else:
                # Default simple tone
                frequency = 440  # A note
                t = np.linspace(0, duration, int(sample_rate * duration))
                wave_data = np.sin(2 * np.pi * frequency * t)
            
            # Normalize to 16-bit range
            wave_data = np.int16(wave_data * 32767)
            
            # Create WAV file in memory
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, 'wb') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(wave_data.tobytes())
            
            # Convert to base64
            wav_buffer.seek(0)
            audio_base64 = base64.b64encode(wav_buffer.read()).decode('utf-8')
            
            logging.info(f"Sound generated: {description}")
            return {
                "success": True,
                "audio_base64": audio_base64,
                "description": description,
                "duration": duration,
                "message": "Sound generated successfully"
            }
            
        except Exception as e:
            logging.error(f"Sound generation error: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Sound generation failed"
            }
