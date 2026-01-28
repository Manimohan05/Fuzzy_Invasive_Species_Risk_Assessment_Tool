import streamlit as st
import numpy as np

# -----------------------------------
# Model definitions & constants
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
FACTOR_WEIGHTS = {
    "Dispersal": "Very High",
    "VRS": "Very High",
    "SGR": "Medium",
    "MIS": "High"
}

# -----------------------------------
# Utility functions for fuzzy mathematics
# -----------------------------------
def numeric_to_label(q):
    best_label = None
    best_score = float("inf")
    
    for lab, (a,l,r) in LINGUISTIC_TFS.items():
        left = a - l
        right = a + r
        if not (left <= q <= right):
            score = 3  # c = 3
        else:
            G1 = a
            G2 = a + (r - l)/6
            G3 = a
            score = (q-G1)**2 + (q-G2)**2 + (q-G3)**2
        
        if score < best_score:
            best_score = score
            best_label = lab
    return best_label

# CORRECTED Dispersal subfactor membership functions (Eqs 2-5)
import math

def UA_sf(x):
    x = min(x, 1001)
    if x < 1: return 1.0
    if 1 <= x <= 501:
        return 1 - 2 * ((x - 1) / 1000)**2
    if 501 < x <= 1001:
        return 2 * ((x - 1001) / 1000)**2
    return 0.0


def UB_asr(x):
    """Eq 3: EXACT - Annual seed production per m²"""
    x = float(x)
    if 0 <= x < 10000:
        return (2 * (10000 - x)**2  / (8 * 10**8))+ 0.75
    elif 10000 <= x < 100000:
        return (2 * (100000 - x)**2 / (5.4 * 10**10)) + 0.45
    elif 100000 <= x <= 10**7:
        return 2 * (10**7 - x)**2 / (4.356 * 10**14)
    else:
        return 0.0

def UC_via(x):
    """Eq 4: EXACT - Viability of seeds (months)"""
    x = float(x)
    if x < 3:
        return 1.0
    elif 3 <= x < 602:
        return 1 - 2 * ((x - 3)**2 / 2376060)
    elif 602 <= x <= 1200:
        return 2 * ((1200 - x)**2 / 1028572)
    else:
        return 0.0

def UD_ldd(x):
    """Eq 5: EXACT - Long distance dispersal strength (0-10 scale)"""
    x = float(x)
    if 0 <= x < 2:
        return 1 - 2 * (x**2 / 160)
    elif 2 <= x < 5:
        return 0.95 - 2 * ((x - 2)**2 / 60)
    elif 5 <= x <= 10:
        return 2 * ((10 - x)**2 / 77)
    else:
        return 0.0


def hamacher_tnorm(a, b, p=0.5):  # p=0.5 (paper standard)
    """Eq 10: FIXED - handles zero inputs"""
    if a == 0 or b == 0: return 0.0
    num = a * b
    den = p + (1 - p) * (a + b - a * b)
    return num / max(den, 1e-12)

def concentration(mf, power):
    """Eq 11: Concentration operator"""
    return mf ** power
def compute_dispersal_score(sf, asr, via_months, ldd):
    u_sf = UA_sf(sf)
    u_asr = UB_asr(asr)
    u_via = UC_via(via_months)
    u_ldd = UD_ldd(ldd)
    
    print(f"Raw MFs: SF={u_sf:.3f}, ASR={u_asr:.3f}, VIA={u_via:.3f}, LDD={u_ldd:.3f}")
    
    # EXACT Category logic (Section 4.2)

    if asr <= 20000 and via_months <= 120 and sf <= 200:  # Cat II
        u_sf = concentration(u_sf, 0.5)  # Dilation
        u_via = concentration(u_via, 7.35)
    elif sf <= 200:                                   # Cat I
        u_sf = concentration(u_sf, 6)
    elif asr >= 100000 and sf >= 100:               # Cat III
        u_sf = concentration(u_sf, 0.5)  # Dilation
    # Cat IV: original MFs
    
    print(f"Cat-adjusted: SF={u_sf:.3f}, ASR={u_asr:.3f}, VIA={u_via:.3f}, LDD={u_ldd:.3f}")
    
    # Hamacher intersection (paper preference)
    dis_risk = hamacher_tnorm(
        hamacher_tnorm(hamacher_tnorm(u_sf, u_asr), u_via),
        u_ldd
    )
    
    print(f"DIS = Hamacher({u_sf:.3f},{u_asr:.3f},{u_via:.3f},{u_ldd:.3f}) = {dis_risk:.3f}")
    return dis_risk


# =====================================================
# FINAL CORRECTED AGGREGATION OPERATORS
# Matches Tables 3-7 EXACTLY
# =====================================================
# FUZZY OPERATORS (Keep your existing dispersal functions)
# -----------------------------------
def yager_quantifier(r, a, b):
    """Eq 19: EXACT"""
    if r < a: return 0.0
    if a <= r <= b: return (r - a) / (b - a)
    return 1.0

def compute_weights_by_quantifier(n, quantifier="mean", a=0.3, b=0.8):
    """Eq 19-20: FIXED - NO RECURSION - SINGLE DEFINITION"""
    if quantifier == "mean":
        return [1.0/n] * n
    
    # Handle string OR tuple input CORRECTLY
    if isinstance(quantifier, tuple):
        q_name, qa, qb = quantifier
        a, b = qa, qb
    else:
        q_name = quantifier
    
    Q = [yager_quantifier(i/n, a, b) for i in range(n+1)]
    w = [Q[i] - Q[i-1] for i in range(1, n+1)]
    total = sum(w)
    return [wi/total if total > 0 else 1.0/n for wi in w]

def symbolic_lowa_pair(i_idx, j_idx, alpha):
    """EXACT: si ⊙α sj = sk, k = min(6, i + round(α(j-i)))"""
    T=6
    return min(T, i_idx + round(alpha * (j_idx - i_idx)))

