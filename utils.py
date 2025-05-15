import plotly.express as px
import pandas as pd

def plot_gantt(df):
    df['StartTime'] = pd.to_datetime(df['Start'], unit='m', origin='2025-01-01')
    df['EndTime'] = pd.to_datetime(df['End'], unit='m', origin='2025-01-01')
    return px.timeline(df, x_start="StartTime", x_end="EndTime", y="JobID", color="PlatingType")
