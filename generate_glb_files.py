#!/usr/bin/env python3
"""
Standalone script to generate GLB files from 2D images using Meshy API.
This separates the 3D model generation from the Claude reasoning step.
"""

import requests
import time
import os
import argparse
import base64
from dotenv import load_dotenv

# Load .env file
load_dotenv()


def encode_image_base64(path: str) -> str:
    """Read an image from disk and return base64-encoded string."""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def get_meshy_model(image_path: str, output_file_path: str):
    """
    Convert a 2D image to a 3D GLB model using Meshy API.

    :param image_path: Path to the input 2D image
    :param output_file_path: Path where the GLB file will be saved
    """
    print(f"Processing: {image_path} -> {output_file_path}")

    payload = {
        "image_url": f"data:image/png;base64,{encode_image_base64(image_path)}",
        "should_remesh": True,
        "should_texture": True,
        "enable_pbr": True,
    }
    headers = {
        "Authorization": f"Bearer {os.getenv('MESHY_API_KEY')}",
    }

    # Submit the image-to-3D request
    print("  Submitting to Meshy API...")
    response = requests.post(
        "https://api.meshy.ai/openapi/v1/image-to-3d",
        headers=headers,
        json=payload,
    )

    response.raise_for_status()

    response_task_id = response.json()["result"]
    print(f"  Task ID: {response_task_id}")

    # Poll for completion
    preview_task = None

    while True:
        preview_task_response = requests.get(
            f"https://api.meshy.ai/openapi/v1/image-to-3d/{response_task_id}",
            headers=headers,
        )

        preview_task_response.raise_for_status()

        preview_task = preview_task_response.json()

        if preview_task["status"] == "SUCCEEDED":
            print("  ✓ Preview task finished.")
            break

        print(
            f"  Status: {preview_task['status']} | "
            f"Progress: {preview_task['progress']}% | "
            f"Waiting 5 seconds..."
        )
        time.sleep(5)

    # Download the resulting 3D model
    preview_model_url = preview_task["model_urls"]["glb"]
    print(f"  Downloading from: {preview_model_url[:60]}...")

    preview_model_response = requests.get(preview_model_url)
    preview_model_response.raise_for_status()

    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

    with open(output_file_path, "wb") as f:
        f.write(preview_model_response.content)

    file_size = len(preview_model_response.content) / 1024  # KB
    print(f"  ✓ Saved: {output_file_path} ({file_size:.1f} KB)")


def generate_glb_for_problems(start: int, end: int, input_dir: str = "./screenshots/cropped", output_dir: str = "./tmp"):
    """
    Generate GLB files for a range of problems.

    :param start: Starting problem number
    :param end: Ending problem number
    :param input_dir: Directory containing input images (named 1.png, 2.png, etc.)
    :param output_dir: Directory where GLB files will be saved
    """
    os.makedirs(output_dir, exist_ok=True)

    total = end - start + 1
    success_count = 0
    failed_problems = []

    print(f"\n{'='*80}")
    print(f"Generating GLB files for problems {start}-{end}")
    print(f"Input directory: {input_dir}")
    print(f"Output directory: {output_dir}")
    print(f"Total problems: {total}")
    print(f"{'='*80}\n")

    for i in range(start, end + 1):
        print(f"\n[{i-start+1}/{total}] Problem {i}")
        print("-" * 60)

        input_image = os.path.join(input_dir, f"{i}.png")
        output_glb = os.path.join(output_dir, f"preview_model_problem_{i}.glb")

        # Check if input exists
        if not os.path.exists(input_image):
            print(f"  ✗ Error: Input image not found: {input_image}")
            failed_problems.append((i, "Input file not found"))
            continue

        # Skip if GLB already exists
        if os.path.exists(output_glb):
            file_size = os.path.getsize(output_glb) / 1024  # KB
            print(f"  ⊙ Already exists: {output_glb} ({file_size:.1f} KB)")
            print(f"  Skipping (delete file to regenerate)")
            success_count += 1
            continue

        # Generate GLB
        try:
            get_meshy_model(input_image, output_glb)
            success_count += 1
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP {e.response.status_code}: {e.response.reason}"
            print(f"  ✗ Error: {error_msg}")
            failed_problems.append((i, error_msg))
        except Exception as e:
            error_msg = str(e)
            print(f"  ✗ Error: {error_msg}")
            failed_problems.append((i, error_msg))

    # Print summary
    print(f"\n{'='*80}")
    print(f"Generation Complete!")
    print(f"{'='*80}")
    print(f"Successful: {success_count}/{total}")
    print(f"Failed: {len(failed_problems)}/{total}")

    if failed_problems:
        print(f"\nFailed problems:")
        for problem_num, error in failed_problems:
            print(f"  Problem {problem_num}: {error}")

    print(f"\nGLB files saved to: {output_dir}/")
    print(f"{'='*80}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Generate GLB files from 2D images using Meshy API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate GLB files for all 29 problems
  python3 generate_glb_files.py

  # Generate for specific range
  python3 generate_glb_files.py --start 1 --end 10

  # Custom input/output directories
  python3 generate_glb_files.py --input ./my_images --output ./my_models

  # Generate single problem
  python3 generate_glb_files.py --start 5 --end 5

Note: Requires MESHY_API_KEY in .env file
        """
    )

    parser.add_argument(
        "--start",
        type=int,
        default=1,
        help="Starting problem number (default: 1)"
    )
    parser.add_argument(
        "--end",
        type=int,
        default=29,
        help="Ending problem number (default: 29)"
    )
    parser.add_argument(
        "--input",
        default="./screenshots/cropped",
        help="Input directory containing images (default: ./screenshots/cropped)"
    )
    parser.add_argument(
        "--output",
        default="./tmp",
        help="Output directory for GLB files (default: ./tmp)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate even if GLB files already exist"
    )

    args = parser.parse_args()

    # Check for API key
    if not os.getenv("MESHY_API_KEY"):
        print("ERROR: MESHY_API_KEY not found in environment")
        print("Please add it to your .env file:")
        print("  MESHY_API_KEY=your_api_key_here")
        return 1

    # Delete existing files if --force is used
    if args.force:
        print("\n--force flag detected: Deleting existing GLB files...")
        for i in range(args.start, args.end + 1):
            glb_path = os.path.join(args.output, f"preview_model_problem_{i}.glb")
            if os.path.exists(glb_path):
                os.remove(glb_path)
                print(f"  Deleted: {glb_path}")

    # Generate GLB files
    generate_glb_for_problems(args.start, args.end, args.input, args.output)

    return 0


if __name__ == "__main__":
    exit(main())
