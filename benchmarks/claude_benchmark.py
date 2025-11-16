import os
import argparse
import base64
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


def send_to_claude(prompt: str, image_paths: Optional[List[str]] = None, model_id="claude-sonnet-4-5") -> str:
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



answer_key = "./rotations.txt"
output_file = "./claude_rotation_responses.txt"
image_dir = "./screenshots/rotations"

with open(answer_key, "r") as answers, open(output_file, "w") as output:
    output_obj = {}
    for line in answers:
    
        i = 0
        while i<5:
            iteration, answer = line.strip().split(": ")
            image_path = os.path.join(image_dir, f"{iteration}.png")

            response = send_to_claude(
                prompt=f"Solve this rotation puzzle and only provide the answer option (1, 2, 3 or 4), numbered from left to right. Only provide the answer option number without any additional text.",
                image_paths=[image_path],
            )
            output_obj[iteration] = {
                "expected_answer": answer,
                "claude_response": response,
            }
            print(f"Iteration {iteration} done. Response: {response}")
            if len(response.strip()) <= 3:
                break
            print("Response too long, retrying...")
            i += 1
    output.write(str(output_obj))

        

        
