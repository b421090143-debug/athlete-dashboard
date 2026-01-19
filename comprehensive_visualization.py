import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
from datetime import datetime

# Set style
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

# Load and process data
print("Loading data...")
df = pd.read_csv("data/mock_data_7athletes.csv")
df["date"] = pd.to_datetime(df["date"])

# Import preprocessing functions
from src.preprocessing import add_week_column, compute_weekly_metrics, analyze_exercise_trends, generate_llm_facts

# Process data
df_with_weeks = add_week_column(df)
weekly_metrics = compute_weekly_metrics(df_with_weeks)
trends = analyze_exercise_trends(weekly_metrics)
llm_facts = generate_llm_facts(trends)

# Create visualizations directory
os.makedirs('visualizations', exist_ok=True)

print("Generating visualizations...")

# 1. Overview Dashboard
fig1 = make_subplots(
    rows=2, cols=2,
    subplot_titles=('Training Volume Over Time', 'Average RPE by Athlete', 
                   'Exercise Distribution', 'Weekly Training Frequency'),
    specs=[[{"secondary_y": False}, {"secondary_y": False}],
           [{"secondary_y": False}, {"secondary_y": False}]]
)

# Training volume over time
volume_by_week = weekly_metrics.groupby('week')['total_volume'].sum()
fig1.add_trace(
    go.Scatter(x=volume_by_week.index, y=volume_by_week.values, 
               mode='lines+markers', name='Total Volume', line=dict(color='#2E86AB')),
    row=1, col=1
)

# Average RPE by athlete
avg_rpe_by_athlete = df.groupby('athlete_id')['rpe'].mean()
fig1.add_trace(
    go.Bar(x=avg_rpe_by_athlete.index, y=avg_rpe_by_athlete.values,
           name='Avg RPE', marker_color='#A23B72'),
    row=1, col=2
)

# Exercise distribution
exercise_counts = df['exercise'].value_counts()
fig1.add_trace(
    go.Bar(x=exercise_counts.index, y=exercise_counts.values,
           name='Exercise Count', marker_color='#F18F01'),
    row=2, col=1
)

# Weekly training frequency
sessions_by_week = df_with_weeks.groupby('week').size()
fig1.add_trace(
    go.Scatter(x=sessions_by_week.index, y=sessions_by_week.values,
               mode='lines+markers', name='Sessions', line=dict(color='#C73E1D')),
    row=2, col=2
)

fig1.update_layout(
    title_text="Athlete Training Analytics Dashboard",
    showlegend=False,
    height=800,
    title_x=0.5
)

fig1.write_html("visualizations/01_dashboard.html")
# fig1.write_image("visualizations/01_dashboard.png", width=1200, height=800)

# 2. Athlete Progression Analysis
fig2 = make_subplots(
    rows=2, cols=2,
    subplot_titles=('Weight Progression by Exercise', 'Volume Trends',
                   'RPE Evolution', 'Performance Status Distribution')
)

# Weight progression by exercise
for exercise in df['exercise'].unique():
    exercise_data = weekly_metrics[weekly_metrics['exercise'] == exercise]
    fig2.add_trace(
        go.Scatter(x=exercise_data['week'], y=exercise_data['avg_weight'],
                   mode='lines+markers', name=exercise,
                   showlegend=False),
        row=1, col=1
    )

# Volume trends
for athlete_id in df['athlete_id'].unique()[:3]:  # Limit to 3 athletes for clarity
    athlete_data = weekly_metrics[weekly_metrics['athlete_id'] == athlete_id]
    fig2.add_trace(
        go.Scatter(x=athlete_data['week'], y=athlete_data['total_volume'],
                   mode='lines+markers', name=f'Athlete {athlete_id}',
                   showlegend=False),
        row=1, col=2
    )

# RPE evolution
rpe_by_week = weekly_metrics.groupby('week')['avg_rpe'].mean()
fig2.add_trace(
    go.Scatter(x=rpe_by_week.index, y=rpe_by_week.values,
               mode='lines+markers', name='Avg RPE', line=dict(color='#E63946'),
               showlegend=False),
    row=2, col=1
)

# Performance status distribution
status_counts = pd.Series([fact['final_status'] for fact in llm_facts]).value_counts()
fig2.add_trace(
    go.Bar(x=status_counts.index, y=status_counts.values,
           name='Status Count', marker_color='#457B9D', showlegend=False),
    row=2, col=2
)

fig2.update_layout(
    title_text="Athlete Performance Analysis",
    showlegend=False,
    height=800,
    title_x=0.5
)

fig2.write_html("visualizations/02_performance_analysis.html")
# fig2.write_image("visualizations/02_performance_analysis.png", width=1200, height=800)

