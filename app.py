import io
import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(
    page_title="DataFlow Studio",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .block-container {padding-top: 2rem; padding-bottom: 3rem; max-width: 1400px;}
    [data-testid="stMetric"] {
        background: #f7f8fa; border: 1px solid #e8ebef;
        padding: 16px; border-radius: 12px;
    }
    .hero {
        padding: 1.4rem 1.6rem; border-radius: 16px;
        background: linear-gradient(120deg, #f4f7fb, #edf3ff);
        border: 1px solid #e5ebf5; margin-bottom: 1.2rem;
    }
    .muted {color: #64748b;}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <h1 style="margin:0;">📊 DataFlow Studio</h1>
  <p style="font-size:1.05rem;margin:.45rem 0 0 0;">
    Clean, explore, and export your data — right in your browser.
  </p>
  <p class="muted" style="margin:.35rem 0 0 0;">
    A lightweight data workflow demo by Ezlivy · Python & Streamlit
  </p>
</div>
""", unsafe_allow_html=True)

def read_file(uploaded_file):
    name = uploaded_file.name.lower()
    if name.endswith(".csv"):
        raw = uploaded_file.getvalue()
        for encoding in ("utf-8-sig", "utf-8", "cp950", "big5", "latin1"):
            try:
                return pd.read_csv(io.BytesIO(raw), encoding=encoding)
            except UnicodeDecodeError:
                continue
        return pd.read_csv(io.BytesIO(raw))
    if name.endswith((".xlsx", ".xls")):
        return pd.read_excel(uploaded_file)
    raise ValueError("Please upload a CSV or Excel file.")

def make_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Cleaned Data")
        summary = pd.DataFrame({
            "Metric": ["Rows", "Columns", "Duplicate rows", "Missing cells"],
            "Value": [
                len(df), len(df.columns), int(df.duplicated().sum()),
                int(df.isna().sum().sum())
            ]
        })
        summary.to_excel(writer, index=False, sheet_name="Summary")
    return output.getvalue()

with st.sidebar:
    st.header("Workspace")
    st.caption("Upload a dataset to get started.")
    uploaded = st.file_uploader(
        "Choose a file",
        type=["csv", "xlsx", "xls"],
        help="Your file is processed in this app session."
    )
    st.divider()
    st.markdown("**Supported workflows**")
    st.markdown("- Data quality checks\n- Duplicate removal\n- Missing-value handling\n- Quick summaries\n- CSV / Excel export")
    st.caption("Demo app · No account required")

if uploaded is None:
    st.subheader("Try it with a sample dataset")
    sample = pd.DataFrame({
        "Customer": ["Alex", "Jamie", "Morgan", "Taylor", "Alex", "Riley", "Jordan"],
        "Region": ["North", "South", "East", "West", "North", None, "East"],
        "Orders": [12, 8, 15, None, 12, 5, 9],
        "Revenue": [1200, 850, 1780, 640, 1200, None, 990],
        "Signup_Date": ["2025-01-10", "2025-02-14", "2025-02-20", "2025-03-01",
                        "2025-01-10", "2025-03-15", "2025-04-02"]
    })
    st.info("Upload your own CSV or Excel file from the sidebar, or explore the sample below.")
    df_original = sample
else:
    try:
        df_original = read_file(uploaded)
    except Exception as e:
        st.error(f"Could not read this file: {e}")
        st.stop()

if df_original.empty:
    st.warning("This file contains no rows.")
    st.stop()

if len(df_original.columns) == 0:
    st.warning("This file contains no columns.")
    st.stop()

st.subheader("1. Data overview")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Rows", f"{len(df_original):,}")
c2.metric("Columns", f"{len(df_original.columns):,}")
c3.metric("Duplicate rows", f"{int(df_original.duplicated().sum()):,}")
c4.metric("Missing cells", f"{int(df_original.isna().sum().sum()):,}")

with st.expander("Preview original data", expanded=True):
    st.dataframe(df_original.head(100), use_container_width=True, height=280)

st.subheader("2. Data quality")
quality = pd.DataFrame({
    "Column": df_original.columns.astype(str),
    "Data type": [str(x) for x in df_original.dtypes],
    "Missing": [int(x) for x in df_original.isna().sum().values],
    "Missing (%)": [
        round(float(x) / max(len(df_original), 1) * 100, 1)
        for x in df_original.isna().sum().values
    ],
    "Unique values": [int(df_original[c].nunique(dropna=True)) for c in df_original.columns],
})
st.dataframe(quality, use_container_width=True, hide_index=True)

st.subheader("3. Clean your data")
working = df_original.copy()
left, right = st.columns(2)

with left:
    st.markdown("**Duplicate rows**")
    remove_duplicates = st.checkbox("Remove duplicate rows", value=True)
    st.markdown("**Missing values**")
    missing_method = st.selectbox(
        "Choose how to handle missing values",
        ["Keep as-is", "Drop rows with missing values", "Fill numeric with median and text with mode", "Fill all missing values with a custom value"]
    )
    fill_value = ""
    if missing_method == "Fill all missing values with a custom value":
        fill_value = st.text_input("Replacement value", value="Not specified")

with right:
    st.markdown("**Column selection**")
    drop_columns = st.multiselect(
        "Remove columns (optional)",
        options=list(working.columns),
        format_func=lambda x: str(x)
    )
    st.markdown("**Text cleanup**")
    trim_text = st.checkbox("Trim leading/trailing spaces in text columns", value=True)

if remove_duplicates:
    working = working.drop_duplicates()
if missing_method == "Drop rows with missing values":
    working = working.dropna()
elif missing_method == "Fill numeric with median and text with mode":
    for col in working.columns:
        if pd.api.types.is_numeric_dtype(working[col]):
            median = working[col].median()
            if pd.notna(median):
                working[col] = working[col].fillna(median)
        else:
            modes = working[col].mode(dropna=True)
            if not modes.empty:
                working[col] = working[col].fillna(modes.iloc[0])
elif missing_method == "Fill all missing values with a custom value":
    working = working.fillna(fill_value)

if trim_text:
    for col in working.select_dtypes(include=["object", "string"]).columns:
        working[col] = working[col].map(lambda x: x.strip() if isinstance(x, str) else x)

if drop_columns:
    working = working.drop(columns=drop_columns)

st.success(f"Preview updated: {len(df_original) - len(working):,} rows removed · {len(working.columns):,} columns remaining")
st.dataframe(working.head(100), use_container_width=True, height=280)

st.subheader("4. Quick analysis")
numeric_cols = list(working.select_dtypes(include="number").columns)
if numeric_cols:
    selected_num = st.selectbox("Select a numeric column", numeric_cols)
    a, b, c = st.columns(3)
    series = working[selected_num].dropna()
    a.metric("Average", f"{series.mean():,.2f}" if len(series) else "—")
    b.metric("Median", f"{series.median():,.2f}" if len(series) else "—")
    c.metric("Std. deviation", f"{series.std():,.2f}" if len(series) > 1 else "—")
    if len(series):
        fig = px.histogram(
            working, x=selected_num, nbins=25,
            title=f"Distribution of {selected_num}",
            template="plotly_white"
        )
        fig.update_layout(margin=dict(l=10, r=10, t=55, b=10))
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No numeric columns found. Add numeric data to see a distribution chart.")

st.subheader("5. Export your cleaned data")
st.caption("Download the current cleaned dataset. Files are generated when you click a button.")
csv_data = working.to_csv(index=False).encode("utf-8-sig")
e1, e2 = st.columns(2)
with e1:
    st.download_button(
        "⬇️ Download CSV",
        data=csv_data,
        file_name="cleaned_data.csv",
        mime="text/csv",
        use_container_width=True
    )
with e2:
    try:
        xlsx_data = make_excel(working)
        st.download_button(
            "⬇️ Download Excel",
            data=xlsx_data,
            file_name="cleaned_data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    except Exception:
        st.warning("Excel export requires openpyxl. CSV export is still available.")

st.divider()
st.markdown(
    "<div style='text-align:center;color:#94a3b8;font-size:.85rem;'>"
    "Built with Python · Pandas · Streamlit · Plotly &nbsp;|&nbsp; "
    "Need a custom workflow? Find me on Fiverr."
    "</div>",
    unsafe_allow_html=True
)
