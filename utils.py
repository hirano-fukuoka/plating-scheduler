import pandas as pd
import plotly.express as px

def plot_gantt_by_tank(schedule_df):
    df = schedule_df.copy()
    df["Start Time"] = pd.to_datetime(df["Start Time"])
    df["End Time"] = pd.to_datetime(df["End Time"])

    fig = px.timeline(
        df,
        x_start="Start Time",
        x_end="End Time",
        y="TankID",
        color="Step",
        hover_data=["JobID", "PlatingType", "Shift"],
        title="Plating Schedule by Tank"
    )

    fig.update_yaxes(title="Tank ID", categoryorder="category ascending")
    fig.update_xaxes(title="Time")
    fig.update_layout(margin=dict(l=40, r=40, t=60, b=30), height=600)
    return fig
