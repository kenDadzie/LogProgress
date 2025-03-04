import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

# Page configuration
st.set_page_config(
    page_title="Skill Challenge Progress Log",
    page_icon="📚",
    layout="wide"
)

# Initialize session state
if 'success_message' not in st.session_state:
    st.session_state.success_message = False

# Initialize names list in session state
if 'names_list' not in st.session_state:
    st.session_state.names_list = []

# Ensure data directory exists
os.makedirs('data', exist_ok=True)
CSV_PATH = 'data/progress_logs.csv'

# Create CSV if it doesn't exist
if not os.path.exists(CSV_PATH):
    pd.DataFrame(columns=[
        'Name', 'Date', 'Skill Focus', 'Hours Practiced',
        'Progress Description', 'Challenges Faced',
        'Commitment Check', 'Additional Comments'
    ]).to_csv(CSV_PATH, index=False)

def load_data():
    """Load existing progress logs"""
    try:
        df = pd.read_csv(CSV_PATH)
        if not df.empty:
            df['Date'] = pd.to_datetime(df['Date'])
            # Update names list in session state
            st.session_state.names_list = sorted(df['Name'].unique().tolist())
        return df
    except:
        return pd.DataFrame()

def save_entry(entry_data):
    """Save new entry to CSV"""
    df = load_data()
    new_entry = pd.DataFrame([entry_data])
    updated_df = pd.concat([new_entry, df], ignore_index=True)
    updated_df.to_csv(CSV_PATH, index=False)
    # Update names list after saving
    st.session_state.names_list = sorted(updated_df['Name'].unique().tolist())

def get_week_range(date):
    """Get the start and end date of the week containing the given date"""
    start = date - timedelta(days=date.weekday())  # Monday
    end = start + timedelta(days=6)  # Sunday
    return start, end

def calculate_weekly_hours(df, user_name):
    """Calculate total hours for the current week for a specific user"""
    if df.empty:
        return 0

    today = pd.Timestamp.now()
    week_start, week_end = get_week_range(today)

    weekly_data = df[
        (df['Name'] == user_name) & 
        (df['Date'] >= week_start) & 
        (df['Date'] <= week_end)
    ]

    return weekly_data['Hours Practiced'].sum()

def create_skill_radar_chart(user_df):
    """Create a radar chart showing skill progress"""
    if user_df.empty:
        return None

    skill_hours = user_df.groupby('Skill Focus')['Hours Practiced'].sum()

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=skill_hours.values,
        theta=skill_hours.index,
        fill='toself',
        name='Hours Spent'
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, max(skill_hours.values) * 1.2]
            )),
        showlegend=False,
        title="Skill Progress Radar"
    )
    return fig

def create_activity_heatmap(user_df):
    """Create a heatmap of daily activity"""
    if user_df.empty:
        return None

    # Create daily activity summary
    daily_activity = user_df.groupby('Date')['Hours Practiced'].sum().reset_index()
    daily_activity['WeekDay'] = daily_activity['Date'].dt.day_name()
    daily_activity['Week'] = daily_activity['Date'].dt.isocalendar().week

    # Pivot for heatmap format
    heatmap_data = daily_activity.pivot_table(
        values='Hours Practiced',
        index='Week',
        columns='WeekDay',
        aggfunc='sum'
    )

    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        z=heatmap_data.values,
        x=heatmap_data.columns,
        y=heatmap_data.index,
        colorscale='Viridis',
        hoverongaps=False
    ))

    fig.update_layout(
        title="Activity Heatmap",
        xaxis_title="Day of Week",
        yaxis_title="Week Number"
    )
    return fig

def create_progress_gauge(value, max_value, title):
    """Create a gauge chart for progress visualization"""
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = value,
        title = {'text': title},
        gauge = {
            'axis': {'range': [None, max_value]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, max_value/3], 'color': "lightgray"},
                {'range': [max_value/3, 2*max_value/3], 'color': "gray"},
                {'range': [2*max_value/3, max_value], 'color': "darkgray"}
            ]
        }
    ))
    return fig

# Load initial data to populate names list
load_data()

# Application header
st.title("🎯 Skill Challenge Progress Log")
st.markdown("""
    Track your skill development journey by logging your practice sessions.
    Fill in the details below to record your progress.
""")

# Create form
with st.form("progress_log_form"):
    col1, col2 = st.columns(2)

    with col1:
        # Name input with autocomplete
        name = st.selectbox("Name *",
            options=[""] + st.session_state.names_list,
            help="Enter your name or select from previous entries")

        # If empty string selected, show text input
        if not name:
            name = st.text_input("Or enter a new name *",
                help="Enter your full name")

        date = st.date_input("Date *", 
            help="Select the date of your practice session")
        skill_focus = st.text_input("Skill Focus *",
            help="What skill are you working on?")
        hours = st.number_input("Hours Practiced *",
            min_value=0.0, max_value=24.0, step=0.5,
            help="How many hours did you practice?")

    with col2:
        progress_description = st.text_area("Progress Description *",
            help="Describe what you accomplished during this session")
        challenges = st.text_area("Challenges Faced",
            help="What difficulties did you encounter?")
        commitment = st.selectbox("Commitment Check *",
            options=["Strong - Exceeded Goals", "Good - Met Goals", 
                    "Fair - Partial Progress", "Needs Improvement"],
            help="How well did you meet your commitment?")
        comments = st.text_area("Additional Comments",
            help="Any other thoughts or reflections?")

    submit_button = st.form_submit_button("Log Progress")

    if submit_button:
        # Validate required fields
        if not all([name, date, skill_focus, hours, progress_description, commitment]):
            st.error("Please fill in all required fields marked with *")
        else:
            # Prepare entry data
            entry_data = {
                'Name': name,
                'Date': date.strftime('%Y-%m-%d'),
                'Skill Focus': skill_focus,
                'Hours Practiced': hours,
                'Progress Description': progress_description,
                'Challenges Faced': challenges,
                'Commitment Check': commitment,
                'Additional Comments': comments
            }

            # Save entry
            save_entry(entry_data)
            st.session_state.success_message = True

