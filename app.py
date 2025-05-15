import streamlit as st
import pandas as pd
from datetime import timedelta
from scheduler import schedule_jobs
from utils import plot_gantt

st.title("めっき工程スケジューリングアプリ")

# 日付選択
start_date = st.date_input("スケジュール開始日を選択", pd.to_datetime("2025-05-15"))

# データ読み込み
jobs_df = pd.read_csv("data/sample_jobs.csv")
tanks_df = pd.read_csv("data/plating_tanks.csv")

st.subheader("品目データ")
st.dataframe(jobs_df)

if st.button("スケジュール作成"):
    schedule_df = schedule_jobs(jobs_df, tanks_df, start_date)
    if schedule_df.empty:
        st.error("スケジューラが解を見つけられませんでした。データを確認してください。")
    else:
        st.success("スケジュール作成完了")
        st.dataframe(schedule_df)
        fig = plot_gantt(schedule_df, start_date)
        st.plotly_chart(fig)

