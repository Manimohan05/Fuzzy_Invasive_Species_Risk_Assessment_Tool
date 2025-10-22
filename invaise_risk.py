import streamlit as st
import numpy as np
import math
from functools import reduce

st.set_page_config(page_title="Invasive Species Risk — Fuzzy Models", layout="centered")

# ---------------------------
# Linguistic term set (7 terms)
# s0=U, s1=VL, s2=L, s3=M, s4=H, s5=VH, s6=EH
LABELS = ["Unlikely", "Very Low", "Low", "Medium", "High", "Very High", "Extremely High"]
LABEL_INDEX = {lab: i for i, lab in enumerate(LABELS)}

# Triangular membership parameters (approx from paper)
LINGUISTIC_TFS = {
    "Unlikely": (0.0, 0.0, 0.16),
    "Very Low": (0.16, 0.16, 0.18),
    "Low": (0.34, 0.18, 0.16),
    "Medium": (0.5, 0.16, 0.16),
    "High": (0.66, 0.16, 0.18),
    "Very High": (0.84, 0.18, 0.16),
    "Extremely High": (1.0, 0.16, 0.0),
}

def triangular_membership(x, a, l, r):
    left = a - l
    right = a + r
    if x <= left or x >= right:
        return 0.0
    if left < x <= a:
        return (x - left) / (a - left) if (a - left) != 0 else 1.0
    if a < x < right:
        return (right - x) / (right - a) if (right - a) != 0 else 1.0
    return 0.0

def linguistic_centroid(label):
    a, l, r = LINGUISTIC_TFS[label]
    left = a - l
    right = a + r
    return (left + a + right) / 3.0

def numeric_to_label(q):
    best = None
    bestd = None
    for lab in LABELS:
        c = linguistic_centroid(lab)
        d = (q - c)**2
        if bestd is None or d < bestd:
            bestd = d
            best = lab
    return best

# -- Dispersal submodel fuzzy membership functions
def UA_sf(x):
    x = float(x)
    if x < 1: return 1.0
    if 1 <= x <= 501:
        return 1 - 2 * ((x - 1) / 1000)**2
    if 501 < x <= 1001:
        return 2 * ((x - 1001) / 1000)**2
    return 0.0

def UB_asr(x):
    x = float(x)
    if 0 <= x < 10000:
        return 2 * (10000 - x) / (8e8) + 0.75
    if 10000 <= x < 100000:
        return 2 * (100000 - x) / (5.4e10) + 0.45
    if 100000 <= x <= 1e7:
        return 2 * (1e7 - x) / (4.356e14)
    return 0.0

def UC_via(x):
    x = float(x)
    if x < 3: return 1.0
    if 3 <= x < 602:
        return 1 - 2 * ((x - 3)**2 / 2376060)
    if 602 <= x <= 1200:
        return 2 * ((1200 - x)**2 / 1028572)
    return 0.0

def UD_ldd(x):
    x = float(x)
    if 0 <= x < 2:
        return 1 - 2 * (x**2 / 160)
    if 2 <= x < 5:
        return 0.95 - 2 * ((x - 2)**2 / 60)
    if 5 <= x <= 10:
        return 2 * ((10 - x)**2 / 77)
    return 0.0

def hamacher_tnorm(a, b, p=0.5):
    num = a * b
    den = p + (1 - p) * (a + b - a * b)
    if den == 0: return 0.0
    return num / den

def compute_dispersal_score(sf, asr, via_months, ldd):
    u_sf = UA_sf(sf)
    u_asr = UB_asr(asr)
    u_via = UC_via(via_months)
    u_ldd = UD_ldd(ldd)
    res = hamacher_tnorm(u_sf, u_asr, p=0.5)
    res = hamacher_tnorm(res, u_via, p=0.5)
    res = hamacher_tnorm(res, u_ldd, p=0.5)
    return 1.0 - res

# ---------- LOWA (Model I)
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

# ---------- LWA (Model II)
def min_transform(weight_label, value_label):
    return min(LABEL_INDEX[weight_label], LABEL_INDEX[value_label])

def lwa_aggregate(weighted_pairs, quantifier_params=(0, 0.5)):
    transformed_idxs = [min_transform(wl, vl) for wl, vl in weighted_pairs]
    labels = [LABELS[i] for i in transformed_idxs]
    return lowa_aggregate(labels, quantifier_params)

# ---------- Streamlit Navigation ----------
if "page" not in st.session_state:
    st.session_state.page = 1

def goto(page): st.session_state.page = page

