import streamlit as st
import numpy as np
import math

# -----------------------------------
# Streamlit setup
# -----------------------------------
st.set_page_config(
    page_title="Invasive Species Risk — Fuzzy Models",
    layout="centered",
    page_icon="🌿"
)

# Custom minimal styling
st.markdown("""
<style>
body {font-family: "Segoe UI", sans-serif; color: #1e293b; background-color: #f8fafc;}
h1, h2, h3 {color: #0f172a; font-weight: 600;}
.stButton>button {
    background-color: #0284c7; color: white; border-radius: 8px;
    padding: 8px 20px; font-weight: 600; transition: 0.3s;
}
.stButton>button:hover {background-color: #0369a1; transform: scale(1.03);}
.block-container {max-width: 850px;}
</style>
""", unsafe_allow_html=True)

# -----------------------------------
# Linguistic Terms & Memberships
# -----------------------------------
LABELS = ["Unlikely", "Very Low", "Low", "Medium", "High", "Very High", "Extremely High"]
LABEL_INDEX = {lab: i for i, lab in enumerate(LABELS)}
LINGUISTIC_TFS = {
    "Unlikely": (0.0, 0.0, 0.16),
    "Very Low": (0.16, 0.16, 0.18),
    "Low": (0.34, 0.18, 0.16),
    "Medium": (0.5, 0.16, 0.16),
    "High": (0.66, 0.16, 0.18),
    "Very High": (0.84, 0.18, 0.16),
    "Extremely High": (1.0, 0.16, 0.0),
}

def linguistic_centroid(label):
    a, l, r = LINGUISTIC_TFS[label]
    return (a - l + a + a + r) / 3.0

def numeric_to_label(q):
    best_label, best_d = None, None
    for lab in LABELS:
        c = linguistic_centroid(lab)
        d = (q - c)**2
        if best_d is None or d < best_d:
            best_label, best_d = lab, d
    return best_label

# -----------------------------------
# Dispersal submodel functions
# -----------------------------------
def UA_sf(x):
    x = float(x)
    if x < 1: return 1.0
    if 1 <= x <= 501: return 1 - 2 * ((x - 1) / 1000)**2
    if 501 < x <= 1001: return 2 * ((x - 1001) / 1000)**2
    return 0.0

def UB_asr(x):
    x = float(x)
    if 0 <= x < 10000: return 2 * (10000 - x) / (8e8) + 0.75
    if 10000 <= x < 100000: return 2 * (100000 - x) / (5.4e10) + 0.45
    if 100000 <= x <= 1e7: return 2 * (1e7 - x) / (4.356e14)
    return 0.0

def UC_via(x):
    x = float(x)
    if x < 3: return 1.0
    if 3 <= x < 602: return 1 - 2 * ((x - 3)**2 / 2376060)
    if 602 <= x <= 1200: return 2 * ((1200 - x)**2 / 1028572)
    return 0.0

def UD_ldd(x):
    x = float(x)
    if 0 <= x < 2: return 1 - 2 * (x**2 / 160)
    if 2 <= x < 5: return 0.95 - 2 * ((x - 2)**2 / 60)
    if 5 <= x <= 10: return 2 * ((10 - x)**2 / 77)
    return 0.0

def hamacher_tnorm(a, b, p=0.5):
    num = a * b
    den = p + (1 - p) * (a + b - a * b)
    return 0.0 if den == 0 else num / den

def compute_dispersal_score(sf, asr, via_months, ldd):
    u_sf = UA_sf(sf)
    u_asr = UB_asr(asr)
    u_via = UC_via(via_months)
    u_ldd = UD_ldd(ldd)
    res = hamacher_tnorm(u_sf, u_asr)
    res = hamacher_tnorm(res, u_via)
    res = hamacher_tnorm(res, u_ldd)
    return 1.0 - res

# -----------------------------------
# LOWA & LWA Model Equations
# -----------------------------------
def yager_quantifier(i_over_n, a, b):
    r = i_over_n
    if r < a: return 0.0
    if a <= r <= b: return (r - a) / (b - a) if (b - a) != 0 else 1.0
    return 1.0

def compute_weights_by_quantifier(n, a, b):
    Q = [yager_quantifier(i/n, a, b) for i in range(0, n+1)]
    w = [Q[i] - Q[i-1] for i in range(1, n+1)]
    s = sum(w)
    return [wi/s for wi in w] if s != 0 else [1.0/n]*n

