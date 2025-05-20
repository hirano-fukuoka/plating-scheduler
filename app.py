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
    try:
        jobs_df = pd.read_csv(uploaded_file)
        st.subheader("Uploaded Job List")
        st.dataframe(jobs_df)

        # めっき槽マスタ読み込み（なければ空で処理）
        try:
            tanks_df = pd.read_csv("data/plating_tanks.csv")
        except FileNotFoundError:
            tanks_df = pd.DataFrame(columns=["TankID", "PlatingType"])

        if st.button("Generate Schedule"):
            try:
                schedule_df = schedule_jobs(jobs_df, tanks_df, start_date)

                if schedule_df.empty:
                    st.error("❌ No schedule could be generated. Please check job data or constraints.")
                else:
                    st.success("✅ Schedule created successfully")
                    st.subheader("Full Schedule Data")
                    st.dataframe(schedule_df)

                    # 人の作業と自動作業に分離
                    df_human = schedule_df[schedule_df["Step"].isin(["Soak", "Rinse"])]
                    df_auto = schedule_df[schedule_df["Step"] == "Plating"]

                    tab1, tab2 = st.tabs(["🧑 Human Work (Soak & Rinse)", "⚙️ Plating Work"])

                    with tab1:
                        fig_human = plot_gantt_by_tank(df_human)
                        st.plotly_chart(fig_human, use_container_width=True)

                    with tab2:
                        fig_auto = plot_gantt_by_tank(df_auto)
                        st.plotly_chart(fig_auto, use_container_width=True)

                    # CSV ダウンロード
                    csv = schedule_df.to_csv(index=False).encode("utf-8")
                    st.download_button("📥 Download Schedule (CSV)", data=csv, file_name="schedule_output.csv", mime="text/csv")

            except Exception as e:
                st.error(f"⚠️ Error while generating schedule:\n{e}")

    except Exception as e:
        st.error(f"⚠️ Failed to read CSV file:\n{e}")