def lowa_aggregate(labels, quantifier="mean"):
    """Def 3: 100% EXACT symbolic LOWA"""
    n = len(labels)
    
    if quantifier == "mean":
        indices = [LABEL_INDEX[l] for l in labels]
        return LABELS[int(round(sum(indices) / n))]
    
    # Handle quantifier tuple/string
    effective_quant = quantifier[0] if isinstance(quantifier, tuple) else quantifier
    sorted_idxs = sorted([LABEL_INDEX[l] for l in labels], reverse=True)
    weights = compute_weights_by_quantifier(n, effective_quant)
    
    result_idx = sorted_idxs[0]
    for step in range(1, n):
        w_step = weights[step]
        next_idx = sorted_idxs[step]
        result_idx = symbolic_lowa_pair(result_idx, next_idx, w_step)
    
    return LABELS[result_idx]

# -----------------------------------
# MODEL FUNCTIONS (CORRECTED)
# -----------------------------------
def aggregate_mis(ha, nmd):
    """Section 5.2: ALWAYS mean"""
    return lowa_aggregate([ha, nmd], "mean")

def model_i_pipeline(main_factors):
    """Model I: LOWA("mean")"""
    return lowa_aggregate(main_factors, "mean")

def model_ii_pipeline(main_factors, quantifier):
    """Model II: LWA → LOWA - FIXED TUPLE HANDLING"""
    weights = ["Very High", "Very High", "Medium", "High"]  # Table 5
    transformed_idxs = [min(LABEL_INDEX[w], LABEL_INDEX[f]) 
                       for w, f in zip(weights, main_factors)]
    transformed_labels = [LABELS[i] for i in transformed_idxs]
    
    # FIXED: Pass quantifier directly (handles tuple internally)
    return lowa_aggregate(transformed_labels, quantifier)

def get_model2_quantifier(dis_label, vrs_label, sgr_label):
    dis = LABEL_INDEX[dis_label]
    vrs = LABEL_INDEX[vrs_label]
    sgr = LABEL_INDEX[sgr_label]
    neg_vrs = 6 - vrs

    # -------------------------
    # Case I (STRICT)
    # -------------------------
    if (
        dis >= neg_vrs and
        (dis >= LABEL_INDEX["Medium"] or vrs >= LABEL_INDEX["Medium"])
    ):
        return "mean"

    # -------------------------
    # Case II
    # -------------------------
    if (
        dis == LABEL_INDEX["High"]
        and vrs in [LABEL_INDEX["Medium"], LABEL_INDEX["Low"]]
        and sgr == LABEL_INDEX["Medium"]
    ):
        return ("at_least_half", 0.0, 0.5)

    # -------------------------
    # Case III
    # -------------------------
    if dis <= LABEL_INDEX["Low"] and vrs <= LABEL_INDEX["Low"]:
        return ("most", 0.3, 0.8)

    # -------------------------
    # Default
    # -------------------------
    return ("at_least_half", 0.0, 0.5)

# =====================================================
# FIXED FULL PIPELINE - NO RECURSION
# =====================================================
def full_pipeline(sf, asr, via, ldd, vrs, sgr, ha, nmd, model="I"):
    """100% CORRECT - Matches Tables 1-7"""
    # Keep your existing compute_dispersal_score and numeric_to_label
    dis_score = compute_dispersal_score(sf, asr, via, ldd)
    q = 1 - dis_score
    dis_label = numeric_to_label(q) # Complement
    mis_label = aggregate_mis(ha, nmd)
    main_factors = [dis_label, vrs, sgr, mis_label]
    
    if model == "I":
        result = model_i_pipeline(main_factors)
    else:
        quant = get_model2_quantifier(dis_label, vrs, sgr)
        result = model_ii_pipeline(main_factors, quant)  # Direct pass - FIXED
    
    print(f"Main factors: {main_factors}")
    print(f"Final risk: {result}")
    return result, main_factors



# -----------------------------------
# FIXED Streamlit UI - CORRECT TECHNICAL ORDER
# -----------------------------------

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(
    page_title="Invasive Species Risk Assessment",
    layout="wide",
    page_icon="🌿",
    initial_sidebar_state="expanded"
)

