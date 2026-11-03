# pages/Gaussian_Bandit.py

import streamlit as st

from bandit_utils import init_state
from gaussian_bandit import (
    PRIOR_MEAN,
    PRIOR_VARIANCE,
    alternative_labels,
    run_gaussian_thompson,
    summary_df,
    validate_inputs,
)

init_state()

st.title("Gaussian Bandit")
st.caption(
    "Thompson sampling for continuous rewards R | A = i ~ Normal(μᵢ, σ²) with known σ. "
    f"Every unknown mean has a Normal({PRIOR_MEAN:g}, {PRIOR_VARIANCE:g}) prior."
)

with st.form("gaussian_bandit_form"):
    st.markdown("**True means** (used only by the simulator to generate rewards)")
    mean_cols = st.columns(3)
    true_means = [
        col.number_input(
            f"True mean of alternative {i}",
            value=float(i),
            step=0.5,
            format="%.2f",
            key=f"gaussian_true_mean_{i}",
        )
        for i, col in enumerate(mean_cols, start=1)
    ]

    sigma_col, rounds_col, seed_col = st.columns(3)
    sigma = sigma_col.number_input("Known noise σ", value=1.0, step=0.1, format="%.2f")
    rounds = rounds_col.number_input("Number of rounds", value=100, step=1, format="%d")
    seed = seed_col.number_input("Random seed", value=42, step=1, format="%d")

    submitted = st.form_submit_button("Run", type="primary")

errors = []
if submitted:
    errors = validate_inputs(true_means, sigma, rounds, seed)
    if errors:
        st.session_state.gaussian_result = None
        for message in errors:
            st.error(message)
    else:
        st.session_state.gaussian_result = run_gaussian_thompson(true_means, sigma, int(rounds), int(seed))

result = st.session_state.gaussian_result

if result is None:
    if not errors:
        st.info("Set the inputs above and press Run.")
else:
    means_text = ", ".join(f"{m:g}" for m in result.true_means)
    st.caption(
        f"Last run: true means [{means_text}] • σ = {result.sigma:g} • "
        f"{result.rounds:,} rounds • seed {result.seed}"
    )

    k1, k2 = st.columns(2)
    k1.metric("Total observed reward", f"{result.total_reward:,.2f}")
    k2.metric("Final recommendation", alternative_labels(len(result.true_means))[result.recommendation])

    st.markdown("**Results by alternative**")
    table = summary_df(result)
    st.dataframe(
        table,
        width="stretch",
        hide_index=True,
        column_config={
            "True mean": st.column_config.NumberColumn(format="%.3f"),
            "Posterior mean": st.column_config.NumberColumn(format="%.3f"),
        },
    )

    total_selections = int(table["Selections"].sum())
    if total_selections == result.rounds:
        st.caption(f"Check: selection counts sum to {total_selections:,}, equal to the number of rounds.")
    else:
        st.error(f"Selection counts sum to {total_selections:,} but {result.rounds:,} rounds were run.")
