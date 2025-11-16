import os
import argparse
import base64
from typing import List, Optional

from dotenv import load_dotenv
from openai import OpenAI


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

    # Attach images first (Openai vision best practice)


def send_to_openai(
    prompt: str, image_paths: Optional[List[str]] = None, model_id="gpt-5.1"
) -> str:
    """Send a prompt (optionally with embedded images) to OpenAI Vision-capable Responses API."""
    load_dotenv()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY not found. Make sure it is defined in your .env file."
        )

    client = OpenAI(api_key=api_key)

    # Build content blocks expected by the Responses API
    content_blocks = []
    if image_paths:
        for i, path in enumerate(image_paths, start=1):
            if not os.path.isfile(path):
                raise FileNotFoundError(f"Image not found: {path}")
            image_data = encode_image_base64(path)
            media_type = guess_media_type(path)
            # optional label
            content_blocks.append({"type": "input_text", "text": f"Image {i}:"})
            # embed image as a data URL
            content_blocks.append(
                {
                    "type": "input_image",
                    "image_url": f"data:{media_type};base64,{image_data}",
                }
            )

    # user prompt text
    content_blocks.append({"type": "input_text", "text": prompt})

    resp = client.responses.create(
        model=model_id,
        input=[{"role": "user", "content": content_blocks}],
        max_output_tokens=1024,
    )

    # Extract textual output: robust handling when SDK returns objects with attributes
    text_parts = []
    for out in getattr(resp, "output", []) or []:
        # get content list whether `out` is a dict or an object
        if isinstance(out, dict):
            content_list = out.get("content", []) or []
        else:
            content_list = getattr(out, "content", []) or []

        for c in content_list:
            if isinstance(c, dict):
                c_type = c.get("type")
                c_text = c.get("text")
            else:
                c_type = getattr(c, "type", None)
                c_text = getattr(c, "text", None)

            if c_type in ("output_text", "text") and c_text:
                text_parts.append(c_text)

    return "\n".join(text_parts).strip()


answer_key = "../rotations.txt"
output_file = "./openai_rotation_responses.txt"
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
                response = send_to_openai(
                    prompt="Solve this rotation puzzle and only provide the answer option (1, 2, 3 or 4), numbered from left to right. Only provide the answer option number without any additional text.",
                    image_paths=[image_path],
                )
                output_obj[iteration] = {
                    "expected_answer": answer,
                    "openai_response": response,
                }
                print(
                    f"Run {run_idx} - Iteration {iteration} done. Response: {response}"
                )
                # Accept short numeric responses; otherwise retry up to 5 times
                if len(response.strip()) <= 3:
                    break
                print("Response too long, retrying...")
            retry += 1

        out_path = f"./openai_rotation_responses_run{run_idx}.txt"
        with open(out_path, "w") as out_f:
            out_f.write(str(output_obj))
        print(f"Run {run_idx} written to {out_path}")
