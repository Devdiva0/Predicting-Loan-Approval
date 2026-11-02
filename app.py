import streamlit as st
import subprocess
import re
import pandas as pd
import os
import sys
from PIL import Image

# ── PAGE CONFIG ──────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Loan Approval Dashboard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CUSTOM CSS ───────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Dark background */
.stApp {
    background: linear-gradient(135deg, #0b1120 0%, #111827 100%);
    color: #e2e8f0;
}

/* Hide default header */
header[data-testid="stHeader"] { background: transparent; }

/* Main title */
.main-title {
    font-size: 2.4rem;
    font-weight: 800;
    background: linear-gradient(135deg, #ffffff 0%, #93c5fd 50%, #f5c842 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    text-align: center;
    padding: 0.5rem 0 0.2rem;
    line-height: 1.2;
}
.main-sub {
    text-align: center;
    color: #64748b;
    font-size: 1rem;
    margin-bottom: 1.5rem;
}

/* KPI cards */
.kpi-card {
    background: linear-gradient(145deg, #1a2540, #0f1a2e);
    border: 1px solid #243057;
    border-radius: 16px;
    padding: 1.4rem 1rem;
    text-align: center;
    position: relative;
    overflow: hidden;
    margin-bottom: 1rem;
}
.kpi-card::after {
    content: '';
    position: absolute;
    bottom: 0; left: 0; right: 0;
    height: 3px;
}
.kpi-blue::after   { background: #4f8ef7; }
.kpi-green::after  { background: #34d399; }
.kpi-gold::after   { background: #f5c842; }
.kpi-red::after    { background: #f87171; }

.kpi-icon  { font-size: 1.8rem; margin-bottom: 0.3rem; }
.kpi-label { font-size: 0.72rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.1em; }
.kpi-value { font-size: 2rem; font-weight: 800; margin-top: 0.2rem; }
.kpi-blue  .kpi-value { color: #93c5fd; }
.kpi-green .kpi-value { color: #6ee7b7; }
.kpi-gold  .kpi-value { color: #fde68a; }
.kpi-red   .kpi-value { color: #fca5a5; }

/* Section headers */
.section-title {
    font-size: 1.2rem;
    font-weight: 700;
    color: #e2e8f0;
    border-left: 4px solid #4f8ef7;
    padding-left: 0.8rem;
    margin: 1.5rem 0 1rem;
}

/* Terminal output box */
.terminal-box {
    background: #0d1117;
    border: 1px solid #243057;
    border-radius: 12px;
    padding: 1.2rem 1.5rem;
    font-family: 'Courier New', monospace;
    font-size: 0.82rem;
    color: #b0c4de;
    white-space: pre;
    overflow-x: auto;
    line-height: 1.6;
}

/* Confusion matrix cells */
.cm-grid {
    display: grid;
    grid-template-columns: 120px 1fr 1fr;
    grid-template-rows: 40px 1fr 1fr;
    gap: 6px;
    max-width: 360px;
    margin: 0 auto;
}
.cm-header { display: flex; align-items: center; justify-content: center;
             font-size: 0.75rem; font-weight: 600; color: #64748b; }
.cm-cell {
    border-radius: 10px;
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    padding: 1rem;
    font-weight: 700;
}
.cm-tn { background: #1a3a6e44; border: 1px solid #34d39966; }
.cm-tn .cm-val { color: #6ee7b7; font-size: 1.6rem; }
.cm-fp { background: #7c3a1044; border: 1px solid #f8717166; }
.cm-fp .cm-val { color: #fca5a5; font-size: 1.6rem; }
.cm-fn { background: #7c3a1044; border: 1px solid #f8717166; }
.cm-fn .cm-val { color: #fca5a5; font-size: 1.6rem; }
.cm-tp { background: #1a3a6e44; border: 1px solid #34d39966; }
.cm-tp .cm-val { color: #6ee7b7; font-size: 1.6rem; }
.cm-label { font-size: 0.65rem; color: #64748b; margin-top: 0.2rem; }

/* Run button */
div[data-testid="stButton"] > button {
    background: linear-gradient(135deg, #4f8ef7, #2563eb);
    color: white;
    border: none;
    border-radius: 12px;
    padding: 0.7rem 2rem;
    font-weight: 700;
    font-size: 1rem;
    width: 100%;
    transition: all 0.2s;
    box-shadow: 0 4px 20px #4f8ef740;
}
div[data-testid="stButton"] > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 30px #4f8ef760;
}

/* Metric bar */
.metric-bar-bg {
    background: #1e2d4a;
    border-radius: 99px;
    height: 10px;
    overflow: hidden;
    margin-top: 0.3rem;
}
.metric-bar-fill {
    height: 100%;
    border-radius: 99px;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #0f1729;
    border-right: 1px solid #243057;
}

/* Dataframe */
.stDataFrame { border-radius: 12px; overflow: hidden; }
</style>
""", unsafe_allow_html=True)


# ── HELPER: RUN SPARK SCRIPT ─────────────────────────────────────────────
def run_spark_script():
    """Run loan_approval_spark.py and return stdout."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(script_dir, "loan_approval_spark.py")
    python_exec = sys.executable

    result = subprocess.run(
        [python_exec, script_path],
        capture_output=True,
        text=True,
        cwd=script_dir
    )
    return result.stdout, result.stderr


# ── HELPER: PARSE OUTPUT ─────────────────────────────────────────────────
def parse_spark_output(output: str):
    """Extract metrics from loan_approval_spark.py stdout."""
    data = {
        "total_records": None,
        "accuracy": None,
        "tn": None, "fp": None, "fn": None, "tp": None
    }

    # Total records
    m = re.search(r"Total Records:\s*(\d+)", output)
    if m:
        data["total_records"] = int(m.group(1))

    # Accuracy
    m = re.search(r"Model Accuracy:\s*([\d.]+)\s*%", output)
    if m:
        data["accuracy"] = float(m.group(1))

    # Confusion matrix rows:  "Rejected   286     7"  /  "Approved   33    477"
    m = re.search(r"Rejected\s+(\d+)\s+(\d+)", output)
    if m:
        data["tn"] = int(m.group(1))
        data["fp"] = int(m.group(2))

    m = re.search(r"Approved\s+(\d+)\s+(\d+)", output)
    if m:
        data["fn"] = int(m.group(1))
        data["tp"] = int(m.group(2))

    return data


# ── HELPER: LOAD DATASET ─────────────────────────────────────────────────
@st.cache_data
def load_dataset():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(script_dir, "loan_approval_dataset.csv")
    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.strip()
    for col in df.select_dtypes("object").columns:
        df[col] = df[col].str.strip()
    df = df.drop(columns=["loan_id"], errors="ignore")
    return df


# ── SESSION STATE INIT ───────────────────────────────────────────────────
if "results" not in st.session_state:
    st.session_state.results = None
if "raw_output" not in st.session_state:
    st.session_state.raw_output = None
if "ran" not in st.session_state:
    st.session_state.ran = False

# Check if PNGs already exist from a previous run
script_dir = os.path.dirname(os.path.abspath(__file__))
cm_path    = os.path.join(script_dir, "confusion_matrix.png")
inc_path   = os.path.join(script_dir, "approval_by_income.png")


# ── SIDEBAR ──────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚡ Loan Approval")
    st.markdown("**Big Data Analytics Dashboard**")
    st.markdown("---")
    st.markdown("### 📌 Project Info")
    st.markdown("""
- **Algorithm:** Decision Tree  
- **Framework:** Apache Spark  
- **Language:** Python 3  
- **Split:** 80% Train / 20% Test  
- **Max Depth:** 5  
- **Seed:** 42  
""")
    st.markdown("---")
    st.markdown("### 🗂️ Source")
    st.code("loan_approval_spark.py", language="text")
    st.markdown("Results are fetched **directly** from this PySpark script.")
    st.markdown("---")

    run_clicked = st.button("▶ Run PySpark Analysis", use_container_width=True)


# ── HEADER ───────────────────────────────────────────────────────────────
st.markdown('<div class="main-title">⚡ Loan Approval Prediction</div>', unsafe_allow_html=True)
st.markdown('<div class="main-sub">Apache Spark · Decision Tree · Real-time ML Dashboard</div>', unsafe_allow_html=True)

# ── RUN SPARK ────────────────────────────────────────────────────────────
if run_clicked:
    with st.spinner("🔥 Running `loan_approval_spark.py` via Apache Spark…  (may take ~30 sec)"):
        stdout, stderr = run_spark_script()

    if "Project Completed Successfully" in stdout:
        st.session_state.results   = parse_spark_output(stdout)
        st.session_state.raw_output = stdout
        st.session_state.ran = True
        st.success("✅ Spark job completed successfully!")
    else:
        st.error("❌ Spark job failed. See error below.")
        st.code(stderr[-3000:], language="bash")
        st.stop()


# ── LOAD DATA ─────────────────────────────────────────────────────────────
df = load_dataset()

# ── SHOW KPI CARDS ───────────────────────────────────────────────────────
results = st.session_state.results

total_records = results["total_records"] if results else len(df)
accuracy      = results["accuracy"]      if results else "—"
approved_count = int((df["loan_status"] == "Approved").sum())
rejected_count = int((df["loan_status"] == "Rejected").sum())

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(f"""
    <div class="kpi-card kpi-blue">
        <div class="kpi-icon">🗄️</div>
        <div class="kpi-label">Total Records</div>
        <div class="kpi-value kpi-blue">{total_records:,}</div>
    </div>""", unsafe_allow_html=True)

with c2:
    acc_display = f"{accuracy} %" if isinstance(accuracy, float) else "Run Analysis ↖"
    acc_color   = "#6ee7b7" if isinstance(accuracy, float) else "#64748b"
    st.markdown(f"""
    <div class="kpi-card kpi-green">
        <div class="kpi-icon">🎯</div>
        <div class="kpi-label">Model Accuracy</div>
        <div class="kpi-value" style="color:{acc_color}; font-size:{'1.8rem' if isinstance(accuracy,float) else '1.1rem'};">{acc_display}</div>
    </div>""", unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="kpi-card kpi-gold">
        <div class="kpi-icon">✅</div>
        <div class="kpi-label">Approved</div>
        <div class="kpi-value kpi-gold">{approved_count:,}</div>
    </div>""", unsafe_allow_html=True)

with c4:
    st.markdown(f"""
    <div class="kpi-card kpi-red">
        <div class="kpi-icon">❌</div>
        <div class="kpi-label">Rejected</div>
        <div class="kpi-value kpi-red">{rejected_count:,}</div>
    </div>""", unsafe_allow_html=True)


st.markdown("---")

# ── TABS ─────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["📊 Model Results", "📈 Visualizations", "🔍 Dataset", "📟 Terminal Output", "📋 Pipeline"]
)

# ────────────────────────────────────────────────────
# TAB 1 – MODEL RESULTS
# ────────────────────────────────────────────────────
with tab1:
    if not st.session_state.ran:
        st.info("👈 Click **▶ Run PySpark Analysis** in the sidebar to fetch live results from `loan_approval_spark.py`.")
    else:
        r = st.session_state.results
        tn, fp, fn, tp = r["tn"], r["fp"], r["fn"], r["tp"]

        # ── Accuracy bar ──────────────────────────────
        st.markdown('<div class="section-title">Model Accuracy</div>', unsafe_allow_html=True)
        col_a, col_b = st.columns([2, 1])
        with col_a:
            pct = r["accuracy"]
            st.markdown(f"""
            <div style="font-size:3.5rem; font-weight:800; color:#6ee7b7; line-height:1;">{pct}%</div>
            <div class="metric-bar-bg" style="margin-top:0.8rem;">
              <div class="metric-bar-fill" style="width:{pct}%; background:linear-gradient(90deg,#34d399,#10b981);"></div>
            </div>
            <div style="color:#64748b; font-size:0.82rem; margin-top:0.4rem;">
              MulticlassClassificationEvaluator · 20% test split · seed=42
            </div>""", unsafe_allow_html=True)

        with col_b:
            total_test = tn + fp + fn + tp
            correct    = tn + tp
            st.metric("Correct Predictions",  f"{correct:,}")
            st.metric("Incorrect Predictions", f"{total_test - correct:,}")
            st.metric("Test Set Size",         f"{total_test:,}")

        # ── Confusion Matrix ──────────────────────────
        st.markdown('<div class="section-title">Confusion Matrix</div>', unsafe_allow_html=True)
        cm_col, metrics_col = st.columns([1, 1])

        with cm_col:
            st.markdown(f"""
            <div class="cm-grid">
              <!-- row 0: empty + headers -->
              <div></div>
              <div class="cm-header">Pred: Rejected</div>
              <div class="cm-header">Pred: Approved</div>

              <!-- row 1: Actual Rejected -->
              <div class="cm-header" style="justify-content:flex-end; padding-right:8px;">Actual<br>Rejected</div>
              <div class="cm-cell cm-tn">
                <div class="cm-val">{tn}</div>
                <div class="cm-label">True Negative</div>
              </div>
              <div class="cm-cell cm-fp">
                <div class="cm-val">{fp}</div>
                <div class="cm-label">False Positive</div>
              </div>

              <!-- row 2: Actual Approved -->
              <div class="cm-header" style="justify-content:flex-end; padding-right:8px;">Actual<br>Approved</div>
              <div class="cm-cell cm-fn">
                <div class="cm-val">{fn}</div>
                <div class="cm-label">False Negative</div>
              </div>
              <div class="cm-cell cm-tp">
                <div class="cm-val">{tp}</div>
                <div class="cm-label">True Positive</div>
              </div>
            </div>
            """, unsafe_allow_html=True)

        with metrics_col:
            # Derived metrics
            precision = round(tp / (tp + fp) * 100, 2) if (tp + fp) > 0 else 0
            recall    = round(tp / (tp + fn) * 100, 2) if (tp + fn) > 0 else 0
            f1        = round(2 * precision * recall / (precision + recall), 2) if (precision + recall) > 0 else 0
            specificity = round(tn / (tn + fp) * 100, 2) if (tn + fp) > 0 else 0

            metrics_df = pd.DataFrame({
                "Metric":  ["Accuracy", "Precision", "Recall (Sensitivity)", "F1 Score", "Specificity"],
                "Value %": [r["accuracy"], precision, recall, f1, specificity]
            })
            st.dataframe(
                metrics_df.style.format({"Value %": "{:.2f}%"}),
                use_container_width=True,
                hide_index=True
            )

            for name, val, color in [
                ("Precision",   precision,      "#93c5fd"),
                ("Recall",      recall,         "#6ee7b7"),
                ("F1 Score",    f1,             "#fde68a"),
                ("Specificity", specificity,    "#c4b5fd"),
            ]:
                st.markdown(f"""
                <div style="margin-top:0.5rem;">
                  <div style="display:flex;justify-content:space-between;font-size:0.8rem;">
                    <span style="color:#94a3b8;">{name}</span>
                    <span style="color:{color};font-weight:700;">{val}%</span>
                  </div>
                  <div class="metric-bar-bg">
                    <div class="metric-bar-fill" style="width:{val}%;background:{color};"></div>
                  </div>
                </div>""", unsafe_allow_html=True)


# ────────────────────────────────────────────────────
# TAB 2 – VISUALIZATIONS (Spark-generated PNGs)
# ────────────────────────────────────────────────────
with tab2:
    st.markdown('<div class="section-title">Charts Generated by loan_approval_spark.py</div>',
                unsafe_allow_html=True)

    if not os.path.exists(cm_path) or not os.path.exists(inc_path):
        st.info("👈 Run the PySpark analysis first to generate the charts.")
    else:
        v1, v2 = st.columns(2)
        with v1:
            st.markdown("**Confusion Matrix Heatmap**")
            st.image(Image.open(cm_path), use_container_width=True)
            st.caption("confusion_matrix.png — generated by Matplotlib")

        with v2:
            st.markdown("**Approval Rate by Income Group**")
            st.image(Image.open(inc_path), use_container_width=True)
            st.caption("approval_by_income.png — generated by Matplotlib")

    # ── Approval split pie (from dataset)
    st.markdown('<div class="section-title">Dataset Overview Charts</div>', unsafe_allow_html=True)

    try:
        import plotly.express as px
        import plotly.graph_objects as go

        d1, d2 = st.columns(2)

        with d1:
            counts = df["loan_status"].value_counts().reset_index()
            counts.columns = ["Status", "Count"]
            fig = px.pie(
                counts, names="Status", values="Count",
                title="Approved vs Rejected Split",
                color="Status",
                color_discrete_map={"Approved": "#34d399", "Rejected": "#f87171"},
                hole=0.5
            )
            fig.update_layout(
                paper_bgcolor="#1a2540", plot_bgcolor="#1a2540",
                font_color="#e2e8f0", title_font_size=14,
                legend=dict(font_color="#94a3b8")
            )
            st.plotly_chart(fig, use_container_width=True)

        with d2:
            income_df = df.copy()
            income_df["income_group"] = pd.cut(
                income_df["income_annum"],
                bins=[0, 2_500_000, 5_000_000, float("inf")],
                labels=["Low Income", "Middle Income", "High Income"]
            )
            approval_rate = (
                income_df.groupby("income_group", observed=True)
                .apply(lambda x: (x["loan_status"] == "Approved").mean() * 100)
                .reset_index(name="approval_rate")
            )
            fig2 = px.bar(
                approval_rate, x="income_group", y="approval_rate",
                title="Approval Rate by Income Group (%)",
                color="income_group",
                color_discrete_map={
                    "Low Income": "#f87171",
                    "Middle Income": "#fbbf24",
                    "High Income": "#34d399"
                },
                text=approval_rate["approval_rate"].round(1).astype(str) + "%"
            )
            fig2.update_layout(
                paper_bgcolor="#1a2540", plot_bgcolor="#1a2540",
                font_color="#e2e8f0", title_font_size=14,
                showlegend=False, yaxis_range=[0, 100],
                yaxis_gridcolor="#243057"
            )
            fig2.update_traces(textposition="outside")
            st.plotly_chart(fig2, use_container_width=True)

        # CIBIL score distribution by status
        fig3 = px.histogram(
            df, x="cibil_score", color="loan_status",
            nbins=40, barmode="overlay",
            title="CIBIL Score Distribution by Loan Status",
            color_discrete_map={"Approved": "#34d399", "Rejected": "#f87171"},
            opacity=0.8
        )
        fig3.update_layout(
            paper_bgcolor="#1a2540", plot_bgcolor="#1a2540",
            font_color="#e2e8f0", title_font_size=14,
            xaxis_gridcolor="#243057", yaxis_gridcolor="#243057",
            legend=dict(font_color="#94a3b8")
        )
        st.plotly_chart(fig3, use_container_width=True)

    except ImportError:
        st.warning("Install plotly for interactive charts: `pip install plotly`")


# ────────────────────────────────────────────────────
# TAB 3 – DATASET
# ────────────────────────────────────────────────────
with tab3:
    st.markdown('<div class="section-title">Dataset Preview</div>', unsafe_allow_html=True)

    # Filters
    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        edu_filter = st.selectbox("Education", ["All"] + sorted(df["education"].unique().tolist()))
    with fc2:
        emp_filter = st.selectbox("Self Employed", ["All"] + sorted(df["self_employed"].unique().tolist()))
    with fc3:
        status_filter = st.selectbox("Loan Status", ["All", "Approved", "Rejected"])

    filtered = df.copy()
    if edu_filter    != "All": filtered = filtered[filtered["education"]     == edu_filter]
    if emp_filter    != "All": filtered = filtered[filtered["self_employed"] == emp_filter]
    if status_filter != "All": filtered = filtered[filtered["loan_status"]   == status_filter]

    st.caption(f"Showing {len(filtered):,} of {len(df):,} records")
    st.dataframe(filtered, use_container_width=True, height=400)

    st.markdown('<div class="section-title">Column Statistics</div>', unsafe_allow_html=True)
    numeric_df = df.select_dtypes(include="number")
    st.dataframe(
        numeric_df.describe().round(2).T.rename(columns={"50%": "median"}),
        use_container_width=True
    )


# ────────────────────────────────────────────────────
# TAB 4 – TERMINAL OUTPUT
# ────────────────────────────────────────────────────
with tab4:
    st.markdown('<div class="section-title">Raw Output from loan_approval_spark.py</div>',
                unsafe_allow_html=True)

    if st.session_state.raw_output:
        # Show only the lines printed by the script (after Spark logs)
        lines = st.session_state.raw_output.strip().split("\n")
        clean = [l for l in lines if not l.startswith("26/") and "WARN" not in l]
        st.markdown(
            f'<div class="terminal-box">{chr(10).join(clean)}</div>',
            unsafe_allow_html=True
        )
    else:
        st.info("👈 Run the analysis to see live terminal output here.")


# ────────────────────────────────────────────────────
# TAB 5 – PIPELINE
# ────────────────────────────────────────────────────
with tab5:
    st.markdown('<div class="section-title">PySpark ML Pipeline</div>', unsafe_allow_html=True)

    steps = [
        ("1", "SparkSession", "Creates Spark session in local[*] mode (all CPU cores)", "#4f8ef7"),
        ("2", "Read CSV",     "Loads dataset, strips whitespace, drops loan_id column", "#818cf8"),
        ("3", "Imputer",      "Fills missing numerical values using median strategy across 9 columns", "#a78bfa"),
        ("4", "StandardScaler", "Normalizes CIBIL score to mean=0, std=1 via z-score scaling", "#c084fc"),
        ("5", "StringIndexer", "Encodes education & self_employed to numeric; loan_status → label (Approved=1)", "#e879f9"),
        ("6", "VectorAssembler", "Merges all 11 feature columns into a single features vector", "#f472b6"),
        ("7", "DecisionTreeClassifier", "Trains Decision Tree (maxDepth=5, seed=42) on 80% training data", "#fb7185"),
        ("8", "Evaluate",     "Computes accuracy using MulticlassClassificationEvaluator on 20% test set", "#f97316"),
        ("9", "Confusion Matrix", "Counts TP/TN/FP/FN using PySpark agg + F.when; saves heatmap PNG", "#eab308"),
        ("10","Income Analysis", "Groups by income tier, computes approval rate, saves bar chart PNG", "#84cc16"),
    ]

    for num, name, desc, color in steps:
        st.markdown(f"""
        <div style="display:flex; align-items:flex-start; gap:1rem; 
                    background:#1a2540; border:1px solid #243057; 
                    border-radius:12px; padding:1rem 1.2rem; margin-bottom:0.6rem;">
          <div style="min-width:36px; height:36px; border-radius:10px; background:{color}22;
                      border:1px solid {color}66; color:{color}; font-weight:800;
                      font-size:0.9rem; display:flex; align-items:center; justify-content:center;">
            {num}
          </div>
          <div>
            <div style="font-weight:700; color:#e2e8f0; font-size:0.95rem;">{name}</div>
            <div style="color:#64748b; font-size:0.83rem; margin-top:0.15rem;">{desc}</div>
          </div>
        </div>""", unsafe_allow_html=True)

    st.markdown('<div class="section-title">Pipeline Stage Order</div>', unsafe_allow_html=True)
    st.code("""Pipeline(stages=[
    imputer,           # Step 3 — fills NaN with median
    credit_assembler,  # Step 4a — wraps cibil_score in vector
    scaler,            # Step 4b — standardizes cibil_score
    *indexers,         # Step 5a — encodes education, self_employed
    label_indexer,     # Step 5b — encodes loan_status → label
    assembler,         # Step 6  — assembles all features into 1 vector
    dt                 # Step 7  — Decision Tree classifier
])""", language="python")


# ── FOOTER ───────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style="text-align:center; color:#334155; font-size:0.8rem; padding:0.5rem 0 1rem;">
  ⚡ Loan Approval Prediction &nbsp;·&nbsp; Apache Spark + PySpark ML &nbsp;·&nbsp; 
  Results sourced from <code>loan_approval_spark.py</code> &nbsp;·&nbsp; 2026–27
</div>""", unsafe_allow_html=True)