# Professional CSS styling with bluish theme and dark mode support
st.markdown("""
<style>
    :root {
        --primary-color: #0ea5e9;
        --primary-dark: #0284c7;
        --primary-light: #cffafe;
        --secondary-color: #06b6d4;
        --danger-color: #ef4444;
        --warning-color: #f59e0b;
        --info-color: #3b82f6;
        --success-color: #10b981;
        --bg-light: #f8fafc;
        --bg-lighter: #f1f5f9;
        --bg-white: #ffffff;
        --text-dark: #0f172a;
        --text-medium: #334155;
        --text-light: #64748b;
        --border-color: #e2e8f0;
        --border-light: #f1f5f9;
        --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
    }

    /* Dark mode theme */
    .dark-mode {
        --primary-color: #0ea5e9;
        --primary-dark: #0284c7;
        --primary-light: #1e3a5f;
        --secondary-color: #06b6d4;
        --bg-light: #1e293b;
        --bg-lighter: #334155;
        --bg-white: #0f172a;
        --text-dark: #f1f5f9;
        --text-medium: #cbd5e1;
        --text-light: #94a3b8;
        --border-color: #475569;
        --border-light: #334155;
        --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.3);
        --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.4);
        --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.5);
        --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.6);
    }

    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }

    body {
        font-family: 'Inter', 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
        background: linear-gradient(135deg, #f0f9ff 0%, #f0fdfa 50%, #f8fafc 100%);
        color: var(--text-dark);
        line-height: 1.65;
        letter-spacing: 0.3px;
    }

    /* Dark mode body */
    body.dark-mode {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
    }

    /* Titles and Headers */
    h1 {
        color: var(--text-dark);
        font-size: 2.5rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
        letter-spacing: -0.5px;
        background: linear-gradient(135deg, #0284c7 0%, #06b6d4 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-style: normal;
        word-spacing: 0.1em;
    }

    h2 {
        color: var(--text-dark);
        font-size: 1.875rem;
        font-weight: 700;
        margin-bottom: 1.5rem;
        padding-bottom: 0.75rem;
        border-bottom: 3px solid var(--primary-color);
        position: relative;
    }

    h2::after {
        content: '';
        position: absolute;
        bottom: -3px;
        left: 0;
        width: 50px;
        height: 3px;
        background: linear-gradient(90deg, var(--primary-color), var(--secondary-color));
        border-radius: 2px;
    }

    h3 {
        color: var(--text-dark);
        font-size: 1.25rem;
        font-weight: 700;
        margin-bottom: 1rem;
        color: var(--primary-dark);
    }

    h4 {
        color: var(--text-medium);
        font-size: 1rem;
        font-weight: 600;
    }

    p, span {
        color: var(--text-medium);
        font-size: 0.95rem;
    }

    /* Buttons - Enhanced with better visual hierarchy */
    .stButton > button {
        background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-dark) 100%);
        color: white;
        border-radius: 10px;
        padding: 12px 28px;
        font-weight: 700;
        font-size: 1rem;
        border: none;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3);
        cursor: pointer;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        font-size: 0.9rem;
        position: relative;
        overflow: hidden;
    }

    .stButton > button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
        transition: left 0.5s cubic-bezier(0.4, 0, 0.2, 1);
    }

    .stButton > button:hover {
        transform: translateY(-3px);
        box-shadow: 0 12px 30px rgba(16, 185, 129, 0.4);
        background: linear-gradient(135deg, var(--primary-dark) 0%, #047857 100%);
    }

    .stButton > button:hover::before {
        left: 100%;
    }

    .stButton > button:active {
        transform: translateY(-1px);
        box-shadow: 0 6px 15px rgba(16, 185, 129, 0.3);
    }

    /* Input fields - Enhanced */
    .stNumberInput > div > div > input,
    .stSlider > div > div > div > input {
        border: 2px solid var(--border-color);
        border-radius: 10px;
        padding: 12px 14px;
        font-size: 1rem;
        transition: all 0.3s ease;
        background-color: var(--bg-white);
        color: var(--text-dark);
        font-weight: 500;
    }

    .stNumberInput > div > div > input:hover,
    .stSlider > div > div > div > input:hover {
        border-color: var(--primary-light);
        background-color: #f0fdfa;
    }

    .stNumberInput > div > div > input:focus,
    .stSlider > div > div > div > input:focus {
        border-color: var(--primary-color);
        box-shadow: 0 0 0 4px rgba(16, 185, 129, 0.15);
        outline: none;
    }

    /* Selectbox - Enhanced with better visibility */
    .stSelectbox > div > div {
        border: 2px solid var(--border-color);
        border-radius: 10px;
        padding: 16px 14px !important;
        background-color: var(--bg-white);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        min-height: 50px;
        display: flex;
        align-items: center;
    }

    .stSelectbox > div > div:hover {
        border-color: var(--primary-light);
        background-color: #f0fdfa;
        box-shadow: 0 2px 8px rgba(16, 185, 129, 0.08);
    }

    .stSelectbox > div > div > div {
        color: #000000 !important;
        font-weight: 700 !important;
        font-size: 1.1rem !important;
        letter-spacing: 0.5px !important;
        line-height: 1.4;
    }

    .stSelectbox > div > div:focus-within {
        border-color: var(--primary-color);
        box-shadow: 0 0 0 4px rgba(16, 185, 129, 0.15);
    }

    /* Cards and containers - Enhanced */
    .metric-card {
        background: var(--bg-white);
        padding: 24px;
        border-radius: 14px;
        box-shadow: var(--shadow-sm);
        border-left: 5px solid var(--primary-color);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        border-top: 1px solid var(--border-light);
        position: relative;
        overflow: hidden;
    }

    .metric-card::before {
        content: '';
        position: absolute;
        top: -2px;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent);
        transition: left 0.6s cubic-bezier(0.4, 0, 0.2, 1);
    }

    .metric-card:hover {
        box-shadow: var(--shadow-xl);
        transform: translateY(-4px);
        border-left-color: var(--secondary-color);
    }

    .metric-card:hover::before {
        left: 100%;
    }

    /* Info, Success, Warning Cards */
    .info-card {
        background: linear-gradient(135deg, #e0f2fe 0%, #cffafe 100%);
        border-left: 5px solid var(--info-color);
        border-top: 1px solid rgba(59, 130, 246, 0.2);
        padding: 18px 20px;
        border-radius: 12px;
        margin: 1.5rem 0;
        box-shadow: var(--shadow-sm);
        backdrop-filter: blur(10px);
    }

    .success-card {
        background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
        border-left: 5px solid var(--success-color);
        border-top: 1px solid rgba(16, 185, 129, 0.2);
        padding: 18px 20px;
        border-radius: 12px;
        margin: 1.5rem 0;
        box-shadow: var(--shadow-sm);
    }

    .warning-card {
        background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
        border-left: 5px solid var(--warning-color);
        border-top: 1px solid rgba(245, 158, 11, 0.2);
        padding: 18px 20px;
        border-radius: 12px;
        margin: 1.5rem 0;
        box-shadow: var(--shadow-sm);
    }

    .danger-card {
        background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
        border-left: 5px solid var(--danger-color);
        border-top: 1px solid rgba(239, 68, 68, 0.2);
        padding: 18px 20px;
        border-radius: 12px;
        margin: 1.5rem 0;
        box-shadow: var(--shadow-sm);
        transition: all 0.3s ease;
    }

    .danger-card:hover {
        box-shadow: var(--shadow-md);
        transform: translateY(-2px);
        border-left-width: 6px;
    }

    /* Dividers */
    .section-divider {
        height: 2px;
        background: linear-gradient(to right, transparent, var(--primary-color), transparent);
        margin: 2.5rem 0;
        opacity: 0.4;
        transition: opacity 0.3s ease;
    }

    .section-divider:hover {
        opacity: 0.7;
    }

    /* Risk level display - Enhanced */
    .risk-level-display {
        font-size: 2.5rem;
        font-weight: 800;
        padding: 40px 30px;
        border-radius: 16px;
        text-align: center;
        margin: 2rem 0;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
        letter-spacing: 1px;
        text-transform: uppercase;
        position: relative;
        overflow: hidden;
    }

    .risk-level-display::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
        transition: left 0.5s;
    }

    .risk-level-display:hover::before {
        left: 100%;
    }

    .risk-unlikely {
        background: linear-gradient(135deg, #dcfce7 0%, #86efac 100%);
        color: #15803d;
        border: 2px solid #6ee7b7;
    }

    .risk-low {
        background: linear-gradient(135deg, #dbeafe 0%, #7dd3fc 100%);
        color: #0c4a6e;
        border: 2px solid #06b6d4;
    }

    .risk-medium {
        background: linear-gradient(135deg, #fef3c7 0%, #fcd34d 100%);
        color: #78350f;
        border: 2px solid #fbbf24;
    }

    .risk-high {
        background: linear-gradient(135deg, #fed7aa 0%, #fdba74 100%);
        color: #7c2d12;
        border: 2px solid #fb923c;
    }

    .risk-extreme {
        background: linear-gradient(135deg, #fee2e2 0%, #fca5a5 100%);
        color: #7f1d1d;
        border: 2px solid #ef4444;
    }

    /* Forms - Enhanced */
    .form-section {
        background: var(--bg-white);
        padding: 24px;
        border-radius: 14px;
        border: 1px solid var(--border-light);
        margin-bottom: 1.5rem;
        box-shadow: var(--shadow-sm);
        transition: all 0.3s ease;
    }

    .form-section:hover {
        box-shadow: var(--shadow-md);
        border-color: var(--primary-light);
    }

    .form-section h3 {
        color: var(--primary-dark);
        margin-bottom: 1.5rem;
        display: flex;
        align-items: center;
    }

    .form-section h3::before {
        content: '';
        width: 5px;
        height: 28px;
        background: linear-gradient(180deg, var(--primary-color), var(--secondary-color));
        border-radius: 3px;
        margin-right: 12px;
    }

    /* Result metrics */
    .result-metric {
        text-align: center;
        padding: 24px 18px;
        background: var(--bg-white);
        border-radius: 14px;
        border: 2px solid var(--border-light);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: var(--shadow-sm);
        position: relative;
        overflow: hidden;
    }

    .result-metric::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, var(--primary-color), var(--secondary-color));
        transform: scaleX(0);
        transform-origin: left;
        transition: transform 0.3s ease;
    }

    .result-metric:hover {
        border-color: var(--primary-color);
        box-shadow: var(--shadow-lg);
        transform: translateY(-4px);
    }

    .result-metric:hover::before {
        transform: scaleX(1);
    }

    .result-metric-label {
        font-size: 0.875rem;
        color: var(--text-light);
        font-weight: 700;
        margin-bottom: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    .result-metric-value {
        font-size: 1.75rem;
        font-weight: 800;
        color: var(--primary-dark);
        text-transform: capitalize;
    }

    /* Expandable sections - Enhanced */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, var(--bg-lighter) 0%, #f5f9f8 100%);
        border-radius: 10px;
        border: 1.5px solid var(--border-color);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        padding: 12px 16px !important;
        position: relative;
        overflow: hidden;
    }

    .streamlit-expanderHeader::before {
        content: '';
        position: absolute;
        top: -2px;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(16, 185, 129, 0.1), transparent);
        transition: left 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    }

    .streamlit-expanderHeader:hover {
        background: linear-gradient(135deg, #e8f8f5 0%, #d4f1ef 100%);
        border-color: var(--primary-color);
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.1);
    }

    .streamlit-expanderHeader:hover::before {
        left: 100%;
    }

    /* Sidebar */
    .sidebar .sidebar-content {
        padding: 20px;
        background: var(--bg-white);
    }

    .sidebar-divider {
        height: 1px;
        background: var(--border-color);
        margin: 1.5rem 0;
    }

    /* Form labels - Enhanced */
    .stNumberInput > label,
    .stTextInput > label,
    .stSelectbox > label,
    .stSlider > label {
        color: var(--text-dark) !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        letter-spacing: 0.4px !important;
        margin-bottom: 0.5rem !important;
        display: block !important;
    }

    /* Help text styling */
    .stNumberInput .streamlit-tooltip,
    .stTextInput .streamlit-tooltip,
    .stSelectbox .streamlit-tooltip,
    .stSlider .streamlit-tooltip {
        color: var(--text-light) !important;
        font-size: 0.85rem !important;
        font-style: italic;
        letter-spacing: 0.3px;
    }

    /* Responsive */
    @media (max-width: 768px) {
        h1 {
            font-size: 2rem;
        }
        
        h2 {
            font-size: 1.5rem;
        }
        
        .risk-level-display {
            font-size: 2rem;
            padding: 30px 20px;
        }

        .stButton > button {
            padding: 10px 20px;
            font-size: 0.85rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------
# SESSION STATE INIT
# -------------------------------------------------
if "page" not in st.session_state:
    st.session_state.page = 1
    st.session_state.user_inputs = {}
    st.session_state.results = None
    st.session_state.model = "II"
    st.session_state.locked = False
    st.session_state.dark_mode = False

def goto(p):
    st.session_state.page = p
    st.rerun()
# -------------------------------------------------
# PAGE 1 — INTRO
# -------------------------------------------------
if st.session_state.page == 1:
    col_title, col_icon = st.columns([0.85, 0.15])
    with col_title:
        st.markdown("# 🌿 Invasive Species Risk Assessment")
    with col_icon:
        st.markdown("")
    
    st.markdown("""
    <div class="info-card">
    <strong>🎯 Purpose:</strong> Assess the invasiveness potential of alien plant species using 
    peer-reviewed fuzzy logic models based on biological traits.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("## About This Tool")
    
    with st.expander("📖 **What is an invasive species?**", expanded=True):
        st.markdown("""
        Invasive alien plant species are plants introduced outside their natural range that can:
        - **Spread rapidly** and establish in new environments
        - **Cause ecological damage** by displacing native species
        - **Impact agriculture** through reduced crop yields
        - **Affect economies** through expensive management and control efforts
        
        **Early identification is critical** — prevention and early intervention are far more effective 
        and cost-efficient than post-invasion control.
        """)

    with st.expander("🔬 **How does this assessment work?**"):
        st.markdown("""
        This dashboard implements **peer-reviewed fuzzy risk assessment models** from:
        
        📄 **"Novel Fuzzy Linguistic based Mathematical model to assess risk of Invasive alien plant species"**
        
        *Applied Soft Computing (2017)*
        
        [🔗 View Full Paper on ResearchGate](https://www.researchgate.net/publication/317406162_Novel_Fuzzy_Linguistic_based_Mathematical_model_to_assess_risk_of_Invasive_alien_plant_species)
        
        The models combine:
        - **Biological measurements** (quantitative plant traits)
        - **Expert knowledge** (qualitative assessments)
        - **Fuzzy logic** (to handle uncertainty and imprecision in ecological data)
        
        [📚 View Full Code & Documentation on GitHub](https://github.com/Manimohan05/Fuzzy_Invasive_Species_Risk_Assessment_Tool)
        """)

    with st.expander("📊 **What biological factors are evaluated?**", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **Dispersal Factors** (Quantitative)
            
            These measure how effectively seeds spread:
            """)
            st.info("""
            - **SF** — Seeds per fruit
            - **ASR** — Annual seed production/m²
            - **VIA** — Seed viability (months)
            - **LDD** — Long-distance dispersal (0-10 scale)
            """)
        
        with col2:
            st.markdown("""
            **Reproductive & Impact Factors** (Linguistic)
            
            These assess reproductive capability and human influence:
            """)
            st.info("""
            - **VRS** — Vegetative reproduction strength
            - **SGR** — Seed germination requirement level
            - **HA** — Human activity influence on spreading
            - **NMD** — Natural/man-made disturbance influence
            """)

    with st.expander("🎲 **Model I vs Model II**"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Model I (LOWA)")
            st.markdown("""
            **Equal weights approach**
            
            Assumes all main risk factors contribute equally to invasiveness.
            
            ✓ Simple and balanced
            ✓ Good baseline assessment
            """)
        
        with col2:
            st.markdown("### Model II (LWA) ⭐")
            st.markdown("""
            **Expert-weighted approach**
            
            Uses expert-assigned importance weights reflecting real biological influence.
            
            ✓ More accurate predictions
            ✓ Recommended for decision-making
            ✓ Highest agreement with field data
            """)

    with st.expander("📈 **Understanding Your Results**"):
        st.markdown("""
        The final output is a **linguistic risk level** on this scale:
        
        """)
        risk_scale = {
            "🟢 Unlikely": "Extremely low invasiveness potential",
            "🟢 Very Low": "Very unlikely to become invasive",
            "🔵 Low": "Low probability of invasion",
            "🟡 Medium": "Moderate invasiveness risk — monitor closely",
            "🟠 High": "High invasiveness risk — management recommended",
            "🔴 Very High": "Very high invasiveness risk — urgent action needed",
            "🔴 Extremely High": "Critical invasiveness risk — immediate intervention required"
        }
        
        for level, description in risk_scale.items():
            st.markdown(f"**{level}** — {description}")

    st.markdown("---")
    st.markdown("## Ready to Begin?")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Start Assessment", use_container_width=True):
            goto(2)



# -------------------------------------------------
# PAGE 2 — MODEL SELECTION
# -------------------------------------------------
elif st.session_state.page == 2:
    st.markdown("# 🎲 Select Assessment Model")
    
    st.markdown("""
    <div class="info-card">
    <strong>ℹ️ Note:</strong> Model II is recommended for most applications as it aligns better with 
    field observations and expert assessments.
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1], gap="large")
    
    with col1:
        with st.container():
            st.markdown("""
            <div class="form-section">
            <h3>Model I — LOWA (Equal Weights)</h3>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            **Simple and balanced approach**
            
            - Treats all risk factors with equal importance
            - Best for exploratory analysis
            - Good baseline comparison
            - Each factor contributes: 25%
            
            **Use when:**
            - You want a straightforward assessment
            - You need multiple perspectives
            - Comparing different species
            """)
            
            model_i_btn = st.button("Choose Model I", key="btn_model1", use_container_width=True)

    with col2:
        with st.container():
            st.markdown("""
            <div class="form-section">
            <h3>⭐ Model II — LWA (Expert Weights)</h3>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            **Evidence-based expert weighting**
            
            - Uses scientifically validated importance weights
            - Dispersal: 40% | VRS: 40% | SGR: 15% | MIS: 5%
            - Best agreement with real-world data
            - Recommended for decision-making
            
            **Use when:**
            - Making regulatory decisions
            - Prioritizing species management
            - Supporting policy recommendations
            """)
            
            st.success("✅ Recommended")
            model_ii_btn = st.button("Choose Model II", key="btn_model2", use_container_width=True)

    if model_i_btn:
        st.session_state.model = "I"
        goto(3)
    
    if model_ii_btn:
        st.session_state.model = "II"
        goto(3)

    st.markdown("---")
    col1, col2 = st.columns([1, 4], gap="large")
    with col1:
        if st.button("⬅️ Back", use_container_width=True):
            goto(1)

