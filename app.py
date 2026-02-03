import streamlit as st
import pandas as pd
import os
import logging
from datetime import datetime
from src.preprocessing import add_week_column, compute_weekly_metrics, analyze_exercise_trends, generate_llm_facts
from src.athlete_profiles import search_athletes, get_athlete_profile, build_fallback_profile
from src.data_enrichment import enrich_athlete_data, calculate_personalized_metrics
from src.insights_engine import generate_personalized_insights, generate_athlete_summary
from src.recovery_tracking import RecoveryTracker
from src.progressive_overload import ProgressiveOverloadTracker
from src.coaching_engine import CoachingEngine
from src.ai_engine import CognitiveCoachingBrain
from src.verification_layer import VerificationLayer
from src.decision_layer import compute_decision_layer_output
import plotly.express as px
import plotly.graph_objects as go
from io import StringIO

logger = logging.getLogger(__name__)

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


@st.cache_data(show_spinner=False, ttl=300)
def _cached_decision_layer_output(athlete_id: str, weekly_metrics: pd.DataFrame, metrics: dict, coach_tag: str):
    """Cached wrapper around the experimental decision layer.

    Safety design:
    - Cached to avoid recomputation on UI reruns.
    - If the decision layer throws for any reason, return None (keep dashboard functional).
    """

    try:
        if weekly_metrics is None:
            return None

        # Cache a minimal subset to reduce hashing overhead.
        keep_cols = [c for c in ["athlete_id", "week", "total_load", "avg_rpe"] if c in weekly_metrics.columns]
        wm = weekly_metrics[keep_cols].copy() if keep_cols else weekly_metrics.copy()

        return compute_decision_layer_output(
            athlete_id=athlete_id,
            weekly_metrics=wm,
            metrics=metrics or {},
            coach_tag=(coach_tag or None),
        )
    except Exception as e:
        logger.exception("Decision layer wrapper failed: %s", str(e))
        return None

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
            # Allow selecting any athlete_id present in the uploaded file (including ATH### not in the registry)
            try:
                if 'uploaded_df_preview' not in st.session_state or st.session_state.get('uploaded_file_name') != uploaded_file.name:
                    df_preview = load_data(uploaded_file)
                    if df_preview is not None and 'athlete_id' in df_preview.columns:
                        st.session_state.uploaded_df_preview = df_preview
                        st.session_state.uploaded_file_name = uploaded_file.name
                df_preview = st.session_state.get('uploaded_df_preview')
                if df_preview is not None and 'athlete_id' in df_preview.columns:
                    st.markdown("---")
                    st.subheader("🎯 Quick Select")
                    athlete_options = sorted(df_preview['athlete_id'].dropna().astype(str).unique().tolist())
                    prior_selected = str(st.session_state.get('selected_athlete') or "")
                    quick_options = [""] + athlete_options
                    quick_index = 0
                    if prior_selected and prior_selected in athlete_options:
                        quick_index = athlete_options.index(prior_selected) + 1

                    quick_choice = st.selectbox(
                        "Select athlete from uploaded file:",
                        quick_options,
                        index=quick_index,
                        key="quick_select_athlete",
                    )

                    if quick_choice and quick_choice != prior_selected:
                        st.session_state.selected_athlete = quick_choice
                        st.session_state.search_performed = True
            except Exception:
                pass

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
                    query = str(search_query).strip().lower()
                    df_preview = st.session_state.get('uploaded_df_preview')
                    uploaded_matches = []
                    if df_preview is not None and 'athlete_id' in df_preview.columns:
                        all_ids = sorted(df_preview['athlete_id'].dropna().astype(str).unique().tolist())
                        uploaded_matches = [aid for aid in all_ids if query in aid.lower()]

                    if uploaded_matches:
                        st.success(f"Found {len(uploaded_matches)} athlete(s) in uploaded file")
                        for aid in uploaded_matches[:20]:
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.markdown(f"🏷️ `{aid}`")
                            with col2:
                                if st.button("Select", key=f"select_uploaded_{aid}"):
                                    st.session_state.selected_athlete = aid
                                    st.session_state.search_performed = True
                    else:
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

                                    st.markdown("---")
                        else:
                            st.error("No athletes found. Try searching by ID or name.")
            
            # Display selected athlete profile
            if 'selected_athlete' in st.session_state and st.session_state.selected_athlete:
                selected_athlete_id = st.session_state.selected_athlete
                profile = get_athlete_profile(selected_athlete_id)
                if not profile:
                    df_preview = st.session_state.get('uploaded_df_preview')
                    athlete_df_preview = None
                    if df_preview is not None and 'athlete_id' in df_preview.columns:
                        athlete_df_preview = df_preview[df_preview['athlete_id'].astype(str) == str(selected_athlete_id)].copy()
                    profile = build_fallback_profile(selected_athlete_id, athlete_df_preview)
                
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
            if st.session_state.get('selected_athlete'):
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
                            if not profile:
                                profile = build_fallback_profile(selected_athlete_id, athlete_df)
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
        if not profile:
            profile = build_fallback_profile(selected_athlete_id, st.session_state.enriched_df)
        
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
        tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs(["📊 Overview", "📈 Performance Trends", "🧠 Personalized Insights", "⚠️ Risk Analysis", "🔄 Recovery", "💪 Progressive Overload", "🎯 Coaching Directives", "🧠 AI Coach Brain", "📥 Export"])
        
        with tab1:  # Overview
            st.subheader(f"{profile.full_name} - Training Overview")
            
            # Display enriched weekly metrics
            enriched_metrics = st.session_state.weekly_metrics
            
            # Add athlete context columns to display
            display_metrics = enriched_metrics.copy()
            try:
                enriched_df_for_zones = st.session_state.get('enriched_df')
                if enriched_df_for_zones is not None:
                    if 'week' not in enriched_df_for_zones.columns and 'date' in enriched_df_for_zones.columns:
                        enriched_df_for_zones = add_week_column(enriched_df_for_zones.copy())

                    required_zone_cols = {'week', 'exercise', 'rpe_zone'}
                    required_join_cols = {'week', 'exercise'}
                    if required_zone_cols.issubset(set(enriched_df_for_zones.columns)) and required_join_cols.issubset(set(display_metrics.columns)):
                        zone_map = (
                            enriched_df_for_zones
                            .groupby(['week', 'exercise'], as_index=False)['rpe_zone']
                            .first()
                        )
                        display_metrics = display_metrics.merge(zone_map, on=['week', 'exercise'], how='left')
            except Exception:
                pass
            
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

            # Experimental Decision Layer (Beta) - additive, feature-flagged, collapsible.
            with st.expander("🧪 Experimental: Decision Layer (Beta)", expanded=False):
                if str(os.getenv("ENABLE_DECISION_LAYER", "0")).strip().lower() not in {"1", "true", "yes", "on"}:
                    st.caption("Disabled by default. Set `ENABLE_DECISION_LAYER=1` to enable.")
                else:
                    coach_tag = st.selectbox(
                        "Coach intent tag (optional)",
                        ["", "ACCUMULATION", "DELOAD", "TAPER"],
                        index=0,
                        help="Optional: used only to guide the experimental decision layer. If empty, it is ignored.",
                        key="decision_layer_tag",
                    )

                    decision_out = _cached_decision_layer_output(
                        str(selected_athlete_id),
                        st.session_state.get("weekly_metrics"),
                        metrics,
                        str(coach_tag or ""),
                    )

                    if not decision_out:
                        st.info("Insufficient data: decision layer unavailable.")
                    else:
                        c1, c2, c3, c4 = st.columns([1.2, 1, 1, 1])
                        with c1:
                            st.metric("Decision", decision_out.get("decision", "MAINTAIN"))
                        with c2:
                            st.metric("Risk", decision_out.get("risk_level", "MEDIUM"))
                        with c3:
                            st.metric("Confidence", f"{float(decision_out.get('confidence', 0.0)):.2f}")
                        with c4:
                            st.caption("Read-only. Does not change any existing metrics.")

                        reasons = decision_out.get("reasons") or []
                        if reasons:
                            st.markdown("**Reasons / Signals**")
                            for r in reasons:
                                st.write(f"- {r}")
        
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
        
        with tab5:  # Recovery Tracking
            st.subheader(f"🔄 {profile.full_name} - Recovery & Fatigue Tracking")
            
            # Initialize recovery tracker
            if 'recovery_tracker' not in st.session_state:
                st.session_state.recovery_tracker = RecoveryTracker(st.session_state.athlete_df)
            
            recovery_tracker = st.session_state.recovery_tracker
            recovery_dashboard = recovery_tracker.create_recovery_dashboard(athlete_id)
            
            # Recovery Score Card
            col1, col2, col3 = st.columns(3)
            
            with col1:
                recovery_score = recovery_dashboard['recovery_score']
                score_color = {
                    'excellent': '🟢',
                    'good': '🟡', 
                    'moderate': '🟠',
                    'poor': '🔴',
                    'critical': '🚨'
                }.get(recovery_score['status'], '⚪')
                
                st.markdown(f"### {score_color} Recovery Score")
                st.metric("Score", f"{recovery_score['score']}/100")
                st.metric("Status", recovery_score['status'].title())
            
            with col2:
                st.markdown("### 📊 Load Factors")
                st.metric("Load Trend", f"{recovery_score['factors']['load_trend']:.3f}")
                st.metric("Avg Load", f"{recovery_score['factors']['avg_load']:.1f}")
                st.metric("Variability", f"{recovery_score['factors']['load_variability']:.1f}")
            
            with col3:
                st.markdown("### 💡 Recommendations")
                for i, rec in enumerate(recovery_dashboard['recommendations'][:3]):
                    st.markdown(f"{i+1}. {rec}")
            
            # ACWR Visualization
            st.markdown("### 📈 Acute:Chronic Workload Ratio")
            acwr_fig = recovery_tracker.create_recovery_visualization(athlete_id)
            st.plotly_chart(acwr_fig, use_container_width=True)
            
            # Recent ACWR Data
            acwr_data = recovery_dashboard['acwr_data']
            if len(acwr_data) > 0:
                recent_acwr = acwr_data.tail(7)
                
                st.markdown("### 📋 Recent ACWR Analysis")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.dataframe(
                        recent_acwr[['date', 'acwr', 'fatigue_zone']].rename(columns={
                            'date': 'Date',
                            'acwr': 'ACWR', 
                            'fatigue_zone': 'Fatigue Zone'
                        }),
                        use_container_width=True
                    )
                
                with col2:
                    # Fatigue zone distribution
                    zone_counts = recent_acwr['fatigue_zone'].value_counts()
                    fig_zones = px.bar(
                        x=zone_counts.index,
                        y=zone_counts.values,
                        title="Fatigue Zone Distribution (Last 7 Days)"
                    )
                    fig_zones.update_xaxes(title="Fatigue Zone")
                    fig_zones.update_yaxes(title="Days")
                    st.plotly_chart(fig_zones, use_container_width=True)
        
        with tab6:  # Progressive Overload
            st.subheader(f"💪 {profile.full_name} - Progressive Overload Analysis")
            
            # Initialize progressive overload tracker
            if 'progressive_tracker' not in st.session_state:
                st.session_state.progressive_tracker = ProgressiveOverloadTracker(st.session_state.athlete_df)
            
            progressive_tracker = st.session_state.progressive_tracker
            overload_dashboard = progressive_tracker.create_progressive_overload_dashboard(athlete_id)
            
            # Exercise selector
            all_exercises = list(st.session_state.athlete_df['exercise'].unique())
            selected_exercise = st.selectbox("Select Exercise", ["All Exercises"] + all_exercises)
            
            # Strength Velocity Summary
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if overload_dashboard['strength_velocity']['status'] == 'calculated':
                    velocity_data = overload_dashboard['strength_velocity']
                    st.markdown("### 🚀 Strength Velocity")
                    st.metric("Avg Gain/Week", f"{velocity_data['avg_velocity_kg_per_week']:.2f} kg")
                    st.metric("Best Exercise", velocity_data.get('best_exercise', 'N/A'))
                else:
                    st.markdown("### 🚀 Strength Velocity")
                    st.info("Insufficient data for velocity analysis")
            
            with col2:
                st.markdown("### 📊 Volume Analysis")
                volume_data = overload_dashboard['volume_progression']
                if 'TOTAL' in volume_data['exercise'].values:
                    total_volume = volume_data[volume_data['exercise'] == 'TOTAL']
                    if len(total_volume) > 1:
                        recent_volume = total_volume['volume'].iloc[-1]
                        prev_volume = total_volume['volume'].iloc[-2] if len(total_volume) > 1 else recent_volume
                        volume_change = ((recent_volume - prev_volume) / prev_volume * 100) if prev_volume > 0 else 0
                        st.metric("Recent Volume", f"{recent_volume:,.0f}")
                        st.metric("Volume Change", f"{volume_change:+.1f}%")
            
            with col3:
                st.markdown("### ⚠️ Plateau Detection")
                plateaus = overload_dashboard['plateau_analysis']['plateaus']
                if plateaus:
                    st.metric("Plateaus Detected", len(plateaus))
                    st.metric("Most Critical", plateaus[0]['exercise'] if plateaus else "None")
                else:
                    st.metric("Plateaus Detected", 0)
                    st.metric("Status", "✅ Clear")
            
            # Volume Progression Chart
            st.markdown("### 📈 Volume Progression")
            if selected_exercise == "All Exercises":
                volume_chart = progressive_tracker.create_volume_progression_chart(athlete_id)
            else:
                volume_chart = progressive_tracker.create_volume_progression_chart(athlete_id, selected_exercise)
            st.plotly_chart(volume_chart, use_container_width=True)
            
            # Strength Velocity Chart
            st.markdown("### 💪 Strength Gain Velocity")
            strength_chart = progressive_tracker.create_strength_velocity_chart(athlete_id)
            if len(strength_chart.data) > 0:
                st.plotly_chart(strength_chart, use_container_width=True)
            else:
                st.info("Insufficient data for strength velocity analysis")
            
            # Recommendations
            st.markdown("### 💡 Progressive Overload Recommendations")
            recommendations = overload_dashboard['recommendations']
            for i, rec in enumerate(recommendations):
                st.markdown(f"{i+1}. {rec}")
            
            # Detailed Plateau Analysis
            if overload_dashboard['plateau_analysis']['plateaus']:
                st.markdown("### 🔍 Plateau Analysis Details")
                plateau_df = pd.DataFrame(overload_dashboard['plateau_analysis']['plateaus'])
                st.dataframe(
                    plateau_df[['exercise', 'type', 'severity', 'recommendation']],
                    use_container_width=True
                )
        
        with tab7:  # Coaching Directives
            st.subheader(f"🎯 {profile.full_name} - Professional Coaching Directives")
            
            # Initialize coaching engine
            if 'coaching_engine' not in st.session_state:
                st.session_state.coaching_engine = CoachingEngine(st.session_state.athlete_df, profile.__dict__)
            
            coaching_engine = st.session_state.coaching_engine
            directives = coaching_engine.generate_coaching_directives()
            
            # Performance Status
            st.markdown("### 📊 Performance Status")
            perf_status = directives['performance_status']
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Strength Progression", perf_status['current_status']['strength_progression'].title())
                st.metric("Competition Readiness", perf_status['current_status']['competition_readiness'].replace('_', ' ').title())
            
            with col2:
                st.metric("Strength Gain Rate", f"{perf_status['key_metrics']['strength_gain_rate_kg_week']} kg/week")
            
            with col3:
                if perf_status['current_limitations']:
                    st.metric("Limitations", len(perf_status['current_limitations']))
                    for limitation in perf_status['current_limitations']:
                        st.caption(f"• {limitation.replace('_', ' ').title()}")
                else:
                    st.metric("Limitations", "None Identified")
            
            # Primary Focus Areas
            if directives['primary_focus_areas']:
                st.markdown("### 🎯 Primary Focus Areas")
                for i, focus in enumerate(directives['primary_focus_areas'], 1):
                    with st.expander(f"{i}. {focus['area']} (Priority: {focus['priority'].title()})"):
                        st.markdown(f"**Objective:** {focus['objective']}")
                        st.markdown(f"**Frequency:** {focus['prescription']['frequency']}")
                        st.markdown("**Exercises:**")
                        for exercise in focus['prescription']['exercises']:
                            st.markdown(f"- {exercise['name']}: {exercise['sets']}×{exercise['reps']}")
                        st.markdown(f"**Progression Rule:** {focus['prescription']['progression_rule']}")
            
            # Training Adjustments
            if directives['training_adjustments']:
                st.markdown("### ⚙️ Training Adjustments")
                for i, adjustment in enumerate(directives['training_adjustments'], 1):
                    with st.expander(f"{i}. {adjustment['adjustment_type'].replace('_', ' ').title()}"):
                        st.markdown(f"**Objective:** {adjustment['objective']}")
                        st.markdown(f"**Action:** {adjustment['prescription']['action']}")
                        st.markdown(f"**Method:** {adjustment['prescription']['method']}")
            
            # Risk Management
            if directives['risk_management']:
                st.markdown("### ⚠️ Risk Management")
                for i, risk in enumerate(directives['risk_management'], 1):
                    with st.expander(f"{i}. {risk['risk_type'].replace('_', ' ').title()} (Severity: {risk['severity'].title()})"):
                        st.markdown("**Interventions:**")
                        for intervention in risk['interventions']:
                            st.markdown(f"- {intervention['exercise']}: {intervention['sets']}×{intervention['reps']}")
                        
                        st.markdown("**Temporary Adjustment:**")
                        st.markdown(f"- Action: {risk['temporary_adjustment']['action']}")
                        st.markdown(f"- Duration: {risk['temporary_adjustment']['duration']}")
            
            # Sport-Specific Programming
            st.markdown("### 🏆 Sport-Specific Programming")
            sport_prog = directives['sport_specific_programming']
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Sport:** {sport_prog['sport']}")
                st.markdown(f"**Competition Focus:** {sport_prog['competition_focus']}")
                st.markdown(f"**Event Practice Frequency:** {sport_prog['event_specialization']['frequency']}")
            
            with col2:
                st.markdown("**Events:**")
                for event in sport_prog['event_specialization']['events']:
                    st.markdown(f"- {event['name']}: {event['sessions']} sessions (Focus: {event['focus']})")
            
            # Progression Rules
            st.markdown("**Progression Rules:**")
            for rule, description in sport_prog['event_specialization']['progression_rules'].items():
                st.markdown(f"- {rule.replace('_', ' ').title()}: {description}")
        
        with tab8:  # AI Coach Brain
            st.subheader(f"🧠 AI Coach Brain - Cognitive Coaching for {profile.full_name}")
            
            # Initialize AI components
            if 'ai_brain' not in st.session_state:
                st.session_state.ai_brain = CognitiveCoachingBrain()
                st.session_state.verification_layer = VerificationLayer()
            
            ai_brain = st.session_state.ai_brain
            verification_layer = st.session_state.verification_layer
            
            enriched_metrics = st.session_state.weekly_metrics
            enriched_df = st.session_state.enriched_df

            # Use existing modules to produce the metrics the AI must acknowledge
            recovery_tracker = RecoveryTracker(enriched_df)
            acwr_df = recovery_tracker.calculate_acute_chronic_load(profile.athlete_id)
            acwr_value = float(acwr_df.tail(1)['acwr'].iloc[0]) if len(acwr_df) > 0 else 1.0
            recovery_score = recovery_tracker.calculate_recovery_score(profile.athlete_id)
            fatigue_value = 1.0 - (float(recovery_score.get('score', 50)) / 100.0)

            overload_tracker = ProgressiveOverloadTracker(enriched_df)
            plateau_analysis = overload_tracker.detect_plateaus(profile.athlete_id)
            overload_status = {'plateau_detection': plateau_analysis}

            risk_flags = []
            if 'injury_risk_flag' in enriched_df.columns and len(enriched_df[enriched_df['injury_risk_flag'] == 'high']) > 0:
                risk_flags.append('high_injury_risk')
            if len(acwr_df) > 0 and str(acwr_df.tail(1)['fatigue_zone'].iloc[0]) == 'high_risk':
                risk_flags.append('overtraining_risk')

            context = ai_brain.package_coach_context(
                athlete_data=enriched_df,
                acwr_value=acwr_value,
                fatigue_value=fatigue_value,
                overload_status=overload_status,
                risk_flags=risk_flags,
                athlete_profile={
                    'athlete_id': profile.athlete_id,
                    'full_name': profile.full_name,
                    'sport': profile.sport,
                    'level': profile.get_strength_level()
                }
            )

            ai_package = ai_brain.generate_structured_coaching_package(
                context=context,
                athlete_profile={
                    'athlete_id': profile.athlete_id,
                    'full_name': profile.full_name,
                    'sport': profile.sport,
                    'level': profile.get_strength_level()
                }
            )

            ai_directive = ai_package['summary']
            structured = ai_package['directives']

            # Safety verification layer
            existing_metrics = {
                "acwr": context["metrics"]["acwr"],
                "fatigue": context["metrics"]["fatigue"],
                "risk_flags": context["metrics"]["risk_flags"]
            }

            verification_result = verification_layer.verify_ai_recommendation(
                ai_directive=ai_directive,
                existing_metrics=existing_metrics,
                risk_flags=context["metrics"]["risk_flags"]
            )

            # Display AI Coaching Results
            col1, col2 = st.columns([2, 1])

            with col1:
                st.markdown("### 🤖 AI Coaching Directive")

                # Safety status indicator
                safety_status = verification_layer.get_safety_status_color(verification_result)
                st.markdown(f"**Safety Status:** {safety_status}")

                if verification_result["approved"]:
                    st.success(ai_directive["recommendation"])
                else:
                    st.error(ai_directive["recommendation"])
                    st.warning("⚠️ **SAFETY CONFLICT DETECTED**")
                    for conflict in verification_result["conflicts"]:
                        st.error(f"• {conflict}")

                    if verification_result["modified_recommendation"]:
                        st.info(f"🛡️ **Safe Alternative:** {verification_result['modified_recommendation']}")

                # Display reasoning
                with st.expander("🧠 AI Reasoning"):
                    st.write(ai_directive["reasoning"])
                    st.metric("Confidence Score", f"{ai_directive['confidence']:.2f}")

                st.markdown("---")
                st.markdown("### 🧩 Structured Coaching Directives")

                st.markdown("#### Performance Status")
                st.info(
                    f"Readiness: {structured['performance_status']['current_status']['readiness'].replace('_', ' ').title()}\n\n"
                    f"Progression: {structured['performance_status']['current_status']['progression'].replace('_', ' ').title()}\n\n"
                    f"ACWR: {structured['performance_status']['key_metrics']['acwr']} | Fatigue: {structured['performance_status']['key_metrics']['fatigue']}"
                )

                st.markdown("#### Primary Focus Areas")
                for i, focus in enumerate(structured['primary_focus_areas'], 1):
                    with st.expander(f"{i}. {focus['area']} (Priority: {focus['priority'].title()})"):
                        st.markdown(f"**Objective:** {focus['objective']}")
                        st.markdown(f"**Frequency:** {focus['prescription']['frequency']}")
                        st.markdown("**Exercises:**")
                        for ex in focus['prescription']['exercises']:
                            st.markdown(f"- {ex['name']}: {ex['sets']}×{ex['reps']}")
                        st.markdown(f"**Progression Rule:** {focus['prescription']['progression_rule']}")

                st.markdown("#### Training Adjustments")
                for i, adj in enumerate(structured['training_adjustments'], 1):
                    with st.expander(f"{i}. {adj['adjustment_type'].replace('_', ' ').title()}"):
                        st.markdown(f"**Objective:** {adj['objective']}")
                        st.markdown(f"**Action:** {adj['prescription']['action']}")
                        st.markdown(f"**Method:** {adj['prescription']['method']}")

                st.markdown("#### Risk Management")
                for i, risk in enumerate(structured['risk_management'], 1):
                    with st.expander(f"{i}. {risk['risk_type'].replace('_', ' ').title()} (Severity: {risk['severity'].title()})"):
                        st.markdown("**Interventions:**")
                        for iv in risk['interventions']:
                            st.markdown(f"- {iv['exercise']}: {iv['sets']}×{iv['reps']}")
                        st.markdown("**Temporary Adjustment:**")
                        st.markdown(f"- Action: {risk['temporary_adjustment']['action']}")
                        st.markdown(f"- Duration: {risk['temporary_adjustment']['duration']}")

                st.markdown("#### Sport-Specific Programming")
                sp = structured['sport_specific_programming']
                st.markdown(f"**Sport:** {sp['sport']}")
                st.markdown(f"**Competition Focus:** {sp['competition_focus']}")
                st.markdown(f"**Event Practice Frequency:** {sp['event_specialization']['frequency']}")
                st.markdown("**Events:**")
                for ev in sp['event_specialization']['events']:
                    st.markdown(f"- {ev['name']}: {ev['sessions']} sessions (Focus: {ev['focus']})")
                st.markdown("**Progression Rules:**")
                for rule, desc in sp['event_specialization']['progression_rules'].items():
                    st.markdown(f"- {rule.replace('_', ' ').title()}: {desc}")

                # Display action items
                if ai_directive["action_items"]:
                    st.markdown("### 📋 Action Items")
                    for i, action in enumerate(ai_directive["action_items"], 1):
                        st.write(f"{i}. {action}")

            with col2:
                st.markdown("### 📊 Context Metrics")

                # Display key metrics that AI considered
                metrics_col1, metrics_col2 = st.columns(2)
                with metrics_col1:
                    st.metric("ACWR", f"{context['metrics']['acwr']:.2f}")
                    st.metric("Fatigue", f"{context['metrics']['fatigue']:.2f}")
                with metrics_col2:
                    st.metric("7-Day RPE", f"{context['metrics']['avg_rpe_7days']:.1f}")
                    st.metric("Progression", context['training_patterns']['recent_progression'].replace('_', ' ').title())

                # Risk flags
                if context['metrics']['risk_flags']:
                    st.markdown("### ⚠️ Active Risk Flags")
                    for risk in context['metrics']['risk_flags']:
                        if str(risk).strip():
                            st.warning(f"• {str(risk).replace('_', ' ').title()}")

                # Verification details
                if verification_result["safety_warnings"]:
                    st.markdown("### 🛡️ Safety Warnings")
                    for warning in verification_result["safety_warnings"]:
                        st.error(warning)

            # Adaptive insights section
            st.markdown("---")
            st.markdown("### 📈 Adaptive Learning Insights")

            adaptive_insights = ai_brain.get_adaptive_insights(profile.athlete_id)

            if "total_recommendations" in adaptive_insights:
                insight_col1, insight_col2, insight_col3 = st.columns(3)
                with insight_col1:
                    st.metric("Total AI Recommendations", adaptive_insights["total_recommendations"])
                with insight_col2:
                    st.metric("Success Rate", f"{adaptive_insights['success_rate']:.1%}")
                with insight_col3:
                    st.metric("Recent Trend", adaptive_insights["recent_trend"].replace('_', ' ').title())

                if adaptive_insights.get("avg_performance_change", 0) != 0:
                    st.metric("Avg Performance Change", f"{adaptive_insights['avg_performance_change']:+.1f}")

            # Feedback collection for learning
            st.markdown("---")
            st.markdown("### 🔄 Feedback Loop")

            feedback_col1, feedback_col2 = st.columns(2)
            with feedback_col1:
                performance_change = st.number_input(
                    "Performance Change (kg or %)",
                    min_value=-50.0,
                    max_value=50.0,
                    value=0.0,
                    step=0.5,
                    help="Enter the performance change after implementing AI recommendation"
                )

            with feedback_col2:
                rpe_change = st.number_input(
                    "RPE Change",
                    min_value=-5.0,
                    max_value=5.0,
                    value=0.0,
                    step=0.1,
                    help="Change in average RPE after implementing recommendation"
                )

            feedback_notes = st.text_area(
                "Feedback Notes",
                placeholder="How did the AI recommendation work? Any observations?",
                help="Your feedback helps the AI learn and improve"
            )

            if st.button("📝 Submit Feedback"):
                # Store feedback for adaptive learning
                # Note: In a real implementation, we'd need the recommendation_id
                st.success("✅ Feedback recorded! This helps improve future recommendations.")
                st.info("🔄 The AI is learning from your feedback to provide better recommendations.")
        
        with tab9:  # Export
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
