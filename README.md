# Gaussian Bandit: Thompson Sampling for Continuous Rewards

**DS223 Marketing Analytics** — Gaussian Bandit Assignment

**Team:** Sereen Sipan, Hayk Daghunts, Margarita Hambaryan, Stepan Titanyan, Robert Sarinyan

This project extends the Streamlit carousel frontend with **Thompson sampling for continuous
Gaussian rewards with known noise standard deviation**. The original application learns from
click / no-click feedback with Beta posteriors; the new **Gaussian Bandit** page learns the mean
reward of three alternatives from real-valued rewards with Normal posteriors.

## Credit

The frontend is based on the starting repository
[hovhannisyan91/DS223_Group_Project](https://github.com/hovhannisyan91/DS223_Group_Project)
(the contents of `app/front/`). The starting application is deployed at
<https://carousel-mvp.streamlit.app/>. The original pages (Create Carousels, Interaction,
Analytics) and `bandit_utils.py` are unchanged except for one line in `init_state` and one entry in
`main.py`; everything Gaussian is new.

## Links

| | |
|---|---|
| GitHub repository | <https://github.com/StepanTitanyan/Carousel_Group_Work_1> |
| Deployed Streamlit app | **TODO: add the Streamlit Community Cloud URL after deployment** |
| Starting repository | <https://github.com/hovhannisyan91/DS223_Group_Project> |
| Starting application | <https://carousel-mvp.streamlit.app/> |

## Setup

