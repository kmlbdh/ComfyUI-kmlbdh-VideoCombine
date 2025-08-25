# kmlbdh_video_combine.py
"""
kmlbdh Video Combine (Smart + Tiled)
Auto-optimizes for RAM/VRAM. Safe for 4K/8K. Built by kmlbdh.
"""
import os
import torch
import numpy as np
import psutil
import subprocess
from comfy.utils import ProgressBar

# Import local utils
from .kmlbdh_utils import save_video


# 🔁 Backward-compatible helpers
def get_output_directory():
    import folder_paths
    return folder_paths.get_output_directory()

def get_save_image_counter(output_dir, prefix="kmlbdh"):
    from pathlib import Path
    counter = 1
    for file in Path(output_dir).glob(f"{prefix}_*.mp4"):
        try:
            num = int(file.stem[len(prefix)+1:])
            if num >= counter:
                counter = num + 1
        except:
            continue
    return counter


class KMLBDH_VideoCombine:
    @classmethod
    def INPUT_TYPES(s):
        ram_gb = round(psutil.virtual_memory().total / (1024**3))
        vram_gb = round(torch.cuda.get_device_properties(0).total_memory / (1024**3)) if torch.cuda.is_available() else 0

        if ram_gb < 16 or vram_gb < 10:
            default_chunk = 6
            default_tile = 1024
            default_save_in_mem = False
            perf_hint = "Low VRAM/RAM"
        elif ram_gb < 32 or vram_gb < 16:
            default_chunk = 8
            default_tile = 1024
            default_save_in_mem = False
            perf_hint = "Mid-range"
        else:
            default_chunk = 12
            default_tile = 0
            default_save_in_mem = True
            perf_hint = "High-end"

        return {
            "required": {
                "images": ("IMAGE",),
                "frame_rate": ("INT", {"default": 16, "min": 1, "max": 120}),
                "codec": (["h264", "hevc"], {"default": "h264"}),
                "crf": ("INT", {"default": 15, "min": 0, "max": 50}),
                "preset": (["ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow"], {"default": "fast"}),
                "pix_fmt": (["yuv420p", "yuv444p"], {"default": "yuv420p"}),
                "chunk_size": ("INT", {
                    "default": default_chunk,
                    "min": 1,
                    "max": 64,
                    "label": f"Chunk Size ({perf_hint})"
                }),
                "save_images_in_memory": ("BOOLEAN", {
                    "default": default_save_in_mem,
                    "label": "Save in RAM?"
                }),
                "tile_size": ("INT", {
                    "default": default_tile,
                    "min": 0,
                    "max": 8192,
                    "step": 64,
                    "label": "Tile Size (0=off)"
                }),
                "tile_overlap": ("INT", {
                    "default": 8,
                    "min": 0,
                    "max": 64,
                    "label": "Tile Overlap"
                }),
                "filename_prefix": ("STRING", {
                    "default": "kmlbdh",
                    "multiline": False,
                    "dynamicPrompts": False,
                    "placeholder": "Enter output prefix",
                    "label": "📁 Filename Prefix"
                }),
            },
            "optional": {
                "audio": ("AUDIO",),
            },
            "hidden": {
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO"
            }
        }

    RETURN_TYPES = ("VHS_FILENAMES",)
    FUNCTION = "combine"
    CATEGORY = "kmlbdh"
    OUTPUT_NODE = True

    def combine(self, images, frame_rate, codec, crf, preset, pix_fmt, chunk_size, save_images_in_memory, tile_size, tile_overlap, filename_prefix, audio=None, prompt=None, extra_pnginfo=None):
        frames = images.cpu()
        total_frames = frames.shape[0]
        if total_frames == 0:
            raise ValueError("No frames to save")

        output_dir = get_output_directory()
        counter = get_save_image_counter(output_dir, filename_prefix)
        file = f"{filename_prefix}_{counter:05d}.mp4"
        file_path = os.path.join(output_dir, file)

        pbar = ProgressBar(total_frames)
        use_tiling = tile_size > 0
        final_tile_size = tile_size if use_tiling else None

        try:
            if save_images_in_memory:
                # Full RAM mode
                save_video(
                    file_path, frames,
                    fps=frame_rate,
                    codec=codec,
                    crf=crf,
                    preset=preset,
                    pix_fmt=pix_fmt,
                    tile_size=final_tile_size,
                    overlap=tile_overlap
                )
            else:
                # Chunked streaming mode
                temp_dir = os.path.join(output_dir, "temp_kmlbdh")
                os.makedirs(temp_dir, exist_ok=True)
                chunk_files = []

                for i in range(0, total_frames, chunk_size):
                    chunk = frames[i:i+chunk_size]
                    chunk_file = os.path.join(temp_dir, f"chunk_{i//chunk_size:03d}.mp4")
                    save_video(
                        chunk_file, chunk,
                        fps=frame_rate,
                        codec=codec,
                        crf=crf,
                        preset=preset,
                        pix_fmt=pix_fmt,
                        tile_size=final_tile_size,
                        overlap=tile_overlap
                    )
                    chunk_files.append(chunk_file)
                    pbar.update(len(chunk))

                # Concatenate chunks
                concat_file = os.path.join(temp_dir, "concat_list.txt")
                with open(concat_file, 'w') as f:
                    for cf in chunk_files:
                        f.write(f"file '{os.path.abspath(cf)}'\n")

                cmd = ['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', concat_file, '-c', 'copy', file_path]
                subprocess.run(cmd, check=True, capture_output=True)

                # Cleanup
                for f in chunk_files:
                    try: os.remove(f)
                    except: pass
                try:
                    os.remove(concat_file)
                    os.rmdir(temp_dir)
                except: pass

        except Exception as e:
            raise RuntimeError(f"kmlbdh Video Combine failed: {str(e)}")

        # UI preview
        result = {
            "filename": file,
            "subfolder": "",
            "type": "output",
            "format": "video/mp4"
        }
        return {"ui": {"video": [result]}, "result": ((file, "", "output"),)}


NODE_CLASS_MAPPINGS = {
    "KMLBDH_VideoCombine": KMLBDH_VideoCombine
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "KMLBDH_VideoCombine": "📹 kmlbdh Video Combine (Smart + Tiled)"
}