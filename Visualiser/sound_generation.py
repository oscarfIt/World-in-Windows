import os, base64, requests
from pathlib import Path
from enum import Enum


class AudioGenerationMode(Enum):
    """Audio generation modes for different types of sound creation"""
    SOUND_EFFECTS = "sound_effects"    # For sound effects like cow mooing, sword clashing
    AMBIENT = "ambient"                # For ambient sounds like forest, tavern noise
    MUSIC = "music"                   # For background music generation


class SoundGenerator:
    def __init__(self):
        self.api_key = os.environ["STABILITY_API_KEY"]
        if not self.api_key:
            raise ValueError("No API key found. Set STABILITY_API_KEY environment variable.")

    def get_credits_remaining(self):
        """Check how many credits remain on the Stability AI account"""
        balance_url = "https://api.stability.ai/v1/user/balance"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json"
        }
        
        try:
            resp = requests.get(balance_url, headers=headers, timeout=30)
            
            if resp.ok:
                balance_info = resp.json()
                
                # Check multiple possible field names for credits
                credits = balance_info.get('credits')
                if credits is None:
                    credits = balance_info.get('balance')
                if credits is None:
                    credits = balance_info.get('credit_balance')
                
                return credits
            else:
                print(f"Failed to get credits info: {resp.status_code}")
                return None
        except Exception as e:
            print(f"Error checking credits: {e}")
            return None

    def generate_sound_clip(self, prompt: str, duration: float = 5.0, mode: AudioGenerationMode = AudioGenerationMode.SOUND_EFFECTS) -> bytes:
        """
        Generate a sound clip based on a text prompt using Stability AI's audio generation API
        
        Args:
            prompt: Description of the sound to generate (e.g., "a cow mooing in a field")
            duration: Length of audio in seconds (typically 1-10 seconds)
            mode: Type of audio generation mode
            
        Returns:
            bytes: Raw audio data (typically MP3 or WAV format)
        """
        # Note: Stability AI's audio API endpoint - this may need to be updated based on their actual API
        url = "https://api.stability.ai/v2beta/audio/stable-audio-2/text-to-audio"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "audio/*",  # Request raw audio bytes
        }
        
        # Prepare the request data
        files = {
            "prompt": (None, prompt),
            "duration": (None, str(duration)),
            "output_format": (None, "mp3"),  # or "wav"
        }
        
        # Add mode-specific parameters
        if mode == AudioGenerationMode.SOUND_EFFECTS:
            files["category"] = (None, "sound_effects")
        elif mode == AudioGenerationMode.AMBIENT:
            files["category"] = (None, "ambient")
            files["loop"] = (None, "true")  # Ambient sounds often should loop
        elif mode == AudioGenerationMode.MUSIC:
            files["category"] = (None, "music")
            files["duration"] = (None, str(max(duration, 10.0)))  # Music usually needs longer duration
        
        try:
            resp = requests.post(url, headers=headers, files=files, timeout=180)
            
            if not resp.ok:
                print(f"Audio generation failed: {resp.status_code}")
                print(f"Response: {resp.text[:500]}")
                resp.raise_for_status()
            
            return resp.content  # Raw audio bytes
            
        except Exception as e:
            print(f"Error generating sound: {e}")
            raise

    def generate_and_save_sound(self, prompt: str, filename: str = None, duration: float = 5.0, 
                               mode: AudioGenerationMode = AudioGenerationMode.SOUND_EFFECTS) -> Path:
        """
        Generate a sound clip and save it to the Media/Audio directory
        
        Args:
            prompt: Description of the sound to generate
            filename: Optional custom filename (without extension)
            duration: Length of audio in seconds
            mode: Type of audio generation mode
            
        Returns:
            Path: Path to the saved audio file
        """
        # Generate the audio
        audio_bytes = self.generate_sound_clip(prompt, duration, mode)
        
        # Create audio directory if it doesn't exist
        audio_dir = Path("Media") / "Audio"
        audio_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename if not provided
        if filename is None:
            # Create safe filename from prompt
            safe_name = prompt[:50].replace(' ', '_').lower()
            safe_name = "".join(c for c in safe_name if c.isalnum() or c in "._-")
            filename = safe_name
        
        # Save the audio file
        audio_path = audio_dir / f"{filename}.mp3"
        
        with open(audio_path, "wb") as f:
            f.write(audio_bytes)
        
        # Check remaining credits after generation
        credits_left = self.get_credits_remaining()
        if credits_left is not None:
            print(f"Credits remaining: {credits_left}")
        else:
            print("Could not retrieve credits information")
            
        print(f"Sound clip saved to: {audio_path}")
        return audio_path

    def generate_npc_voice_clip(self, npc_name: str, dialogue: str, voice_style: str = "neutral") -> Path:
        """
        Generate a voice clip for an NPC speaking specific dialogue
        
        Args:
            npc_name: Name of the NPC
            dialogue: What the NPC is saying
            voice_style: Style of voice (e.g., "gruff", "melodic", "whispered", "shouting")
            
        Returns:
            Path: Path to the saved audio file
        """
        prompt = f"A {voice_style} voice saying: '{dialogue}'"
        filename = f"{npc_name.replace(' ', '_').lower()}_voice"
        
        return self.generate_and_save_sound(
            prompt=prompt,
            filename=filename,
            duration=max(3.0, len(dialogue) * 0.1),  # Estimate duration based on text length
            mode=AudioGenerationMode.SOUND_EFFECTS
        )

    def generate_location_ambience(self, location_name: str, location_type: str, duration: float = 30.0) -> Path:
        """
        Generate ambient sound for a location
        
        Args:
            location_name: Name of the location
            location_type: Type of location (e.g., "tavern", "forest", "dungeon", "city")
            duration: Length of ambient sound in seconds
            
        Returns:
            Path: Path to the saved audio file
        """
        ambient_descriptions = {
            "tavern": "bustling tavern with chatter, clinking mugs, and crackling fireplace",
            "forest": "peaceful forest with rustling leaves, bird songs, and distant wildlife",
            "dungeon": "eerie dungeon with dripping water, echoing footsteps, and distant whispers",
            "city": "busy medieval city with market sounds, cart wheels, and crowd chatter",
            "cave": "dark cave with water drops, echo, and subtle wind sounds",
            "castle": "grand castle with footsteps on stone, distant conversations, and wind through corridors",
            "battlefield": "chaotic battlefield with clashing weapons, shouting, and dramatic tension"
        }
        
        description = ambient_descriptions.get(location_type.lower(), f"{location_type} environment sounds")
        prompt = f"Ambient soundscape of a {description}"
        
        filename = f"{location_name.replace(' ', '_').lower()}_ambience"
        
        return self.generate_and_save_sound(
            prompt=prompt,
            filename=filename,
            duration=duration,
            mode=AudioGenerationMode.AMBIENT
        )

    def generate_combat_sound(self, action_description: str) -> Path:
        """
        Generate sound effects for combat actions
        
        Args:
            action_description: Description of the combat action (e.g., "sword hitting shield", "fireball explosion")
            
        Returns:
            Path: Path to the saved audio file
        """
        prompt = f"Sound effect of {action_description}"
        filename = f"combat_{action_description.replace(' ', '_').lower()}"
        
        return self.generate_and_save_sound(
            prompt=prompt,
            filename=filename,
            duration=3.0,  # Combat sounds are usually short
            mode=AudioGenerationMode.SOUND_EFFECTS
        )