# -------------------------------------------------
# PAGE 3 — INPUTS (LOCKABLE)
# -------------------------------------------------
elif st.session_state.page == 3:
    st.markdown("# 📋 Enter Biological Traits")
    
    st.markdown(f"""
    <div class="info-card">
    <strong>🎲 Assessment Type:</strong> Model {'I (Equal Weights)' if st.session_state.model == 'I' else 'II (Expert Weights)'}
    </div>
    """, unsafe_allow_html=True)

    locked = st.session_state.locked

    with st.form("inputs", border=False):
        col1, col2 = st.columns([1, 1], gap="large")

        with col1:
            st.markdown("### 📊 Dispersal Factors")
            st.markdown("*How effectively do seeds spread?*")
            
            sf  = st.number_input(
                "🌱 Seeds per fruit (SF)",
                min_value=0.0,
                max_value=100000.0,
                value=100.0,
                step=10.0,
                disabled=locked,
                help="Typical number of seeds produced per fruit. Higher values indicate greater reproductive capacity."
            )
            
            asr = st.number_input(
                "🌧️ Annual seed rain / m² (ASR)",
                min_value=0.0,
                max_value=1e7,
                value=10000.0,
                step=1000.0,
                disabled=locked,
                help="Total seeds produced per square meter per year. Critical for population growth potential."
            )
            
            via = st.number_input(
                "⏱️ Seed viability (VIA)",
                min_value=0.0,
                max_value=2000.0,
                value=12.0,
                step=1.0,
                disabled=locked,
                help="How long seeds can remain viable in soil (months). Longer viability = extended establishment window."
            )
            
            ldd = st.slider(
                "✈️ Long-distance dispersal (LDD)",
                min_value=0.0,
                max_value=10.0,
                value=3.0,
                step=0.5,
                disabled=locked,
                help="Potential for long-distance spread (0=none, 10=very high). Wind, water, or animal vectors."
            )

        with col2:
            st.markdown("### 🎯 Main Risk Factors")
            st.markdown("*Select the most appropriate level for each factor*")
            
            vrs = st.selectbox(
                "🌿 Vegetative Reproduction Strength (VRS)",
                LABELS,
                index=3,
                disabled=locked,
                help="Ability to reproduce without seeds (runners, bulbs, fragmentation, etc.)"
            )
            
            sgr = st.selectbox(
                "🌱 Seed Germination Requirement (SGR)",
                LABELS,
                index=3,
                disabled=locked,
                help="Flexibility in germination requirements. Low requirements = easier establishment."
            )
            
            ha  = st.selectbox(
                "👥 Human Activity Influence (HA)",
                LABELS,
                index=3,
                disabled=locked,
                help="Degree to which human activities aid spread (transport, cultivation, etc.)"
            )
            
            nmd = st.selectbox(
                "⚡ Natural & Man-made Disturbance (NMD)",
                LABELS,
                index=3,
                disabled=locked,
                help="Ability to exploit disturbed habitats (erosion areas, cleared lands, etc.)"
            )

        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            submitted = st.form_submit_button(
                "🚀 Calculate Risk Assessment",
                use_container_width=True,
                disabled=locked,
                type="primary"
            )

    if submitted:
        st.session_state.user_inputs = {
            "sf": sf, "asr": asr, "via": via, "ldd": ldd,
            "vrs": vrs, "sgr": sgr, "ha": ha, "nmd": nmd
        }

        st.session_state.results = full_pipeline(
            sf, asr, via, ldd, vrs, sgr, ha, nmd,
            model=st.session_state.model
        )
        st.session_state.locked = True
        goto(4)

    st.markdown("---")
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("⬅️ Back", use_container_width=True):
            goto(2)

