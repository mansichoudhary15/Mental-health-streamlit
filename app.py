
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Mental Health in Tech — EDA Dashboard",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Styling ----------
st.markdown("""
<style>
    .main { background: #f7f9fc; }
    .block-container { padding-top: 2rem; padding-bottom: 3rem; }
    .hero {
        padding: 1.4rem 1.6rem;
        border-radius: 18px;
        background: linear-gradient(135deg,#eef5ff,#ffffff);
        border: 1px solid #e3eaf4;
        margin-bottom: 1.2rem;
    }
    .hero h1 { margin: 0; color:#172033; font-size: 2.2rem; }
    .hero p { color:#536176; margin: .5rem 0 0; }
    .section-title {
        color:#172033; font-size:1.55rem; font-weight:700;
        margin-top:1.5rem; margin-bottom:.7rem;
    }
    .metric-card {
        background:#fff; border:1px solid #e7edf5; border-radius:16px;
        padding:1rem 1.1rem; box-shadow:0 2px 12px rgba(20,35,60,.05);
        min-height:115px;
    }
    .metric-label { color:#667085; font-size:.92rem; }
    .metric-value { color:#172033; font-size:2rem; font-weight:750; margin-top:.15rem; }
    .small-note { color:#667085; font-size:.86rem; }
</style>
""", unsafe_allow_html=True)

# ---------- Data ----------
@st.cache_data
def load_data(file):
    df = pd.read_csv(file)
    # Basic cleaning used in the notebook
    df = df.dropna(how="all").dropna(axis=1, how="all").copy()
    if "Age" in df.columns:
        df["Age"] = pd.to_numeric(df["Age"], errors="coerce")
        df.loc[~df["Age"].between(18,100), "Age"] = np.nan
    if "Gender" in df.columns:
        g = df["Gender"].astype(str).str.strip().str.lower()
        g = g.replace({
            "m":"Male","male":"Male","man":"Male","cis male":"Male","cis man":"Male",
            "f":"Female","female":"Female","woman":"Female","cis female":"Female","cis woman":"Female"
        })
        df["Gender"] = g
    return df

# Find a local survey.csv first; otherwise let the user upload it.
try:
    df = load_data("survey.csv")
except Exception:
    st.sidebar.info("Upload the same `survey.csv` used in your EDA notebook.")
    uploaded = st.sidebar.file_uploader("Upload survey.csv", type=["csv"])
    if uploaded is None:
        st.markdown("""
        <div class="hero">
          <h1>🧠 Mental Health in Tech — EDA Dashboard</h1>
          <p>Interactive Streamlit version of the EDA notebook.</p>
        </div>
        """, unsafe_allow_html=True)
        st.warning("Please upload `survey.csv` in the sidebar to open the dashboard.")
        st.stop()
    df = load_data(uploaded)

# ---------- Header ----------
st.markdown("""
<div class="hero">
  <h1>🧠 Mental Health in Tech — EDA Dashboard</h1>
  <p>Explore treatment-seeking patterns and workplace mental-health factors from the 2014 OSMI survey.</p>
</div>
""", unsafe_allow_html=True)

# ---------- Sidebar filters ----------
st.sidebar.header("🔎 Filters")

def options(col):
    if col not in df.columns:
        return []
    vals = df[col].dropna().astype(str).unique().tolist()
    return sorted(vals)

selected_gender = st.sidebar.multiselect("Gender", options("Gender"), default=options("Gender"))
selected_country = st.sidebar.multiselect("Country", options("Country"), default=options("Country"))

age_min = int(df["Age"].dropna().min()) if "Age" in df.columns and df["Age"].notna().any() else 18
age_max = int(df["Age"].dropna().max()) if "Age" in df.columns and df["Age"].notna().any() else 100
age_range = st.sidebar.slider("Age", min_value=age_min, max_value=age_max,
                              value=(age_min, age_max))

treatment_filter = st.sidebar.multiselect(
    "Treatment", options("treatment"), default=options("treatment")
)

filtered = df.copy()
if selected_gender and "Gender" in filtered.columns:
    filtered = filtered[filtered["Gender"].isin(selected_gender)]
if selected_country and "Country" in filtered.columns:
    filtered = filtered[filtered["Country"].astype(str).isin(selected_country)]
if "Age" in filtered.columns:
    filtered = filtered[filtered["Age"].between(age_range[0], age_range[1], inclusive="both")]
if treatment_filter and "treatment" in filtered.columns:
    filtered = filtered[filtered["treatment"].isin(treatment_filter)]