def lowa_aggregate(labels, quantifier_params=(0.3, 0.8)):
    n = len(labels)
    idxs = sorted([LABEL_INDEX[l] for l in labels], reverse=True)
    a, b = quantifier_params
    w = compute_weights_by_quantifier(n, a, b)
    current_idx = idxs[0]
    for i in range(1, n):
        wi = w[i-1]
        next_idx = idxs[i]
        k = min(len(LABELS)-1, current_idx + round(wi*(next_idx - current_idx)))
        current_idx = k
    return LABELS[current_idx]

def lwa_aggregate(weighted_pairs, quantifier_params=(0.3, 0.8)):
    transformed_idxs = [min(LABEL_INDEX[wl], LABEL_INDEX[vl]) for wl, vl in weighted_pairs]
    labels = [LABELS[i] for i in transformed_idxs]
    return lowa_aggregate(labels, quantifier_params)

# -----------------------------------
# Navigation
# -----------------------------------
if "page" not in st.session_state:
    st.session_state.page = 1
def goto(page): st.session_state.page = page

# -----------------------------------
# Page 1 — Introduction
# -----------------------------------
if st.session_state.page == 1:
    st.title("🌿 Invasive Species Risk Assessment Dashboard")
    st.markdown("""
    Welcome to the **Fuzzy Invasive Species Risk Assessment Tool**,  
    developed following the models described in *Peiris et al., Applied Soft Computing (2017)*.

    This dashboard estimates the likelihood that an **alien plant species** becomes invasive in an ecosystem.

    ### Models:
    - **Model I (LOWA)** — all ecological and anthropogenic factors are equally weighted.
    - **Model II (LWA)** — factors are weighted by their expert-assigned importance.

    You will:
    1. Choose the model.
    2. Provide the biological and environmental factors.
    3. View an interpretable fuzzy risk output indicating potential invasiveness.
    """)
    if st.button("Next ➡️"): goto(2)

# -----------------------------------
# Page 2 — Model Selection
# -----------------------------------
elif st.session_state.page == 2:
    st.header("⚙️ Model Selection")
    st.markdown("Please select the fuzzy model appropriate for your analysis.")
    st.markdown("<br>", unsafe_allow_html=True)

    model_choice = st.radio(
        "Select Model Type",
        ["Model I (LOWA) — Equal Importance",
         "Model II (LWA) — Weighted by Expert Importance"],
        index=0,
        horizontal=False,
    )

    st.markdown("""
    - **Model I (LOWA):** All ecological and human-influence factors contribute equally.  
    - **Model II (LWA):** Factors are weighted by expert importance (Dispersal ≫ VRS ≫ MIS ≫ SGR).
    """)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("✅ Confirm and Continue"):
        st.session_state.chosen_model = model_choice
        # route user to correct factors page
        if "LOWA" in model_choice:
            goto("3A")     # Model I inputs
        else:
            goto("3B")     # Model II inputs
    if st.button("⬅️ Back"):
        goto(1)

# -----------------------------------
# Page 3A — Model I (LOWA) Inputs
# -----------------------------------
elif st.session_state.page == "3A":
    st.header("📊 Input Factors — Model I (LOWA)")
    st.info("All four main factors contribute equally to the invasion-risk result.")
    with st.form("inputs_lowa"):
        st.subheader("Dispersal Subfactors")
        sf = st.number_input("Seeds per fruit", 0, 100000, 100)
        asr = st.number_input("Annual seed rain (per m²)", 0, 10000000, 10000)
        via = st.number_input("Seed viability (months)", 0, 2000, 12)
        ldd = st.slider("Long-distance dispersal (0–10)", 0.0, 10.0, 3.0)

        opts = LABELS
        st.subheader("Other Main Factors")
        vrs = st.selectbox("Vegetative reproduction strength", opts, index=3)
        sgr = st.selectbox("Seed germination requirement", opts, index=3)
        ha = st.selectbox("Human activity influence", opts, index=3)
        nmd = st.selectbox("Natural/man-made disturbance", opts, index=3)
        submitted = st.form_submit_button("Next ➡️")

    if submitted:
        st.session_state.update(
            {"sf": sf, "asr": asr, "via": via, "ldd": ldd,
             "vrs": vrs, "sgr": sgr, "ha": ha, "nmd": nmd}
        )
        goto(4)
    if st.button("⬅️ Back"): goto(2)

