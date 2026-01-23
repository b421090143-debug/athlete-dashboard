import streamlit as st
import pandas as pd
import os
from datetime import datetime
from src.preprocessing import add_week_column, compute_weekly_metrics, analyze_exercise_trends, generate_llm_facts
from src.athlete_profiles import search_athletes, get_athlete_profile
from src.data_enrichment import enrich_athlete_data, calculate_personalized_metrics
from src.insights_engine import generate_personalized_insights, generate_athlete_summary
import plotly.express as px
import plotly.graph_objects as go
from io import StringIO

# Set page config
st.set_page_config(
    page_title="Athlete Analytics Dashboard",
    page_icon="🏋️",
    layout="wide",
    initial_sidebar_state="expanded"
)

def load_data(uploaded_file):
    """Load data from uploaded file (CSV or Excel)"""
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:  # Excel
            df = pd.read_excel(uploaded_file)
        return df
    except Exception as e:
        st.error(f"Error loading file: {str(e)}")
        return None

def validate_data(df):
    """Basic data validation"""
    # Strip whitespace from column names
    df.columns = df.columns.str.strip()
    
    # Accept both raw and processed data formats
    raw_columns = ['athlete_id', 'exercise', 'date', 'weight_kg', 'sets', 'reps', 'rpe']
    processed_columns = ['athlete_id', 'exercise', 'date', 'week', 'total_load', 'total_volume', 'avg_rpe', 'avg_weight', 'total_sets']
    
    # Check for either format
    if all(col in df.columns for col in raw_columns):
        required_columns = raw_columns
    elif all(col in df.columns for col in processed_columns):
        required_columns = processed_columns
    else:
        return False, f"Data must contain either raw format columns: {', '.join(raw_columns)} OR processed format columns: {', '.join(processed_columns)}. Found columns: {', '.join(df.columns.tolist())}"

    # Check for missing values in required columns
    missing_values = df[required_columns].isnull().sum()
    if missing_values.sum() > 0:
        return False, f"Missing values found in: {missing_values[missing_values > 0].to_dict()}"
    
    return True, "Data validated successfully"

def format_insights(insights):
    """Format insights for display"""
    formatted = []
    for insight in insights:
        if "**" in insight:  # This is a header
            formatted.append(f"### {insight.strip('* ')}")
        else:
            formatted.append(f"- {insight}")
    return "\n\n".join(formatted)

def filter_data_by_athlete(df, selected_athlete):
    """
    Filter dataset based on selected athlete.
    
    Args:
        df: Full dataset
        selected_athlete: Athlete ID or "All Athletes"
    
    Returns:
        Filtered DataFrame
    """
    if selected_athlete == "All Athletes":
        return df.copy()
    else:
        return df[df['athlete_id'] == selected_athlete].copy()

def get_athlete_summary(df, athlete_id):
    """
    Generate athlete-specific summary statistics.
    
    Args:
        df: Filtered dataset for athlete
        athlete_id: Athlete ID
    
    Returns:
        Dictionary with summary stats
    """
    if athlete_id == "All Athletes":
        return {
            'total_sessions': len(df),
            'total_weeks': df['week'].nunique() if 'week' in df.columns else 0,
            'total_exercises': df['exercise'].nunique(),
            'avg_rpe': df['rpe'].mean(),
            'total_volume': (df['weight_kg'] * df['sets'] * df['reps']).sum()
        }
    else:
        return {
            'total_sessions': len(df),
            'total_weeks': df['week'].nunique() if 'week' in df.columns else 0,
            'total_exercises': df['exercise'].nunique(),
            'avg_rpe': df['rpe'].mean(),
            'total_volume': (df['weight_kg'] * df['sets'] * df['reps']).sum()
        }

