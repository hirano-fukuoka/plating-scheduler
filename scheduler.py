import pandas as pd
from ortools.sat.python import cp_model

def generate_working_minutes(num_days=14):
    minutes = set()
    for day in range(num_days):
        base = day * 1440
        minutes.update(range(base + 510, base + 1050))  # 甲番 8:30〜17:30
        minutes.update(range(base + 900, base + 1440))  # 乙番 15:00〜24:00
    return sorted(list(minutes))

def schedule_jobs(jobs_df, tanks_df, start_date):
    model = cp_model.CpModel()
    jobs_df["PlatingMin"] = (jobs_df["DurationHour"] * 60).astype(int)
    jobs_df["SoakMin"] = jobs_df["入槽時間"].astype(int)
    jobs_df["RinseMin"] = jobs_df["出槽時間"].astype(int)

    horizon = int(jobs_df[["PlatingMin", "SoakMin", "RinseMin"]].sum().sum() * 2)
    working_minutes = generate_working_minutes(num_days=30)

    def limit_to_working(var):
        model.AddAllowedAssignments([var], [[m] for m in working_minutes])

    job_vars = {}
    for _, row in jobs_df.iterrows():
        jid = row['JobID']
        soak_dur = row['SoakMin']
        plate_dur = row['PlatingMin']
        rinse_dur = row['RinseMin']

        s1 = model.NewIntVar(0, horizon, f"start_soak_{jid}")
        e1 = model.NewIntVar(0, horizon, f"end_soak_{jid}")
        iv1 = model.NewIntervalVar(s1, soak_dur, e1, f"iv_soak_{jid}")

        s2 = model.NewIntVar(0, horizon, f"start_plate_{jid}")
        e2 = model.NewIntVar(0, horizon, f"end_plate_{jid}")
        iv2 = model.NewIntervalVar(s2, plate_dur, e2, f"iv_plate_{jid}")

        s3 = model.NewIntVar(0, horizon, f"start_rinse_{jid}")
        e3 = model.NewIntVar(0, horizon, f"end_rinse_{jid}")
        iv3 = model.NewIntervalVar(s3, rinse_dur, e3, f"iv_rinse_{jid}")

        # 順序制約
        model.Add(s2 >= e1)
        model.Add(s3 >= e2)

        # 人が必要な作業に時間帯制限
        limit_to_working(s1)
        limit_to_working(s3)

        job_vars[jid] = {
            "PlatingType": row["PlatingType"],
            "iv_plate": iv2
        }

    # 同じPlatingTypeは同時実行不可
    for pt in jobs_df["PlatingType"].unique():
        ivs = [job_vars[jid]["iv_plate"] for jid in job_vars if job_vars[jid]["PlatingType"] == pt]
        if len(ivs) > 1:
            model.AddNoOverlap(ivs)

    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    results = []
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        for jid in jobs_df['JobID']:
            base = pd.to_datetime(start_date)
            times = {
                'JobID': jid,
                'PlatingType': job_vars[jid]['PlatingType'],
                '入槽開始': (base + pd.to_timedelta(solver.Value(model.VarFromName(f"start_soak_{jid}")), unit='m')).strftime('%Y-%m-%d %H:%M'),
                'めっき開始': (base + pd.to_timedelta(solver.Value(model.VarFromName(f"start_plate_{jid}")), unit='m')).strftime('%Y-%m-%d %H:%M'),
                'めっき終了': (base + pd.to_timedelta(solver.Value(model.VarFromName(f"end_plate_{jid}")), unit='m')).strftime('%Y-%m-%d %H:%M'),
                '出槽終了': (base + pd.to_timedelta(solver.Value(model.VarFromName(f"end_rinse_{jid}")), unit='m')).strftime('%Y-%m-%d %H:%M'),
            }
            results.append(times)
    return pd.DataFrame(results)
