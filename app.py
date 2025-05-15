import streamlit as st
import pandas as pd
from datetime import datetime
from scheduler import schedule_jobs
from utils import plot_gantt

st.set_page_config(layout="wide")
st.title("めっき工程スケジューリングアプリ")

# 開始日
start_date = st.date_input("スケジュール開始日を選択", datetime(2025, 5, 15))

# CSV アップロード
uploaded_file = st.file_uploader("めっき対象の品物リスト（CSV）をアップロード", type=["csv"])
if uploaded_file:
    jobs_df = pd.read_csv(uploaded_file)
    st.subheader("品目一覧")
    st.dataframe(jobs_df)

    tanks_df = pd.read_csv("data/plating_tanks.csv")

    if st.button("スケジュール作成"):
        schedule_df = schedule_jobs(jobs_df, tanks_df, start_date)

        if schedule_df.empty:
            st.error("⚠️ スケジュールが作成できませんでした。")
        else:
            st.success("✅ スケジュール作成完了")
            schedule_df_sorted = schedule_df.sort_values("JobID")

            # 表示
            st.subheader("スケジュール結果")
            st.dataframe(schedule_df_sorted[['JobID', 'PlatingType', '入槽日時', '出槽日時']])

            # Gantt チャート
            st.subheader("工程ガントチャート")
            fig = plot_gantt(schedule_df_sorted, start_date)
            st.plotly_chart(fig, use_container_width=True)

            # CSV 出力
            csv = schedule_df_sorted.to_csv(index=False).encode('utf-8')
            st.download_button("📥 CSVでダウンロード", data=csv, file_name="schedule_output.csv", mime="text/csv")