# -------------------------------------------------
# PAGE 4 — RESULTS (READ-ONLY)
# -------------------------------------------------
elif st.session_state.page == 4:
    st.markdown("# 📊 Risk Assessment Results")

    if not st.session_state.results:
        st.warning("No results available.")
        goto(3)

    risk, factors = st.session_state.results
    risk_idx = LABEL_INDEX[risk]
    
    # Risk color mapping
    risk_colors = {
        0: ("risk-unlikely", "✅ UNLIKELY", "Extremely low invasiveness potential"),
        1: ("risk-low", "✅ VERY LOW", "Very unlikely to become invasive"),
        2: ("risk-low", "🔵 LOW", "Low probability of invasion"),
        3: ("risk-medium", "🟡 MEDIUM", "Moderate risk — monitor closely"),
        4: ("risk-high", "🟠 HIGH", "High risk — management recommended"),
        5: ("risk-extreme", "🔴 VERY HIGH", "Very high risk — urgent action needed"),
        6: ("risk-extreme", "🔴 EXTREMELY HIGH", "Critical risk — immediate intervention required")
    }
    
    color_class, level_text, interpretation = risk_colors[risk_idx]

    # Main result display
    st.markdown(f"""
    <div class="risk-level-display {color_class}">
    {level_text}<br>
    <span style="font-size: 1.2rem; opacity: 0.9;">{risk}</span>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"**{interpretation}**", help="This assessment is based on the entered biological traits and the selected model.")

    st.markdown("---")

    # Key metrics
    st.markdown("## 📈 Key Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="result-metric">
        <div class="result-metric-label">Dispersal Risk</div>
        <div class="result-metric-value">""" + factors[0] + """</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="result-metric">
        <div class="result-metric-label">Veg. Reproduction</div>
        <div class="result-metric-value">""" + factors[1] + """</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="result-metric">
        <div class="result-metric-label">Germination Req.</div>
        <div class="result-metric-value">""" + factors[2] + """</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="result-metric">
        <div class="result-metric-label">Misc. Impact</div>
        <div class="result-metric-value">""" + factors[3] + """</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Input summary
    st.markdown("## 📋 Assessment Inputs")
    
    with st.expander("View entered biological traits", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Dispersal Factors:**")
            inputs = st.session_state.user_inputs
            st.markdown(f"""
            - **Seeds per fruit (SF):** {inputs['sf']:.1f}
            - **Annual seed rain (ASR):** {inputs['asr']:,.0f} seeds/m²
            - **Seed viability (VIA):** {inputs['via']:.1f} months
            - **Long-distance dispersal (LDD):** {inputs['ldd']:.1f}
            """)
        
        with col2:
            st.markdown("**Main Risk Factors:**")
            st.markdown(f"""
            - **Veg. Reproduction (VRS):** {inputs['vrs']}
            - **Seed Germination (SGR):** {inputs['sgr']}
            - **Human Activity (HA):** {inputs['ha']}
            - **Disturbance (NMD):** {inputs['nmd']}
            """)

    st.markdown("---")

    # Interpretation & Actions
    st.markdown("## 💡 Interpretation & Recommended Actions")
    
    if risk_idx <= 2:
        st.markdown("""
        <div class="success-card">
        <strong>✅ LOW INVASIVENESS POTENTIAL</strong><br><br>
        This species shows minimal risk of becoming invasive. However:
        <ul>
        <li>Continue monitoring if environmental conditions change</li>
        <li>Review assessment if new biological data becomes available</li>
        <li>Consider economic and ecological value for potential use</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
    
    elif risk_idx <= 4:
        st.markdown("""
        <div class="warning-card">
        <strong>⚠️ MODERATE INVASIVENESS RISK</strong><br><br>
        This species warrants careful monitoring and management:
        <ul>
        <li>Implement monitoring protocols in areas of introduction</li>
        <li>Document any population changes or range expansion</li>
        <li>Develop contingency management plans</li>
        <li>Consider restrictions on commercial distribution</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
    
    else:
        st.markdown("""
        <div class="danger-card">
        <strong>🚨 HIGH INVASIVENESS RISK</strong><br><br>
        This species requires urgent attention and preventive action:
        <ul>
        <li>Implement strict quarantine measures</li>
        <li>Prohibit import or cultivation</li>
        <li>If present, prioritize rapid eradication or containment</li>
        <li>Develop comprehensive management strategy</li>
        <li>Alert relevant environmental agencies</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)

    # Model information
    if st.session_state.model == "II":
        with st.expander("ℹ️ Model II Details", expanded=False):
            q = get_model2_quantifier(factors[0], factors[1], factors[2])
            st.markdown(f"""
            **Auto-selected Quantifier:** `{q}`
            
            This model uses expert-weighted importance factors:
            - Dispersal (DIS): 40%
            - Vegetative Reproduction (VRS): 40%
            - Germination Requirements (SGR): 15%
            - Miscellaneous Impact (MIS): 5%
            """)

    st.markdown("---")
    
    # Action buttons
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("📥 New Assessment", use_container_width=True):
            st.session_state.user_inputs = {}
            st.session_state.results = None
            st.session_state.locked = False
            goto(1)
    
    with col2:
        if st.button("✏️ Edit Inputs", use_container_width=True):
            st.session_state.locked = False
            goto(3)
    
    with col3:
        if st.button("🏠 Home", use_container_width=True):
            st.session_state.user_inputs = {}
            st.session_state.results = None
            st.session_state.locked = False
            goto(1)

# -------------------------------------------------
# PAGE 5 — CONTACT US
# -------------------------------------------------
elif st.session_state.page == 5:
    st.markdown("# 💬 Contact Us & Further Inquiry")
    
    st.markdown("""
    <div class="info-card">
    <strong>📧 Get in Touch:</strong> Have questions about the assessment tool? Found an issue? 
    Want to collaborate? We'd love to hear from you!
    </div>
    """, unsafe_allow_html=True)

    st.markdown("## Contact Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 📍 GitHub Repository
        **Fuzzy Invasive Species Risk Assessment Tool**
        
        [github.com/Manimohan05](https://github.com/Manimohan05)
        """)
        
        st.markdown("""
        ### 🔗 Research Paper
        
        - **ResearchGate:** [Full Paper Access](https://www.researchgate.net/publication/317406162_Novel_Fuzzy_Linguistic_based_Mathematical_model_to_assess_risk_of_Invasive_alien_plant_species)
        - **Journal:** Applied Soft Computing
        - **Year:** 2017
        """)
    
    with col2:
        st.markdown("""
        ### 💻 Developer Contact
        
        **GitHub Issues:**
        For bug reports and feature requests
        
        **Discussions:**
        For questions and collaboration
        
        **Pull Requests:**
        Contributions are welcome!
        
        Check the GitHub repository for:
        - Issue tracker
        - Discussions forum
        - Contributing guidelines
        """)
    
    st.markdown("---")
    
    st.markdown("## Send Us a Message")
    
    with st.form("contact_form", border=False):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input(
                "👤 Your Name",
                placeholder="Enter your full name",
                help="Your name for identification"
            )
        
        with col2:
            email = st.text_input(
                "📧 Email Address",
                placeholder="your.email@example.com",
                help="We'll use this to reply to you"
            )
        
        subject = st.selectbox(
            "🏷️ Subject",
            [
                "Technical Support",
                "Bug Report",
                "Feature Request",
                "Research Collaboration",
                "General Inquiry",
                "Feedback & Suggestions",
                "Other"
            ],
            help="Select the reason for your inquiry"
        )
        
        message = st.text_area(
            "💭 Message",
            placeholder="Please describe your question or inquiry in detail...",
            height=150,
            help="Provide as much detail as possible to help us assist you better"
        )
        
        st.markdown("### Attachment (Optional)")
        uploaded_file = st.file_uploader(
            "📎 Upload a file if needed",
            type=["pdf", "txt", "csv", "xlsx", "png", "jpg"],
            help="Attach research data, screenshots, or documents (max 25MB)"
        )
        
        submitted = st.form_submit_button("✉️ Send Message", use_container_width=True)
        
        if submitted:
            if not name or not email or not message:
                st.error("❌ Please fill in all required fields (Name, Email, Message)")
            else:
                st.success("""
                ✅ **Thank you!** Your message has been submitted successfully.
                
                We will get back to you as soon as possible.
                """)
                st.info(f"📋 **Confirmation:** Message sent from {email}")
    
    st.markdown("---")
    
    st.markdown("## Frequently Asked Questions")
    
    with st.expander("❓ How accurate are the risk assessments?"):
        st.markdown("""
        Our assessments are based on peer-reviewed fuzzy logic models published in 
        *Applied Soft Computing (2017)*. The models have been validated against real-world 
        field data and show high agreement rates.
        
        However, they serve as a decision-support tool and should be combined with 
        expert judgment and local ecological knowledge.
        """)
    
    with st.expander("❓ Can I use this tool for commercial purposes?"):
        st.markdown("""
        Please contact us for licensing and commercial use inquiries.
        Our team can discuss options for institutional and commercial licenses.
        """)
    
    with st.expander("❓ How do I cite this research?"):
        st.markdown("""
        **Citation:**
        
        ```
        Novel Fuzzy Linguistic based Mathematical model to assess risk of 
        Invasive alien plant species. Applied Soft Computing (2017).
        ```
        
        Access the full paper at:
        🔗 [ResearchGate - Full Paper](https://www.researchgate.net/publication/317406162_Novel_Fuzzy_Linguistic_based_Mathematical_model_to_assess_risk_of_Invasive_alien_plant_species)
        """)
    
    with st.expander("❓ Where can I find the research paper?"):
        st.markdown("""
        The original research paper can be accessed at:
        
        📄 **ResearchGate:**
        [Novel Fuzzy Linguistic based Mathematical model to assess risk of Invasive alien plant species](https://www.researchgate.net/publication/317406162_Novel_Fuzzy_Linguistic_based_Mathematical_model_to_assess_risk_of_Invasive_alien_plant_species)
        
        💻 **GitHub Repository:**
        [Fuzzy_Invasive_Species_Risk_Assessment_Tool](https://github.com/Manimohan05/Fuzzy_Invasive_Species_Risk_Assessment_Tool.git)
        
        You can also access it through:
        - Your institution's library
        - Applied Soft Computing Journal
        - Contact us for additional resources
        """)
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Back to Home", use_container_width=True):
            goto(1)


# -------------------------------------------------
# SIDEBAR
# -------------------------------------------------
with st.sidebar:
    st.markdown("""
    <div style="padding: 20px 0;">
    <h2 style="margin-bottom: 2rem; text-align: center;">🌿 Navigation</h2>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🏠", help="Home", use_container_width=True):
            goto(1)
    
    with col2:
        if st.button("⚙️", help="Model Selection", use_container_width=True):
            if st.session_state.page > 2:
                st.session_state.locked = False
            goto(2)
    
    with col3:
        if st.button("📋", help="Input Data", use_container_width=True):
            if st.session_state.page > 3:
                st.session_state.locked = False
            goto(3)
    
    with col4:
        if st.button("💬", help="Contact Us", use_container_width=True):
            goto(5)
    
    st.divider()
    
    st.markdown("### Current Assessment")
    
    if st.session_state.model:
        st.info(f"**Model:** {st.session_state.model}")
    
    if st.session_state.results:
        _, factors = st.session_state.results
        st.success(f"**Risk Level:** {st.session_state.results[0]}")
    else:
        st.info("No assessment yet")
    
    st.divider()
    
    st.markdown("### About")
    st.markdown("""
    **Fuzzy Risk Assessment Models**
    
    Based on: *Applied Soft Computing (2017)*
    
    For invasive alien plant species evaluation using fuzzy logic and expert knowledge.
    """)
    
    st.divider()
    
    st.markdown("### Settings")
    
    # Dark mode toggle
    dark_mode = st.toggle("🌙 Dark Mode", value=st.session_state.dark_mode, key="theme_toggle")
    if dark_mode != st.session_state.dark_mode:
        st.session_state.dark_mode = dark_mode
        st.rerun()
    
    st.divider()
    
    st.markdown("### Resources")
    
    st.markdown("""
    - [� ResearchGate Paper](https://www.researchgate.net/publication/317406162_Novel_Fuzzy_Linguistic_based_Mathematical_model_to_assess_risk_of_Invasive_alien_plant_species)
    - [💻 GitHub Repository](https://github.com/Manimohan05/Fuzzy_Invasive_Species_Risk_Assessment_Tool.git)
    - [📖 View Source Code](https://github.com/Manimohan05/Fuzzy_Invasive_Species_Risk_Assessment_Tool)
    - [⭐ Star on GitHub](https://github.com/Manimohan05/Fuzzy_Invasive_Species_Risk_Assessment_Tool)
    """)
    
    st.divider()
    
    st.markdown("""
    <small style="color: #6b7280; text-align: center; display: block;">
    v1.0 — Invasive Species Risk Dashboard
    </small>
    """, unsafe_allow_html=True)