# -----------------------------------
# Page 3B — Model II (LWA) Inputs
# -----------------------------------
elif st.session_state.page == "3B":
    st.header("📊 Input Factors — Model II (LWA)")
    st.info("Main factors are weighted according to expert importance "
            "(Peiris et al., 2017).")

    st.markdown("""
    | Factor | Expert Weight Importance |
    |:--------|:------------------------:|
    | Dispersal (D) | Very High |
    | Vegetative Reproduction Strength (VRS) | Very High |
    | Seed Germination Requirement (SGR) | Medium |
    | Man-made/Natural Disturbance (MIS) | High |
    """)

    with st.form("inputs_lwa"):
        st.subheader("Dispersal Subfactors")
        sf = st.number_input("Seeds per fruit", 0, 100000, 100)
        asr = st.number_input("Annual seed rain (per m²)", 0, 10000000, 10000)
        via = st.number_input("Seed viability (months)", 0, 2000, 12)
        ldd = st.slider("Long-distance dispersal (0–10)", 0.0, 10.0, 3.0)

        opts = LABELS
        st.subheader("Other Main Factors")
        vrs = st.selectbox("Vegetative reproduction strength", opts, index=3)
        sgr = st.selectbox("Seed germination requirement", opts, index=3)
        ha = st.selectbox("Human activity influence", opts, index=3)
        nmd = st.selectbox("Natural/man-made disturbance", opts, index=3)
        submitted = st.form_submit_button("Next ➡️")

    if submitted:
        st.session_state.update(
            {"sf": sf, "asr": asr, "via": via, "ldd": ldd,
             "vrs": vrs, "sgr": sgr, "ha": ha, "nmd": nmd}
        )
        goto(4)
    if st.button("⬅️ Back"): goto(2)


# -----------------------------------
# Page 4 — Quantifier & Compute
# -----------------------------------
elif st.session_state.page == 4:
    st.header("🔢 Select Quantifier and Compute Risk")
    quant = st.selectbox(
        "Select fuzzy quantifier (represents linguistic aggregation preference)",
        ["Mean (0.0,1.0)", "Most (0.3,0.8)", "At least half (0,0.5)"]
    )
    qparams = {"Mean (0.0,1.0)": (0.0,1.0), "Most (0.3,0.8)": (0.3,0.8), "At least half (0,0.5)": (0.0,0.5)}[quant]

    if st.button("⬅️ Back"): goto(3)
    if st.button("🚀 Calculate Risk"):
        disp_score = compute_dispersal_score(st.session_state.sf, st.session_state.asr, st.session_state.via, st.session_state.ldd)
        disp_label = numeric_to_label(disp_score)
        mis_label = lwa_aggregate([(st.session_state.ha, st.session_state.ha),
                                   (st.session_state.nmd, st.session_state.nmd)], quantifier_params=(0.0,1.0))
        st.session_state.update({
            "disp_score": disp_score,
            "disp_label": disp_label,
            "mis_label": mis_label,
            "quant_params": qparams
        })
        goto(5)

# -----------------------------------
# Page 5 — Results
# -----------------------------------
elif st.session_state.page == 5:
    st.header("🌱 Final Results")
    model = st.session_state.get("chosen_model", "Model I (LOWA)")
    quant_params = st.session_state.get("quant_params", (0.3, 0.8))
    main_factors = {
        "Dispersal": st.session_state.disp_label,
        "VRS": st.session_state.vrs,
        "SGR": st.session_state.sgr,
        "MIS": st.session_state.mis_label
    }

    st.subheader("📋 Model Summary")
    st.write(f"**Model Used:** {model}")
    st.write(f"**Dispersal Score (0–1):** {st.session_state.disp_score:.4f}")
    st.json(main_factors)

    if "LOWA" in model:
        labels = list(main_factors.values())
        result_label = lowa_aggregate(labels, quantifier_params=quant_params)
    else:
        weights = {"Dispersal": "Very High", "VRS": "Very High", "SGR": "Medium", "MIS": "High"}
        pairs = [(weights[k], v) for k, v in main_factors.items()]
        result_label = lwa_aggregate(pairs, quantifier_params=quant_params)

    st.subheader("🧭 Invasion Risk Result")
    st.markdown(f"### **{result_label}**")

    # Interpretation
    risk_idx = LABEL_INDEX[result_label]
    if risk_idx <= 2:
        st.success("✅ This species shows **low invasion risk** under current conditions.")
    elif 3 <= risk_idx <= 4:
        st.warning("⚠️ This species shows a **moderate invasion risk**. Monitoring recommended.")
    else:
        st.error("🚨 This species is **highly likely to be invasive** and requires immediate management!")

    st.caption("Derived from fuzzy linguistic aggregation models (LOWA/LWA) — Peiris et al., Applied Soft Computing (2017).")
    centroids = {lab: linguistic_centroid(lab) for lab in LABELS}
    st.bar_chart(centroids)
    if st.button("🔁 Start New Assessment"): goto(1)
    if st.button("⬅️ Back"): goto(4)


#python -m streamlit run invasive_risk_dashboard_app.py