import streamlit as st
import pandas as pd
from scheduler import schedule_jobs
from utils import plot_gantt

st.title("めっき工程スケジューリングアプリ")

# データ読み込み
jobs_df = pd.read_csv("data/sample_jobs.csv")
tanks_df = pd.read_csv("data/plating_tanks.csv")

st.subheader("品目データ")
st.dataframe(jobs_df)

if st.button("スケジュール作成"):
    schedule_df = schedule_jobs(jobs_df, tanks_df)
    st.success("スケジュール作成完了")
    st.dataframe(schedule_df)
    fig = plot_gantt(schedule_df)
    st.plotly_chart(fig)
