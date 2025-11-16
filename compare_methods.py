import ast
from pathlib import Path
from typing import Dict, Any, List

import matplotlib.pyplot as plt
import numpy as np  


BASE_DIR = Path(__file__).resolve().parent

# Directories containing multiple runs (txt files) for each method
CLAUDE_RESULTS_DIR = BASE_DIR / "LLM responses" / "claude"
OPENAI_RESULTS_DIR = BASE_DIR / "LLM responses" / "openai"
CLAUDE_IMPROVED_RESULTS_DIR   = BASE_DIR / "LLM responses" / "claude_improved" 


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


def load_all_results_from_dir(dir_path: Path) -> List[Dict[str, Any]]:
    """
    Load all .txt result files from a directory.
    Returns a list of parsed dicts (one per run).
    """
    txt_files = sorted(dir_path.glob("*.txt"))
    if not txt_files:
        raise FileNotFoundError(f"No .txt result files found in {dir_path}")

    all_data = [load_results(p) for p in txt_files]
    print(f"Loaded {len(all_data)} runs from {dir_path}")
    return all_data


def evaluate_results(data: Dict[str, Any], response_key: str) -> Dict[str, Any]:
    """
    Compute accuracy for a given model on one run.
    response_key is something like 'claude_response' (for now).
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


def evaluate_multiple_runs(all_data: List[Dict[str, Any]], response_key: str) -> Dict[str, Any]:
    """
    Evaluate multiple runs for one model.
    Returns per-run metrics and average accuracy.
    """
    per_run_metrics = [evaluate_results(d, response_key=response_key) for d in all_data]

    # Simple average of accuracies across runs
    avg_accuracy = (
        sum(m["accuracy"] for m in per_run_metrics) / len(per_run_metrics)
        if per_run_metrics else 0.0
    )

    # Aggregated totals across runs
    total_questions = sum(m["total"] for m in per_run_metrics)
    total_correct = sum(m["correct"] for m in per_run_metrics)
    overall_accuracy = total_correct / total_questions if total_questions > 0 else 0.0

    return {
        "per_run": per_run_metrics,
        "avg_accuracy": avg_accuracy,
        "overall_total": total_questions,
        "overall_correct": total_correct,
        "overall_accuracy": overall_accuracy,
    }


def visualize_runs_for_model(model_name: str,
                             per_run_metrics: List[Dict[str, Any]],
                             avg_accuracy: float,
                             save_path: Path) -> None:
    """
    Create and save a bar chart showing per-run accuracies for a single model,
    plus a horizontal line for the average accuracy.
    """
    run_indices = list(range(1, len(per_run_metrics) + 1))
    accuracies = [m["accuracy"] * 100 for m in per_run_metrics]

    plt.figure()
    plt.bar(run_indices, accuracies)
    plt.ylabel("Accuracy (%)")
    plt.ylim(0, 100)
    plt.xlabel("Run #")
    plt.title(f"{model_name} Accuracy Across Runs")

    # Add value labels on top of bars
    for i, acc in enumerate(accuracies):
        plt.text(run_indices[i], acc + 1, f"{acc:.1f}%", ha="center")

    # Average accuracy line
    avg_acc_pct = avg_accuracy * 100
    plt.axhline(avg_acc_pct, linestyle="--")
    plt.text(
        0.95,
        avg_acc_pct + 1,
        f"Avg: {avg_acc_pct:.1f}%",
        ha="right",
        va="bottom",
        transform=plt.gca().get_yaxis_transform()
    )

    plt.tight_layout()
    save_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(str(save_path), dpi=150)
    print(f"Saved per-run plot for {model_name} to {save_path}")
    plt.close()


def visualize_average_accuracies(model_avg_metrics: Dict[str, float], save_path: Path) -> None:
    """
    Create and save a bar chart comparing average accuracies across models.
    """
    model_names = list(model_avg_metrics.keys())
    accuracies = [acc * 100 for acc in model_avg_metrics.values()]

    plt.figure()
    plt.bar(model_names, accuracies)
    plt.ylabel("Average Accuracy (%)")
    plt.ylim(0, 100)
    plt.title("Average Multiple-Choice Accuracy Comparison (Across Runs)")

    # Add value labels on top of bars
    for i, acc in enumerate(accuracies):
        plt.text(i, acc + 1, f"{acc:.1f}%", ha="center")

    plt.tight_layout()
    save_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(str(save_path), dpi=150)
    print(f"Saved average comparison plot to {save_path}")
    plt.close()


def visualize_accuracy_boxplot(model_run_metrics: Dict[str, List[Dict[str, Any]]],
                               save_path: Path) -> None:
    """
    Create and save a box-and-whisker plot showing the distribution of
    per-run accuracies for each model, with individual runs overlaid as dots.
    model_run_metrics: { model_name: [ { 'accuracy': float, ... }, ... ], ... }
    """
    model_names = list(model_run_metrics.keys())
    # Convert accuracies to percentages
    data = [
        [run["accuracy"] * 100 for run in model_run_metrics[model]]
        for model in model_names
    ]

    plt.figure()
    plt.boxplot(data, labels=model_names)
    plt.ylabel("Accuracy (%)")
    plt.ylim(0, 100)
    plt.title("Accuracy Distribution Across Runs")

    # Overlay individual run accuracies as jittered points
    for i, accuracies in enumerate(data, start=1):
        x = np.random.normal(loc=i, scale=0.04, size=len(accuracies))
        plt.scatter(x, accuracies, alpha=0.7)

    plt.tight_layout()
    save_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(str(save_path), dpi=150)
    print(f"Saved boxplot to {save_path}")
    plt.close()


if __name__ == "__main__":
    # ----- Claude (multiple runs) -----
    claude_all_data = load_all_results_from_dir(CLAUDE_RESULTS_DIR)
    claude_multi = evaluate_multiple_runs(claude_all_data, response_key="claude_response")

    print("== claude ==")
    for i, run in enumerate(claude_multi["per_run"], start=1):
        print(f"Run {i}: {run['correct']}/{run['total']} "
              f"({run['accuracy'] * 100:.2f}%)")
    print(f"Avg accuracy: {claude_multi['avg_accuracy'] * 100:.2f}%")
    print(f"Overall (aggregated) accuracy: {claude_multi['overall_accuracy'] * 100:.2f}%")
    print()

    # ----- OpenAI (multiple runs) -----
    openai_all_data = load_all_results_from_dir(OPENAI_RESULTS_DIR)
    # If/when you have a separate key like "openai_response", change this:
    openai_multi = evaluate_multiple_runs(openai_all_data, response_key="claude_response")

    print("== openai ==")
    for i, run in enumerate(openai_multi["per_run"], start=1):
        print(f"Run {i}: {run['correct']}/{run['total']} "
              f"({run['accuracy'] * 100:.2f}%)")
    print(f"Avg accuracy: {openai_multi['avg_accuracy'] * 100:.2f}%")
    print(f"Overall (aggregated) accuracy: {openai_multi['overall_accuracy'] * 100:.2f}%")
    print()

    # ----- Our method (multiple runs) -----
    claude_improved_all_data = load_all_results_from_dir(CLAUDE_IMPROVED_RESULTS_DIR)
    # Adjust response_key if your method uses a different field name
    claude_improved_multi = evaluate_multiple_runs(claude_improved_all_data, response_key="claude_response")

    print("== ours ==")
    for i, run in enumerate(claude_improved_multi["per_run"], start=1):
        print(f"Run {i}: {run['correct']}/{run['total']} "
              f"({run['accuracy'] * 100:.2f}%)")
    print(f"Avg accuracy: {claude_improved_multi['avg_accuracy'] * 100:.2f}%")
    print(f"Overall (aggregated) accuracy: {claude_improved_multi['overall_accuracy'] * 100:.2f}%")
    print()

    views_dir = BASE_DIR / "views_out"

    # ---- Per-method bar graph (one for each) ----
    claude_plot_path = views_dir / "claude_accuracy_runs.png"
    visualize_runs_for_model(
        model_name="claude",
        per_run_metrics=claude_multi["per_run"],
        avg_accuracy=claude_multi["avg_accuracy"],
        save_path=claude_plot_path,
    )

    openai_plot_path = views_dir / "openai_accuracy_runs.png"
    visualize_runs_for_model(
        model_name="openai",
        per_run_metrics=openai_multi["per_run"],
        avg_accuracy=openai_multi["avg_accuracy"],
        save_path=openai_plot_path,
    )

    ours_plot_path = views_dir / "ours_accuracy_runs.png"
    visualize_runs_for_model(
        model_name="ours",
        per_run_metrics=claude_improved_multi["per_run"],
        avg_accuracy=claude_improved_multi["avg_accuracy"],
        save_path=ours_plot_path,
    )

    # ---- Combined bar chart of average accuracies across methods ----
    model_avg_metrics = {
        "claude": claude_multi["avg_accuracy"],
        "openai": openai_multi["avg_accuracy"],
        "ours": claude_improved_multi["avg_accuracy"],
    }
    avg_plot_path = views_dir / "average_accuracy.png"
    visualize_average_accuracies(model_avg_metrics, save_path=avg_plot_path)

    # ---- Box-and-whisker plot of distributions across runs ----
    model_run_metrics = {
        "claude": claude_multi["per_run"],
        "openai": openai_multi["per_run"],
        "ours": claude_improved_multi["per_run"],
    }
    boxplot_path = views_dir / "accuracy_boxplot.png"
    visualize_accuracy_boxplot(model_run_metrics, save_path=boxplot_path)
