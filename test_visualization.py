import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.visualization import TrainingVisualizer
import plotly.io as pio

# Generate sample data
np.random.seed(42)
dates = pd.date_range(start='2023-01-01', periods=12, freq='W')
week_ids = [f"{d.year}-{d.isocalendar()[1]}" for d in dates]

data = {
    'athlete_id': ['A1'] * 12,
    'date_min': dates,
    'date_max': [d + timedelta(days=6) for d in dates],
    'internal_load': np.random.normal(3000, 500, 12).cumsum(),
    'rpe_mean': np.random.uniform(5, 9, 12),
    'acwr': np.random.uniform(0.5, 1.8, 12),
    'monotony': np.random.uniform(1.0, 3.0, 12),
    'total_volume': np.random.normal(10000, 2000, 12).cumsum(),
    'exercise': ['Squat', 'Bench', 'Deadlift'] * 4,
    'week_id': week_ids,
    'load_sum': np.random.normal(5000, 1000, 12),
    'volume_sum': np.random.normal(15000, 3000, 12),
    'date_count': [3, 4, 3, 4, 3, 4, 3, 4, 3, 4, 3, 4]
}

# Create risk scores
risk_data = {
    'date': dates,
    'week_id': week_ids,
    'fatigue_risk_score': np.clip(np.random.normal(0.5, 0.2, 12), 0, 1),
    'risk_category': np.random.choice(['low', 'medium', 'high'], 12, p=[0.5, 0.3, 0.2])
}

# Create DataFrames
weekly_metrics = pd.DataFrame(data)
risk_scores = pd.DataFrame(risk_data)

# Initialize visualizer
visualizer = TrainingVisualizer(weekly_metrics, athlete_id='A1')

# 1. Show Load vs RPE plot
print("Generating Load vs RPE plot...")
fig1 = visualizer.plot_load_vs_rpe(interactive=True)
fig1.show()

# 2. Show Workload Balance (ACWR) plot
print("Generating Workload Balance plot...")
fig2 = visualizer.plot_workload_balance(interactive=True)
fig2.show()

# 3. Show Fatigue Risk Timeline
print("Generating Fatigue Risk Timeline...")
fig3 = visualizer.plot_fatigue_risk_timeline(risk_scores, interactive=True)
fig3.show()

# 4. Create a complete dashboard
print("Generating Athlete Dashboard...")
dashboard = visualizer.create_athlete_dashboard(weekly_metrics, risk_scores)
dashboard.show()

print("All visualizations generated successfully!")
