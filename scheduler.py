import pandas as pd
from ortools.sat.python import cp_model

def generate_working_minutes(num_days=30):
    minutes = set()
    for day in range(num_days):
        base = day * 1440
        minutes.update(range(base + 510, base + 1050))  # Day shift (8:30–17:30)
        minutes.update(range(base + 900, base + 1440))  # Evening shift (15:00–24:00)
    return sorted(minutes)

def get_shift(minute):
    m = minute % 1440
    if 510 <= m < 1050:
        return "Day"
    elif 900 <= m < 1440:
        return "Evening"
    else:
        return "Off Hours"

def schedule_jobs(jobs_df, tanks_df, start_date):
    model = cp_model.CpModel()

    if "DurationHour" in jobs_df.columns:
        jobs_df["PlatingMin"] = (jobs_df["DurationHour"] * 60).astype(int)
    elif "DurationMin" in jobs_df.columns:
        jobs_df["PlatingMin"] = jobs_df["DurationMin"].astype(int)
    else:
        raise KeyError("CSV must include DurationHour or DurationMin.")

    jobs_df["SoakMin"] = jobs_df["入槽時間"].astype(int)
    jobs_df["RinseMin"] = jobs_df["出槽時間"].astype(int)

    plating_to_tank = dict(zip(tanks_df["PlatingType"], tanks_df["TankID"])) if "PlatingType" in tanks_df.columns else {"Ni": "T1", "Cr": "T2", "Zn": "T3"}

    horizon = int(jobs_df[["PlatingMin", "SoakMin", "RinseMin"]].sum().sum() * 1.5)
    working_minutes = generate_working_minutes()

    def restrict_to_working(var):
        model.AddAllowedAssignments([var], [[m] for m in working_minutes])

    job_vars = {}
    for _, row in jobs_df.iterrows():
        jid = str(row['JobID'])
        pt = row['PlatingType']
        soak_dur, plate_dur, rinse_dur = row['SoakMin'], row['PlatingMin'], row['RinseMin']

        s1 = model.NewIntVar(0, horizon, f"start_soak_{jid}")
        e1 = model.NewIntVar(0, horizon, f"end_soak_{jid}")
        iv1 = model.NewIntervalVar(s1, soak_dur, e1, f"iv_soak_{jid}")

        s2 = model.NewIntVar(0, horizon, f"start_plate_{jid}")
        e2 = model.NewIntVar(0, horizon, f"end_plate_{jid}")
        iv2 = model.NewIntervalVar(s2, plate_dur, e2, f"iv_plate_{jid}")

        s3 = model.NewIntVar(0, horizon, f"start_rinse_{jid}")
        e3 = model.NewIntVar(0, horizon, f"end_rinse_{jid}")
        iv3 = model.NewIntervalVar(s3, rinse_dur, e3, f"iv_rinse_{jid}")

        model.Add(s2 >= e1)
        model.Add(s3 >= e2)
        restrict_to_working(s1)
        restrict_to_working(s3)

        job_vars[jid] = {
            "PlatingType": pt, "TankID": plating_to_tank.get(pt, ""),
            "Soak": (s1, e1, soak_dur),
            "Plating": (s2, e2, plate_dur),
            "Rinse": (s3, e3, rinse_dur),
            "iv_plate": iv2
        }

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
            tank = job_vars[jid]["TankID"]
            pt = job_vars[jid]["PlatingType"]
            for step in ["Soak", "Plating", "Rinse"]:
                s, e, dur = job_vars[jid][step]
                start_val = solver.Value(s)
                end_val = solver.Value(e)
                results.append({
                    "JobID": jid,
                    "PlatingType": pt,
                    "TankID": tank,
                    "Step": step,
                    "Start Time": (base + pd.to_timedelta(start_val, unit='m')).strftime('%Y-%m-%d %H:%M'),
                    "End Time": (base + pd.to_timedelta(end_val, unit='m')).strftime('%Y-%m-%d %H:%M'),
                    "Duration (min)": dur,
                    "Shift": get_shift(start_val)
                })
    return pd.DataFrame(results)
