from collections import Counter

def generate_athlete_insights(llm_facts: list, filename="athlete_report.txt") -> None:
    """
    Converts structured LLM facts into bullet-style insights for each athlete/exercise,
    includes detailed recommendations, summary per athlete, and saves to a text file.
    """
    athlete_summary = {}
    lines = []  # store all lines for file output

    for fact in llm_facts:
        athlete = fact["athlete_id"]
        exercise = fact["exercise"]
        load = fact["load_trend"]
        volume = fact["volume_trend"]
        rpe = fact["rpe_trend"]
        flags = fact["flags"]
        status = fact["final_status"]

        if athlete not in athlete_summary:
            athlete_summary[athlete] = {"strong": 0, "fatigue": 0, "neutral": 0}

        header = f"\n=== {exercise} (Athlete {athlete}) ==="
        print(header)
        lines.append(header)

        bullets = []

        # Load trend
        if load == "progression":
            bullets.append("Load is increasing steadily — maintain intensity and focus on form.")
        elif load == "regression":
            bullets.append("Load is decreasing — consider reviewing technique or adjusting intensity.")
        elif load == "plateau":
            bullets.append("Load is stable — consider small variations (sets, reps, intensity) to stimulate adaptation.")
        else:
            bullets.append("Load trend is neutral or insufficient data.")

        # Volume trend
        if volume == "progression":
            bullets.append("Weekly volume is increasing steadily — maintain current plan. If athlete reports fatigue, consider active recovery or slight deloads.")
        elif volume == "regression":
            bullets.append("Weekly volume is decreasing — check for missed sessions or consistency issues. Adjust plan to ensure progressive overload.")
        elif volume == "plateau":
            bullets.append("Weekly volume is stable — consider adding small variations (sets, reps, intensity) to stimulate adaptation.")
        else:
            bullets.append("Volume trend is neutral or insufficient data — track more sessions to evaluate.")

        # RPE trend
        if rpe == "progression":
            bullets.append("RPE is increasing — athlete may be approaching fatigue. Ensure recovery strategies are applied.")
        elif rpe == "regression":
            bullets.append("RPE is decreasing — sessions may feel easier, may indicate underload or improved fitness.")
        elif rpe == "plateau":
            bullets.append("RPE is stable — training intensity is controlled, continue monitoring fatigue.")
        else:
            bullets.append("RPE trend is neutral or insufficient data — monitor athlete perception.")

        # Flags
        if flags.get("fatigue_risk"):
            bullets.append("⚠️ Fatigue risk detected — monitor recovery closely.")
            athlete_summary[athlete]["fatigue"] += 1
        if flags.get("strong_progress"):
            bullets.append("✅ Strong progress observed — keep current approach.")
            athlete_summary[athlete]["strong"] += 1
        if flags.get("accumulation_phase"):
            bullets.append("📈 Accumulation phase — expect gradual improvement.")

        # Generate final recommendation based on trends and flags
        if flags.get("strong_progress") or (load=="progression" and volume=="progression" and rpe in ["plateau","neutral"]):
            recommendation = "Continue current plan, gradually increase weights while keeping reps consistent, and focus on recovery."
        elif flags.get("fatigue_risk") or (rpe=="progression" and load in ["plateau","regression"]):
            recommendation = "Consider reducing load or volume for 1–2 sessions and prioritize recovery and mobility work."
        elif volume=="plateau" and load=="plateau":
            recommendation = "Introduce small variations in sets, reps, or intensity to stimulate adaptation."
        else:
            recommendation = "Maintain current plan and monitor progress."

        bullets.append(f"💡 Recommendation: {recommendation}")

        # Final status
        bullets.append(f"Overall status: {status}")
        if status == "neutral":
            athlete_summary[athlete]["neutral"] += 1

        # Print and store bullets
        for b in bullets:
            print(f"- {b}")
            lines.append(f"- {b}")

    # Print and store summary per athlete
    for athlete, counts in athlete_summary.items():
        summary_lines = [
            f"\n--- Athlete {athlete} Summary ---",
            f"✅ Strong progress on {counts['strong']} exercise(s)",
            f"⚠️ Monitor fatigue on {counts['fatigue']} exercise(s)",
            f"Neutral status on {counts['neutral']} exercise(s)"
        ]
        for line in summary_lines:
            print(line)
            lines.append(line)

    # Save all lines to text file
    with open(filename, "w") as f:
        f.write("\n".join(lines))

    print(f"\n✅ Athlete report saved to '{filename}'")
    return lines
