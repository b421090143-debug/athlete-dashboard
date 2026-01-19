import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os

def generate_small_mock_data():
    """Generate small mock training data for 2 athletes"""
    
    # Two focused athlete profiles
    athletes = [
        {
            'id': 'ATH001', 
            'name': 'John "The Beast" Smith', 
            'age': 28, 
            'gender': 'Male',
            'sport': 'Powerlifting', 
            'training_age': 6, 
            'recovery': 'slow'
        },
        {
            'id': 'ATH002', 
            'name': 'Sarah "Thunder" Johnson', 
            'age': 25, 
            'gender': 'Female',
            'sport': 'Olympic Weightlifting', 
            'training_age': 4, 
            'recovery': 'normal'
        }
    ]
    
    # Core exercises with realistic weight ranges
    exercises = {
        'Squat': {'male': {'intermediate': (80, 140), 'advanced': (120, 200)},
                'female': {'intermediate': (60, 100), 'advanced': (80, 140)}},
        'Bench Press': {'male': {'intermediate': (60, 100), 'advanced': (80, 150)},
                      'female': {'intermediate': (40, 70), 'advanced': (50, 90)}},
        'Deadlift': {'male': {'intermediate': (90, 160), 'advanced': (140, 250)},
                    'female': {'intermediate': (70, 120), 'advanced': (100, 180)}},
        'Overhead Press': {'male': {'intermediate': (40, 70), 'advanced': (50, 90)},
                         'female': {'intermediate': (25, 45), 'advanced': (30, 60)}},
        'Barbell Row': {'male': {'intermediate': (50, 80), 'advanced': (70, 120)},
                      'female': {'intermediate': (30, 50), 'advanced': (40, 70)}},
        'Pull-up': {'male': {'intermediate': (10, 25), 'advanced': (20, 40)},
                  'female': {'intermediate': (5, 15), 'advanced': (10, 25)}},
        'Clean & Jerk': {'male': {'intermediate': (40, 70), 'advanced': (60, 100)},
                        'female': {'intermediate': (30, 50), 'advanced': (40, 70)}},
        'Snatch': {'male': {'intermediate': (35, 60), 'advanced': (50, 80)},
                  'female': {'intermediate': (25, 40), 'advanced': (30, 60)}},
        'Front Squat': {'male': {'intermediate': (60, 100), 'advanced': (80, 140)},
                       'female': {'intermediate': (40, 70), 'advanced': (50, 100)}},
        'Romanian Deadlift': {'male': {'intermediate': (70, 120), 'advanced': (100, 160)},
                           'female': {'intermediate': (50, 80), 'advanced': (70, 110)}},
        'Lat Pulldown': {'male': {'intermediate': (50, 80), 'advanced': (70, 110)},
                       'female': {'intermediate': (35, 55), 'advanced': (45, 75)}},
        'Bicep Curl': {'male': {'intermediate': (20, 35), 'advanced': (25, 50)},
                     'female': {'intermediate': (15, 25), 'advanced': (20, 35)}},
        'Tricep Extension': {'male': {'intermediate': (18, 30), 'advanced': (25, 45)},
                           'female': {'intermediate': (12, 22), 'advanced': (18, 30)}},
        'Leg Curl': {'male': {'intermediate': (30, 50), 'advanced': (40, 70)},
                    'female': {'intermediate': (20, 35), 'advanced': (25, 50)}},
        'Dumbbell Press': {'male': {'intermediate': (30, 50), 'advanced': (40, 70)},
                         'female': {'intermediate': (20, 35), 'advanced': (25, 50)}}
    }
    
    # Determine athlete level based on training age
    def get_level(training_age):
        if training_age < 2:
            return 'beginner'
        elif training_age < 4:
            return 'intermediate'
        elif training_age < 7:
            return 'advanced'
        else:
            return 'elite'
    
    # Generate 12 weeks of training data for each athlete
    data = []
    start_date = datetime(2024, 1, 1)
    
    for athlete in athletes:
        level = get_level(athlete['training_age'])
        gender = athlete['gender'].lower()
        
        # Vary start dates for different athletes
        athlete_start = start_date + timedelta(days=random.randint(0, 7))
        
        for week in range(12):  # 12 weeks of data
            # Training frequency varies by sport and recovery profile
            if athlete['sport'] == 'Powerlifting':
                sessions_per_week = random.randint(3, 4)
            elif athlete['sport'] == 'Olympic Weightlifting':
                sessions_per_week = random.randint(3, 4)
            else:
                sessions_per_week = random.randint(3, 4)
            
            # Adjust for recovery profile
            if athlete['recovery'] == 'slow':
                sessions_per_week = max(2, sessions_per_week - 1)
            elif athlete['recovery'] == 'fast':
                sessions_per_week = min(4, sessions_per_week + 1)
            
            session_days = sorted(random.sample(range(7), sessions_per_week))
            
            for day in session_days:
                current_date = athlete_start + timedelta(weeks=week, days=day)
                
                # Select exercises based on sport
                if athlete['sport'] == 'Powerlifting':
                    main_exercises = ['Squat', 'Bench Press', 'Deadlift']
                    accessory_exercises = ['Barbell Row', 'Lat Pulldown', 'Dumbbell Press', 'Tricep Extension', 'Bicep Curl']
                elif athlete['sport'] == 'Olympic Weightlifting':
                    main_exercises = ['Snatch', 'Clean & Jerk', 'Front Squat']
                    accessory_exercises = ['Overhead Press', 'Romanian Deadlift', 'Pull-up']
                else:
                    main_exercises = ['Squat', 'Bench Press', 'Deadlift']
                    accessory_exercises = ['Barbell Row', 'Lat Pulldown', 'Dumbbell Press']
                
                # Select exercises for this session
                num_main = random.randint(1, 2)
                num_accessory = random.randint(1, 2)
                
                session_exercises = random.sample(main_exercises, num_main) + random.sample(accessory_exercises, num_accessory)
                
                for exercise in session_exercises:
                    # Get weight range for this exercise
                    if exercise in exercises:
                        weight_range = exercises[exercise][gender][level]
                        base_weight = random.uniform(weight_range[0], weight_range[1])
                    else:
                        # Default weight if exercise not found
                        base_weight = random.uniform(20, 100)
                    
                    # Progressive overload with realistic variation
                    week_factor = 1 + (week * 0.03)  # 3% progression per week
                    progression_factor = random.uniform(0.95, 1.05)  # Natural variation
                    final_weight = base_weight * week_factor * progression_factor
                    
                    # Round to realistic increments
                    if 'Pull-up' in exercise:
                        final_weight = max(0, round(final_weight / 2.5) * 2.5)
                    else:
                        final_weight = round(final_weight / 2.5) * 2.5
                    
                    # Generate sets and reps based on exercise type
                    if exercise in ['Squat', 'Bench Press', 'Deadlift']:
                        sets = random.choice([3, 4, 5])
                        reps = random.choice([3, 5, 6, 8])
                    elif exercise in ['Snatch', 'Clean & Jerk']:
                        sets = random.choice([3, 4, 5])
                        reps = random.choice([1, 2, 3])
                    else:
                        sets = random.choice([3, 4])
                        reps = random.choice([8, 10, 12, 15])
                    
                    # RPE calculation based on athlete profile
                    base_rpe = 7  # Base RPE
                    
                    # Adjust for sport
                    if athlete['sport'] == 'Powerlifting':
                        base_rpe += 1
                    
                    # Adjust for recovery profile
                    if athlete['recovery'] == 'slow':
                        base_rpe += 0.5
                    elif athlete['recovery'] == 'fast':
                        base_rpe -= 0.5
                    
                    # Adjust for training age
                    if athlete['training_age'] < 2:
                        base_rpe -= 0.5
                    elif athlete['training_age'] > 7:
                        base_rpe += 0.5
                    
                    # Add variation and fatigue
                    rpe_variation = random.uniform(-1, 1)
                    fatigue_factor = min(week / 12, 0.5)  # Gradual fatigue accumulation
                    
                    rpe = max(1, min(10, base_rpe + rpe_variation + fatigue_factor))
                    rpe = round(rpe * 2) / 2  # Round to nearest 0.5
                    
                    # Occasional bad days or PR attempts
                    if random.random() < 0.05:  # 5% chance of bad day
                        final_weight *= 0.9
                        rpe = max(rpe + 1, 8)
                    elif random.random() < 0.02:  # 2% chance of PR attempt
                        final_weight *= 1.05
                        rpe = min(10, rpe + 0.5)
                    
                    data.append({
                        'date': current_date.strftime('%Y-%m-%d'),
                        'athlete_id': athlete['id'],
                        'exercise': exercise,
                        'weight_kg': final_weight,
                        'sets': sets,
                        'reps': reps,
                        'rpe': rpe
                    })
    
    # Create DataFrame and sort
    df = pd.DataFrame(data)
    df = df.sort_values(['date', 'athlete_id']).reset_index(drop=True)
    
    return df

