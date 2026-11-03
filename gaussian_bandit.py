# gaussian_bandit.py
"""Gaussian Thompson sampling for continuous rewards with known noise.

Model:   R | A = i  ~  Normal(mu_i, sigma^2)      sigma known and shared
Prior:   mu_i       ~  Normal(0, 25)              independent for every arm

Each arm's posterior stays Normal, so it is tracked with two numbers:
    precision     lambda_i = 1/25 + n_i / sigma^2
    weighted sum  b_i      = 0/25  + (sum of rewards of arm i) / sigma^2
giving posterior mean b_i / lambda_i and posterior variance 1 / lambda_i.

This module has no Streamlit imports so it can be tested on its own.
"""

from dataclasses import dataclass
from typing import Sequence

import numpy as np
import pandas as pd


PRIOR_MEAN = 0.0
PRIOR_VARIANCE = 25.0


@dataclass(frozen=True, eq=False)
class GaussianBanditResult:
    true_means: np.ndarray
    sigma: float
    rounds: int
    seed: int
    choices: np.ndarray  # arm index selected in every round, shape (rounds,)
    rewards: np.ndarray  # reward observed in every round, shape (rounds,)
    posterior_means: np.ndarray
    posterior_stds: np.ndarray
    selection_counts: np.ndarray

    @property
    def total_reward(self) -> float:
        return float(self.rewards.sum())

    @property
    def recommendation(self) -> int:
        """Arm with the largest posterior mean (ties go to the lowest index)."""
        return int(np.argmax(self.posterior_means))

    @property
    def cumulative_regret(self) -> np.ndarray:
        gaps = self.true_means.max() - self.true_means[self.choices]
        return np.cumsum(gaps)


def alternative_labels(count: int) -> list:
    return [f"Alternative {i}" for i in range(1, count + 1)]


def _is_integer(value) -> bool:
    if isinstance(value, bool):
        return False
    try:
        return int(value) == value
    except (TypeError, ValueError, OverflowError):
        return False


def validate_inputs(true_means: Sequence[float], sigma: float, rounds, seed) -> list:
    """Return a list of human-readable problems; empty means the inputs are valid."""
    errors = []

    try:
        means_ok = len(true_means) >= 2 and bool(np.all(np.isfinite(np.asarray(true_means, dtype=float))))
    except (TypeError, ValueError):
        means_ok = False
    if not means_ok:
        errors.append("True means must be finite numbers (at least two alternatives).")

    try:
        sigma_ok = bool(np.isfinite(sigma)) and float(sigma) > 0
    except (TypeError, ValueError):
        sigma_ok = False
    if not sigma_ok:
        errors.append("Known σ must be a positive number.")

    if not _is_integer(rounds) or int(rounds) < 1:
        errors.append("Number of rounds must be a positive integer.")

    if not _is_integer(seed) or int(seed) < 0:
        errors.append("Random seed must be a non-negative integer.")

    return errors


def run_gaussian_thompson(
    true_means: Sequence[float],
    sigma: float,
    rounds: int,
    seed: int,
    prior_mean: float = PRIOR_MEAN,
    prior_variance: float = PRIOR_VARIANCE,
) -> GaussianBanditResult:
    errors = validate_inputs(true_means, sigma, rounds, seed)
    if prior_variance <= 0:
        errors.append("Prior variance must be positive.")
    if errors:
        raise ValueError(" ".join(errors))

    true_means = np.asarray(true_means, dtype=float)
    sigma = float(sigma)
    rounds = int(rounds)
    n_arms = len(true_means)

    # One generator drives both posterior sampling and reward noise, so a
    # (config, seed) pair always reproduces the same run.
    rng = np.random.default_rng(int(seed))
    noise_precision = 1.0 / sigma**2

    precision = np.full(n_arms, 1.0 / prior_variance)
    weighted_sum = np.full(n_arms, prior_mean / prior_variance)

    choices = np.empty(rounds, dtype=int)
    rewards = np.empty(rounds, dtype=float)

    for t in range(rounds):
        # 1. sample a possible mean from each arm's current posterior
        sampled_means = rng.normal(weighted_sum / precision, 1.0 / np.sqrt(precision))
        # 2. select the largest
        arm = int(np.argmax(sampled_means))
        # 3. generate one Gaussian reward from the true (hidden) mean
        reward = rng.normal(true_means[arm], sigma)
        # 4. update only the selected arm, using the reward and known sigma
        precision[arm] += noise_precision
        weighted_sum[arm] += reward * noise_precision

        choices[t] = arm
        rewards[t] = reward

    return GaussianBanditResult(
        true_means=true_means,
        sigma=sigma,
        rounds=rounds,
        seed=int(seed),
        choices=choices,
        rewards=rewards,
        posterior_means=weighted_sum / precision,
        posterior_stds=1.0 / np.sqrt(precision),
        selection_counts=np.bincount(choices, minlength=n_arms),
    )


def summary_df(result: GaussianBanditResult) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Alternative": alternative_labels(len(result.true_means)),
            "True mean": result.true_means,
            "Posterior mean": result.posterior_means,
            "Selections": result.selection_counts,
        }
    )
