#!/usr/bin/env python3

from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
import subprocess
import tempfile
import zlib
from pathlib import Path


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def read_png(path: Path) -> tuple[int, int, int, int, bytes]:
    with path.open("rb") as handle:
        if handle.read(8) != PNG_SIGNATURE:
            raise ValueError(f"{path} is not a PNG")

        width = 0
        height = 0
        bit_depth = 0
        color_type = 0
        idat_chunks: list[bytes] = []

        while True:
            length_bytes = handle.read(4)
            if not length_bytes:
                break
            length = struct.unpack(">I", length_bytes)[0]
            chunk_type = handle.read(4)
            chunk_data = handle.read(length)
            handle.read(4)

            if chunk_type == b"IHDR":
                width, height, bit_depth, color_type, compression, filter_method, interlace = struct.unpack(
                    ">IIBBBBB", chunk_data
                )
                if compression != 0 or filter_method != 0 or interlace != 0:
                    raise ValueError(f"{path} uses unsupported PNG features")
            elif chunk_type == b"IDAT":
                idat_chunks.append(chunk_data)
            elif chunk_type == b"IEND":
                break

        return width, height, bit_depth, color_type, zlib.decompress(b"".join(idat_chunks))


def bytes_per_pixel(color_type: int, bit_depth: int) -> int:
    if bit_depth != 8:
        raise ValueError(f"Unsupported bit depth: {bit_depth}")
    if color_type == 6:
        return 4
    if color_type == 2:
        return 3
    if color_type == 0:
        return 1
    raise ValueError(f"Unsupported PNG color type: {color_type}")


def paeth_predictor(left: int, up: int, up_left: int) -> int:
    prediction = left + up - up_left
    left_distance = abs(prediction - left)
    up_distance = abs(prediction - up)
    up_left_distance = abs(prediction - up_left)
    if left_distance <= up_distance and left_distance <= up_left_distance:
        return left
    if up_distance <= up_left_distance:
        return up
    return up_left


