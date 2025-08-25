# kmlbdh_utils.py
"""
kmlbdh_utils.py - Core video encoding with tiling support
Used by KMLBDH_VideoCombine for safe, high-res video export.
"""
import os
import numpy as np
import subprocess
import torch
from typing import Iterator

def tensor_to_bytes(tensor: torch.Tensor) -> np.ndarray:
    """Convert tensor to uint8 numpy array."""
    if tensor.dtype == torch.bfloat16:
        tensor = tensor.to(torch.float32)
    tensor = torch.clamp(tensor, 0, 1)
    tensor = tensor.cpu().numpy()
    return (tensor * 255).astype(np.uint8)

def save_video(
    file_path: str,
    images: np.ndarray | torch.Tensor,
    fps: int = 16,
    codec: str = "h264",
    crf: int = 15,
    preset: str = "medium",
    pix_fmt: str = "yuv420p",
    tile_size: int = None,
    overlap: int = 8
):
    """
    Save video with optional tiling for giant frames.
    If tile_size is provided, processes each frame in tiles.
    """
    if isinstance(images, torch.Tensor):
        images = tensor_to_bytes(images)

    T, H, W, C = images.shape

    if tile_size is None:
        # Normal mode: direct rawvideo encode
        _write_video(file_path, images, fps, codec, crf, preset, pix_fmt)
        return

    # Tiled mode
    temp_dir = os.path.join(os.path.dirname(file_path), "temp_kmlbdh_tiles")
    os.makedirs(temp_dir, exist_ok=True)
    temp_video = os.path.join(temp_dir, "output.mp4")

    # FFmpeg command: accept PNG frames via pipe
    cmd = [
        'ffmpeg', '-y', '-f', 'image2pipe', '-vcodec', 'png',
        '-r', str(fps), '-i', '-',  # read from stdin
        '-vcodec', codec, '-pix_fmt', pix_fmt,
        '-crf', str(crf), '-preset', preset,
        '-loglevel', 'error'
    ]

    if codec == "h264":
        cmd += ['-c:v', 'libx264']
    elif codec == "hevc":
        cmd += ['-c:v', 'libx265']

    cmd += [temp_video]

    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)

    try:
        for frame in images:
            for tile in _extract_tiles(frame, tile_size, overlap):
                tile_uint8 = tile.astype(np.uint8)
                _write_png_to_pipe(proc.stdin, tile_uint8)
            proc.stdin.flush()  # Ensure frame separation

        proc.stdin.close()
        stderr = proc.stderr.read()
        proc.wait()
        if proc.returncode != 0:
            raise RuntimeError(f"FFmpeg tiling error: {stderr.decode()}")

        # Move to final location
        os.replace(temp_video, file_path)
    finally:
        _cleanup_temp(temp_dir)

def _extract_tiles(
    img: np.ndarray,
    tile_size: int,
    overlap: int
) -> Iterator[np.ndarray]:
    """Yield overlapping tiles from image."""
    H, W, C = img.shape
    step = tile_size - overlap

    y = 0
    while y < H:
        x = 0
        while x < W:
            y1, x1 = y, x
            y2 = min(y + tile_size, H)
            x2 = min(x + tile_size, W)

            tile = img[y1:y2, x1:x2]
            yield tile

            x += step
        y += step

def _write_png_to_pipe(pipe, img: np.ndarray):
    """Write a single image to ffmpeg stdin using PPM format (simple, reliable)."""
    try:
        h, w, c = img.shape
        # Convert to RGB if grayscale
        if c == 1:
            img = np.broadcast_to(img, (h, w, 3))
        # PPM header: P6 W H 255\n + raw bytes
        header = f"P6 {w} {h} 255\n".encode('ascii')
        pipe.write(header)
        pipe.write(img.tobytes())
    except Exception as e:
        print(f"[kmlbdh] PPM write error: {e}")

def _write_video(
    file_path: str,
    images: np.ndarray,
    fps: int,
    codec: str,
    crf: int,
    preset: str,
    pix_fmt: str
):
    """Normal video write (non-tiled)."""
    h, w = images.shape[1:3]
    cmd = [
        'ffmpeg', '-y', '-f', 'rawvideo', '-vcodec', 'rawvideo',
        '-s', f'{w}x{h}', '-pix_fmt', 'rgb24', '-r', str(fps), '-i', '-',
        '-vcodec', codec, '-pix_fmt', pix_fmt, '-crf', str(crf),
        '-preset', preset, '-loglevel', 'error'
    ]
    if codec == "h264":
        cmd += ['-c:v', 'libx264']
    elif codec == "hevc":
        cmd += ['-c:v', 'libx265']
    cmd += [file_path]

    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    for frame in images:
        proc.stdin.write(frame.tobytes())
    proc.stdin.close()
    stderr = proc.stderr.read()
    proc.wait()
    if proc.returncode != 0:
        raise RuntimeError(f"FFmpeg error: {stderr.decode()}")

def _cleanup_temp(temp_dir: str):
    """Safely remove temporary directory."""
    import shutil
    try:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
    except Exception as e:
        print(f"[kmlbdh] Temp cleanup failed: {e}")