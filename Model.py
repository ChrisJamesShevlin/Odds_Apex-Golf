import tkinter as tk
from tkinter import messagebox
import numpy as np
import math

# Parametric logistic calibration (re-anchored: Score=20→0.64%, Score=60→10%)
p1, s1 = 0.0064, 20
p2, s2 = 0.10,   60
L1 = math.log(p1/(1-p1))
L2 = math.log(p2/(1-p2))
a  = (L2 - L1) / (s2 - s1)
b  = s1 - L1/a

# Controls for probability floor and odds cap
P_FLOOR = 0.02       # never below 2%
MAX_FAIR  = 50.0      # cap raw fair odds at 50×


def calculate_score():
    try:
        # Basic metrics
        name            = name_entry.get().strip()
        xwins           = float(xwins_entry.get())
        total_shots     = float(total_shots_entry.get())
        putt            = float(putt_entry.get())
        T2G             = float(t2g_entry.get())
        sg_true         = float(sg_true_entry.get())
        sg_expected     = float(sg_expected_entry.get())
        course_fit      = float(course_fit_entry.get())
        ranking         = float(ranking_entry.get())
        live_odds       = float(live_odds_entry.get())
        leaderboard_pos = float(leaderboard_pos_entry.get())
        shots_behind    = float(shots_behind_entry.get())
        finishes        = [float(e.get()) for e in finish_entries]
        sg_off_tee      = float(sg_off_tee_entry.get())
        sg_approach     = float(sg_approach_entry.get())
        sg_putting      = float(sg_putting_entry.get())
        scrambling      = float(scrambling_entry.get())
    except ValueError:
        messagebox.showerror("Input Error", "Please enter valid numbers in every field.")
        return

    # Derived metrics
    sg_diff   = sg_true - sg_expected
    avg_last5 = sum(finishes) / len(finishes)
    pressure  = sg_diff * 15

    # Heuristic score (0–100)
    score = (
        50
        + xwins
        + total_shots * 0.5
        + putt * 0.5
        + T2G * 0.5
        + pressure
        + course_fit * 20
        - ranking * 0.5
        - leaderboard_pos * 0.3
        - shots_behind * 0.2
        - avg_last5 * 0.5
        + sg_off_tee  * 0.5
        + sg_approach * 0.5
        + sg_putting  * 0.5
        - (100 - scrambling) * 0.2
    )
    score = float(np.clip(score, 0, 100))

    # Calibrated win probability via logistic mapping
    p_model = 1.0 / (1.0 + math.exp(-a * (score - b)))
    p_model = max(p_model, P_FLOOR)
    p_implied = 1.0 / live_odds
    edge      = p_model - p_implied

    # Fair odds and blend: cap raw fair at MAX_FAIR
    fair_model = min(1.0 / p_model, MAX_FAIR)
    fair_blend = 0.7 * fair_model + 0.3 * live_odds

    # EV for a £1 back bet
    ev_back = p_model * (live_odds - 1) - (1 - p_model)

    # Format strings
    score_s = f"{score:.2f}%"
    pmod_s  = f"{p_model*100:.2f}%"
    pimp_s  = f"{p_implied*100:.2f}%"
    edge_s  = f"{edge*100:+.2f}%"
    fair_s  = f"{fair_blend:.2f}"
    ev_s    = f"{ev_back:+.3f}"

    out = (
        f"{name}  |  Score: {score_s:<7} "
        f"Model%: {pmod_s:<7}  Mkt%: {pimp_s:<7}  "
        f"Edge: {edge_s:<7}  FairOdds: {fair_s:<5}  "
        f"LiveOdds: {live_odds:.2f}  EV: {ev_s}"
    )

    print(out)
    result_label.config(text=out)


# ------------------
# Build the GUI
# ------------------
root = tk.Tk()
root.title("Odds Apex - Golf Model")

# Input fields
fields = [
    "Golfer Name", "Expected Wins (xwins)", "Total Shots Gained",
    "Putt", "T2G", "SG True", "SG Expected",
    "Course Fit", "Current Ranking", "Live Odds",
    "Leaderboard Position", "Shots Behind Leader"
]
entries = {}
for i, lbl in enumerate(fields):
    tk.Label(root, text=lbl).grid(row=i, column=0, sticky="e", padx=4, pady=2)
    e = tk.Entry(root)
    e.grid(row=i, column=1, padx=4, pady=2)
    entries[lbl] = e

(name_entry, xwins_entry, total_shots_entry, putt_entry,
 t2g_entry, sg_true_entry, sg_expected_entry,
 course_fit_entry, ranking_entry, live_odds_entry,
 leaderboard_pos_entry, shots_behind_entry) = [entries[l] for l in fields]

# Last 5 finishes
last5 = len(fields)
tk.Label(root, text="Last 5 Finishes").grid(row=last5, column=0, sticky="e", padx=4, pady=2)
finish_frame = tk.Frame(root)
finish_frame.grid(row=last5, column=1, pady=2)
finish_entries = []
for j in range(5):
    e = tk.Entry(finish_frame, width=4)
    e.grid(row=0, column=j, padx=2)
    finish_entries.append(e)

# In-play SG stats
sg_stats = ["SG Off Tee", "SG Approach", "SG Putting", "Scrambling %"]
for k, lbl in enumerate(sg_stats, start=last5+1):
    tk.Label(root, text=lbl).grid(row=k, column=0, sticky="e", padx=4, pady=2)
    e = tk.Entry(root)
    e.grid(row=k, column=1, padx=4, pady=2)
    if lbl == "SG Off Tee":    sg_off_tee_entry = e
    if lbl == "SG Approach":   sg_approach_entry = e
    if lbl == "SG Putting":    sg_putting_entry = e
    if lbl == "Scrambling %":  scrambling_entry = e

# Calculate + Result
bottom = last5 + 1 + len(sg_stats)
calc_btn = tk.Button(root, text="Calculate Score & EV", command=calculate_score)
calc_btn.grid(row=bottom, column=0, columnspan=2, pady=10)

result_label = tk.Label(root, text="", font=("Helvetica", 10, "bold"), anchor="w", justify="left")
result_label.grid(row=bottom+1, column=0, columnspan=2, sticky="we", pady=4)

root.mainloop()