# Page 1: Intro
if st.session_state.page == 1:
    st.title("Invasive Species Risk — Fuzzy Linguistic Models")
    st.markdown("""
    This dashboard implements **Model I (LOWA)** and **Model II (LWA)** from
    *Peiris et al., Applied Soft Computing (2017)* to assess alien plant species risk.
    """)
    st.markdown("""
    **Main factors:** Dispersal, VRS, SGR, MIS  
    **Subfactors:** Seeds/fruit, Seed rain, Viability, LDD, Human Activity, Disturbances.
    """)
    if st.button("Next"):
        goto(2)

# Page 2: Model selection
elif st.session_state.page == 2:
    st.header("Model Selection")
    st.selectbox("Choose model", ["Model I (LOWA)", "Model II (LWA)"], key="chosen_model")
    if st.button("Back"): goto(1)
    if st.button("Next"): goto(3)

# Page 3: Inputs
elif st.session_state.page == 3:
    st.header("Input Factors")
    with st.form("inputs_form"):
        sf = st.number_input("Seeds per fruit", 0, 100000, 100)
        asr = st.number_input("Annual seed rain (m²)", 0, 10000000, 10000)
        via = st.number_input("Viability (months)", 0, 2000, 12)
        ldd = st.slider("LDD (0-10)", 0.0, 10.0, 3.0)
        opts = LABELS
        vrs = st.selectbox("Vegetative reproduction strength", opts, index=3)
        sgr = st.selectbox("Seed germination requirement", opts, index=3)
        ha = st.selectbox("Human activity influence", opts, index=3)
        nmd = st.selectbox("Natural/man-made disturbance", opts, index=3)
        submitted = st.form_submit_button("Save and Continue")
    if submitted:
        st.session_state.sf = sf
        st.session_state.asr = asr
        st.session_state.via = via
        st.session_state.ldd = ldd
        st.session_state.vrs = vrs
        st.session_state.sgr = sgr
        st.session_state.ha = ha
        st.session_state.nmd = nmd
        goto(4)
    if st.button("Back"): goto(2)

# Page 4: Quantifier & run
elif st.session_state.page == 4:
    st.header("Select Quantifier and Run")
    quant = st.selectbox("Quantifier", ["Mean (0.0,1.0)", "Most (0.3,0.8)", "At least half (0,0.5)"])
    quant_map = {"Mean (0.0,1.0)": (0.0,1.0), "Most (0.3,0.8)": (0.3,0.8), "At least half (0,0.5)": (0.0,0.5)}
    qparams = quant_map[quant]
    if st.button("Back"): goto(3)
    if st.button("Calculate Risk"):
        disp_score = compute_dispersal_score(st.session_state.sf, st.session_state.asr, st.session_state.via, st.session_state.ldd)
        disp_label = numeric_to_label(disp_score)
        mis_label = lwa_aggregate([(st.session_state.ha, st.session_state.ha), (st.session_state.nmd, st.session_state.nmd)], quantifier_params=(0.0,1.0))
        main_factors = {
            "Dispersal": disp_label,
            "VRS": st.session_state.vrs,
            "SGR": st.session_state.sgr,
            "MIS": mis_label
        }
        st.session_state.main_factors = main_factors
        st.session_state.disp_score = disp_score
        st.session_state.disp_label = disp_label
        st.session_state.quant_params = qparams
        goto(5)

# Page 5: Results
elif st.session_state.page == 5:
    st.header("Results")
    model = st.session_state.get("chosen_model", "Model I (LOWA)")
    quant_params = st.session_state.get("quant_params", (0.3,0.8))
    st.write(f"**Model used:** {model}")
    st.write(f"Dispersal score: {st.session_state.disp_score:.4f}")
    st.write(f"Dispersal label: {st.session_state.disp_label}")
    st.json(st.session_state.main_factors)

    if model == "Model I (LOWA)":
        labels = list(st.session_state.main_factors.values())
        result_label = lowa_aggregate(labels, quantifier_params=quant_params)
    else:
        weights = {"Dispersal": "Very High", "VRS": "Very High", "SGR": "Medium", "MIS": "High"}
        pairs = [(weights[k], v) for k, v in st.session_state.main_factors.items()]
        result_label = lwa_aggregate(pairs, quantifier_params=quant_params)

    st.subheader("Final Invasion Risk")
    st.markdown(f"### **{result_label}**")
    centroids = {lab: linguistic_centroid(lab) for lab in LABELS}
    st.bar_chart(centroids)
    if st.button("Run another assessment"): goto(1)
    if st.button("Back"): goto(4)