def main():
    st.title("🏋️ Athlete Intelligence Platform")
    st.write("Search athletes, enrich training data, and generate personalized coaching insights.")
    
    # Sidebar for file upload and athlete search
    with st.sidebar:
        st.header("🔍 Athlete Intelligence")
        
        # File upload section
        st.subheader("📁 Upload Training Data")
        uploaded_file = st.file_uploader(
            "Choose a CSV or Excel file",
            type=['csv', 'xlsx', 'xls']
        )
        
        # Athlete search section (show after file is uploaded)
        if uploaded_file is not None:
            st.subheader("👤 Search Athlete")
            
            # Search input
            search_query = st.text_input(
                "Search by ID or Name:",
                placeholder="e.g., ATH001 or John",
                key="athlete_search"
            )
            
            # Search button
            search_button = st.button("🔍 Search", type="secondary")
            
            # Display search results
            if search_query and search_button:
                with st.spinner("Searching athletes..."):
                    search_results = search_athletes(search_query)
                    
                    if search_results:
                        st.success(f"Found {len(search_results)} athlete(s)")
                        
                        # Display search results as selectable cards
                        for i, athlete in enumerate(search_results):
                            with st.container():
                                col1, col2 = st.columns([3, 1])
                                
                                with col1:
                                    # Athlete info card
                                    st.markdown(f"""
                                    **{athlete.full_name}**  
                                    🏷️ `{athlete.athlete_id}` | 🎯 {athlete.sport} | 📊 {athlete.get_strength_level().title()}
                                    """)
                                
                                with col2:
                                    # Select button
                                    if st.button(f"Select", key=f"select_{athlete.athlete_id}"):
                                        st.session_state.selected_athlete = athlete.athlete_id
                                        st.session_state.search_performed = True
                                        st.rerun()
                                
                                st.markdown("---")
                    else:
                        st.error("No athletes found. Try searching by ID or name.")
            
            # Display selected athlete profile
            if 'selected_athlete' in st.session_state and st.session_state.selected_athlete:
                selected_athlete_id = st.session_state.selected_athlete
                profile = get_athlete_profile(selected_athlete_id)
                
                if profile:
                    st.markdown("---")
                    st.markdown(f"### 🎯 {profile.full_name}")
                    
                    # Profile metrics
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Age", f"{profile.age} years")
                        st.metric("Sport", profile.sport)
                        st.metric("Level", profile.get_strength_level().title())
                    
                    with col2:
                        st.metric("Training Age", f"{profile.training_age_years} years")
                        st.metric("Recovery", profile.recovery_profile.title())
                        st.metric("Baseline RPE", profile.baseline_rpe)
                    
                    # Injury history warning
                    if profile.injury_history:
                        st.warning(f"⚠️ Injury History: {', '.join(profile.injury_history)}")
                    
                    # Training goals
                    if profile.training_goals:
                        st.info(f"🎯 Goals: {', '.join(profile.training_goals)}")
        
        # Process button
        if uploaded_file is not None:
            if 'selected_athlete' in st.session_state:
                st.success("Data loaded and athlete selected!")
                
                if st.button("🚀 Generate Personalized Analysis", type="primary"):
                    with st.spinner('Analyzing athlete data...'):
                        # Load and validate data
                        df = load_data(uploaded_file)
                        if df is not None:
                            is_valid, validation_msg = validate_data(df)
                            if not is_valid:
                                st.error(f"Validation Error: {validation_msg}")
                                return
                            
                            # Store original data in session state
                            st.session_state.df = df
                            st.session_state.processed = False
                            
                            # Get selected athlete
                            selected_athlete_id = st.session_state.selected_athlete
                            
                            # Filter data for selected athlete
                            athlete_df = df[df['athlete_id'] == selected_athlete_id].copy()
                            
                            if len(athlete_df) == 0:
                                st.error(f"No training data found for athlete {selected_athlete_id}")
                                return
                            
                            # Enrich data with athlete profile
                            enriched_df = enrich_athlete_data(athlete_df, selected_athlete_id)
                            
                            # Process enriched data
                            df_with_weeks = add_week_column(enriched_df)
                            weekly_metrics = compute_weekly_metrics(df_with_weeks)
                            trends = analyze_exercise_trends(weekly_metrics)
                            llm_facts = generate_llm_facts(trends)
                            
                            # Generate personalized insights
                            personalized_insights = generate_personalized_insights(enriched_df, selected_athlete_id)
                            athlete_summary = generate_athlete_summary(enriched_df, selected_athlete_id)
                            
                            # Store results in session state
                            st.session_state.weekly_metrics = weekly_metrics
                            st.session_state.trends = trends
                            st.session_state.insights = personalized_insights
                            st.session_state.enriched_df = enriched_df
                            st.session_state.athlete_summary = athlete_summary
                            st.session_state.processed = True
                            
                            profile = get_athlete_profile(selected_athlete_id)
                            st.success(f"✅ Personalized analysis complete for {profile.full_name}!")
            else:
                st.info("📁 Data uploaded! Now search and select an athlete to begin analysis.")
            
            # Add "Analyze All Athletes" option
            st.markdown("---")
            st.subheader("👥 Team Analysis")
            if st.button("🚀 Generate All Athletes Analysis", type="primary"):
                with st.spinner('Analyzing all athletes...'):
                    # Load and validate data
                    df = load_data(uploaded_file)
                    if df is not None:
                        is_valid, validation_msg = validate_data(df)
                        if not is_valid:
                            st.error(f"Validation Error: {validation_msg}")
                            return
                        
                        # Store original data in session state
                        st.session_state.df = df
                        st.session_state.processed_all = False
                        
                        # Get all unique athletes in the data
                        all_athlete_ids = df['athlete_id'].unique()
                        
                        # Process each athlete
                        all_athletes_data = {}
                        all_athletes_summaries = {}
                        
                        for athlete_id in all_athlete_ids:
                            # Filter data for this athlete
                            athlete_df = df[df['athlete_id'] == athlete_id].copy()
                            
                            if len(athlete_df) > 0:
                                # Enrich data with athlete profile
                                enriched_df = enrich_athlete_data(athlete_df, athlete_id)
                                
                                # Process enriched data
                                df_with_weeks = add_week_column(enriched_df)
                                weekly_metrics = compute_weekly_metrics(df_with_weeks)
                                trends = analyze_exercise_trends(weekly_metrics)
                                llm_facts = generate_llm_facts(trends)
                                
                                # Generate personalized insights
                                personalized_insights = generate_personalized_insights(enriched_df, athlete_id)
                                athlete_summary = generate_athlete_summary(enriched_df, athlete_id)
                                
                                # Store results
                                all_athletes_data[athlete_id] = {
                                    'weekly_metrics': weekly_metrics,
                                    'trends': trends,
                                    'insights': personalized_insights,
                                    'enriched_df': enriched_df,
                                    'athlete_summary': athlete_summary
                                }
                                all_athletes_summaries[athlete_id] = athlete_summary
                        
                        # Store all results in session state
                        st.session_state.all_athletes_data = all_athletes_data
                        st.session_state.all_athletes_summaries = all_athletes_summaries
                        st.session_state.processed_all = True
                        
                        st.success(f"✅ Analysis complete for all {len(all_athlete_ids)} athletes!")
    
    # Display results if data is processed
    if 'processed_all' in st.session_state and st.session_state.processed_all:
        st.header("👥 Team Performance Analytics - All Athletes")
        
        # Team overview metrics
        all_athletes_summaries = st.session_state.all_athletes_summaries
        all_athletes_data = st.session_state.all_athletes_data
        
        # Team summary cards
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Athletes", len(all_athletes_summaries))
        with col2:
            total_sessions = sum(len(data['enriched_df']) for data in all_athletes_data.values())
            st.metric("Total Sessions", total_sessions)
        with col3:
            all_exercises = set()
            for data in all_athletes_data.values():
                all_exercises.update(data['enriched_df']['exercise'].unique())
            st.metric("Total Exercises", len(all_exercises))
        with col4:
            avg_rpe = sum(data['athlete_summary']['training_metrics']['personalized_rpe_stats']['avg_rpe'] 
                         for data in all_athletes_data.values()) / len(all_athletes_data)
            st.metric("Team Avg RPE", f"{avg_rpe:.1f}")
        
        # Tabs for team analysis
        tab1, tab2, tab3, tab4 = st.tabs(["👥 Athlete Profiles", "📊 Team Insights", "📈 Comparative Analysis", "📥 Team Export"])
        
        with tab1:  # Athlete Profiles
            st.subheader("Individual Athlete Profiles")
            
            for athlete_id, athlete_summary in all_athletes_summaries.items():
                profile = get_athlete_profile(athlete_id)
                athlete_name = profile.full_name if profile else f"Athlete {athlete_id}"
                
                with st.expander(f"👤 {athlete_name} - {profile.sport if profile else 'Unknown Sport'}"):
                    # Athlete info
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        age = profile.age if profile else "Unknown"
                        level = profile.get_strength_level().title() if profile else "Unknown"
                        st.metric("Age", f"{age} years")
                        st.metric("Level", level)
                    with col2:
                        training_age = profile.training_age_years if profile else "Unknown"
                        recovery = profile.recovery_profile.title() if profile else "Unknown"
                        st.metric("Training Age", f"{training_age} years")
                        st.metric("Recovery", recovery)
                    with col3:
                        sessions = len(all_athletes_data[athlete_id]['enriched_df'])
                        status = athlete_summary['performance_status'].replace('_', ' ').title()
                        st.metric("Sessions", sessions)
                        st.metric("Status", status)
                    
                    # Add visualizations for this athlete
                    st.markdown("### 📊 Performance Visualizations")
                    
                    # Get athlete data
                    athlete_data = all_athletes_data[athlete_id]
                    enriched_df = athlete_data['enriched_df']
                    weekly_metrics = athlete_data['weekly_metrics']
                    
                    # Visualization 1: RPE Trend
                    if 'date' in enriched_df.columns:
                        enriched_df['date'] = pd.to_datetime(enriched_df['date'])
                        rpe_trend = enriched_df.groupby('date')['rpe'].mean().reset_index()
                        
                        fig_rpe = px.line(
                            rpe_trend, 
                            x='date', 
                            y='rpe',
                            title=f"{athlete_name} - RPE Trend Over Time",
                            labels={'rpe': 'Average RPE', 'date': 'Date'}
                        )
                        fig_rpe.add_hline(
                            y=profile.baseline_rpe if profile else 7,
                            line_dash="dash",
                            annotation_text="Baseline RPE" if profile else "Default RPE",
                            annotation_position="top right"
                        )
                        st.plotly_chart(fig_rpe, use_container_width=True)
                    
                    # Visualization 2: Exercise Volume Distribution
                    if not weekly_metrics.empty:
                        volume_by_exercise = weekly_metrics.groupby('exercise')['total_volume'].sum().reset_index()
                        
                        fig_volume = px.bar(
                            volume_by_exercise,
                            x='exercise',
                            y='total_volume',
                            title=f"{athlete_name} - Total Volume by Exercise",
                            labels={'total_volume': 'Total Volume (kg)', 'exercise': 'Exercise'}
                        )
                        st.plotly_chart(fig_volume, use_container_width=True)
                    
                    # Visualization 3: Fatigue Risk Analysis
                    if 'fatigue_risk_score' in enriched_df.columns:
                        fatigue_data = enriched_df.groupby('date')['fatigue_risk_score'].mean().reset_index()
                        
                        fig_fatigue = px.line(
                            fatigue_data,
                            x='date',
                            y='fatigue_risk_score',
                            title=f"{athlete_name} - Fatigue Risk Trend",
                            labels={'fatigue_risk_score': 'Fatigue Risk Score', 'date': 'Date'}
                        )
                        fig_fatigue.add_hline(
                            y=3,
                            line_dash="dash",
                            line_color="red",
                            annotation_text="High Risk Threshold",
                            annotation_position="top right"
                        )
                        st.plotly_chart(fig_fatigue, use_container_width=True)
                    
                    # Personalized insights for this athlete
                    insights = all_athletes_data[athlete_id]['insights']
                    if insights:
                        st.markdown("### 🧠 Personalized Insights")
                        for i, insight in enumerate(insights[:3], 1):  # Show top 3 insights
                            st.markdown(f"{i}. {insight}")
                    
                    # Individual export for this athlete
                    st.markdown("### 📥 Export Individual Data")
                    
                    # Create individual report
                    individual_report = f"""
Individual Athlete Report
=======================

Athlete: {athlete_name} ({athlete_id})
Date: {datetime.now().strftime('%Y-%m-%d')}
Sport: {profile.sport if profile else 'Unknown'}
Level: {profile.get_strength_level().title() if profile else 'Unknown'}

Training Summary
----------------
Total Sessions: {len(enriched_df)}
Performance Status: {status}

Personalized Insights
--------------------
"""
                    
                    for i, insight in enumerate(insights, 1):
                        individual_report += f"{i}. {insight}\n"
                    
                    individual_report += f"\nCoaching Priorities: {', '.join(athlete_summary.get('coaching_priorities', []))}"
                    individual_report += "\n\nGenerated by Athlete Intelligence Platform"
                    
                    # Export buttons
                    col1, col2 = st.columns(2)
                    with col1:
                        st.download_button(
                            label=f"📄 Download {athlete_name} Report",
                            data=individual_report,
                            file_name=f"{athlete_id}_individual_report_{datetime.now().strftime('%Y%m%d')}.txt",
                            mime="text/plain",
                            key=f"report_{athlete_id}"
                        )
                    
                    with col2:
                        # Export metrics as CSV
                        if not weekly_metrics.empty:
                            csv_data = weekly_metrics.to_csv(index=False).encode('utf-8')
                            st.download_button(
                                label=f"📊 Download {athlete_name} Metrics",
                                data=csv_data,
                                file_name=f"{athlete_id}_metrics_{datetime.now().strftime('%Y%m%d')}.csv",
                                mime="text/csv",
                                key=f"metrics_{athlete_id}"
                            )
        
        with tab2:  # Team Insights
            st.subheader("Team-Wide Insights & Patterns")
            
            # Aggregate insights from all athletes
            all_insights = []
            for athlete_id, data in all_athletes_data.items():
                profile = get_athlete_profile(athlete_id)
                insights = data['insights']
                athlete_name = profile.full_name if profile else f"Athlete {athlete_id}"
                for insight in insights:
                    all_insights.append(f"**{athlete_name}**: {insight}")
            
            # Display all insights
            if all_insights:
                for i, insight in enumerate(all_insights, 1):
                    st.markdown(f"{i}. {insight}")
            else:
                st.info("No insights available.")
            
            # Team coaching priorities
            st.markdown("---")
            st.markdown("### 🎯 Team Coaching Priorities")
            
            # Aggregate priorities
            all_priorities = []
            for athlete_summary in all_athletes_summaries.values():
                priorities = athlete_summary.get('coaching_priorities', [])
                all_priorities.extend(priorities)
            
            # Count and display top priorities
            from collections import Counter
            priority_counts = Counter(all_priorities)
            
            for priority, count in priority_counts.most_common():
                st.markdown(f"- **{priority}** ({count} athletes)")
        
        with tab3:  # Comparative Analysis
            st.subheader("Comparative Performance Analysis")
            
            # Performance status distribution
            status_data = {}
            for athlete_id, athlete_summary in all_athletes_summaries.items():
                profile = get_athlete_profile(athlete_id)
                status = athlete_summary['performance_status']
                athlete_name = profile.full_name if profile else f"Athlete {athlete_id}"
                if status not in status_data:
                    status_data[status] = []
                status_data[status].append(athlete_name)
            
            st.markdown("### 📊 Performance Status Distribution")
            for status, athletes in status_data.items():
                st.markdown(f"**{status.replace('_', ' ').title()}**: {', '.join(athletes)}")
            
            # Fatigue risk comparison
            st.markdown("### ⚠️ Fatigue Risk Comparison")
            fatigue_data = []
            for athlete_id, data in all_athletes_data.items():
                profile = get_athlete_profile(athlete_id)
                athlete_name = profile.full_name if profile else f"Athlete {athlete_id}"
                sport = profile.sport if profile else "Unknown"
                fatigue_score = data['athlete_summary']['training_metrics']['fatigue_analysis']['avg_fatigue_risk']
                fatigue_data.append({
                    'Athlete': athlete_name,
                    'Fatigue Risk': fatigue_score,
                    'Sport': sport
                })
            
            fatigue_df = pd.DataFrame(fatigue_data)
            fig_fatigue = px.bar(fatigue_df, x='Athlete', y='Fatigue Risk', color='Sport', 
                                title="Average Fatigue Risk by Athlete")
            st.plotly_chart(fig_fatigue, use_container_width=True)
        
        with tab4:  # Team Export
            st.subheader("Export Team Analysis")
            
            # Generate comprehensive team report
            team_report = f"""
Team Performance Report
======================

Date: {datetime.now().strftime('%Y-%m-%d')}
Total Athletes: {len(all_athletes_summaries)}
Total Sessions: {sum(len(data['enriched_df']) for data in all_athletes_data.values())}

Individual Athlete Summaries
----------------------------
"""
            
            for athlete_id, athlete_summary in all_athletes_summaries.items():
                profile = get_athlete_profile(athlete_id)
                if profile:
                    team_report += f"""
{profile.full_name} ({athlete_id})
- Sport: {profile.sport}
- Level: {profile.get_strength_level().title()}
- Sessions: {len(all_athletes_data[athlete_id]['enriched_df'])}
- Status: {athlete_summary['performance_status'].replace('_', ' ').title()}
- Priorities: {', '.join(athlete_summary.get('coaching_priorities', []))}

Key Insights:
"""
                    insights = all_athletes_data[athlete_id]['insights']
                    for i, insight in enumerate(insights[:3], 1):
                        team_report += f"{i}. {insight}\n"
                    team_report += "\n"
                else:
                    team_report += f"""
Athlete {athlete_id}
- Sport: Unknown
- Level: Unknown
- Sessions: {len(all_athletes_data[athlete_id]['enriched_df'])}
- Status: {athlete_summary['performance_status'].replace('_', ' ').title()}
- Priorities: {', '.join(athlete_summary.get('coaching_priorities', []))}

Key Insights:
"""
                    insights = all_athletes_data[athlete_id]['insights']
                    for i, insight in enumerate(insights[:3], 1):
                        team_report += f"{i}. {insight}\n"
                    team_report += "\n"
            
            team_report += "\nGenerated by Athlete Intelligence Platform"
            
            st.download_button(
                label="📥 Download Team Report",
                data=team_report,
                file_name=f"team_analysis_{datetime.now().strftime('%Y%m%d')}.txt",
                mime="text/plain"
            )
    
    # Display results if single athlete is processed
    elif 'processed' in st.session_state and st.session_state.processed:
        selected_athlete_id = st.session_state.selected_athlete
        profile = get_athlete_profile(selected_athlete_id)
        
        # Dynamic title based on selected athlete
        st.header(f"👤 {profile.full_name} - Personalized Performance Analytics")
        
        # Athlete context bar
        context_col1, context_col2, context_col3 = st.columns(3)
        with context_col1:
            st.info(f"🎯 {profile.sport} | 📊 {profile.get_strength_level().title()}")
        with context_col2:
            st.info(f"📅 Training Age: {profile.training_age_years} years")
        with context_col3:
            st.info(f"♻️ Recovery Profile: {profile.recovery_profile.title()}")
        
        # Tabs for different sections
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Overview", "📈 Performance Trends", "🧠 Personalized Insights", "⚠️ Risk Analysis", "📥 Export"])
        
        with tab1:  # Overview
            st.subheader(f"{profile.full_name} - Training Overview")
            
            # Display enriched weekly metrics
            enriched_metrics = st.session_state.weekly_metrics
            
            # Add athlete context columns to display
            display_metrics = enriched_metrics.copy()
            display_metrics['rpe_zone'] = st.session_state.enriched_df.groupby(['week', 'exercise'])['rpe_zone'].first().reset_index()['rpe_zone']
            
            st.dataframe(display_metrics, use_container_width=True)
            
            # Personalized metrics
            athlete_summary = st.session_state.athlete_summary
            metrics = athlete_summary['training_metrics']
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Training Sessions", len(st.session_state.enriched_df))
            with col2:
                st.metric("Avg RPE", f"{metrics['personalized_rpe_stats']['avg_rpe']:.1f}")
            with col3:
                st.metric("Fatigue Risk", f"{metrics['fatigue_analysis']['avg_fatigue_risk']:.1f}/5")
            with col4:
                status = athlete_summary['performance_status'].replace('_', ' ').title()
                st.metric("Performance Status", status)
        
        with tab2:  # Performance Trends
            st.subheader(f"{profile.full_name} - Performance Trends")
            
            # Exercise selector
            exercises = st.session_state.weekly_metrics['exercise'].unique()
            selected_exercise = st.selectbox("Select Exercise", exercises)
            
            # Filter data for selected exercise
            exercise_data = st.session_state.weekly_metrics[
                st.session_state.weekly_metrics['exercise'] == selected_exercise
            ]
            
            # Personalized chart title
            chart_title = f"{selected_exercise} - {profile.full_name} Progression"
            
            # Create line chart for weight progression
            fig = px.line(
                exercise_data, 
                x='week', 
                y='avg_weight',
                title=chart_title,
                labels={'avg_weight': 'Average Weight (kg)', 'week': 'Week'},
                line_shape='spline'
            )
            
            # Add athlete-specific benchmarks
            if selected_exercise.lower() in ['squat', 'bench press', 'deadlift']:
                max_strength = profile.max_strength
                exercise_key = selected_exercise.title()
                if exercise_key in max_strength:
                    fig.add_hline(
                        y=max_strength[exercise_key], 
                        line_dash="dash", 
                        annotation_text=f"Personal Max: {max_strength[exercise_key]}kg",
                        annotation_position="top right"
                    )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Volume over time with personalization
            volume_title = f"{selected_exercise} - {profile.full_name} Volume Analysis"
            
            fig2 = px.bar(
                exercise_data,
                x='week',
                y='total_volume',
                title=volume_title,
                labels={'total_volume': 'Total Volume (kg)', 'week': 'Week'}
            )
            
            # Add preference scoring
            preference_score = st.session_state.enriched_df[
                st.session_state.enriched_df['exercise'] == selected_exercise
            ]['preference_score'].mean()
            
            fig2.add_annotation(
                text=f"Preference Score: {preference_score:.1%}",
                xref="paper", yref="paper",
                x=0.02, y=0.98,
                showarrow=False,
                font=dict(size=12, color="black")
            )
            
            st.plotly_chart(fig2, use_container_width=True)
        
        with tab3:  # Personalized Insights
            st.subheader(f"🧠 {profile.full_name} - Personalized Coaching Insights")
            
            if 'insights' in st.session_state and st.session_state.insights:
                insights = st.session_state.insights
                
                # Display insights with better formatting
                for i, insight in enumerate(insights, 1):
                    st.markdown(f"**{i}.** {insight}")
                
                # Coaching priorities
                athlete_summary = st.session_state.athlete_summary
                if 'coaching_priorities' in athlete_summary:
                    priorities = athlete_summary['coaching_priorities']
                    if priorities:
                        st.markdown("---")
                        st.markdown("### 🎯 Coaching Priorities")
                        for priority in priorities:
                            st.markdown(f"- **{priority}**")
            else:
                st.info("No insights available. Please run the analysis first.")
        
        with tab4:  # Risk Analysis
            st.subheader(f"⚠️ {profile.full_name} - Risk & Recovery Analysis")
            
            # Fatigue risk analysis
            metrics = athlete_summary['training_metrics']
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 📊 Fatigue Indicators")
                st.metric("Average Fatigue Risk", f"{metrics['fatigue_analysis']['avg_fatigue_risk']:.1f}/5")
                st.metric("High-Risk Sessions", metrics['fatigue_analysis']['high_risk_sessions'])
                st.metric("Critical RPE Sessions", metrics['personalized_rpe_stats']['critical_sessions'])
            
            with col2:
                st.markdown("### 🏥 Injury Risk Factors")
                st.metric("Total Risk Factors", metrics['injury_risk_summary']['total_risk_factors'])
                st.metric("High-Risk Exercises", len(metrics['injury_risk_summary']['high_risk_exercises']))
                
                if profile.injury_history:
                    st.markdown("**Injury History:**")
                    for injury in profile.injury_history:
                        st.markdown(f"- {injury}")
            
            # RPE zone distribution
            enriched_df = st.session_state.enriched_df
            rpe_zones = enriched_df['rpe_zone'].value_counts()
            
            st.markdown("### 🎯 RPE Zone Distribution")
            fig_rpe = px.pie(
                values=rpe_zones.values,
                names=rpe_zones.index,
                title="Training Intensity Distribution"
            )
            st.plotly_chart(fig_rpe, use_container_width=True)
        
        with tab5:  # Export
            st.subheader(f"📥 Export {profile.full_name} Results")
            
            # Export personalized insights
            if 'insights' in st.session_state:
                insights_text = "\n".join([f"{i+1}. {insight}" for i, insight in enumerate(st.session_state.insights)])
                
                # Create comprehensive report
                report_content = f"""
Athlete Performance Report
========================

Athlete: {profile.full_name} ({profile.athlete_id})
Sport: {profile.sport}
Level: {profile.get_strength_level().title()}
Date: {datetime.now().strftime('%Y-%m-%d')}

Athlete Profile
---------------
Age: {profile.age} years
Training Age: {profile.training_age_years} years
Recovery Profile: {profile.recovery_profile}
Baseline RPE: {profile.baseline_rpe}

Training Goals: {', '.join(profile.training_goals) if profile.training_goals else 'Not specified'}

Personalized Insights
------------------
{insights_text}

Performance Status: {athlete_summary['performance_status'].replace('_', ' ').title()}

Coaching Priorities: {', '.join(athlete_summary.get('coaching_priorities', []))}

Generated by Athlete Intelligence Platform
"""
                
                st.download_button(
                    label=f"📥 Download {profile.full_name} Report",
                    data=report_content,
                    file_name=f"{profile.athlete_id}_personalized_report_{datetime.now().strftime('%Y%m%d')}.txt",
                    mime="text/plain"
                )
            
            # Export enriched metrics
            if 'weekly_metrics' in st.session_state:
                csv = st.session_state.weekly_metrics.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label=f"📊 Download {profile.full_name} Metrics (CSV)",
                    data=csv,
                    file_name=f"{profile.athlete_id}_metrics_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
    
    else:
        # Show instructions if no file uploaded
        st.info(
            "👈 Please upload your training data file and search for an athlete to begin personalized analysis. "
            "The file should include columns for athlete_id, exercise, date, weight_kg, sets, reps, and rpe."
        )
        
        # Example data format
        with st.expander("📋 Example Data Format"):
            example_data = {
                'athlete_id': ['ATH001', 'ATH001', 'ATH002', 'ATH002'],
                'date': ['2023-01-01', '2023-01-03', '2023-01-02', '2023-01-04'],
                'exercise': ['Squat', 'Bench Press', 'Squat', 'Deadlift'],
                'weight_kg': [100, 80, 120, 150],
                'sets': [3, 4, 3, 5],
                'reps': [5, 8, 6, 3],
                'rpe': [8, 7, 8.5, 9]
            }
            st.dataframe(pd.DataFrame(example_data))
        
        # Available athletes demo
        with st.expander("👥 Available Athletes for Search"):
            st.markdown("""
            **Try searching for these athletes:**
            - **ATH001** - John "The Beast" Smith (Powerlifting)
            - **ATH002** - Sarah "Thunder" Johnson (Olympic Weightlifting)
            - **ATH003** - Mike "Rookie" Chen (Bodybuilding)
            - **ATH004** - Emily "Precision" Davis (CrossFit)
            - **ATH005** - Alex "Powerhouse" Rodriguez (Strongman)
            
            **Search Examples:**
            - Type "ATH001" to find John Smith
            - Type "John" to find all athletes named John
            - Type "Powerlifting" to find powerlifters
            """)

if __name__ == "__main__":
    main()
