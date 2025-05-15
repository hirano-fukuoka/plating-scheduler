import pandas as pd
from ortools.sat.python import cp_model

def schedule_jobs(jobs_df, tanks_df, start_date):
    model = cp_model.CpModel()

    # 🔄 DurationMinは「時間」単位 → 分に変換
    jobs_df["DurationMinInt"] = (jobs_df["DurationMin"].astype(float) * 60).astype(int)

    # ✅ horizon を動的に決定：総処理時間の合計 + 30% のバッファ
    total_required_minutes = jobs_df["DurationMinInt"].sum()
    horizon = int(total_required_minutes * 1.3)

    job_vars = {}
    for _, row in jobs_df.iterrows():
        job_id = row['JobID']
        dur_min = row["DurationMinInt"]
        start = model.NewIntVar(0, horizon, f"start_{job_id}")
        end = model.NewIntVar(0, horizon, f"end_{job_id}")
        interval = model.NewIntervalVar(start, dur_min, end, f"interval_{job_id}")
        job_vars[job_id] = {'start': start, 'end': end, 'interval': interval}

    # PlatingTypeごとに重複不可制約（後で拡張可）
    for plating in jobs_df['PlatingType'].unique():
        intervals = [job_vars[row['JobID']]['interval'] for _, row in jobs_df.iterrows() if row['PlatingType'] == plating]
        if len(intervals) > 1:
            model.AddNoOverlap(intervals)

    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    results = []
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        for job_id in jobs_df['JobID']:
            s = solver.Value(job_vars[job_id]['start'])
            e = solver.Value(job_vars[job_id]['end'])
            plating = jobs_df[jobs_df['JobID'] == job_id]['PlatingType'].values[0]

            dt_start = pd.to_datetime(start_date) + pd.to_timedelta(s, unit='m')
            dt_end = pd.to_datetime(start_date) + pd.to_timedelta(e, unit='m')

            results.append({
                'JobID': job_id,
                'PlatingType': plating,
                'Start': s,
                'End': e,
                '入槽日時': dt_start.strftime('%Y-%m-%d %H:%M'),
                '出槽日時': dt_end.strftime('%Y-%m-%d %H:%M')
            })

    return pd.DataFrame(results)
