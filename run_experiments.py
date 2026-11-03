# run_experiments.py
"""Reproduce the three Gaussian Thompson sampling experiments from the assignment.

    uv run python run_experiments.py

Same prior Normal(0, 25) and the same seed (42) for every experiment. A
robustness check over many seeds is printed afterwards so the discussion in the
README does not rest on a single random draw.
"""

import numpy as np

from gaussian_bandit import run_gaussian_thompson


SEED = 42
TRUE_MEANS = [1, 2, 3]
EXPERIMENTS = [
    ("Short run", 1.0, 100),
    ("Longer run", 1.0, 1000),
    ("Higher noise", 3.0, 1000),
]
ROBUSTNESS_SEEDS = range(200)


def single_run_tables() -> None:
    print(f"## Single runs (seed {SEED}, true means {TRUE_MEANS}, prior Normal(0, 25))\n")
    for name, sigma, rounds in EXPERIMENTS:
        r = run_gaussian_thompson(TRUE_MEANS, sigma, rounds, SEED)
        print(f"### {name}: sigma = {sigma:g}, rounds = {rounds:,}\n")
        print("| Alternative | True mean | Posterior mean | Posterior std | Selections | Share |")
        print("|---|---|---|---|---|---|")
        for i in range(3):
            print(
                f"| {i + 1} | {r.true_means[i]:g} | {r.posterior_means[i]:.3f} | "
                f"{r.posterior_stds[i]:.3f} | {r.selection_counts[i]} | "
                f"{100 * r.selection_counts[i] / rounds:.1f}% |"
            )
        print(
            f"\nTotal observed reward: {r.total_reward:.2f} | "
            f"Final recommendation: Alternative {r.recommendation + 1} | "
            f"Cumulative regret: {r.cumulative_regret[-1]:.1f} | "
            f"Counts sum: {int(r.selection_counts.sum())}\n"
        )


def reproducibility_check() -> None:
    print("## Reproducibility\n")
    for name, sigma, rounds in EXPERIMENTS:
        a = run_gaussian_thompson(TRUE_MEANS, sigma, rounds, SEED)
        b = run_gaussian_thompson(TRUE_MEANS, sigma, rounds, SEED)
        same = (
            np.array_equal(a.choices, b.choices)
            and np.array_equal(a.rewards, b.rewards)
            and np.array_equal(a.posterior_means, b.posterior_means)
        )
        print(f"- {name}: identical on rerun = {same}; counts sum = {int(a.selection_counts.sum())} (rounds = {rounds})")
    print()


def robustness_table() -> None:
    print(f"## Robustness over {len(ROBUSTNESS_SEEDS)} seeds (0..{ROBUSTNESS_SEEDS[-1]})\n")
    print(
        "| Experiment | Recommends Alt 3 | Mean share of Alt 3 | Mean share of Alt 1 | "
        "Mean posterior mean (1 / 2 / 3) | Mean cumulative regret |"
    )
    print("|---|---|---|---|---|---|")
    for name, sigma, rounds in EXPERIMENTS:
        runs = [run_gaussian_thompson(TRUE_MEANS, sigma, rounds, s) for s in ROBUSTNESS_SEEDS]
        correct = np.mean([r.recommendation == 2 for r in runs])
        share = np.mean([r.selection_counts / rounds for r in runs], axis=0)
        post = np.mean([r.posterior_means for r in runs], axis=0)
        regret = np.mean([r.cumulative_regret[-1] for r in runs])
        print(
            f"| {name} (sigma={sigma:g}, n={rounds:,}) | {100 * correct:.1f}% | "
            f"{100 * share[2]:.1f}% | {100 * share[0]:.1f}% | "
            f"{post[0]:.2f} / {post[1]:.2f} / {post[2]:.2f} | {regret:.1f} |"
        )
    print()


if __name__ == "__main__":
    single_run_tables()
    reproducibility_check()
    robustness_table()