st.sidebar.caption(f"Showing **{len(filtered):,}** of **{len(df):,}** respondents")

# ---------- Metrics ----------
st.markdown('<div class="section-title">Key Metrics (filtered)</div>', unsafe_allow_html=True)

n = len(filtered)
treat_rate = (filtered["treatment"].eq("Yes").mean() * 100) if n and "treatment" in filtered else np.nan
family_rate = (filtered["family_history"].eq("Yes").mean() * 100) if n and "family_history" in filtered else np.nan
anon_unknown = (filtered["anonymity"].eq("Don't know").mean() * 100) if n and "anonymity" in filtered else np.nan

m1,m2,m3,m4 = st.columns(4)
metrics = [
    ("👥","Respondents", f"{n:,}"),
    ("💊","Sought Treatment", f"{treat_rate:.1f}%" if pd.notna(treat_rate) else "—"),
    ("🧬","Family History", f"{family_rate:.1f}%" if pd.notna(family_rate) else "—"),
    ("🔒","Unsure re: Anonymity", f"{anon_unknown:.1f}%" if pd.notna(anon_unknown) else "—"),
]
for col,(icon,label,value) in zip([m1,m2,m3,m4],metrics):
    with col:
        st.markdown(f"""
        <div class="metric-card">
          <div style="font-size:1.6rem">{icon}</div>
          <div class="metric-value">{value}</div>
          <div class="metric-label">{label}</div>
        </div>
        """, unsafe_allow_html=True)

# ---------- Treatment gauge ----------
st.markdown('<div class="section-title">Treatment-Seeking Rate</div>', unsafe_allow_html=True)
if pd.notna(treat_rate):
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=treat_rate,
        number={"suffix":"%","font":{"size":48}},
        gauge={
            "axis":{"range":[0,100]},
            "bar":{"color":"#4169a8"},
            "steps":[
                {"range":[0,40],"color":"#f6c7c7"},
                {"range":[40,70],"color":"#f7e5ad"},
                {"range":[70,100],"color":"#cfe6c8"}
            ],
            "threshold":{"line":{"color":"#222","width":2},"thickness":0.75,"value":treat_rate}
        },
        title={"text":"Treatment-Seeking Rate"}
    ))
    fig_gauge.update_layout(height=330, margin=dict(l=20,r=20,t=65,b=10), paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig_gauge, use_container_width=True)
    st.caption("Green (70–100%) indicates a higher treatment-seeking share; red (0–40%) indicates a lower share.")

# ---------- Chart helper ----------
def countplot(data, x, title, xlabel=None, order=None, hue="treatment", height=420):
    if x not in data.columns:
        return
    d = data.copy()
    if order is not None:
        d[x] = pd.Categorical(d[x], categories=order, ordered=True)
    if hue and hue in d.columns:
        fig = px.histogram(d, x=x, color=hue, barmode="group", category_orders={x:order} if order else None)
    else:
        fig = px.histogram(d, x=x)
    fig.update_layout(
        title=title, height=height, margin=dict(l=20,r=20,t=55,b=50),
        xaxis_title=xlabel or x, yaxis_title="Number of Respondents",
        legend_title=hue.title() if hue else ""
    )
    st.plotly_chart(fig, use_container_width=True)

# ---------- Charts ----------
st.markdown('<div class="section-title">EDA Visualizations</div>', unsafe_allow_html=True)

# 1 Age
if "Age" in filtered.columns:
    fig = px.histogram(filtered.dropna(subset=["Age"]), x="Age", nbins=15,
                       title="Distribution of Respondents by Age")
    fig.update_layout(height=420, xaxis_title="Age", yaxis_title="Number of Respondents",
                      margin=dict(l=20,r=20,t=55,b=50))
    st.plotly_chart(fig, use_container_width=True)

# 2 Gender
if "Gender" in filtered.columns:
    g = filtered[filtered["Gender"].isin(["Male","Female"])]
    fig = px.histogram(g, x="Gender", title="Gender Distribution of Survey Respondents")
    fig.update_layout(height=420, xaxis_title="Gender", yaxis_title="Number of Respondents",
                      margin=dict(l=20,r=20,t=55,b=50))
    st.plotly_chart(fig, use_container_width=True)

# 3–5
countplot(filtered, "family_history", "Mental Health Treatment by Family History of Mental Illness",
           "Family History of Mental Illness")
countplot(filtered, "treatment", "Distribution of Mental Health Treatment Responses", "Mental Health Treatment", hue=None)
countplot(filtered, "work_interfere", "Mental Health Impact on Work",
           "Work Interference", order=["Never","Rarely","Sometimes","Often","NA"], hue=None)

