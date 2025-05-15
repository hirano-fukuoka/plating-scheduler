import streamlit as st
import pandas as pd
from datetime import datetime
from scheduler import schedule_jobs
from utils import plot_gantt

st.set_page_config(layout="wide")
st.title("めっき工程スケジューリング（完全版）")

start_date = st.date_input("スケジュール開始日", datetime.today())

uploaded_file = st.file_uploader("工程CSVファイルをアップロード", type=["csv"])
if uploaded_file:
    jobs_df = pd.read_csv(uploaded_file)
    st.subheader("アップロードされた品目一覧")
    st.dataframe(jobs_df)

    tanks_df = pd.read_csv("data/plating_tanks.csv")

    if st.button("スケジュール作成"):
        schedule_df = schedule_jobs(jobs_df, tanks_df, start_date)
        if schedule_df.empty:
            st.error("⚠️ スケジュールが作成できませんでした。")
        else:
            st.success("✅ スケジュール作成完了")
            st.dataframe(schedule_df)
            csv = schedule_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 CSVダウンロード", csv, file_name="schedule_result.csv", mime="text/csv")
