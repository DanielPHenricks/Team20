import ast
from pathlib import Path
from typing import Dict, Any, List

import numpy as np
from scipy.stats import ttest_ind  # pip install scipy


BASE_DIR = Path(__file__).resolve().parent

# Directories for Claude and OpenAI runs
CLAUDE_RESULTS_DIR = BASE_DIR / "LLM responses" / "claude"
OPENAI_RESULTS_DIR = BASE_DIR / "LLM responses" / "openai"

# Keys used inside dictionaries (adjust if needed)
CLAUDE_RESPONSE_KEY = "claude_response"
OPENAI_RESPONSE_KEY = "openai_response"   # <- change this if different


#####################################################################
# Your manual improved method result:
#             20 correct out of 40
# => accuracy = 20 / 40 = 0.50
#####################################################################

OURS_ACCURACY = 20 / 40   # = 0.50

# OPTION A: treat your method as ONE run
OURS_ACCS = [OURS_ACCURACY]

# OPTION B (recommended): treat your method as many identical runs
# e.g., match Claude's number of runs for fair variance comparison:
# (Uncomment this instead)
# OURS_ACCS = [OURS_ACCURACY] * 6
#####################################################################


def load_results(path: Path) -> Dict[str, Any]:
    """Load dict-like results stored in a .txt file."""
    with path.open("r") as f:
        content = f.read().strip()

    if not content.startswith("{"):
        content = "{" + content + "}"

    return ast.literal_eval(content)


def load_all_results_from_dir(dir_path: Path) -> List[Dict[str, Any]]:
    """Load all .txt result files from a directory."""
    txt_files = sorted(dir_path.glob("*.txt"))
    if not txt_files:
        raise FileNotFoundError(f"No .txt files found in {dir_path}")

    data = [load_results(p) for p in txt_files]
    print(f"Loaded {len(data)} runs from {dir_path}")
    return data


def evaluate_results(data: Dict[str, Any], response_key: str) -> float:
    """Compute accuracy for one run (0–1)."""
    total = 0
    correct = 0

    for _, info in data.items():
        expected = str(info["expected_answer"])
        resp = str(info[response_key])
        total += 1
        correct += (expected == resp)

    return correct / total


def evaluate_multiple_runs(all_data: List[Dict[str, Any]], response_key: str) -> List[float]:
    """Return list of per-run accuracies."""
    return [evaluate_results(d, response_key) for d in all_data]


def describe(name: str, accs: List[float]) -> None:
    """Pretty-print group statistics."""
    accs_pct = np.array(accs) * 100
    print(f"== {name} ==")
    print(f"  runs: {len(accs)}")
    print(f"  mean: {accs_pct.mean():.2f}%")
    print(f"  std:  {accs_pct.std(ddof=1) if len(accs)>1 else 0:.2f}%")
    print()


def run_ttest(name_a: str, accs_a: List[float], name_b: str, accs_b: List[float]) -> None:
    """Runs Welch’s t-test between two accuracy samples."""
    t, p = ttest_ind(accs_a, accs_b, equal_var=False)

    print(f"{name_a} vs {name_b}")
    print(f"  mean {name_a}: {np.mean(accs_a)*100:.2f}%")
    print(f"  mean {name_b}: {np.mean(accs_b)*100:.2f}%")
    print(f"  t-statistic: {t:.4f}")
    print(f"  p-value:     {p:.6f}")

    if p < 0.05:
        print("  => Statistically significant difference (p < 0.05)")
    else:
        print("  => NOT statistically significant (p >= 0.05)")
    print()


if __name__ == "__main__":
    # Load Claude + OpenAI accuracies from files
    claude_runs = load_all_results_from_dir(CLAUDE_RESULTS_DIR)
    openai_runs = load_all_results_from_dir(OPENAI_RESULTS_DIR)

    claude_accs = evaluate_multiple_runs(claude_runs, CLAUDE_RESPONSE_KEY)
    openai_accs = evaluate_multiple_runs(openai_runs, OPENAI_RESPONSE_KEY)

    print("\n--- Descriptive Statistics ---\n")
    describe("Claude", claude_accs)
    describe("OpenAI", openai_accs)
    describe("Ours (manual)", OURS_ACCS)

    print("\n--- Significance Tests (Welch t-test) ---\n")
    run_ttest("Team 20 Model", OURS_ACCS, "Claude", claude_accs)
    run_ttest("Team 20 Model", OURS_ACCS, "OpenAI", openai_accs)