Requires Python 3.12 and [uv](https://docs.astral.sh/uv/). From the project root:

```bash
uv sync --locked
uv run streamlit run main.py
```

Reproduce every number in the experiments section:

```bash
uv run python run_experiments.py
```

### Project layout

| File | Purpose |
|---|---|
| `main.py` | Entrypoint; calls `init_state()` and registers the four pages with `st.navigation` |
| `bandit_utils.py` | Original Beta–Bernoulli carousel logic and session-state helpers |
| `gaussian_bandit.py` | **New.** Gaussian Thompson sampling, input validation, result tables (no Streamlit imports) |
| `pages/Create_Carousels.py`, `Interaction.py`, `Analytics.py` | Original pages |
| `pages/Gaussian_Bandit.py` | **New.** Gaussian Bandit page |
| `run_experiments.py` | **New.** Runs the three assignment experiments plus a many-seed robustness check |

## 1. The original algorithm (Beta–Bernoulli Thompson sampling)

The original app manages *carousels*. Each carousel has several alternatives (e.g. banners) and
shows only `visible_count` of them per round. Feedback is binary: a displayed alternative is
clicked or not. Every alternative starts with a Beta(1, 1) (uniform) belief about its click-through
rate θ.

**Alternative selection** (`sample_carousel`). For every alternative the app draws one sample
θ ~ Beta(α, β) from its current posterior, sorts the samples in descending order and displays the
top `visible_count` alternatives (stored as `current_display_ids`). Alternatives with a high
posterior mean are shown often; alternatives with an uncertain, wide posterior still get shown
sometimes, which is the exploration part of Thompson sampling.

**Reward recording** (`update_after_feedback`). On the Interaction page the user either clicks one
displayed alternative or presses *No click / Next round*. For **every displayed alternative** the
impression count goes up by one. The clicked alternative gets α + 1 and clicks + 1 (reward 1); the
other displayed alternatives get β + 1 (reward 0). Alternatives that were not displayed are not
touched. The round is appended to `history` (timestamp, round, displayed ids, clicked id, reward =
1 if there was a click else 0), the round counter increases and a new set is sampled for the next
round. *Resample without update* draws a new set without learning anything.

**Beta posterior updates.** The Beta distribution is conjugate to the Bernoulli likelihood, so the
posterior stays Beta and the update is just counting:

```
alpha = 1 + clicks        beta = 1 + (impressions - clicks)        posterior mean = alpha / (alpha + beta)
```

The Analytics page shows posterior means, the Beta density of every alternative, empirical CTR,
and names as *champion* the alternative with the largest posterior mean.

**How session state connects the pages.** Streamlit re-runs a page script on every interaction, so
anything that must survive lives in `st.session_state`. `main.py` and every page call
`init_state()`, which creates two keys once per browser session:

- `carousels`: a dict `carousel_id → {name, total_alternatives, visible_count, round_number,
  alternatives (DataFrame with α, β, impressions, clicks), history, current_display_ids}`.
- `active_carousel_id`: the carousel currently selected.

*Create Carousels* writes a new entry (`create_carousel`), *Interaction* reads the entry and
mutates it (`update_after_feedback`), and *Analytics* reads the same entry to plot it. The shared
`select_carousel_widget` keeps `active_carousel_id` in sync, so the carousel picked on one page is
preselected on the next. There is no database yet (the code has `TODO` markers for API calls), so
state lives in the server's memory for one browser session and is lost on refresh.
The new page adds a third key, `gaussian_result`, created in the same `init_state()`, which holds
the result of the last Gaussian run so it survives widget reruns and page switches.

## 2. The Gaussian adaptation

**Model.** Three alternatives. Selecting alternative *i* gives one continuous reward

```
R | A = i  ~  Normal(mu_i, sigma^2)
```

with a **shared, known** noise standard deviation σ > 0 (reward precision 1/σ²) and unknown
means μᵢ. Every mean gets the same prior **Normal(0, 25)** (prior mean 0, variance 25, so
precision 1/25 = 0.04). Rewards are continuous and may be negative.

**Posterior update.** A Normal prior with a Normal likelihood of known variance gives a Normal
posterior, so each alternative keeps two numbers, a precision λ and a precision-weighted sum b,
starting at λ = 1/25 and b = 0 (prior mean 0). After alternative *i* is selected and reward *r*
observed:

```
lambda_i <- lambda_i + 1/sigma^2          (every observation adds 1/sigma^2 of precision)
b_i      <- b_i      + r/sigma^2
posterior mean m_i = b_i / lambda_i       posterior variance = 1 / lambda_i
```

In closed form, after n observations with reward sum S: precision λ = 1/25 + n/σ² and mean
m = (S/σ²) / λ. The posterior mean is a precision-weighted average of the prior mean (0) and the
sample mean, so the data dominate quickly. Because σ is known the result is exact, with no
approximation. Known σ is what makes the update so simple: a large σ means each reward carries
less information, so the posterior narrows more slowly (std = 1/√λ ≈ σ/√n).

**One round** (`run_gaussian_thompson`):

1. For each alternative sample a possible mean θᵢ ~ Normal(mᵢ, 1/λᵢ) from its current posterior.
2. Select the alternative with the largest θᵢ.
3. Generate one reward r ~ Normal(μ_selected, σ²) from the *true* mean.
4. Update **only the selected alternative's** posterior with r and the known σ.

The true means are used only by the simulator to generate rewards and by us to evaluate learning
(comparing estimates with the truth, and regret in the experiments); selection uses only the
learned posteriors. A single
`numpy.random.default_rng(seed)` drives both posterior sampling and reward noise, so the same
configuration and seed always reproduce the same run.

**Final recommendation:** the alternative with the largest posterior mean.

### Differences from the original algorithm

| | Original (Beta–Bernoulli) | New (Gaussian) |
|---|---|---|
| Reward | 0 / 1 click | continuous, any real value |
| Unknown | click rate θ ∈ (0, 1) | mean reward μ ∈ ℝ |
| Posterior | Beta(α, β) | Normal(m, 1/λ) |
| Noise | implicit (Bernoulli) | explicit, known σ |
| Per round | top-k alternatives shown, all get feedback | one alternative selected, only it is updated |
| Randomness | Python `random` | seeded `numpy` generator (reproducible) |

### The Gaussian Bandit page

Open **Gaussian Bandit** in the sidebar. Inputs: the three true means, the known σ, the number of
rounds and the random seed, plus a **Run** button. Invalid input is rejected with an error and
nothing is run: σ must be a positive finite number, rounds a positive integer, the seed a
non-negative integer, and the means finite numbers. The page shows, per alternative, the **true
mean, posterior estimated mean and selection count**, the **total observed reward**, and the
**final recommendation**, together with a check that the selection counts sum to the number of
rounds.

## 3. Experiments

Setup for all runs: true means [1, 2, 3], prior Normal(0, 25), **seed 42**. Reproduce with
`uv run python run_experiments.py`.

| Experiment | True means | Known σ | Rounds | Seed |
|---|---|---|---|---|
| Short run | [1, 2, 3] | 1 | 100 | 42 |
| Longer run | [1, 2, 3] | 1 | 1,000 | 42 |
| Higher noise | [1, 2, 3] | 3 | 1,000 | 42 |

**Estimated means** (posterior mean ± posterior std) and **selection counts**:

| Experiment | Alt 1 (true 1) | Alt 2 (true 2) | Alt 3 (true 3) | Selections 1 / 2 / 3 | Total reward | Recommendation |
|---|---|---|---|---|---|---|
| Short run (σ=1, n=100) | 1.570 ± 0.498 | 1.729 ± 0.700 | 2.995 ± 0.103 | 4 / 2 / 94 | 291.52 | Alternative 3 |
| Longer run (σ=1, n=1,000) | 1.306 ± 0.445 | 2.142 ± 0.277 | 2.979 ± 0.032 | 5 / 13 / 982 | 2960.20 | Alternative 3 |
| Higher noise (σ=3, n=1,000) | 1.154 ± 0.649 | 1.484 ± 0.621 | 2.954 ± 0.097 | 21 / 23 / 956 | 2884.60 | Alternative 3 |

**Checks.** Rerunning each configuration with seed 42 reproduces the result exactly (identical
choices, rewards and posteriors), and selection counts sum to the number of rounds in every run
(100, 1,000, 1,000). `run_experiments.py` prints both checks, and the Gaussian Bandit page shows the
counts check after every run.

**Robustness over 200 seeds (0–199).** Seed 42 is one draw, so we repeated every experiment with
200 seeds to see what is systematic:

| Experiment | Recommends Alt 3 | Mean share of Alt 3 | Mean share of Alt 1 | Mean posterior mean (Alt 1 / 2 / 3) | Mean cumulative regret |
|---|---|---|---|---|---|
| Short run (σ=1, n=100) | 100% | 91.7% | 2.3% | 0.70 / 1.71 / 3.00 | 10.6 |
| Longer run (σ=1, n=1,000) | 100% | 98.8% | 0.3% | 0.68 / 1.76 / 3.00 | 15.4 |
| Higher noise (σ=3, n=1,000) | 100% | 93.3% | 1.6% | 0.33 / 1.61 / 3.00 | 83.3 |

### Discussion

**All three runs recommend the right alternative (Alternative 3)**, and so do all 200 seeds in each
setting. The alternatives are well separated (gaps of 1 against σ ≤ 3), and Thompson sampling
concentrates on the best one quickly: 94–98% of the rounds.

**Effect of more observations (short vs longer run, σ = 1).** Ten times more rounds make the
estimate of the best alternative much sharper (posterior std 0.103 → 0.032, roughly σ/√n), and
the share of rounds going to Alternative 3 rises from 94% to 98.2%. Regret grows only from 10 to 23
(mean over seeds 10.6 → 15.4): 10× the rounds costs about 2× the regret, because as the posteriors
separate the sampler stops exploring. The recommendation does not change, since 100 rounds were
already enough to identify the best alternative.

**Effect of higher noise (σ = 3 vs σ = 1, both 1,000 rounds).** Each reward carries 9× less
information, so the posterior of Alternative 3 is about three times wider (std 0.097 vs 0.032);
the noisy 1,000-round run is only as precise about Alternative 3 as the σ = 1 run with 100
rounds (0.097 vs 0.103). The noisier rewards also keep the sampler exploring: the weaker
alternatives are selected 21 and 23 times instead of 5 and 13, the share of Alternative 3 falls
from 98.2% to 95.6%, and regret is much higher (65 vs 23; mean over seeds 83.3 vs 15.4). Even so, the
recommendation stays correct.

**Unexpected result: more data did not improve the estimates of the weaker alternatives, and
those estimates are biased downward.** Going from 100 to 1,000 rounds hardly changed how often
Alternative 1 was tried (4 → 5 selections, median over seeds 2 → 3), so its posterior stays wide
(std 0.45–0.50), and Alternative 2's estimate is still off by 0.14. Single-seed errors point in both
directions (Alternative 1 is overestimated at 1.57, 1.31 and 1.15), but averaged over 200 seeds the
estimate of Alternative 1 is **below** its true mean of 1: 0.70, 0.68 and, with higher noise, only
0.33. We checked two natural explanations and rejected both: the prior pulling estimates toward 0
(the raw sample means of the pulled alternatives are practically identical: 0.71, 0.68, 0.30;
shrinkage with a handful of observations is about 1%) and the alternative simply never being
pulled (it was pulled at least once in all 200 seeds). The remaining explanation is the adaptive
sampling itself: an alternative that happens to produce low early rewards looks bad and is rarely
sampled again, so its low estimate is never corrected, while one with lucky early rewards keeps
being sampled and regresses to its true mean. With more noise, unlucky draws are larger, so the
effect is stronger. This is acceptable for the purpose of the bandit: Thompson sampling spends data
where it matters for the decision (separating the best alternative from the rest), not on
estimating every mean precisely, so the final recommendation is reliable even though the weaker
estimates are not.

## 4. Deployment

Streamlit Community Cloud settings: repository `StepanTitanyan/Carousel_Group_Work_1`, branch
`main`, entrypoint `main.py`, Python 3.12. Dependencies come from `pyproject.toml` and `uv.lock`.
The deployed URL is listed under [Links](#links).
