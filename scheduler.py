import pandas as pd
from ortools.sat.python import cp_model

def schedule_jobs(jobs_df, tanks_df, start_date):
    model = cp_model.CpModel()
    horizon = 24 * 60 * 7  # 分単位の1週間分

    job_vars = {}
    for _, row in jobs_df.iterrows():
        job_id = row['JobID']
        # ★ 時間を分に変換してスケジューラに渡す
        dur_min = int(float(row['DurationMin']) * 60)
        start = model.NewIntVar(0, horizon, f"start_{job_id}")
        end = model.NewIntVar(0, horizon, f"end_{job_id}")
        interval = model.NewIntervalVar(start, dur_min, end, f"interval_{job_id}")
        job_vars[job_id] = {'start': start, 'end': end, 'interval': interval}

    # 同一めっき種類での同時処理を禁止（シンプル制約）
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