# 3. Individual Athlete Deep Dive
fig3 = make_subplots(
    rows=3, cols=1,
    subplot_titles=('Athlete 1 - Performance Trends', 'Athlete 2 - Performance Trends', 
                   'Athlete 3 - Performance Trends'),
    vertical_spacing=0.08
)

for i, athlete_id in enumerate([1, 2, 3]):
    athlete_data = weekly_metrics[weekly_metrics['athlete_id'] == athlete_id]
    
    for exercise in athlete_data['exercise'].unique():
        exercise_data = athlete_data[athlete_data['exercise'] == exercise]
        fig3.add_trace(
            go.Scatter(x=exercise_data['week'], y=exercise_data['avg_weight'],
                       mode='lines+markers', name=f'{exercise} (Athlete {athlete_id})',
                       showlegend=(i == 0)),  # Only show legend for first subplot
            row=i+1, col=1
        )

fig3.update_layout(
    title_text="Individual Athlete Progression Deep Dive",
    height=1200,
    title_x=0.5,
    showlegend=True
)

fig3.write_html("visualizations/03_athlete_deep_dive.html")
# fig3.write_image("visualizations/03_athlete_deep_dive.png", width=1200, height=1200)

# 4. Trend Analysis Heatmap
# Create trend matrix
trend_matrix = []
for fact in llm_facts:
    trend_matrix.append({
        'athlete_id': fact['athlete_id'],
        'exercise': fact['exercise'],
        'load_trend': fact['load_trend'],
        'volume_trend': fact['volume_trend'],
        'rpe_trend': fact['rpe_trend'],
        'status': fact['final_status']
    })

trend_df = pd.DataFrame(trend_matrix)

# Create pivot tables for heatmaps
load_pivot = trend_df.pivot_table(index='athlete_id', columns='exercise', values='load_trend', aggfunc='first')
status_pivot = trend_df.pivot_table(index='athlete_id', columns='exercise', values='status', aggfunc='first')

# Convert trends to numeric values for heatmap
trend_mapping = {'regression': -1, 'plateau': 0, 'progression': 1}
status_mapping = {'needs_attention': -1, 'neutral': 0, 'excellent_progress': 1, 'monitor_fatigue': 0.5}

load_numeric = load_pivot.replace(trend_mapping)
status_numeric = status_pivot.replace(status_mapping)

fig4 = make_subplots(
    rows=1, cols=2,
    subplot_titles=('Load Progression Heatmap', 'Performance Status Heatmap')
)

# Load progression heatmap
fig4.add_trace(
    go.Heatmap(z=load_numeric.values, x=load_numeric.columns, y=load_numeric.index,
               colorscale='RdYlGn', name='Load Trend',
               showscale=False),
    row=1, col=1
)

# Performance status heatmap
fig4.add_trace(
    go.Heatmap(z=status_numeric.values, x=status_numeric.columns, y=status_numeric.index,
               colorscale='RdYlGn', name='Status',
               showscale=True),
    row=1, col=2
)

fig4.update_layout(
    title_text="Trend Analysis Heatmaps",
    height=600,
    title_x=0.5
)

fig4.write_html("visualizations/04_trend_heatmaps.html")
# fig4.write_image("visualizations/04_trend_heatmaps.png", width=1200, height=600)

# 5. Statistical Summary
fig5, axes = plt.subplots(2, 2, figsize=(15, 12))
fig5.suptitle('Training Data Statistical Summary', fontsize=16, fontweight='bold')

# Weight distribution by exercise
sns.boxplot(data=df, x='exercise', y='weight_kg', ax=axes[0,0])
axes[0,0].set_title('Weight Distribution by Exercise')
axes[0,0].tick_params(axis='x', rotation=45)

# RPE distribution
sns.histplot(data=df, x='rpe', bins=10, kde=True, ax=axes[0,1])
axes[0,1].set_title('RPE Distribution')
axes[0,1].set_xlabel('Rate of Perceived Exertion')

# Volume vs Weight scatter
sns.scatterplot(data=weekly_metrics, x='avg_weight', y='total_volume', 
                hue='athlete_id', size='avg_rpe', sizes=(50, 200), ax=axes[1,0])
axes[1,0].set_title('Volume vs Weight Analysis')

# Training frequency by athlete
sns.countplot(data=df, x='athlete_id', ax=axes[1,1])
axes[1,1].set_title('Training Sessions by Athlete')

plt.tight_layout()
plt.savefig('visualizations/05_statistical_summary.png', dpi=300, bbox_inches='tight')
plt.close()

print("✅ All visualizations generated successfully!")
print(f"📁 Visualizations saved in 'visualizations/' directory:")
print("   - 01_dashboard.png/html - Overview dashboard")
print("   - 02_performance_analysis.png/html - Performance trends")
print("   - 03_athlete_deep_dive.png/html - Individual athlete analysis")
print("   - 04_trend_heatmaps.png/html - Trend heatmaps")
print("   - 05_statistical_summary.png - Statistical summary")
