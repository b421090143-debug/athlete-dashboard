import pandas as pd
import sys
import os

# Add src to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.preprocessing import (
    add_week_column,
    compute_weekly_metrics,
    analyze_exercise_trends,
    generate_llm_facts
)

# 1️⃣ Load mock data
print("Loading data...")
df = pd.read_csv("data/mock_data.csv")
df["date"] = pd.to_datetime(df["date"])

# 2️⃣ Add week column
print("Adding week column...")
df = add_week_column(df)

# 3️⃣ Compute weekly metrics
print("Computing weekly metrics...")
weekly_metrics = compute_weekly_metrics(df)
print("\n=== Weekly Metrics ===")
print(weekly_metrics.to_string())

# 4️⃣ Analyze trends
print("\nAnalyzing trends...")
trend_analysis = analyze_exercise_trends(weekly_metrics)
print("\n=== Trend Analysis ===")
for k, v in trend_analysis.items():
    print(f"\n{k}:")
    for k2, v2 in v.items():
        print(f"  {k2}: {v2}")

# 5️⃣ Generate LLM facts
print("\nGenerating LLM facts...")
llm_facts = generate_llm_facts(trend_analysis)
print("\n=== LLM Facts ===")
for fact in llm_facts:
    print(f"\n--- {fact['exercise']} (Athlete {fact['athlete_id']}) ---")
    print(f"Load Trend: {fact['load_trend']}")
    print(f"Volume Trend: {fact['volume_trend']}")
    print(f"RPE Trend: {fact['rpe_trend']}")
    print(f"Flags: {fact['flags']}")
    print(f"Final Status: {fact['final_status']}")

# 6️⃣ Generate insights
print("\nGenerating insights...")
from generate_insights import generate_athlete_insights
generate_athlete_insights(llm_facts, filename="athlete_report.txt")

print("\n✅ Analysis complete! Check athlete_report.txt for detailed insights.")
