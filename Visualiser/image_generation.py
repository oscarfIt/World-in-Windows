import os, base64, requests
from pathlib import Path
from enum import Enum

from npc import NPC

class ImageGenerationMode(Enum):
    CORE = "core"
    STYLE_CONTROL = "style_control"
    SD3_IMG2IMG = "sd3_img2img"

class ImageGenerator:
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

    def generate_with_style_control(self, style_image_path: str, prompt: str, seed: int | None = None) -> bytes:
        url = "https://api.stability.ai/v2beta/stable-image/control/style"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "image/*",  # raw image bytes back
        }
        files = {
            # real file upload: (filename, fileobj, mimetype)
            "image": ("style_ref.png", open(style_image_path, "rb"), "image/png"),
            # IMPORTANT: keep text fields in `files` as (None, value) to force multipart/form-data
            "prompt": (None, prompt),
            "negative_prompt": (None, "blurry, watermark, text, photo-realistic, realism"),
            "output_format": (None, "png"),
        }
        # if seed is not None:
        #     files["seed"] = (None, str(seed))

        resp = requests.post(url, headers=headers, files=files, timeout=180)
        if not resp.ok:
            print("DEBUG", resp.status_code, resp.headers.get("content-type"), resp.text[:500])
        resp.raise_for_status()
        return resp.content  # PNG bytes

    def generate_img2img_sd3(self, ref_image_path: str, prompt: str, strength: float = 0.4, seed: int | None = None):
        """
        SD3 image-to-image: uses your reference image as base; 'strength' controls how much it changes (0.2–0.6 good).
        """
        url = "https://api.stability.ai/v2beta/stable-image/generate/sd3"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "image/*",
        }
        files = {
            "image": ("reference.png", open(ref_image_path, "rb"), "image/png"),
            "prompt": (None, prompt),
            # API expects multipart; field name for strength is 'strength' on this route
            "negative_prompt": (None, "blurry, watermark, text, photo-realistic, realism"),
            "strength": (None, str(strength)),
            "output_format": (None, "png"),
            # Optional: if you pass aspect_ratio with img2img, some routes ignore it (composition comes from image)
            # "aspect_ratio": (None, "3:4"),
        }
        # if seed is not None:
        #     files["seed"] = (None, str(seed))
        # Some routes want an explicit mode:
        files["mode"] = (None, "image-to-image")
        resp = requests.post(url, headers=headers, files=files, timeout=180)
        if not resp.ok:
            print("DEBUG", resp.status_code, resp.headers.get("content-type"), resp.text[:500])
        resp.raise_for_status()
        return resp.content  # bytes of PNG

    def create_character_portrait(self, npc: NPC, mode: ImageGenerationMode):

        img_bytes = bytes()
        prompt = npc.to_prompt()

        if mode == ImageGenerationMode.CORE:

            url = "https://api.stability.ai/v2beta/stable-image/generate/core"

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/json",          # <- ask for JSON (base64 image)
            }

            # Put ALL form fields in `files` as (None, value) tuples to force multipart
            files = {
                "prompt": (None, prompt),
                "negative_prompt": (None, "blurry, watermark, text, photo-realistic, realism"),
                "output_format": (None, "png"),     # png | jpeg | webp
                "aspect_ratio": (None, "3:2")
            }

            resp = requests.post(url, headers=headers, files=files, timeout=120)
            if not resp.ok:
                print("DEBUG", resp.status_code, resp.headers.get("content-type"), resp.text[:500])
            resp.raise_for_status()

            b64 = resp.json()["image"]                # field name per API
            img_bytes = base64.b64decode(b64)
        elif mode == ImageGenerationMode.STYLE_CONTROL:
            style_image_path = Path("Media") / "Image References" / "character_portrait.png"
            img_bytes = self.generate_with_style_control(style_image_path, prompt, seed=12345)

        elif mode == ImageGenerationMode.SD3_IMG2IMG:
            ref_image_path = Path("Media") / "Image References" / "character_portrait.png"
            img_bytes = self.generate_img2img_sd3(ref_image_path, prompt, strength=0.3, seed=12345)

        else:
            raise ValueError("Unknown MODE")
        
        # Save the image to the NPCs directory
        npc_dir = Path("Media") / "NPCs"
        npc_dir.mkdir(parents=True, exist_ok=True)  # Create directory if it doesn't exist
        
        # Create a safe filename from NPC name
        safe_name = npc.name.replace(' ', '_').lower()
        safe_name = "".join(c for c in safe_name if c.isalnum() or c in "._-")
        image_path = npc_dir / f"{safe_name}.png"
        
        # Write the image file
        with open(image_path, "wb") as f:
            f.write(img_bytes)
        
        # Check remaining credits after generation
        credits_left = self.get_credits_remaining()
        if credits_left is not None:
            print(f"Credits remaining: {credits_left}")
        else:
            print("Could not retrieve credits information")
            
        print(f"Portrait saved to: {image_path}")
        return img_bytes

