# kmlbdh_ram_cleaner.py
"""
kmlbdh RAM Cleaner
Forces garbage collection and CUDA cache cleanup to prevent OOM during RIFE or upscaling.
Use after heavy nodes like Upscale, VAEDecode, etc.
"""
import gc
import torch
from comfy.utils import ProgressBar

class KMLBDH_RAMCleaner:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "images": ("IMAGE",),
                "message": ("STRING", {
                    "default": "🧹 kmlbdh RAM Cleaner: Cache cleared",
                    "multiline": False,
                    "label": "Log Message"
                })
            }
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "clean"
    CATEGORY = "kmlbdh"
    DESCRIPTION = "Forces CPU/GPU memory cleanup. Use after Upscale or before RIFE to prevent crashes."

    def clean(self, images, message):
        # Log message
        print(message)

        # Force Python garbage collection
        gc.collect()

        # Clear CUDA cache if GPU available
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()  # Ensure all ops are done

        return (images,)


# Register node
NODE_CLASS_MAPPINGS = {
    "KMLBDH_RAMCleaner": KMLBDH_RAMCleaner
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "KMLBDH_RAMCleaner": "🧹 kmlbdh RAM Cleaner"
}