# 6 Age group
if "Age" in filtered.columns and "treatment" in filtered.columns:
    d = filtered.dropna(subset=["Age"]).copy()
    d["Age_Group"] = pd.cut(d["Age"], bins=[17,25,35,45,55,100],
                            labels=["18-25","26-35","36-45","46-55","56+"])
    countplot(d, "Age_Group", "Mental Health Treatment by Age Group", "Age Group",
              order=["18-25","26-35","36-45","46-55","56+"])

# 7–13
countplot(filtered, "remote_work", "Mental Health Treatment by Remote Work Status", "Remote Work")
countplot(filtered, "no_employees", "Mental Health Treatment by Company Size", "Company Size",
          order=["1-5","6-25","26-100","100-500","500-1000","More than 1000"])
countplot(filtered, "benefits", "Mental Health Treatment by Availability of Mental Health Benefits",
          "Mental Health Benefits")
countplot(filtered, "care_options", "Mental Health Treatment by Availability of Care Options",
          "Mental Health Care Options")
countplot(filtered, "wellness_program", "Mental Health Treatment by Workplace Wellness Program",
          "Workplace Wellness Program")
countplot(filtered, "seek_help", "Mental Health Treatment by Availability of Mental Health Resources",
          "Employer Provides Mental Health Resources")
countplot(filtered, "anonymity", "Mental Health Treatment by Anonymity Protection",
          "Anonymity Protection")

# 14 Correlation heatmap
st.markdown('<div class="section-title">Correlation Heatmap</div>', unsafe_allow_html=True)
binary_columns = ["treatment","family_history","remote_work","tech_company","self_employed"]
available_binary = [c for c in binary_columns if c in filtered.columns]
corr_df = filtered.copy()
for col in available_binary:
    corr_df[col] = corr_df[col].map({"Yes":1,"No":0})
corr_cols = [c for c in ["Age"] + available_binary if c in corr_df.columns]
corr_data = corr_df[corr_cols].corr(numeric_only=True)
if not corr_data.empty:
    fig = px.imshow(corr_data, text_auto=".2f", aspect="auto",
                    color_continuous_scale="RdBu_r",
                    title="Correlation Heatmap of Selected Variables")
    fig.update_layout(height=520, margin=dict(l=20,r=20,t=55,b=20))
    st.plotly_chart(fig, use_container_width=True)

# 15 Pair plot equivalent
st.markdown('<div class="section-title">Pair Plot of Important Variables</div>', unsafe_allow_html=True)
pair_cols = [c for c in ["Age","treatment","family_history","remote_work"] if c in filtered.columns]
if len(pair_cols) >= 2:
    pair_df = filtered[pair_cols].copy()
    if "Age" in pair_df:
        pair_df["Age"] = pd.to_numeric(pair_df["Age"], errors="coerce")
        pair_df = pair_df[pair_df["Age"].between(18,100)]
    for col in ["treatment","family_history","remote_work"]:
        if col in pair_df.columns:
            pair_df[col] = pair_df[col].map({"Yes":1,"No":0})
    pair_df = pair_df.dropna()
    if len(pair_df) > 0:
        # Scatter-matrix is the Plotly interactive equivalent of seaborn pairplot.
        fig = px.scatter_matrix(pair_df, dimensions=pair_df.columns.tolist(),
                                color="treatment" if "treatment" in pair_df.columns else None,
                                title="Pair Plot of Important Variables")
        fig.update_layout(height=800, margin=dict(l=20,r=20,t=55,b=20))
        st.plotly_chart(fig, use_container_width=True)

# ---------- Data preview ----------
st.markdown('<div class="section-title">Filtered Data Preview</div>', unsafe_allow_html=True)
st.dataframe(filtered.head(10), use_container_width=True, height=390)

# ---------- Business objective ----------
st.markdown('<div class="section-title">Business Objective</div>', unsafe_allow_html=True)
st.write(
    "Identify which employer policies and workplace characteristics are most strongly associated "
    "with (a) seeking treatment and (b) willingness to discuss mental health openly, so employers "
    "can prioritize interventions that may reduce stigma and increase treatment-seeking."
)

st.markdown('<div class="section-title">Project Summary</div>', unsafe_allow_html=True)
st.write(
    "This project explores the 2014 OSMI survey on attitudes toward mental health and the frequency "
    "of mental health conditions in the tech workplace. The dashboard applies the cleaning and analysis "
    "steps from the EDA notebook and makes the results interactive through filters."
)

st.caption("Note: These survey relationships are associations, not proof of causation.")
