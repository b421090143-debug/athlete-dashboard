import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os

def generate_comprehensive_mock_data():
    """Generate comprehensive mock training data for athlete intelligence platform"""
    
    # Expanded athlete profiles with realistic data
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
        },
        {
            'id': 'ATH003', 
            'name': 'Mike "Rookie" Chen', 
            'age': 22, 
            'gender': 'Male',
            'sport': 'Bodybuilding', 
            'training_age': 1.5, 
            'recovery': 'fast'
        },
        {
            'id': 'ATH004', 
            'name': 'Emily "Precision" Davis', 
            'age': 30, 
            'gender': 'Female',
            'sport': 'CrossFit', 
            'training_age': 5, 
            'recovery': 'normal'
        },
        {
            'id': 'ATH005', 
            'name': 'Alex "Powerhouse" Rodriguez', 
            'age': 26, 
            'gender': 'Male',
            'sport': 'Strongman', 
            'training_age': 3, 
            'recovery': 'slow'
        },
        {
            'id': 'ATH006', 
            'name': 'David "Iron" Wilson', 
            'age': 35, 
            'gender': 'Male',
            'sport': 'Powerlifting', 
            'training_age': 12, 
            'recovery': 'slow'
        },
        {
            'id': 'ATH007', 
            'name': 'Lisa "Lightning" Brown', 
            'age': 24, 
            'gender': 'Female',
            'sport': 'Olympic Weightlifting', 
            'training_age': 3, 
            'recovery': 'fast'
        },
        {
            'id': 'ATH008', 
            'name': 'Mark "Rocket" Taylor', 
            'age': 29, 
            'gender': 'Male',
            'sport': 'Bodybuilding', 
            'training_age': 2, 
            'recovery': 'normal'
        },
        {
            'id': 'ATH009', 
            'name': 'Jessica "Phoenix" Martinez', 
            'age': 27, 
            'gender': 'Female',
            'sport': 'CrossFit', 
            'training_age': 4, 
            'recovery': 'normal'
        },
        {
            'id': 'ATH010', 
            'name': 'Tom "Titan" Anderson', 
            'age': 31, 
            'gender': 'Male',
            'sport': 'Strongman', 
            'training_age': 5, 
            'recovery': 'slow'
        }
    ]
    
    # Comprehensive exercise list with realistic weight ranges
    exercises = {
        'Squat': {'male': {'beginner': (40, 80), 'intermediate': (80, 140), 'advanced': (120, 200), 'elite': (180, 280)},
                'female': {'beginner': (20, 60), 'intermediate': (60, 100), 'advanced': (80, 140), 'elite': (120, 200)}},
        'Bench Press': {'male': {'beginner': (30, 60), 'intermediate': (60, 100), 'advanced': (80, 150), 'elite': (120, 200)},
                      'female': {'beginner': (15, 40), 'intermediate': (40, 70), 'advanced': (50, 90), 'elite': (70, 120)}},
        'Deadlift': {'male': {'beginner': (50, 90), 'intermediate': (90, 160), 'advanced': (140, 250), 'elite': (200, 350)},
                    'female': {'beginner': (30, 70), 'intermediate': (70, 120), 'advanced': (100, 180), 'elite': (140, 250)}},
        'Overhead Press': {'male': {'beginner': (20, 40), 'intermediate': (40, 70), 'advanced': (50, 90), 'elite': (70, 120)},
                         'female': {'beginner': (10, 25), 'intermediate': (25, 45), 'advanced': (30, 60), 'elite': (40, 80)}},
        'Barbell Row': {'male': {'beginner': (30, 50), 'intermediate': (50, 80), 'advanced': (70, 120), 'elite': (100, 160)},
                      'female': {'beginner': (15, 30), 'intermediate': (30, 50), 'advanced': (40, 70), 'elite': (50, 100)}},
        'Pull-up': {'male': {'beginner': (0, 10), 'intermediate': (10, 25), 'advanced': (20, 40), 'elite': (30, 60)},
                  'female': {'beginner': (0, 5), 'intermediate': (5, 15), 'advanced': (10, 25), 'elite': (15, 35)}},
        'Clean & Jerk': {'male': {'beginner': (20, 40), 'intermediate': (40, 70), 'advanced': (60, 100), 'elite': (80, 140)},
                        'female': {'beginner': (10, 30), 'intermediate': (30, 50), 'advanced': (40, 70), 'elite': (50, 100)}},
        'Snatch': {'male': {'beginner': (15, 35), 'intermediate': (35, 60), 'advanced': (50, 80), 'elite': (70, 110)},
                  'female': {'beginner': (10, 25), 'intermediate': (25, 40), 'advanced': (30, 60), 'elite': (40, 80)}},
        'Front Squat': {'male': {'beginner': (30, 60), 'intermediate': (60, 100), 'advanced': (80, 140), 'elite': (120, 200)},
                       'female': {'beginner': (20, 40), 'intermediate': (40, 70), 'advanced': (50, 100), 'elite': (80, 140)}},
        'Romanian Deadlift': {'male': {'beginner': (40, 70), 'intermediate': (70, 120), 'advanced': (100, 160), 'elite': (140, 220)},
                           'female': {'beginner': (25, 50), 'intermediate': (50, 80), 'advanced': (70, 110), 'elite': (100, 150)}},
        'Leg Press': {'male': {'beginner': (80, 150), 'intermediate': (150, 250), 'advanced': (200, 350), 'elite': (300, 500)},
                    'female': {'beginner': (50, 100), 'intermediate': (100, 180), 'advanced': (150, 250), 'elite': (200, 350)}},
        'Lat Pulldown': {'male': {'beginner': (30, 50), 'intermediate': (50, 80), 'advanced': (70, 110), 'elite': (90, 140)},
                       'female': {'beginner': (20, 35), 'intermediate': (35, 55), 'advanced': (45, 75), 'elite': (60, 100)}},
        'Dumbbell Press': {'male': {'beginner': (15, 30), 'intermediate': (30, 50), 'advanced': (40, 70), 'elite': (50, 90)},
                         'female': {'beginner': (8, 20), 'intermediate': (20, 35), 'advanced': (25, 50), 'elite': (35, 65)}},
        'Lateral Raise': {'male': {'beginner': (5, 15), 'intermediate': (15, 25), 'advanced': (20, 35), 'elite': (25, 45)},
                        'female': {'beginner': (3, 10), 'intermediate': (10, 18), 'advanced': (15, 25), 'elite': (20, 35)}},
        'Bicep Curl': {'male': {'beginner': (10, 20), 'intermediate': (20, 35), 'advanced': (25, 50), 'elite': (35, 65)},
                     'female': {'beginner': (5, 15), 'intermediate': (15, 25), 'advanced': (20, 35), 'elite': (25, 45)}},
        'Tricep Extension': {'male': {'beginner': (8, 18), 'intermediate': (18, 30), 'advanced': (25, 45), 'elite': (35, 55)},
                           'female': {'beginner': (5, 12), 'intermediate': (12, 22), 'advanced': (18, 30), 'elite': (25, 40)}},
        'Leg Curl': {'male': {'beginner': (15, 30), 'intermediate': (30, 50), 'advanced': (40, 70), 'elite': (50, 90)},
                    'female': {'beginner': (10, 20), 'intermediate': (20, 35), 'advanced': (25, 50), 'elite': (35, 65)}},
        'Calf Raise': {'male': {'beginner': (20, 40), 'intermediate': (40, 70), 'advanced': (60, 100), 'elite': (80, 140)},
                      'female': {'beginner': (15, 30), 'intermediate': (30, 50), 'advanced': (40, 70), 'elite': (50, 100)}},
        'Face Pull': {'male': {'beginner': (10, 20), 'intermediate': (20, 35), 'advanced': (30, 50), 'elite': (40, 70)},
                    'female': {'beginner': (8, 15), 'intermediate': (15, 25), 'advanced': (20, 35), 'elite': (30, 50)}},
        'Farmers Walk': {'male': {'beginner': (40, 80), 'intermediate': (80, 120), 'advanced': (100, 160), 'elite': (140, 220)},
                       'female': {'beginner': (25, 50), 'intermediate': (50, 80), 'advanced': (70, 110), 'elite': (90, 140)}},
        'Log Press': {'male': {'beginner': (20, 40), 'intermediate': (40, 70), 'advanced': (60, 100), 'elite': (80, 140)},
                    'female': {'beginner': (10, 25), 'intermediate': (25, 45), 'advanced': (35, 65), 'elite': (50, 90)}},
        'Stone Load': {'male': {'beginner': (30, 60), 'intermediate': (60, 100), 'advanced': (80, 140), 'elite': (120, 200)},
                     'female': {'beginner': (20, 40), 'intermediate': (40, 70), 'advanced': (60, 100), 'elite': (80, 140)}},
        'Yoke Walk': {'male': {'beginner': (100, 200), 'intermediate': (200, 300), 'advanced': (250, 400), 'elite': (350, 550)},
                     'female': {'beginner': (60, 120), 'intermediate': (120, 200), 'advanced': (150, 280), 'elite': (200, 350)}},
        'Box Jump': {'male': {'beginner': (20, 30), 'intermediate': (30, 40), 'advanced': (35, 50), 'elite': (40, 60)},
                    'female': {'beginner': (15, 25), 'intermediate': (25, 35), 'advanced': (30, 45), 'elite': (35, 55)}},
        'Burpees': {'male': {'beginner': (0, 10), 'intermediate': (10, 20), 'advanced': (20, 30), 'elite': (25, 40)},
                   'female': {'beginner': (0, 8), 'intermediate': (8, 15), 'advanced': (15, 25), 'elite': (20, 35)}},
        'Muscle Up': {'male': {'beginner': (0, 5), 'intermediate': (5, 10), 'advanced': (10, 15), 'elite': (15, 25)},
                     'female': {'beginner': (0, 3), 'intermediate': (3, 8), 'advanced': (8, 12), 'elite': (12, 20)}},
        'Handstand Push-up': {'male': {'beginner': (0, 3), 'intermediate': (3, 8), 'advanced': (8, 15), 'elite': (15, 25)},
                           'female': {'beginner': (0, 2), 'intermediate': (2, 5), 'advanced': (5, 10), 'elite': (10, 20)}},
        'Rowing Machine': {'male': {'beginner': (100, 200), 'intermediate': (200, 300), 'advanced': (300, 400), 'elite': (400, 500)},
                         'female': {'beginner': (80, 150), 'intermediate': (150, 250), 'advanced': (250, 350), 'elite': (350, 450)}},
        'Assault Bike': {'male': {'beginner': (200, 300), 'intermediate': (300, 400), 'advanced': (400, 500), 'elite': (500, 600)},
                        'female': {'beginner': (150, 250), 'intermediate': (250, 350), 'advanced': (350, 450), 'elite': (450, 550)}},
        'Ski Erg': {'male': {'beginner': (150, 250), 'intermediate': (250, 350), 'advanced': (350, 450), 'elite': (450, 550)},
                   'female': {'beginner': (120, 200), 'intermediate': (200, 300), 'advanced': (300, 400), 'elite': (400, 500)}}
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
    
    # Generate 24 weeks of training data for each athlete
    data = []
    start_date = datetime(2023, 1, 1)
    
    for athlete in athletes:
        level = get_level(athlete['training_age'])
        gender = athlete['gender'].lower()
        
        # Vary start dates for different athletes
        athlete_start = start_date + timedelta(days=random.randint(0, 14))
        
        for week in range(24):  # 24 weeks of data
            # Training frequency varies by sport and recovery profile
            if athlete['sport'] in ['Powerlifting', 'Strongman']:
                sessions_per_week = random.randint(3, 4)
            elif athlete['sport'] == 'CrossFit':
                sessions_per_week = random.randint(4, 6)
            else:
                sessions_per_week = random.randint(3, 5)
            
            # Adjust for recovery profile
            if athlete['recovery'] == 'slow':
                sessions_per_week = max(2, sessions_per_week - 1)
            elif athlete['recovery'] == 'fast':
                sessions_per_week = min(6, sessions_per_week + 1)
            
            session_days = sorted(random.sample(range(7), sessions_per_week))
            
            for day in session_days:
                current_date = athlete_start + timedelta(weeks=week, days=day)
                
                # Select exercises based on sport with some variety
                if athlete['sport'] == 'Powerlifting':
                    main_exercises = ['Squat', 'Bench Press', 'Deadlift']
                    accessory_exercises = ['Barbell Row', 'Lat Pulldown', 'Dumbbell Press', 'Tricep Extension', 'Bicep Curl']
                elif athlete['sport'] == 'Olympic Weightlifting':
                    main_exercises = ['Snatch', 'Clean & Jerk', 'Front Squat']
                    accessory_exercises = ['Overhead Press', 'Romanian Deadlift', 'Pull-up', 'Face Pull']
                elif athlete['sport'] == 'Bodybuilding':
                    main_exercises = ['Squat', 'Bench Press', 'Deadlift', 'Overhead Press']
                    accessory_exercises = ['Lateral Raise', 'Leg Curl', 'Calf Raise', 'Bicep Curl', 'Tricep Extension']
                elif athlete['sport'] == 'CrossFit':
                    main_exercises = ['Squat', 'Deadlift', 'Box Jump', 'Burpees']
                    accessory_exercises = ['Pull-up', 'Muscle Up', 'Rowing Machine', 'Assault Bike', 'Handstand Push-up']
                elif athlete['sport'] == 'Strongman':
                    main_exercises = ['Deadlift', 'Log Press', 'Stone Load', 'Yoke Walk']
                    accessory_exercises = ['Farmers Walk', 'Front Squat', 'Overhead Press', 'Barbell Row']
                else:
                    main_exercises = ['Squat', 'Bench Press', 'Deadlift']
                    accessory_exercises = ['Barbell Row', 'Lat Pulldown', 'Dumbbell Press']
                
                # Select exercises for this session
                num_main = random.randint(1, 2)
                num_accessory = random.randint(1, 3)
                
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
                    week_factor = 1 + (week * 0.02)  # 2% progression per week
                    progression_factor = random.uniform(0.95, 1.05)  # Natural variation
                    final_weight = base_weight * week_factor * progression_factor
                    
                    # Round to realistic increments
                    if 'Pull-up' in exercise or 'Muscle Up' in exercise or 'Handstand' in exercise:
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
                    elif exercise in ['Box Jump', 'Burpees', 'Muscle Up', 'Handstand Push-up']:
                        sets = random.choice([3, 4, 5])
                        reps = random.choice([5, 10, 15, 20])
                    elif 'Rowing Machine' in exercise or 'Assault Bike' in exercise or 'Ski Erg' in exercise:
                        sets = 1  # Time-based or distance-based
                        reps = random.randint(500, 2000)  # Calories/meters
                    else:
                        sets = random.choice([3, 4])
                        reps = random.choice([8, 10, 12, 15])
                    
                    # RPE calculation based on athlete profile
                    base_rpe = 7  # Base RPE
                    
                    # Adjust for sport
                    if athlete['sport'] in ['Powerlifting', 'Strongman']:
                        base_rpe += 1
                    elif athlete['sport'] == 'CrossFit':
                        base_rpe += 0.5
                    
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
                    fatigue_factor = min(week / 24, 0.5)  # Gradual fatigue accumulation
                    
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

# Generate the comprehensive dataset
print("🏋️ Generating comprehensive mock training data...")
print("This may take a moment as we're creating a large dataset...")

comprehensive_data = generate_comprehensive_mock_data()

# Save to CSV
comprehensive_data.to_csv('comprehensive_athlete_data.csv', index=False)

# Display statistics
print(f"\n📊 Dataset Statistics:")
print(f"Total training sessions: {len(comprehensive_data):,}")
print(f"Number of athletes: {comprehensive_data['athlete_id'].nunique()}")
print(f"Number of exercises: {comprehensive_data['exercise'].nunique()}")
print(f"Date range: {comprehensive_data['date'].min()} to {comprehensive_data['date'].max()}")
print(f"Training weeks: {(pd.to_datetime(comprehensive_data['date']).max() - pd.to_datetime(comprehensive_data['date']).min()).days // 7 + 1}")

print(f"\n👥 Athlete Breakdown:")
for athlete_id in comprehensive_data['athlete_id'].unique():
    athlete_data = comprehensive_data[comprehensive_data['athlete_id'] == athlete_id]
    print(f"{athlete_id}: {len(athlete_data):,} sessions, {athlete_data['date'].nunique()} training days")

print(f"\n💪 Exercise Distribution:")
exercise_counts = comprehensive_data['exercise'].value_counts()
for exercise, count in exercise_counts.items():
    avg_weight = comprehensive_data[comprehensive_data['exercise'] == exercise]['weight_kg'].mean()
    print(f"{exercise}: {count:,} sessions, avg weight: {avg_weight:.1f}kg")

# File size information
file_size = os.path.getsize('comprehensive_athlete_data.csv')
print(f"\n📁 File size: {file_size / (1024*1024):.1f} MB")

print(f"\n✅ Comprehensive mock data saved as 'comprehensive_athlete_data.csv'")
print(f"🎯 This dataset is perfect for testing the Athlete Intelligence Platform!")
print(f"📈 Contains realistic training patterns, progressive overload, and athlete-specific variations")
