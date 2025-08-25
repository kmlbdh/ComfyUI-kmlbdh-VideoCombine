# mtb_utils.py (v2 - with tiled support)

import os
import numpy as np
import subprocess
import torch
from typing import Iterator, Tuple

def tensor_to_bytes(tensor: torch.Tensor) -> np.ndarray:
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
    tile_size: int = None,  # New: tile size for giant frames
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
        # Normal mode
        _write_video(file_path, images, fps, codec, crf, preset, pix_fmt)
        return

    # Tiled mode
    temp_dir = os.path.join(os.path.dirname(file_path), "temp_tiles")
    os.makedirs(temp_dir, exist_ok=True)

    temp_image = os.path.join(temp_dir, "frame.png")
    temp_video = os.path.join(temp_dir, "output.mp4")

    cmd = [
        'ffmpeg',
        '-y',
        '-f', 'image2pipe',
        '-vcodec', 'png',
        '-r', str(fps),
        '-i', '-',
        '-vcodec', codec,
        '-pix_fmt', pix_fmt,
        '-crf', str(crf),
        '-preset', preset,
        '-loglevel', 'error'
    ]

    if codec == "h264":
        cmd += ['-c:v', 'libx264']
    elif codec == "hevc":
        cmd += ['-c:v', 'libx265']

    cmd += [temp_video]

    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)

    for frame in images:
        for tile in _extract_tiles(frame, tile_size, overlap):
            tile_uint8 = tile.astype(np.uint8)
            success = _write_image_to_pipe(proc.stdin, tile_uint8)
            if not success:
                break
        # Optional: write last tile again to hold duration
        proc.stdin.flush()

    proc.stdin.close()
    stderr = proc.stderr.read()
    proc.wait()
    if proc.returncode != 0:
        raise RuntimeError(f"FFmpeg tiling error: {stderr.decode()}")

    # Move final video
    os.replace(temp_video, file_path)
    _cleanup_temp(temp_dir)

def _extract_tiles(
    img: np.ndarray,
    tile_size: int,
    overlap: int
) -> Iterator[np.ndarray]:
    """Yield overlapping tiles from image."""
    H, W, C = img.shape
    step = tile_size - overlap

    for y in range(0, H, step):
        for x in range(0, W, step):
            y1, x1 = y, x
            y2 = min(y + tile_size, H)
            x2 = min(x + tile_size, W)

            tile = img[y1:y2, x1:x2]
            yield tile

def _write_image_to_pipe(pipe, img: np.ndarray):
    try:
        height, width = img.shape[:2]
        header = f"P6 {width} {height} 255\n"
        pipe.write(header.encode('ascii'))
        pipe.write(img.tobytes())
        return True
    except Exception:
        return False

def _write_video(file_path: str, images: np.ndarray, fps: int, codec: str, crf: int, preset: str, pix_fmt: str):
    """Normal video write (non-tiled)."""
    h, w = images.shape[1:3]
    cmd = [
        'ffmpeg', '-y', '-f', 'rawvideo', '-vcodec', 'rawvideo',
        '-s', f'{w}x{h}', '-pix_fmt', 'rgb24', '-r', str(fps), '-i', '-',
        '-vcodec', codec, '-pix_fmt', pix_fmt, '-crf', str(crf), '-preset', preset,
        '-loglevel', 'error'
    ]
    if codec == "h264": cmd += ['-c:v', 'libx264']
    elif codec == "hevc": cmd += ['-c:v', 'libx265']
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
    import shutil
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)