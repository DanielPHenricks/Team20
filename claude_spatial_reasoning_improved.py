import requests
import time
import os
import argparse
import base64
from typing import List, Optional
from render_improved import render_views_improved
from PIL import Image, ImageDraw, ImageFont

from anthropic import Anthropic
from dotenv import load_dotenv

import trimesh
import pyrender
import numpy as np

# load .env file
load_dotenv()


def encode_image_base64(path: str) -> str:
    """Read an image from disk and return base64-encoded string."""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def guess_media_type(path: str) -> str:
    """Very small helper to guess the image media type from the file extension."""
    ext = os.path.splitext(path)[1].lower()
    if ext in {".jpg", ".jpeg"}:
        return "image/jpeg"
    if ext == ".png":
        return "image/png"
    if ext == ".gif":
        return "image/gif"
    if ext == ".webp":
        return "image/webp"
    # Fallback
    return "image/jpeg"


def annotate_image(image_path: str, label: str, output_path: str):
    """Add a text label to an image."""
    img = Image.open(image_path)
    draw = ImageDraw.Draw(img)

    # Try to use a nice font, fall back to default if not available
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 36)
    except:
        font = ImageFont.load_default()

    # Add semi-transparent background for text
    text_bbox = draw.textbbox((0, 0), label, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]

    # Position at top-center
    x = (img.width - text_width) // 2
    y = 10

    # Draw background rectangle
    padding = 10
    draw.rectangle(
        [x - padding, y - padding, x + text_width + padding, y + text_height + padding],
        fill=(0, 0, 0, 180)
    )

    # Draw text
    draw.text((x, y), label, fill=(255, 255, 255), font=font)

    img.save(output_path)


def send_to_claude(
    prompt: str, image_paths: Optional[List[str]] = None, model_id="claude-sonnet-4-5", max_tokens=2048
) -> str:
    """Send a prompt (optionally with embedded images) to Claude 3.5 Sonnet and return its reply."""

    load_dotenv()

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY not found. Make sure it is defined in your .env file."
        )

    client = Anthropic(api_key=api_key)

    content = []

    # Attach images first (Claude vision best practice)
    if image_paths:
        for i, path in enumerate(image_paths, start=1):
            if not os.path.isfile(path):
                raise FileNotFoundError(f"Image not found: {path}")

            image_data = encode_image_base64(path)
            media_type = guess_media_type(path)

            # Optional label before each image
            content.append({"type": "text", "text": f"Image {i}:"})
            content.append(
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": image_data,
                    },
                }
            )

    # Then add the user prompt text
    content.append({"type": "text", "text": prompt})

    message = client.messages.create(
        model=model_id,
        max_tokens=max_tokens,
        messages=[
            {
                "role": "user",
                "content": content,
            }
        ],
    )

    # Anthropic returns a list of content blocks; usually the first is the main text
    return message.content[0].text


# get the meshy model
def get_meshy_model(image_path, output_file_path):

    payload = {
        "image_url": f"data:image/png;base64,{encode_image_base64(image_path)}",
        "should_remesh": True,
        "should_texture": True,
        "enable_pbr": True,
    }
    headers = {
        "Authorization": f"Bearer {os.getenv('MESHY_API_KEY')}",
    }

    response = requests.post(
        "https://api.meshy.ai/openapi/v1/image-to-3d",
        headers=headers,
        json=payload,
    )

    response.raise_for_status()

    response_task_id = response.json()["result"]

    preview_task = None

    while True:
        preview_task_response = requests.get(
            f"https://api.meshy.ai/openapi/v1/image-to-3d/{response_task_id}",
            headers=headers,
        )

        preview_task_response.raise_for_status()

        preview_task = preview_task_response.json()

        if preview_task["status"] == "SUCCEEDED":
            print("Preview task finished.")
            break

        print(
            "Preview task status:",
            preview_task["status"],
            "| Progress:",
            preview_task["progress"],
            "| Retrying in 5 seconds...",
        )
        time.sleep(5)

    # download the resulting 3D model
    preview_model_url = preview_task["model_urls"]["glb"]
    print("Downloading preview model from:", preview_model_url)

    preview_model_response = requests.get(preview_model_url)
    preview_model_response.raise_for_status()

    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

    with open(output_file_path, "wb") as f:
        f.write(preview_model_response.content)

    print("Preview model downloaded.")