# Show success message
if st.session_state.success_message:
    st.success("Progress successfully logged!")
    st.session_state.success_message = False

# Display logged entries and analytics
st.markdown("---")
st.subheader("📊 Progress Analytics and History")

df = load_data()
if not df.empty:
    # User filter
    all_users = ['All Users'] + sorted(df['Name'].unique().tolist())
    selected_user = st.selectbox("Select User", all_users)

    # Filter data for selected user
    if selected_user != 'All Users':
        user_df = df[df['Name'] == selected_user]

        # Calculate weekly progress
        weekly_hours = calculate_weekly_hours(df, selected_user)

        # Weekly progress alert/congratulation
        st.subheader("📅 Weekly Progress Update")
        col1, col2 = st.columns(2)

        with col1:
            # Create and display weekly progress gauge
            weekly_gauge = create_progress_gauge(
                weekly_hours, 10,
                "Weekly Hours (Target: 5)"
            )
            st.plotly_chart(weekly_gauge, use_container_width=True)
            week_start, week_end = get_week_range(pd.Timestamp.now())
            st.caption(f"Week of {week_start.strftime('%Y-%m-%d')} to {week_end.strftime('%Y-%m-%d')}")

        with col2:
            if weekly_hours < 5:
                hours_needed = 5 - weekly_hours
                st.warning(f"⚠️ You need {hours_needed:.1f} more hours this week to reach your 5-hour goal!")
            else:
                st.success(f"🎉 Congratulations! You've exceeded your 5-hour weekly goal with {weekly_hours:.1f} hours!")

        # Enhanced visualization dashboard
        st.subheader("🎨 Progress Visualization Dashboard")

        # Create visualization layout
        viz_col1, viz_col2 = st.columns(2)

        with viz_col1:
            # Radar chart for skill progress
            radar_chart = create_skill_radar_chart(user_df)
            if radar_chart:
                st.plotly_chart(radar_chart, use_container_width=True)

        with viz_col2:
            # Activity heatmap
            heatmap = create_activity_heatmap(user_df)
            if heatmap:
                st.plotly_chart(heatmap, use_container_width=True)

    else:
        user_df = df

    # Analytics section
    if not user_df.empty:
        st.subheader("📈 Overall Progress")
        col1, col2, col3 = st.columns(3)

        with col1:
            total_hours = user_df['Hours Practiced'].sum()
            st.metric("Total Hours Practiced", f"{total_hours:.1f}")

        with col2:
            total_sessions = len(user_df)
            st.metric("Total Sessions", total_sessions)

        with col3:
            unique_skills = len(user_df['Skill Focus'].unique())
            st.metric("Skills in Progress", unique_skills)

        # Skill breakdown
        st.subheader("Hours per Skill")
        skill_hours = user_df.groupby('Skill Focus')['Hours Practiced'].sum().sort_values(ascending=False)

        # Create a colorful bar chart using plotly
        fig = px.bar(
            x=skill_hours.index,
            y=skill_hours.values,
            labels={'x': 'Skills', 'y': 'Hours'},
            color=skill_hours.values,
            color_continuous_scale='Viridis'
        )
        fig.update_layout(title="Skill Hours Distribution")
        st.plotly_chart(fig, use_container_width=True)

        # Monthly view
        if selected_user != 'All Users':
            st.subheader("📅 Monthly Overview")
            monthly_hours = user_df.set_index('Date').resample('M')['Hours Practiced'].sum()

            # Create an area chart using plotly
            fig = px.area(
                monthly_hours,
                labels={'value': 'Hours', 'Date': 'Month'},
                color_discrete_sequence=['rgb(67, 133, 244)']
            )
            fig.update_layout(title="Monthly Progress Trend")
            st.plotly_chart(fig, use_container_width=True)

        # Progress timeline
        st.subheader("Recent Progress Entries")
        user_df = user_df.sort_values('Date', ascending=False)

        for idx, row in user_df.iterrows():
            with st.expander(f"{row['Date'].strftime('%Y-%m-%d')} - {row['Skill Focus']}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Name:** {row['Name']}")
                    st.markdown(f"**Hours Practiced:** {row['Hours Practiced']}")
                    st.markdown(f"**Progress Description:**\n{row['Progress Description']}")
                with col2:
                    st.markdown(f"**Commitment Check:** {row['Commitment Check']}")
                    st.markdown(f"**Challenges Faced:**\n{row['Challenges Faced']}")
                    if pd.notna(row['Additional Comments']):
                        st.markdown(f"**Additional Comments:**\n{row['Additional Comments']}")
else:
    st.info("No entries logged yet. Start tracking your progress by filling out the form above!")

# Add custom CSS for better styling
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        margin-top: 10px;
    }
    .stExpander {
        background-color: #f0f2f6;
        border-radius: 5px;
        margin-bottom: 10px;
    }
    .css-1d391kg {
        padding-top: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)