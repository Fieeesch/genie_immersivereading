import base64
import json
import requests
from pathlib import Path

class PanoramaGenerator:
    def __init__(self, database_dir: Path, lora_name: str = "LatentLabs360", lora_weight: float = 1.0):
        '''
        Docstring for __init__
        
        :param database_dir: directory path of the book database
        :type database_dir: Path
        :param lora_name: Name of the LoRA model to use in A1111
        :type lora_name: str
        :param lora_weight: Weight of the LoRA model to use in A1111
        :type lora_weight: float
        '''
        
        self.API_TXT2IMG = "http://127.0.0.1:7860/sdapi/v1/txt2img"
        self.API_UPSCALE = "http://127.0.0.1:7860/sdapi/v1/extra-single-image"
        self.DATA_ROOT = database_dir
        self.DATA_ROOT.mkdir(parents=True, exist_ok=True)

        self.LORA_NAME = lora_name
        self.LORA_WEIGHT = lora_weight

    def generate_360_panorama(self, prompt: str, negative_prompt: str, filepath: str):
        '''
        Generates a 360° panorama image based on the given prompt and saves it to the output directory.
        
        :param prompt: Image Prompt for the panorama
        :type prompt: str
        :param negative_prompt: Negative Prompt to avoid certain elements in the image
        :type negative_prompt: str
        :param filepath: Output filename relative to the database root (including .png ending)
        :type filepath: str
        '''

        payload = {
            "prompt": f"<lora:{self.LORA_NAME}:{self.LORA_WEIGHT}>360° panorama view: {prompt}",
            "negative_prompt": negative_prompt,
            "width": 1024,
            "height": 512,
            "steps": 50,
            "cfg_scale": 7.0,
            "sampler_index": "DPM++ 2M Karras",
            "batch_size": 1,
            "n_iter": 1,
            "alwayson_scripts": {
                "Asymmetric tiling": {
                    "args": [True, True, False, 0, -1] # [active, tile_x, tile_y, margin, seam_fix]
                }
            }
        }  

        response = requests.post(self.API_TXT2IMG, json=payload)
        response.raise_for_status()
        r = response.json()

        for img_data in r.get("images", []):
            upscaled_data = self._upscale_image(img_data)
            b64_str = upscaled_data
            if "," in b64_str:
                b64_str = b64_str.split(",", 1)[1]

            image_bytes = base64.b64decode(b64_str)
            out_path = self.DATA_ROOT / f"{filepath}"
            with open(out_path, "wb") as f:
                f.write(image_bytes)

    def regenerate_360_panoramas(self, book_id: str):
        '''
        regenerates all 360° panoramas for a given book based on previously generated prompts
        
        :param book_id: id of the book (= folder name in the database)
        :type book_id: str
        '''

        book_dir = self.DATA_ROOT / book_id
        if not book_dir.exists() or not book_dir.is_dir():
            raise FileNotFoundError(f"Book directory not found: {book_dir}")
        
        json_file = book_dir / "book.json"
        if not json_file.exists():
            raise FileNotFoundError("book.json missing")

        with json_file.open("r", encoding="utf-8") as f:
            data = json.load(f)

        for scene in data.get("scenes", []):
            prompt = scene.get("image_prompt", "")
            img_filename = scene.get("image_file", f"scene_{scene.get('index', 0)}.png")
            self.generate_360_panorama(prompt, "", f"{book_id}/{img_filename}")

    def _upscale_image(self, img_data):
        payload = {
            "resize_mode": 0,
            "upscaling_resize": 4,
            "upscaling_crop": True,
            "upscaler_1": "SwinIR_4x",
            "upscaler_2": "R-ESRGAN 4x+",
            "extras_upscaler_2_visibility": 0.35,
            "image": img_data
        }

        response = requests.post(self.API_UPSCALE, json=payload)
        response.raise_for_status()
        r = response.json()
        return r.get("image", "")

if __name__ == "__main__":

    # Generate a test panorama
    print("Generating test panorama...")
    generator = PanoramaGenerator(Path("./test_results"))
    prompt = "A sunny riverside meadow with lots of daisies"
    negative_prompt = "lowres, blurry, distorted"
    generator.generate_360_panorama(prompt, negative_prompt, "riverside_upscaled.png")
    print("Done! Output saved to ./test_results")

