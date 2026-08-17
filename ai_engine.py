import os
import json
import pandas as pd
from openai import OpenAI
from pydantic import BaseModel, Field

# 1. Initialize OpenAI Client (Uses your environment key or custom string)
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", "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"))

# 2. Define Output Data Structure
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

# 3. Main Analysis Function
def run_feedback_analysis(csv_file_path="feedback_data.csv", okrs_text="1. Enterprise Readiness (SSO, Security, RBAC)\n2. Performance & Export Speeds"):
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
        print(f"\n⚠️ Note: Add your OpenAI API key to run the live AI call! Error: {e}")