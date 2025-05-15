import streamlit as st
import pandas as pd
from datetime import datetime
from scheduler import schedule_jobs
from utils import plot_gantt

st.title("めっき工程スケジューリングアプリ")

# 開始日選択
start_date = st.date_input("スケジュール開始日", datetime(2025, 5, 15))

# 品物リストのアップロード
uploaded_file = st.file_uploader("めっき対象の品物リストをCSVでアップロード", type=["csv"])
if uploaded_file:
    jobs_df = pd.read_csv(uploaded_file)
    st.dataframe(jobs_df)

    # めっき槽（種類ごとの設定）を固定ファイルから読み込み
    tanks_df = pd.read_csv("data/plating_tanks.csv")

    if st.button("スケジュール作成"):
        schedule_df = schedule_jobs(jobs_df, tanks_df, start_date)
        if schedule_df.empty:
            st.error("スケジューラが解を見つけられませんでした。データや制約条件を確認してください。")
        else:
            st.success("スケジュール作成完了")
            st.dataframe(schedule_df)
            fig = plot_gantt(schedule_df, start_date)
            st.plotly_chart(fig)
