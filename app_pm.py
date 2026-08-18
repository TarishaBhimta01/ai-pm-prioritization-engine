import streamlit as st
import pandas as pd
from dotenv import load_dotenv
import os

# Import the core analysis function from your secure ai_engine.py
from ai_engine import run_feedback_analysis

# Load environment key
load_dotenv()

st.set_page_config(page_title="AI PM Prioritization Dashboard", layout="wide")

st.title("🤖 AI Product Manager: Feedback Prioritizer")
st.write("Upload customer feedback CSV data to synthesize problem clusters, calculate ARR impact, and view prioritized matrix.")

# --- SIDEBAR CONFIGURATION ---
st.sidebar.header("1. API & Configuration")

# Handle API Key
env_key = os.getenv("OPENAI_API_KEY", "")
user_api_key = st.sidebar.text_input("OpenAI API Key", value=env_key, type="password")

if user_api_key:
    os.environ["OPENAI_API_KEY"] = user_api_key

st.sidebar.header("2. Strategic OKRs")
default_okrs = "1. Enterprise Readiness (SSO, Security, RBAC)\n2. Performance & Export Speeds"
okrs_input = st.sidebar.text_area("Current Strategic Goals:", value=default_okrs, height=120)

# --- MAIN BODY: FILE UPLOADER ---
uploaded_file = st.file_uploader("Upload Customer Feedback CSV", type=["csv"])

# Fallback to local sample if no file is uploaded
sample_csv_path = "feedback_data.csv"

if uploaded_file is not None:
    # Save temporary uploaded file
    with open("temp_feedback_data.csv", "wb") as f:
        f.write(uploaded_file.getbuffer())
    target_csv = "temp_feedback_data.csv"
    st.success(f"Uploaded: `{uploaded_file.name}`")
elif os.path.exists(sample_csv_path):
    target_csv = sample_csv_path
    st.info("Using default `feedback_data.csv` found in project folder.")
else:
    target_csv = None
    st.warning("Please upload a CSV file with columns: `feedback_id`, `source`, `feedback_text`, `customer_tier`, `account_arr`.")

# --- RUN ANALYSIS ---
if st.button("🚀 Analyze & Generate Priority Matrix", type="primary"):
    if not os.environ.get("OPENAI_API_KEY"):
        st.error("Please enter a valid OpenAI API key in the sidebar.")
    elif not target_csv:
        st.error("Please upload a feedback CSV file to proceed.")
    else:
        with st.spinner("AI is analyzing customer feedback, calculating ARR impact, and scoring clusters..."):
            try:
                # Run engine logic
                results_df = run_feedback_analysis(csv_file_path=target_csv, okrs_text=okrs_input)
                
                st.subheader("📊 Prioritized Problem Matrix")
                st.dataframe(results_df, use_container_width=True)

                # Export Option
                csv_data = results_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download Priority Matrix (CSV)",
                    data=csv_data,
                    file_name="ai_pm_priority_matrix.csv",
                    mime="text/csv"
                )

            except Exception as e:
                st.error(f"Error during analysis: {e}")

# Cleanup temp files if created
if os.path.exists("temp_feedback_data.csv"):
    os.remove("temp_feedback_data.csv")