kmlbdh Video Combine (Smart + Tiled) 🚀

A custom ComfyUI node designed for stable, high-resolution video export — even on limited hardware.

❌ The Problem

VHS_VideoCombine often crashes on 4K videos due to RAM/VRAM overload.

✅ The Solution

kmlbdh Video Combine (Smart + Tiled) — a smarter, safer, and fully customizable alternative that:

Auto-detects your RAM & VRAM and suggests safe defaults

Splits frames into tiles to avoid VRAM crashes (perfect for 4K/8K)

Streams in chunks to prevent RAM overload

Supports custom filename_prefix for organized output

Clean, modular, and branded for your workflow

🔧 Features

Auto Hardware Detection → Recommends safe settings for your system

Tiled Processing → Split frames via tile_size (512, 1024, etc.)

Chunked Encoding → Control memory usage with chunk_size

Safe Streaming → save_images_in_memory: False = disk-first workflow

Custom Naming → Use filename_prefix just like native nodes

FFmpeg-Powered → High-quality H.264/HEVC encoding

Crash-Free → Tested on 4K+ video sequences

🛠 Installation
cd ComfyUI/custom_nodes
git clone https://github.com/kmlbdh/ComfyUI-kmlbdh-VideoCombine.git


Restart ComfyUI and search for:
👉 kmlbdh Video Combine (Smart + Tiled)

👀 Preview

Here’s how the node looks inside ComfyUI:

🧩 Example Workflow

Use kmlbdh Video Combine (Smart + Tiled) together with:

RIFE VFI → Frame interpolation

4x Upscale → Resolution boost

Wan2.2 I2V (or other video models) → Smooth video generation

Example inside ComfyUI:

🎯 Who Is This For?

AI animators working with 4K image-to-video

Users with 8–16GB VRAM hitting memory limits

Anyone tired of Out of Memory errors during export

Creators who want a stable, branded workflow

📢 Author

Made with ❤️ by kmlbdh
This isn’t just a fix — it’s your tool.
Branded, optimized, and built for your workflow.

📜 [MIT License]
