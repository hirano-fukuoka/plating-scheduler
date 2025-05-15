import pandas as pd
from ortools.sat.python import cp_model

def schedule_jobs(jobs_df, tanks_df):
    model = cp_model.CpModel()
    horizon = 24 * 60 * 7  # 1週間分（分単位）

    # 準備
    job_vars = {}
    for i, row in jobs_df.iterrows():
        job_id = row['JobID']
        dur = int(row['DurationMin'])
        suffix = f"_{job_id}"
        start = model.NewIntVar(0, horizon, "start" + suffix)
        end = model.NewIntVar(0, horizon, "end" + suffix)
        interval = model.NewIntervalVar(start, dur, end, "interval" + suffix)
        job_vars[job_id] = {'start': start, 'end': end, 'interval': interval}

    # シンプルな重複防止制約（同じPlatingTypeは同時にできない）
    for plating in jobs_df['PlatingType'].unique():
        intervals = []
        for i, row in jobs_df.iterrows():
            if row['PlatingType'] == plating:
                intervals.append(job_vars[row['JobID']]['interval'])
        if len(intervals) > 1:
            model.AddNoOverlap(intervals)

    # 求解
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    results = []
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        for job_id in job_vars:
            start = solver.Value(job_vars[job_id]['start'])
            end = solver.Value(job_vars[job_id]['end'])
            plating = jobs_df[jobs_df['JobID'] == job_id]['PlatingType'].values[0]
            results.append({
                'JobID': job_id,
                'Start': start,
                'End': end,
                'PlatingType': plating
            })
    return pd.DataFrame(results)
