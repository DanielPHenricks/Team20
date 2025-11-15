#!/usr/bin/env python3
"""
Codycubes automated solver
Takes screenshots and finds correct answers by clicking through options
"""

import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from PIL import Image
import io

def setup_driver():
    """Initialize Chrome driver with appropriate options"""
    options = webdriver.ChromeOptions()
    options.add_argument('--start-maximized')
    # Uncomment to run headless:
    # options.add_argument('--headless')
    driver = webdriver.Chrome(options=options)
    return driver

def take_bottom_80_percent_screenshot(driver, output_path):
    """Take a screenshot of the bottom 80% of the viewport"""
    # Get full page screenshot
    screenshot = driver.get_screenshot_as_png()

    # Open with PIL
    img = Image.open(io.BytesIO(screenshot))
    width, height = img.size

    # Crop to bottom 80%
    top = int(height * 0.2)
    cropped = img.crop((0, top, width, height))

    # Save
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    cropped.save(output_path)
    print(f"Screenshot saved to {output_path}")

def click_answer_and_check(driver, answer_num):
    """
    Click an answer container and check if it's correct
    Returns True if correct, False otherwise
    """
    container_id = f"answer{answer_num}_container"

    try:
        # Find and click the answer container
        container = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, container_id))
        )

        # Click the container
        ActionChains(driver).move_to_element(container).click().perform()
        time.sleep(1)  # Wait for animation/response

        # Check if "NEXT PUZZLE" button appears (indicates correct answer)
        try:
            next_button = driver.find_element(By.ID, "next_puzzle_button")
            is_visible = next_button.is_displayed()
            return is_visible
        except:
            return False

    except Exception as e:
        print(f"Error clicking answer {answer_num}: {e}")
        return False

def find_correct_answer(driver):
    """
    Try each answer until finding the correct one
    Returns the answer number (1-4) or None if none found
    """
    for answer_num in range(1, 5):
        print(f"Trying answer {answer_num}...")
        if click_answer_and_check(driver, answer_num):
            print(f"Answer {answer_num} is correct!")
            return answer_num
        time.sleep(0.5)

    return None

def click_next_puzzle(driver):
    """Click the next puzzle button using JavaScript to avoid interception"""
    try:
        next_button = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "next_puzzle_button"))
        )
        # Use JavaScript click to avoid element interception issues
        driver.execute_script("arguments[0].click();", next_button)
        time.sleep(2)  # Wait for next puzzle to load
        return True
    except Exception as e:
        print(f"Error clicking next puzzle: {e}")
        return False

def main():
    url = "https://codycubes.geody.games/play"
    num_iterations = 100  # Number of puzzles to solve
    start_iteration = 3
    screenshot_dir = "screenshots/easy"
    answers_file = "answers.txt"

    # Setup
    os.makedirs(screenshot_dir, exist_ok=True)
    driver = setup_driver()

    try:
        # Navigate to page
        print(f"Loading {url}...")
        driver.get(url)

        # Wait for page to load
        time.sleep(3)

        # Open answers file
        with open(answers_file, 'a') as f:
            for i in range(start_iteration, num_iterations + start_iteration):
                print(f"\n=== Iteration {i+1}/{num_iterations} ===")

                # Take screenshot
                screenshot_path = f"{screenshot_dir}/{i+1}.png"
                take_bottom_80_percent_screenshot(driver, screenshot_path)

                # Find correct answer
                correct_answer = find_correct_answer(driver)

                if correct_answer:
                    # Log the answer
                    f.write(f"{correct_answer}\n")
                    f.flush()
                    print(f"Logged answer: {correct_answer}")

                    # Wait a moment before clicking next
                    time.sleep(1)

                    # Click next puzzle
                    if not click_next_puzzle(driver):
                        print("Could not proceed to next puzzle")
                        break
                else:
                    print("Could not find correct answer!")
                    f.write("ERROR\n")
                    f.flush()
                    break

                time.sleep(1)  # Brief pause between iterations

        print("\n=== Complete ===")
        print(f"Screenshots saved to {screenshot_dir}/")
        print(f"Answers logged to {answers_file}")

    finally:
        # Cleanup
        time.sleep(2)
        driver.quit()

if __name__ == "__main__":
    main()
