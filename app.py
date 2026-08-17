import streamlit as st
import pandas as pd
from ai_engine import run_feedback_analysis

# 1. Page Configuration
st.set_page_config(page_title="AI PM Prioritization Engine", page_icon="🚀", layout="wide")

st.title("🚀 AI Product Opportunity & Prioritization Engine")
st.write("Upload raw feedback data to cluster user pain points, align with strategic OKRs, and generate a weighted priority matrix.")

# 2. Sidebar Configuration (Dynamic OKRs)
st.sidebar.header("🎯 Strategic Alignment")
okrs_input = st.sidebar.text_area(
    "Current Company OKRs:",
    value="1. Enterprise Readiness (SSO, Security, RBAC)\n2. Performance & Export Speeds",
    height=150
)

# 3. Main Dashboard UI
st.subheader("1. Input Feedback Data")
uploaded_file = st.file_uploader("Upload Customer Feedback CSV", type=["csv"])

# Use default sample data if no file is uploaded
if uploaded_file is None:
    st.info("💡 No file uploaded. Using default sample dataset (`feedback_data.csv`).")
    csv_path = "feedback_data.csv"
else:
    csv_path = uploaded_file

# 4. Action Button
if st.button("🔥 Generate AI Priority Matrix", type="primary"):
    with st.spinner("🤖 OpenAI GPT-4o is analyzing feedback and calculating scores..."):
        try:
            # Calling your Option 1 backend engine!
            results_df = run_feedback_analysis(csv_file_path=csv_path, okrs_text=okrs_input)
            
            st.success("Analysis Complete!")
            st.subheader("2. AI-Prioritized Problem Matrix")
            
            # Display interactive web table
            st.dataframe(results_df, use_container_width=True)
            
            # Download Results Option
            csv_export = results_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Priority Matrix CSV",
                data=csv_export,
                file_name="ai_prioritized_roadmap.csv",
                mime="text/csv"
            )
        except Exception as e:
            st.error(f"Error running analysis: {e}")