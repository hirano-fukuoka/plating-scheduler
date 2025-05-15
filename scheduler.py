import pandas as pd
from ortools.sat.python import cp_model

def generate_working_minutes(num_days=30):
    minutes = set()
    for day in range(num_days):
        base = day * 1440
        minutes.update(range(base + 510, base + 1050))  # 8:30–17:30
        minutes.update(range(base + 900, base + 1440))  # 15:00–24:00
    return sorted(list(minutes))

def schedule_jobs(jobs_df, tanks_df, start_date):
    model = cp_model.CpModel()

    # 対応：DurationHour or DurationMin
    if "DurationHour" in jobs_df.columns:
        jobs_df["PlatingMin"] = (jobs_df["DurationHour"] * 60).astype(int)
    elif "DurationMin" in jobs_df.columns:
        jobs_df["PlatingMin"] = jobs_df["DurationMin"].astype(int)
    else:
        raise KeyError("CSVに DurationHour または DurationMin の列が必要です。")

    jobs_df["SoakMin"] = jobs_df["入槽時間"].astype(int)
    jobs_df["RinseMin"] = jobs_df["出槽時間"].astype(int)

    horizon = int(jobs_df[["PlatingMin", "SoakMin", "RinseMin"]].sum().sum() * 1.5)
    working_minutes = generate_working_minutes()

    def restrict_to_working(var):
        model.AddAllowedAssignments([var], [[m] for m in working_minutes])

    job_vars = {}
    for _, row in jobs_df.iterrows():
        jid = str(row['JobID'])
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

        # 人が必要な作業は勤務帯内に制限
        restrict_to_working(s1)
        restrict_to_working(s3)

        job_vars[jid] = {
            "PlatingType": row["PlatingType"],
            "s_soak": s1, "s_plate": s2,
            "e_plate": e2, "e_rinse": e3,
            "iv_plate": iv2
        }

    # 同じPlatingTypeのめっき工程は同時不可（仮ルール）
    for pt in jobs_df["PlatingType"].unique():
        ivs = [job_vars[j]["iv_plate"] for j in job_vars if job_vars[j]["PlatingType"] == pt]
        if len(ivs) > 1:
            model.AddNoOverlap(ivs)

    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    results = []
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        base = pd.to_datetime(start_date)
        for jid in job_vars:
            s_soak = solver.Value(job_vars[jid]["s_soak"])
            s_plate = solver.Value(job_vars[jid]["s_plate"])
            e_plate = solver.Value(job_vars[jid]["e_plate"])
            e_rinse = solver.Value(job_vars[jid]["e_rinse"])

            results.append({
                "JobID": jid,
                "PlatingType": job_vars[jid]["PlatingType"],
                "Soak Start": (base + pd.to_timedelta(s_soak, unit="m")).strftime('%Y-%m-%d %H:%M'),
                "Plating Start": (base + pd.to_timedelta(s_plate, unit="m")).strftime('%Y-%m-%d %H:%M'),
                "Plating End": (base + pd.to_timedelta(e_plate, unit="m")).strftime('%Y-%m-%d %H:%M'),
                "Rinse End": (base + pd.to_timedelta(e_rinse, unit="m")).strftime('%Y-%m-%d %H:%M'),
            })


    return pd.DataFrame(results)