def generate_rotated_images(path, outdir="renders", n=12, img_size=768, problem_num=None):
    """
    Generate `n` rotated images of the 3D model at `path` and save them to `outdir`.
    Uses improved rendering with better views and annotations.
    Files are saved with unique problem number suffix.
    """
    # Generate renders with problem number suffix
    render_views_improved(glb_path=path, out_dir=outdir, n_views=n, img_size=img_size, problem_num=problem_num)

    # Define view labels for 12-view system
    view_labels = [
        "Front View", "Right View", "Back View", "Left View",
        "Top View", "Bottom View",
        "Front-Top-Right", "Back-Top-Right", "Back-Top-Left", "Front-Top-Left",
        "Front-Bottom-Right", "Back-Bottom-Left"
    ]

    image_paths = []
    annotated_dir = os.path.join(outdir, "annotated")
    os.makedirs(annotated_dir, exist_ok=True)

    # Determine file suffix based on problem number
    suffix = f"_problem_{problem_num}" if problem_num else ""

    for i in range(n):
        img_path = os.path.join(outdir, f"view_{i:03d}{suffix}.png")
        if os.path.exists(img_path):
            # Create annotated version
            label = view_labels[i] if i < len(view_labels) else f"View {i+1}"
            annotated_path = os.path.join(annotated_dir, f"view_{i:03d}_annotated{suffix}.png")
            annotate_image(img_path, label, annotated_path)
            image_paths.append(annotated_path)

    prefix = f"Problem {problem_num}: " if problem_num else ""
    print(f"{prefix}Generated {len(image_paths)} annotated rotated images.")
    return image_paths


def solve_problem_two_stage(problem_image_path, cutout_image_path, problem_num=None, skip_glb_generation=False):
    """
    Improved two-stage reasoning approach for better accuracy.

    :param skip_glb_generation: If True, assumes GLB file already exists and skips Meshy API call
    """
    # Get the meshy model with unique name per problem
    suffix = f"_problem_{problem_num}" if problem_num else ""
    three_d_model_path = f"./tmp/preview_model{suffix}.glb"

    # Generate GLB if needed
    if skip_glb_generation:
        if not os.path.exists(three_d_model_path):
            raise FileNotFoundError(f"GLB file not found: {three_d_model_path}. Run generate_glb_files.py first or remove --skip-glb flag.")
        print(f"Using existing GLB: {three_d_model_path}")
    else:
        get_meshy_model(cutout_image_path, three_d_model_path)

    # Generate the multiple rotations with improved settings
    rotated_image_paths = generate_rotated_images(three_d_model_path, outdir="renders", n=12, img_size=768, problem_num=problem_num)

    # STAGE 1: Build mental model
    stage1_prompt = """Analyze the reference object focusing on SPATIAL STRUCTURE:

PRIORITY: Study the Top and Bottom views (images 5-6) first to understand the 3D structure.

Map out:
1. Which blocks are adjacent to which other blocks (neighbor relationships)
2. The overall 3D configuration and how blocks connect
3. Unique structural features (protruding blocks, indentations, stacking patterns)

Secondary: Note colors, but focus on spatial adjacency over exact color matching.

Be concise but capture the 3D structure."""

    print("Stage 1: Building mental model...")
    reference_images = [cutout_image_path] + rotated_image_paths[:6]  # Use first 6 views
    description = send_to_claude(stage1_prompt, image_paths=reference_images, max_tokens=1500)
    print(f"Stage 1 description:\n{description}\n")

    # STAGE 2: Solve the puzzle using the mental model
    stage2_prompt = f"""Solve this rotation puzzle using your spatial analysis.

REFERENCE STRUCTURE:
{description}

TASK: Which answer choice (1-4, left to right) in the first image matches the reference object?

PRIORITY ANALYSIS:
- Use Top/Bottom views (images 5-6) to verify 3D structure
- Focus on BLOCK ADJACENCY: Do neighbor relationships match?
- Check spatial configuration, not just individual colors

ELIMINATION:
For each choice, find spatial contradictions:
- Does it have the same blocks adjacent to each other?
- Does the 3D structure match the reference?
- Are there impossible configurations?

Eliminate mismatches quickly. Provide brief reasoning, then final line: ONLY the number (1, 2, 3, or 4)."""

    all_images = [problem_image_path] + rotated_image_paths
    print(f"Stage 2: Solving puzzle with {len(all_images)} images...")
    response = send_to_claude(stage2_prompt, image_paths=all_images, max_tokens=2048)

    return response


