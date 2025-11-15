import ast

def load_results(path: str) -> dict:
    with open(path, "r") as f:
        content = f.read().strip()

    # If the file doesn't have surrounding braces, add them
    if not content.startswith("{"):
        content = "{" + content + "}"

    # Safely parse the string into a Python dict
    data = ast.literal_eval(content)
    return data

def evaluate_results(data: dict) -> None:
    total = 0
    correct = 0

    # Sort by question number (keys are strings like '1', '2', ...)
    for q_id, info in sorted(data.items(), key=lambda kv: int(kv[0])):
        expected = str(info["expected_answer"])
        claude_resp = str(info["claude_response"])

        total += 1
        if expected == claude_resp:
            correct += 1
        else:
            print(f"Q{q_id}: expected {expected}, got {claude_resp}")

    print("\nSummary:")
    print(f"Total questions: {total}")
    print(f"Correct: {correct}")
    print(f"Accuracy: {correct / total * 100:.2f}%")

if __name__ == "__main__":
    # Change this to your actual file path
    path_to_txt = "claude_rotation_responses.txt"
    results = load_results(path_to_txt)
    evaluate_results(results)
