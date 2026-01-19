import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from src.preprocessing import add_week_column, compute_weekly_metrics

# Set style
plt.style.use('ggplot')
sns.set_theme(style="whitegrid")
sns.set_palette("husl")

def load_and_prepare_data(data_file="data/mock_data_7athletes.csv"):
    """Load and prepare the training data."""
    df = pd.read_csv(data_file)
    df["date"] = pd.to_datetime(df["date"])
    df = add_week_column(df)
    df['volume'] = df['weight_kg'] * df['sets'] * df['reps']
    df['load'] = df['volume'] * df['rpe']
    
    # Add session ID for tracking individual training sessions
    df['session_id'] = df.groupby(['athlete_id', 'date']).ngroup()
    return df

def plot_athlete_metrics(athlete_id, df, weekly_metrics, output_dir='visualizations'):
    """Generate metrics plots for a single athlete."""
    athlete_data = weekly_metrics[weekly_metrics['athlete_id'] == athlete_id]
    athlete_exercises = df[df['athlete_id'] == athlete_id]
    
    # Create figure with subplots
    fig = plt.figure(figsize=(15, 18))
    gs = fig.add_gridspec(3, 2, width_ratios=[2, 1])
    
    # Plot 1: Load and Volume (top left)
    ax1 = fig.add_subplot(gs[0, 0])
    ax1_vol = ax1.twinx()
    
    sns.lineplot(data=athlete_data, x='week', y='total_load', marker='o', ax=ax1, label='Total Load')
    sns.barplot(data=athlete_data, x='week', y='total_volume', alpha=0.3, ax=ax1_vol, color='orange', label='Volume')
    
    ax1.set_ylabel('Total Load (kg × RPE)')
    ax1_vol.set_ylabel('Total Volume (kg)')
    ax1.set_xlabel('Week')
    ax1.legend(loc='upper left')
    ax1_vol.legend(loc='upper right')
    ax1.set_title('Weekly Training Load and Volume')
    
    # Plot 2: Average Weight and RPE (middle left)
    ax2 = fig.add_subplot(gs[1, 0])
    ax2_rpe = ax2.twinx()
    
    sns.lineplot(data=athlete_data, x='week', y='avg_weight', marker='o', ax=ax2, color='green', label='Avg Weight')
    sns.lineplot(data=athlete_data, x='week', y='avg_rpe', marker='s', ax=ax2_rpe, color='red', label='Avg RPE')
    
    ax2.set_ylabel('Average Weight (kg)')
    ax2_rpe.set_ylabel('Average RPE')
    ax2.set_xlabel('Week')
    ax2.legend(loc='upper left')
    ax2_rpe.legend(loc='upper right')
    ax2.set_title('Average Weight and RPE')
    
    # Plot 3: Exercise-specific trends (bottom left)
    ax3 = fig.add_subplot(gs[2, 0])
    
    for exercise in athlete_exercises['exercise'].unique():
        ex_data = athlete_exercises[athlete_exercises['exercise'] == exercise]
        ex_weekly = ex_data.groupby('week')['load'].sum().reset_index()
        if not ex_weekly.empty:
            sns.lineplot(data=ex_weekly, x='week', y='load', marker='o', ax=ax3, label=exercise)
    
    ax3.set_ylabel('Exercise Load (kg × RPE)')
    ax3.set_xlabel('Week')
    ax3.set_title('Exercise-Specific Load Trends')
    ax3.legend()
    
    # Plot 4: Exercise distribution (top right)
    ax4 = fig.add_subplot(gs[0, 1])
    ex_counts = athlete_exercises['exercise'].value_counts()
    sns.barplot(x=ex_counts.values, y=ex_counts.index, ax=ax4, palette='viridis')
    ax4.set_title('Exercise Distribution')
    ax4.set_xlabel('Number of Sessions')
    
    # Plot 5: RPE distribution (middle right)
    ax5 = fig.add_subplot(gs[1, 1])
    sns.histplot(athlete_exercises['rpe'], bins=range(5, 11), discrete=True, ax=ax5, kde=True)
    ax5.set_title('RPE Distribution')
    ax5.set_xlabel('RPE')
    ax5.set_xticks(range(5, 11))
    
    # Plot 6: Session volume over time (bottom right)
    ax6 = fig.add_subplot(gs[2, 1])
    session_vol = athlete_exercises.groupby('session_id')['volume'].sum().reset_index()
    sns.lineplot(data=session_vol, x=session_vol.index, y='volume', ax=ax6, marker='o')
    ax6.set_title('Session Volume Over Time')
    ax6.set_xlabel('Session Number')
    ax6.set_ylabel('Total Volume (kg)')
    
    plt.tight_layout()
    plt.suptitle(f'Athlete {athlete_id} - Training Analysis', y=1.02, fontsize=16)
    plt.savefig(f'{output_dir}/athlete_{athlete_id}_analysis.png', dpi=300, bbox_inches='tight')
    plt.close()

def plot_weekly_metrics(df, output_dir='visualizations'):
    """Generate and save weekly metrics plots for all athletes."""
    os.makedirs(output_dir, exist_ok=True)
    weekly_metrics = compute_weekly_metrics(df)
    
    # Create individual athlete reports
    for athlete_id in df['athlete_id'].unique():
        plot_athlete_metrics(athlete_id, df, weekly_metrics, output_dir)
    
    # Create summary visualization
    plt.figure(figsize=(14, 8))
    
    # Plot 1: Load progression across athletes
    plt.subplot(2, 1, 1)
    sns.lineplot(data=weekly_metrics, x='week', y='total_load', hue='athlete_id', 
                 marker='o', palette='tab10')
    plt.title('Weekly Training Load by Athlete')
    plt.xlabel('Week')
    plt.ylabel('Total Load (kg × RPE)')
    plt.legend(title='Athlete ID')
    
    # Plot 2: RPE trends
    plt.subplot(2, 1, 2)
    sns.lineplot(data=weekly_metrics, x='week', y='avg_rpe', hue='athlete_id', 
                 marker='s', palette='tab10')
    plt.title('Average RPE by Athlete')
    plt.xlabel('Week')
    plt.ylabel('Average RPE')
    plt.legend(title='Athlete ID')
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/all_athletes_summary.png', dpi=300, bbox_inches='tight')
    plt.close()

def plot_training_distribution(df, output_dir='visualizations'):
    """Generate distribution plots for training data."""
    os.makedirs(output_dir, exist_ok=True)
    
    # Exercise distribution
    plt.figure(figsize=(12, 6))
    g = sns.countplot(data=df, x='exercise', hue='athlete_id')
    plt.title('Exercise Distribution by Athlete')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f'{output_dir}/exercise_distribution.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # RPE distribution
    plt.figure(figsize=(10, 6))
    sns.histplot(data=df, x='rpe', bins=range(1, 11), discrete=True, hue='athlete_id', multiple='dodge')
    plt.title('RPE Distribution by Athlete')
    plt.xticks(range(1, 11))
    plt.tight_layout()
    plt.savefig(f'{output_dir}/rpe_distribution.png', dpi=300, bbox_inches='tight')
    plt.close()

def main():
    print("Loading and preparing data...")
    df = load_and_prepare_data()
    
    print("Generating weekly metrics plots...")
    plot_weekly_metrics(df)
    
    print("Generating distribution plots...")
    plot_training_distribution(df)
    
    print("Visualizations saved to 'visualizations' directory.")

if __name__ == "__main__":
    main()
