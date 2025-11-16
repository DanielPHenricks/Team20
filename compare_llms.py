import ast
from pathlib import Path
from typing import Dict, Any

import matplotlib.pyplot as plt


BASE_DIR = Path(__file__).resolve().parent

# Paths that match your screenshot structure
CLAUDE_RESULTS_PATH = BASE_DIR / "LLM responses" / "claude_rotation_responses.txt"
OPENAI_RESULTS_PATH = BASE_DIR / "LLM responses" / "openai_rotation_responses.txt"


def load_results(path: Path) -> Dict[str, Any]:
    """Load the dict-like results stored in a text file."""
    with path.open("r") as f:
        content = f.read().strip()

    # If the file doesn't have surrounding braces, add them
    if not content.startswith("{"):
        content = "{" + content + "}"

    # Safely parse the string into a Python dict
    data = ast.literal_eval(content)
    return data


def evaluate_results(data: Dict[str, Any], response_key: str) -> Dict[str, Any]:
    """
    Compute accuracy for a given model.
    response_key is something like 'claude_response' or 'openai_response'.
    """
    total = 0
    correct = 0

    for q_id, info in data.items():
        expected = str(info["expected_answer"])
        resp = str(info[response_key])

        total += 1
        if expected == resp:
            correct += 1

    accuracy = correct / total if total > 0 else 0.0
    return {
        "total": total,
        "correct": correct,
        "accuracy": accuracy,
    }


def visualize_accuracies(model_metrics: Dict[str, Dict[str, Any]], save_path: Path) -> None:
    """Create and save a bar chart comparing accuracies across models."""
    model_names = list(model_metrics.keys())
    accuracies = [m["accuracy"] * 100 for m in model_metrics.values()]

    plt.figure()
    plt.bar(model_names, accuracies)
    plt.ylabel("Accuracy (%)")
    plt.ylim(0, 100)
    plt.title("LLM Multiple-Choice Accuracy Comparison")

    # Add value labels on top of bars
    for i, acc in enumerate(accuracies):
        plt.text(i, acc + 1, f"{acc:.1f}%", ha="center")

    plt.tight_layout()
    plt.savefig(str(save_path), dpi=150)
    print(f"Saved plot to {save_path}")
    plt.show()


if __name__ == "__main__":
    # ----- Claude -----
    claude_data = load_results(CLAUDE_RESULTS_PATH)
    claude_metrics = evaluate_results(claude_data, response_key="claude_response")

    print("== claude ==")
    print(f"Total:   {claude_metrics['total']}")
    print(f"Correct: {claude_metrics['correct']}")
    print(f"Acc:     {claude_metrics['accuracy'] * 100:.2f}%")
    print()

    # ----- OpenAI -----
    openai_data = load_results(OPENAI_RESULTS_PATH)
    openai_metrics = evaluate_results(openai_data, response_key="claude_response")

    print("== openai ==")
    print(f"Total:   {openai_metrics['total']}")
    print(f"Correct: {openai_metrics['correct']}")
    print(f"Acc:     {openai_metrics['accuracy'] * 100:.2f}%")
    print()

    # Combine for plotting
    model_metrics = {
        "claude": claude_metrics,
        "openai": openai_metrics,
    }

    plot_path = BASE_DIR / "views_out" / "llm_accuracy.png"
    plot_path.parent.mkdir(parents=True, exist_ok=True)
    visualize_accuracies(model_metrics, save_path=plot_path)