# Generate the small dataset
print("🏋️ Generating small mock training data...")

small_data = generate_small_mock_data()

# Save to CSV
small_data.to_csv('small_athlete_data.csv', index=False)

# Display statistics
print(f"\n📊 Dataset Statistics:")
print(f"Total training sessions: {len(small_data)}")
print(f"Number of athletes: {small_data['athlete_id'].nunique()}")
print(f"Number of exercises: {small_data['exercise'].nunique()}")
print(f"Date range: {small_data['date'].min()} to {small_data['date'].max()}")
print(f"Training weeks: {(pd.to_datetime(small_data['date']).max() - pd.to_datetime(small_data['date']).min()).days // 7 + 1}")

print(f"\n👥 Athlete Breakdown:")
for athlete_id in small_data['athlete_id'].unique():
    athlete_data = small_data[small_data['athlete_id'] == athlete_id]
    print(f"{athlete_id}: {len(athlete_data)} sessions, {athlete_data['date'].nunique()} training days")

print(f"\n💪 Exercise Distribution:")
exercise_counts = small_data['exercise'].value_counts()
for exercise, count in exercise_counts.items():
    avg_weight = small_data[small_data['exercise'] == exercise]['weight_kg'].mean()
    print(f"{exercise}: {count} sessions, avg weight: {avg_weight:.1f}kg")

# File size information
file_size = os.path.getsize('small_athlete_data.csv')
print(f"\n📁 File size: {file_size / 1024:.1f} KB")

print(f"\n✅ Small mock data saved as 'small_athlete_data.csv'")
print(f"🎯 Perfect for quick testing of the Athlete Intelligence Platform!")
