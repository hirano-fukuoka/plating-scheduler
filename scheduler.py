import pandas as pd
from ortools.sat.python import cp_model

def generate_working_minutes(num_days=14):
    working_minutes = set()
    for day in range(num_days):
        base = day * 1440
        working_minutes.update(range(base + 510, base + 1050))  # 甲番
        working_minutes.update(range(base + 900, base + 1440))  # 乙番
    return sorted(list(working_minutes))

def schedule_jobs(jobs_df, tanks_df, start_date):
    model = cp_model.CpModel()
    jobs_df["PlatingMin"] = (jobs_df["DurationHour"].astype(float) * 60).astype(int)
    jobs_df["SoakMin"] = jobs_df["入槽時間"].astype(int)
    jobs_df["RinseMin"] = jobs_df["出槽時間"].astype(int)

    horizon = int(jobs_df[["PlatingMin", "SoakMin", "RinseMin"]].sum().sum() * 1.5)
    working_minutes = generate_working_minutes(num_days=30)

    def restrict_to_working(var):
        model.AddAllowedAssignments([var], [[m] for m in working_minutes])

    job_vars = {}
    for _, row in jobs_df.iterrows():
        jid = row['JobID']
        soak_dur = row['SoakMin']
        plating_dur = row['PlatingMin']
        rinse_dur = row['RinseMin']

        s1 = model.NewIntVar(0, horizon, f"start_soak_{jid}")
        e1 = model.NewIntVar(0, horizon, f"end_soak_{jid}")
        iv1 = model.NewIntervalVar(s1, soak_dur, e1, f"iv_soak_{jid}")

        s2 = model.NewIntVar(0, horizon, f"start_plate_{jid}")
        e2 = model.NewIntVar(0, horizon, f"end_plate_{jid}")
        iv2 = model.NewIntervalVar(s2, plating_dur, e2, f"iv_plate_{jid}")

        s3 = model.NewIntVar(0, horizon, f"start_rinse_{jid}")
        e3 = model.NewIntVar(0, horizon, f"end_rinse_{jid}")
        iv3 = model.NewIntervalVar(s3, rinse_dur, e3, f"iv_rinse_{jid}")

        # 順序制約
        model.Add(s2 >= e1)
        model.Add(s3 >= e2)

        # 入槽・出槽は勤務時間内に限定
        restrict_to_working(s1)
        restrict_to_working(s3)

        job_vars[jid] = {
            'soak': (s1, e1, iv1),
            'plating': (s2, e2, iv2),
            'rinse': (s3, e3, iv3),
            'PlatingType': row["PlatingType"]
        }

    # 同じPlatingTypeでの重複処理を禁止（単純化版）
    for pt in jobs_df['PlatingType'].unique():
        plating_intervals = [job_vars[j]['plating'][2] for j in job_vars if job_vars[j]["PlatingType"] == pt]
        if len(plating_intervals) > 1:
            model.AddNoOverlap(plating_intervals)

    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    results = []
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        for jid in jobs_df['JobID']:
            s_soak = solver.Value(job_vars[jid]['soak'][0])
            e_soak = solver.Value(job_vars[jid]['soak'][1])
            s_plate = solver.Value(job_vars[jid]['plating'][0])
            e_plate = solver.Value(job_vars[jid]['plating'][1])
            s_rinse = solver.Value(job_vars[jid]['rinse'][0])
            e_rinse = solver.Value(job_vars[jid]['rinse'][1])

            base = pd.to_datetime(start_date)
            results.append({
                'JobID': jid,
                'PlatingType': job_vars[jid]['PlatingType'],
                '入槽開始': (base + pd.to_timedelta(s_soak, unit='m')).strftime('%Y-%m-%d %H:%M'),
                'めっき開始': (base + pd.to_timedelta(s_plate, unit='m')).strftime('%Y-%m-%d %H:%M'),
                'めっき終了': (base + pd.to_timedelta(e_plate, unit='m')).strftime('%Y-%m-%d %H:%M'),
                '出槽終了': (base + pd.to_timedelta(e_rinse, unit='m')).strftime('%Y-%m-%d %H:%M')
            })
    return pd.DataFrame(results)
