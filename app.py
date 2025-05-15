import streamlit as st
import pandas as pd
from scheduler import schedule_jobs

st.set_page_config(layout="wide")
st.title("めっき工程スケジューラ（完全版）")

start_date = st.date_input("スケジュール開始日を選択")

uploaded_file = st.file_uploader("品物リストCSVをアップロード", type=["csv"])
if uploaded_file:
    jobs_df = pd.read_csv(uploaded_file)
    st.write("アップロード内容")
    st.dataframe(jobs_df)

    tanks_df = pd.read_csv("data/plating_tanks.csv")

    if st.button("スケジュール作成"):
        schedule_df = schedule_jobs(jobs_df, tanks_df, start_date)
        if schedule_df.empty:
            st.error("スケジュール作成に失敗しました。")
        else:
            st.success("スケジュール作成完了")
            st.dataframe(schedule_df)
            csv = schedule_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 CSVをダウンロード", data=csv, file_name="schedule_output.csv", mime="text/csv")
