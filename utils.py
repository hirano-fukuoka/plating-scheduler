import pandas as pd
import plotly.express as px

def plot_gantt(df, start_date):
    df['StartTime'] = pd.to_datetime(start_date) + pd.to_timedelta(df['Start'], unit='m')
    df['EndTime'] = pd.to_datetime(start_date) + pd.to_timedelta(df['End'], unit='m')
    fig = px.timeline(
        df,
        x_start="StartTime",
        x_end="EndTime",
        y="JobID",
        color="PlatingType",
        title="めっき工程スケジュール"
    )
    fig.update_layout(
        xaxis_title="日付（%m/%d）",
        yaxis_title="品目（JobID）",
        xaxis_tickformat="%m/%d %H:%M",
        margin=dict(l=30, r=30, t=40, b=20)
    )
    return fig
