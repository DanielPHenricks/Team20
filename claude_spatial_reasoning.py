import requests
import time
import os
import argparse
import base64
from typing import List, Optional
from render import render_views

from anthropic import Anthropic
from dotenv import load_dotenv

import trimesh
import pyrender
import numpy as np
from PIL import Image

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


def send_to_claude(
    prompt: str, image_paths: Optional[List[str]] = None, model_id="claude-sonnet-4-5"
) -> str:
    """Send a prompt (optionally with embedded images) to Claude 3.5 Sonnet and return its reply.

    Requires the `ANTHROPIC_API_KEY` environment variable to be set.
    """

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

    # Claude 3.5 Sonnet model ID (snapshot from 2024-06-20)

    message = client.messages.create(
        model=model_id,
        max_tokens=1024,
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
        # Using data URI example
        # image_url: f'data:image/png;base64,{YOUR_BASE64_ENCODED_IMAGE_DATA}',
        "image_url": f"data:image/png;base64,{encode_image_base64(image_path)}",
        "enable_pbr": True,
        "should_remesh": True,
        "should_texture": False,
    }
    headers = {
        # TODO
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


def generate_rotated_images(path, outdir="renders", n=6):
    """
    Generate `n` rotated images of the 3D model at `path` and save them to `outdir`.
    """
    render_views(glb_path=path, out_dir=outdir, n_views=n, img_size=512)

    image_paths = []
    for i in range(n):
        img_path = os.path.join(outdir, f"view_{i:03d}.png")
        if os.path.exists(img_path):
            image_paths.append(img_path)

    print(f"Generated {len(image_paths)} rotated images.")
    return image_paths


def solve_problem(problem_image_path, cutout_image_path):

    # get the meshy model
    three_d_model_path = "./tmp/preview_model.glb"
    get_meshy_model(cutout_image_path, three_d_model_path)

    # generate the multiple rotations
    rotated_image_paths = generate_rotated_images(three_d_model_path)

    # send to claude with the rotated images
    prompt = "Solve this rotation puzzle and only provide the answer option (1, 2, 3 or 4), numbered from left to right. Only provide the answer option number without any additional text."
    image_paths = [problem_image_path] + rotated_image_paths
    response = send_to_claude(
        prompt, image_paths=image_paths, model_id="claude-sonnet-4-5"
    )
    return response


# solve_problem("./screenshots/rotations/1.png", "./screenshots/cropped/1.png")

if __name__ == "__main__":
    result = generate_rotated_images(
        "./tmp/preview_model.glb", outdir="./test_renders", n=8
    )
    print(f"Generated images: {result}")
    # modelResponse = solve_problem("./rotations", "./test_renders")
    # print(f"Model response: {modelResponse}")
