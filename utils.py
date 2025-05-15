import plotly.express as px
import pandas as pd

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
        xaxis=dict(
            tickformat="%m/%d",
            title="日付"
        ),
        yaxis_title="ジョブID",
        margin=dict(l=20, r=20, t=50, b=20)
    )
    return fig