def solve_problem_single_stage(problem_image_path, cutout_image_path, problem_num=None, skip_glb_generation=False):
    """
    Original single-stage approach but with improved prompt.

    :param skip_glb_generation: If True, assumes GLB file already exists and skips Meshy API call
    """
    # Get the meshy model with unique name per problem
    suffix = f"_problem_{problem_num}" if problem_num else ""
    three_d_model_path = f"./tmp/preview_model{suffix}.glb"

    # Generate GLB if needed
    if skip_glb_generation:
        if not os.path.exists(three_d_model_path):
            raise FileNotFoundError(f"GLB file not found: {three_d_model_path}. Run generate_glb_files.py first or remove --skip-glb flag.")
        print(f"Using existing GLB: {three_d_model_path}")
    else:
        get_meshy_model(cutout_image_path, three_d_model_path)

    # Generate the multiple rotations with improved settings
    rotated_image_paths = generate_rotated_images(three_d_model_path, outdir="renders", n=12, img_size=768, problem_num=problem_num)

    # Improved single-stage prompt
    prompt = """Solve this rotation puzzle by identifying which answer choice (1, 2, 3, or 4, left to right) matches the reference object.

The first image shows the puzzle. The remaining images show the reference object from labeled angles.

CRITICAL: Focus on SPATIAL RELATIONSHIPS between blocks, not just colors.

PRIORITY VIEWS:
- Images 5-6 (Top/Bottom views): Use these to understand the 3D structure and block arrangement
- Corner views: Verify how blocks connect in 3D space

METHOD:
1. Study Top/Bottom views to map the 3D structure
2. For each answer choice, identify spatial mismatches:
   - Which blocks are adjacent to which other blocks?
   - Are the neighbor relationships the same as the reference?
   - Does the overall 3D configuration match?
3. Eliminate choices with spatial contradictions

Focus on BLOCK ADJACENCY and 3D STRUCTURE over individual colors.

Answer with brief reasoning, then final line: ONLY the number (1, 2, 3, or 4)."""

    image_paths = [problem_image_path] + rotated_image_paths
    print(f"Solving with {len(image_paths)} images...")
    response = send_to_claude(prompt, image_paths=image_paths, model_id="claude-sonnet-4-5", max_tokens=2048)
    return response


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Improved spatial reasoning solver (sequential)")
    parser.add_argument("--mode", choices=["single", "two-stage"], default="two-stage",
                        help="Reasoning mode: single-stage or two-stage")
    parser.add_argument("--start", type=int, default=1, help="Starting problem number")
    parser.add_argument("--end", type=int, default=29, help="Ending problem number")
    parser.add_argument("--output", default="output-advanced.txt", help="Output file")
    parser.add_argument("--skip-glb", action="store_true",
                        help="Skip GLB generation, use existing files (faster if you already ran generate_glb_files.py)")

    args = parser.parse_args()

    solve_func = solve_problem_two_stage if args.mode == "two-stage" else solve_problem_single_stage
    problem_numbers = list(range(args.start, args.end + 1))

    print(f"\n{'='*80}")
    print(f"Starting Improved Spatial Reasoning Solver")
    print(f"Mode: {args.mode}")
    print(f"Problems: {args.start} to {args.end} ({len(problem_numbers)} total)")
    print(f"Output: {args.output}")
    print(f"GLB Generation: {'Skipped (using existing)' if args.skip_glb else 'Enabled (via Meshy API)'}")
    print(f"Processing: Sequential (to avoid threading issues with PyRender)")
    print(f"{'='*80}\n")

    # Create output file with header
    with open(args.output, "w") as f:
        f.write(f"Spatial Reasoning Results - {args.mode} mode\n")
        f.write(f"Problems {args.start}-{args.end}\n")
        f.write(f"{'='*80}\n\n")

    success_count = 0

    for i in problem_numbers:
        print(f"\n{'='*60}")
        print(f"Solving problem {i}/{args.end} using {args.mode} mode...")
        print(f"{'='*60}")

        try:
            response = solve_func(
                f"./screenshots/rotations/{i}.png",
                f"./screenshots/cropped/{i}.png",
                problem_num=i,
                skip_glb_generation=args.skip_glb
            )

            with open(args.output, "a") as f:
                f.write(f"{i}: {response}\n")
                f.write(f"\n{'='*60}\n\n")

            print(f"Problem {i} ✓ Completed successfully")
            print(f"Response preview: {response[:200]}...")
            success_count += 1

        except Exception as e:
            error_msg = f"ERROR: {str(e)}"

            with open(args.output, "a") as f:
                f.write(f"{i}: {error_msg}\n")
                f.write(f"\n{'='*60}\n\n")

            print(f"Problem {i} ✗ Failed: {error_msg}")

    # Print summary
    print(f"\n{'='*80}")
    print(f"All problems completed!")
    print(f"Results written to: {args.output}")
    print(f"Successfully solved: {success_count}/{len(problem_numbers)}")
    print(f"{'='*80}\n")
