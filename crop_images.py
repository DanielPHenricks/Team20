#!/usr/bin/env python3
"""
Crop center objects from Codycubes screenshots
Takes images from screenshots/rotations and crops to center object with whitespace
"""

import os
from PIL import Image
import glob

def crop_center_object(img):
    """
    Crop only the center object (below the question text, above the answer boxes)
    Keep only the middle third of the width
    """
    width, height = img.size

    # Vertical cropping: top ~15% is question, middle ~35% is center object, bottom ~50% is answers
    top_crop = int(height * 0.18)
    bottom_crop = int(height * 0.50)

    # Horizontal cropping: keep only the middle third of the width
    left_crop = int(width / 2.66)
    right_crop = int(width * 2 / 3.33)

    # Crop the original image to just the center object
    cropped = img.crop((left_crop, top_crop, right_crop, bottom_crop))

    return cropped

def main():
    input_dir = "screenshots/rotations"
    output_dir = "screenshots/cropped"

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Get all PNG files from input directory
    image_files = sorted(glob.glob(f"{input_dir}/*.png"),
                        key=lambda x: int(os.path.splitext(os.path.basename(x))[0]))

    if not image_files:
        print(f"No images found in {input_dir}")
        return

    print(f"Found {len(image_files)} images to process")

    # Process each image
    for i, image_path in enumerate(image_files, 1):
        filename = os.path.basename(image_path)
        output_path = os.path.join(output_dir, filename)

        try:
            # Open image
            img = Image.open(image_path)

            # Crop to center object only
            cropped = crop_center_object(img)

            # Save cropped image
            cropped.save(output_path)

            print(f"[{i}/{len(image_files)}] Processed {filename} - "
                  f"Original: {img.size}, Cropped: {cropped.size}")

        except Exception as e:
            print(f"Error processing {filename}: {e}")

    print(f"\n=== Complete ===")
    print(f"Cropped images saved to {output_dir}/")

if __name__ == "__main__":
    main()
