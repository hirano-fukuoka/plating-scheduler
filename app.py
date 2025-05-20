import streamlit as st
import pandas as pd
from datetime import datetime
from scheduler import schedule_jobs
from utils import plot_gantt_by_tank

# ============================================
# 日付範囲で3日×2ページ＋1日を分割表示する関数
# ============================================
def show_gantt_by_day_range(df, start_date, title_prefix="Schedule"):
    df["Start Time"] = pd.to_datetime(df["Start Time"])
    df["End Time"] = pd.to_datetime(df["End Time"])

    # 表示分割設定
    segments = [("Day 1–3", 0, 3), ("Day 4–6", 3, 6), ("Day 7", 6, 7)]
    selected_label = st.selectbox(f"{title_prefix} - Select Day Range", [s[0] for s in segments])
    selected_range = next(s for s in segments if s[0] == selected_label)

    base = pd.to_datetime(start_date)
    from_time = base + pd.Timedelta(days=selected_range[1])
    to_time = base + pd.Timedelta(days=selected_range[2])

    df_filtered = df[(df["Start Time"] < to_time) & (df["End Time"] >= from_time)].copy()

    if df_filtered.empty:
        st.warning(f"No jobs in {selected_label}")
        return

    import plotly.express as px
    fig = px.timeline(
        df_filtered,
        x_start="Start Time",
        x_end="End Time",
        y="TankID",
        color="Step",
        hover_data=["JobID", "Shift"]
    )

    fig.update_layout(
        title=f"{title_prefix}: {selected_label}",
        xaxis=dict(title="Time", tickformat="%m/%d %H:%M"),
        yaxis=dict(title="Tank ID", categoryorder="category ascending"),
        margin=dict(l=30, r=30, t=50, b=20),
        height=600
    )
    st.plotly_chart(fig, use_container_width=True)

# ============================================
# メインUI部分
# ============================================
st.set_page_config(layout="wide")
st.title("Plating Process Scheduler (Final Version)")

# 開始日選択
start_date = st.date_input("Select Schedule Start Date", datetime(2025, 5, 15))

# CSVアップロード
uploaded_file = st.file_uploader("Upload plating job CSV", type=["csv"])
if uploaded_file:
    try:
        jobs_df = pd.read_csv(uploaded_file)
        st.subheader("Uploaded Job List")
        st.dataframe(jobs_df)

        # タンクマスタ読み込み（なくても進行可能）
        try:
            tanks_df = pd.read_csv("data/plating_tanks.csv")
        except FileNotFoundError:
            tanks_df = pd.DataFrame(columns=["TankID", "PlatingType"])

        if st.button("Generate Schedule"):
            try:
                schedule_df = schedule_jobs(jobs_df, tanks_df, start_date)

                if schedule_df.empty:
                    st.error("❌ No schedule could be generated. Please check your input data or constraints.")
                else:
                    st.success("✅ Schedule created successfully")
                    st.subheader("Full Schedule Data")
                    st.dataframe(schedule_df)

                    # 工程ごとに分離
                    df_human = schedule_df[schedule_df["Step"].isin(["Soak", "Rinse"])]
                    df_auto = schedule_df[schedule_df["Step"] == "Plating"]

                    tab1, tab2 = st.tabs(["🧑 Human Work (Soak & Rinse)", "⚙️ Plating Work"])
                    
                    with tab1:
                        show_gantt_by_day_range(df_human, start_date, "Human Work")

                    with tab2:
                        show_gantt_by_day_range(df_auto, start_date, "Plating Work")

                    # ダウンロード
                    csv = schedule_df.to_csv(index=False).encode("utf-8")
                    st.download_button("📥 Download Schedule (CSV)", data=csv, file_name="schedule_output.csv", mime="text/csv")

            except Exception as e:
                st.error(f"⚠️ Error during scheduling:\n{e}")

    except Exception as e:
        st.error(f"⚠️ Failed to load CSV file:\n{e}")