def decode_rgba(path: Path) -> tuple[int, int, bytearray]:
    width, height, bit_depth, color_type, raw = read_png(path)
    bpp = bytes_per_pixel(color_type, bit_depth)
    stride = width * bpp
    rows = bytearray(width * height * 4)
    previous = bytearray(stride)
    offset = 0

    for row_index in range(height):
        filter_type = raw[offset]
        offset += 1
        current = bytearray(raw[offset : offset + stride])
        offset += stride

        for index in range(stride):
            left = current[index - bpp] if index >= bpp else 0
            up = previous[index]
            up_left = previous[index - bpp] if index >= bpp else 0
            if filter_type == 1:
                current[index] = (current[index] + left) & 0xFF
            elif filter_type == 2:
                current[index] = (current[index] + up) & 0xFF
            elif filter_type == 3:
                current[index] = (current[index] + ((left + up) // 2)) & 0xFF
            elif filter_type == 4:
                current[index] = (current[index] + paeth_predictor(left, up, up_left)) & 0xFF
            elif filter_type != 0:
                raise ValueError(f"{path} uses unsupported PNG filter type {filter_type}")

        destination = row_index * width * 4
        if color_type == 6:
            rows[destination : destination + width * 4] = current
        elif color_type == 2:
            for pixel_index in range(width):
                source = pixel_index * 3
                target = destination + pixel_index * 4
                rows[target : target + 3] = current[source : source + 3]
                rows[target + 3] = 255
        elif color_type == 0:
            for pixel_index in range(width):
                value = current[pixel_index]
                target = destination + pixel_index * 4
                rows[target : target + 4] = bytes((value, value, value, 255))

        previous = current

    return width, height, rows


def resize_png(source: Path, destination: Path, width: int, height: int) -> None:
    subprocess.run(
        ["sips", "-s", "format", "png", "-z", str(height), str(width), str(source), "--out", str(destination)],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def image_metrics(native_path: Path, safari_path: Path) -> dict[str, float]:
    native_width, native_height, native_pixels = decode_rgba(native_path)
    safari_width, safari_height, safari_pixels = decode_rgba(safari_path)
    if (native_width, native_height) != (safari_width, safari_height):
        raise ValueError("Images must have matching dimensions before diffing")

    total_samples = native_width * native_height * 4
    absolute_sum = 0
    squared_sum = 0
    max_channel_delta = 0
    pixels_over_threshold = 0
    luma_sum = 0.0

    for pixel_start in range(0, len(native_pixels), 4):
        channel_deltas = [
            abs(native_pixels[pixel_start + channel] - safari_pixels[pixel_start + channel]) for channel in range(4)
        ]
        absolute_sum += sum(channel_deltas)
        squared_sum += sum(delta * delta for delta in channel_deltas)
        max_channel_delta = max(max_channel_delta, max(channel_deltas))
        if max(channel_deltas[:3]) > 16:
            pixels_over_threshold += 1
        luma_sum += (
            0.2126 * channel_deltas[0] + 0.7152 * channel_deltas[1] + 0.0722 * channel_deltas[2]
        )

    pixel_count = native_width * native_height
    return {
        "meanAbsoluteError": absolute_sum / total_samples,
        "rootMeanSquareError": math.sqrt(squared_sum / total_samples),
        "meanLumaDelta": luma_sum / pixel_count,
        "pixelsOverThresholdRatio": pixels_over_threshold / pixel_count,
        "maxChannelDelta": float(max_channel_delta),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Pair a native renderer checkpoint with a Safari reference capture.")
    parser.add_argument("--checkpoint-dir", required=True, type=Path)
    parser.add_argument("--safari-golden-dir", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    checkpoint_dir = args.checkpoint_dir.resolve()
    safari_golden_dir = args.safari_golden_dir.resolve()
    output_path = args.output.resolve() if args.output else checkpoint_dir / "renderer-vs-safari.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    native_png = checkpoint_dir / "window.png"
    safari_png = safari_golden_dir / "reference-safari.png"
    native_state = checkpoint_dir / "state.json"
    safari_metadata = safari_golden_dir / "reference-safari-metadata.json"

    for path in (native_png, safari_png, native_state, safari_metadata):
        if not path.exists():
            raise SystemExit(f"missing required file: {path}")

    native_state_payload = json.loads(native_state.read_text(encoding="utf-8"))
    safari_metadata_payload = json.loads(safari_metadata.read_text(encoding="utf-8"))

    native_width, native_height, *_ = read_png(native_png)
    safari_width, safari_height, *_ = read_png(safari_png)
    logical_width = int(safari_metadata_payload.get("windowWidth") or native_width)
    logical_height = int(safari_metadata_payload.get("windowHeight") or native_height)
    scale_factor = safari_width / logical_width if logical_width else 1.0

    normalized_native = output_path.parent / "normalized-native.png"
    normalized_safari = output_path.parent / "normalized-safari.png"

    if (native_width, native_height) == (logical_width, logical_height):
        normalized_native.write_bytes(native_png.read_bytes())
    else:
        resize_png(native_png, normalized_native, logical_width, logical_height)

    if (safari_width, safari_height) == (logical_width, logical_height):
        normalized_safari.write_bytes(safari_png.read_bytes())
    else:
        with tempfile.TemporaryDirectory(prefix="compare-renderer-") as temp_dir:
            temp_safari = Path(temp_dir) / "safari.png"
            temp_safari.write_bytes(safari_png.read_bytes())
            resize_png(temp_safari, normalized_safari, logical_width, logical_height)

    metrics = image_metrics(normalized_native, normalized_safari)

    report = {
        "checkpointDir": str(checkpoint_dir),
        "safariGoldenDir": str(safari_golden_dir),
        "nativeImage": {
            "path": str(native_png),
            "width": native_width,
            "height": native_height,
            "sha256": sha256(native_png),
        },
        "safariImage": {
            "path": str(safari_png),
            "width": safari_width,
            "height": safari_height,
            "sha256": sha256(safari_png),
        },
        "normalizedImages": {
            "native": {
                "path": str(normalized_native),
                "width": logical_width,
                "height": logical_height,
                "sha256": sha256(normalized_native),
            },
            "safari": {
                "path": str(normalized_safari),
                "width": logical_width,
                "height": logical_height,
                "sha256": sha256(normalized_safari),
            },
        },
        "samePixelSize": native_width == safari_width and native_height == safari_height,
        "sameFileHash": sha256(native_png) == sha256(safari_png),
        "estimatedSafariScaleFactor": scale_factor,
        "selectedFile": native_state_payload.get("selectedFile"),
        "viewport": native_state_payload.get("viewport"),
        "safariMetadata": safari_metadata_payload,
        "imageDiff": metrics,
        "note": "This report normalizes Retina-scale Safari captures to the logical viewport before computing pixel-diff metrics.",
    }

    output_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
