import os
import json
import pandas as pd
from openai import OpenAI
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# 1. Safely load environment variables from local .env file
load_dotenv()

# 2. Retrieve API Key dynamically
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 3. Guard clause: Stop execution early if key is missing
if not OPENAI_API_KEY:
    raise RuntimeError(
        "❌ Missing OpenAI API Key!\n"
        "Please create a local .env file with OPENAI_API_KEY=sk-proj-your-key-here"
    )

# Initialize OpenAI Client securely
client = OpenAI(api_key=OPENAI_API_KEY)


# 4. Define Data Structures
class ProblemCluster(BaseModel):
    cluster_id: str = Field(description="Short slug, e.g., sso-security")
    cluster_name: str = Field(description="Clear problem statement title")
    feedback_ids: list[str] = Field(description="List of feedback_ids belonging to this cluster")
    urgency_score: int = Field(description="Pain intensity from 1 to 10")
    strategic_alignment: float = Field(description="OKR alignment score from 0.0 to 1.0")
    estimated_effort: int = Field(description="Rough effort from 1 (easy) to 5 (hard)")
    summary: str = Field(description="2-sentence synthesis of customer requests")

class AnalysisResponse(BaseModel):
    clusters: list[ProblemCluster]


# 5. Core Analysis Pipeline
def run_feedback_analysis(
    csv_file_path="feedback_data.csv", 
    okrs_text="1. Enterprise Readiness (SSO, Security, RBAC)\n2. Performance & Export Speeds"
):
    if not os.path.exists(csv_file_path):
        raise FileNotFoundError(f"Input file not found: {csv_file_path}")

    df = pd.read_csv(csv_file_path)
    feedback_payload = df[["feedback_id", "source", "feedback_text", "customer_tier"]].to_dict(orient="records")

    system_prompt = f"""
    You are an AI Product Manager. Synthesize customer feedback into problem clusters.
    Current Strategic OKRs:
    {okrs_text}
    """

    print("🤖 AI is analyzing and clustering customer feedback...")
    
    response = client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Synthesize this feedback data:\n{json.dumps(feedback_payload)}"}
        ],
        response_format=AnalysisResponse,
        temperature=0.2
    )

    parsed_data = response.choices[0].message.parsed

    cluster_rows = []
    for cluster in parsed_data.clusters:
        matched_df = df[df["feedback_id"].isin(cluster.feedback_ids)]
        reach_count = len(matched_df)
        total_impacted_arr = matched_df["account_arr"].sum()
        
        arr_multiplier = 1 + (total_impacted_arr / 100000)
        raw_impact = (reach_count * cluster.urgency_score * cluster.strategic_alignment) * arr_multiplier
        priority_score = round(raw_impact / cluster.estimated_effort, 2)
        
        cluster_rows.append({
            "Rank": 0,
            "Problem Cluster": cluster.cluster_name,
            "Feedback Volume": reach_count,
            "Impacted ARR ($)": f"${total_impacted_arr:,.2f}",
            "Urgency (1-10)": cluster.urgency_score,
            "OKR Alignment": cluster.strategic_alignment,
            "Est. Effort (1-5)": cluster.estimated_effort,
            "Priority Score": priority_score,
            "Summary": cluster.summary
        })

    results_df = pd.DataFrame(cluster_rows)
    results_df = results_df.sort_values(by="Priority Score", ascending=False).reset_index(drop=True)
    results_df["Rank"] = results_df.index + 1
    return results_df


if __name__ == "__main__":
    try:
        final_table = run_feedback_analysis()
        print("\n### AI-Prioritized Problem Matrix\n")
        print(final_table.to_markdown(index=False))
    except Exception as e:
        print(f"\n⚠️ Execution error: {e}")