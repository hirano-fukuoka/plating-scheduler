import streamlit as st
import pandas as pd
from datetime import datetime
from scheduler import schedule_jobs
from utils import plot_gantt_by_tank

st.set_page_config(layout="wide")
st.title("Plating Process Scheduler (Complete Version)")

# スケジュール開始日
start_date = st.date_input("Select Schedule Start Date", datetime(2025, 5, 15))

# CSV アップロード
uploaded_file = st.file_uploader("Upload plating job CSV", type=["csv"])
if uploaded_file:
    jobs_df = pd.read_csv(uploaded_file)
    st.subheader("Uploaded Job List")
    st.dataframe(jobs_df)

    # めっき槽データを読み込む（例：data/plating_tanks.csv）
    try:
        tanks_df = pd.read_csv("data/plating_tanks.csv")
    except FileNotFoundError:
        tanks_df = pd.DataFrame(columns=["TankID", "PlatingType"])  # 空でも動作可能

    # スケジュール生成ボタン
    if st.button("Generate Schedule"):
        try:
            schedule_df = schedule_jobs(jobs_df, tanks_df, start_date)

            if schedule_df.empty:
                st.error("❌ No schedule could be generated. Check job data or constraints.")
            else:
                st.success("✅ Schedule created successfully")
                st.dataframe(schedule_df)

                # Tank別 Ganttチャート
                fig = plot_gantt_by_tank(schedule_df)
                st.subheader("Schedule by Tank")
                st.plotly_chart(fig, use_container_width=True)

                # CSV出力
                csv = schedule_df.to_csv(index=False).encode("utf-8")
                st.download_button("📥 Download Schedule (CSV)", data=csv, file_name="schedule_output.csv", mime="text/csv")

        except Exception as e:
            st.error(f"⚠️ Error while generating schedule: {e}")
