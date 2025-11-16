import os
import argparse
import base64
import time
from typing import List, Optional

from anthropic import Anthropic
from dotenv import load_dotenv


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


answer_key = "../rotations.txt"
output_file = "./claude_rotation_responses.txt"
image_dir = "./../screenshots/rotations"

with open(answer_key, "r") as f:
    answer_lines = [l.strip() for l in f.readlines() if l.strip()]

    for run_idx in range(1, 6):
        output_obj = {}
        for line in answer_lines:
            iteration, answer = line.split(": ")
            image_path = os.path.join(image_dir, f"{iteration}.png")

            retry = 0
            while retry < 5:
                response = send_to_claude(
                    prompt="Solve this rotation puzzle and only provide the answer option (1, 2, 3 or 4), numbered from left to right. Only provide the answer option number without any additional text.",
                    image_paths=[image_path],
                )
                output_obj[iteration] = {
                    "expected_answer": answer,
                    "claude_response": response,
                }
                print(
                    f"Run {run_idx} - Iteration {iteration} done. Response: {response}"
                )
                # Accept short numeric responses; otherwise retry up to 5 times
                if len(response.strip()) <= 3:
                    break
                print("Response too long, retrying...")
                retry += 1
        pid = os.getpid()
        ts = int(time.time() * 1000)
        out_path = f"./claude_rotation_responses_run{run_idx}_pid{pid}_ts{ts}.txt"
        with open(out_path, "w") as out_f:
            out_f.write(str(output_obj))
        print(f"Run {run_idx} written to {out_path}")
