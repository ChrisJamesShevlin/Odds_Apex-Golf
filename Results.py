import tkinter as tk
from tkinter import messagebox
from tkinter.scrolledtext import ScrolledText
import re

def calculate_lays():
    output_txt.delete("1.0", tk.END)
    lines = input_txt.get("1.0", tk.END).strip().splitlines()

    # Read and validate bankroll
    try:
        bank = float(balance_entry.get())
        if bank <= 0:
            raise ValueError
    except ValueError:
        messagebox.showerror("Input Error", "Please enter a positive number for your account balance.")
        return

    cap_liability = 0.10 * bank
    used_liab = 0.0
    candidates = []

    # Parse each pasted line
    for line in lines:
        if "|" not in line:
            continue
        name, rest = line.split("|", 1)
        name = name.strip()
        rest = rest.strip()

        m_model = re.search(r"Model%:\s*([0-9]+(?:\.[0-9]+)?)%", rest)
        m_odds  = re.search(r"LiveOdds:\s*([0-9]+(?:\.[0-9]+)?)", rest)
        if not (m_model and m_odds):
            continue

        p_model   = float(m_model.group(1)) / 100.0
        live_odds = float(m_odds.group(1))
        if live_odds <= 1:
            continue

        # back‐EV & lay‐EV
        ev_back = p_model * (live_odds - 1) - (1 - p_model)
        ev_lay  = -ev_back
        if ev_lay <= 0:
            continue

        # full‐Kelly fraction for lay
        f_full = ev_lay / (live_odds - 1)
        # 25% Kelly
        f_25   = max(0, f_full) * 0.25
        stake  = f_25 * bank
        liability = stake * (live_odds - 1)

        candidates.append({
            "name": name,
            "ev_lay": ev_lay,
            "odds": live_odds,
            "stake": stake,
            "liability": liability
        })

    # sort by best lay‐EV
    candidates.sort(key=lambda c: c["ev_lay"], reverse=True)

    recs = []
    total_ev = 0.0
    for c in candidates:
        if used_liab >= cap_liability:
            break

        liab = c["liability"]
        st   = c["stake"]
        # scale down if over cap
        if used_liab + liab > cap_liability:
            remaining = cap_liability - used_liab
            if remaining <= 0:
                break
            liab = remaining
            st   = liab / (c["odds"] - 1)

        recs.append({
            "name":      c["name"],
            "odds":      c["odds"],
            "ev_lay":    c["ev_lay"],
            "stake":     st,
            "liability": liab
        })
        used_liab += liab
        total_ev   += st * c["ev_lay"]  # stake × EV per £1

    # Build output
    output_txt.insert(tk.END,
        f"Bankroll: £{bank:.2f}\n"
        f"Liability cap (10%): £{cap_liability:.2f}\n\n"
    )

    if not recs:
        output_txt.insert(tk.END, "No positive‑EV lays found.\n")
    else:
        output_txt.insert(tk.END, "Recommended lays (25% Kelly):\n\n")
        for r in recs:
            output_txt.insert(tk.END,
                f"{r['name']}\n"
                f"  Odds:        {r['odds']:.2f}\n"
                f"  Lay EV:      +{r['ev_lay']:.3f} per £1\n"
                f"  Stake:       £{r['stake']:.2f}\n"
                f"  Liability:   £{r['liability']:.2f}\n\n"
            )
        output_txt.insert(tk.END,
            f"Total liability used: £{used_liab:.2f} "
            f"({used_liab/bank*100:.2f}% of bank)\n"
            f"Total EV (sum):       £{total_ev:.2f}\n"
        )


# Build the GUI
root = tk.Tk()
root.title("Odds Apex - Golf Results")

tk.Label(root, text="Paste your model output below:").grid(row=0, column=0, sticky="w", padx=4, pady=4)
input_txt = ScrolledText(root, width=80, height=8)
input_txt.grid(row=1, column=0, padx=4)

tk.Label(root, text="Account balance (£):").grid(row=2, column=0, sticky="w", padx=4, pady=(10,2))
balance_entry = tk.Entry(root)
balance_entry.grid(row=3, column=0, sticky="w", padx=4)

tk.Button(root, text="Calculate Lays", command=calculate_lays)\
  .grid(row=4, column=0, sticky="w", padx=4, pady=8)

tk.Label(root, text="Recommendations:").grid(row=5, column=0, sticky="w", padx=4, pady=(10,2))
output_txt = ScrolledText(root, width=80, height=12)
output_txt.grid(row=6, column=0, padx=4, pady=(0,8))

root.mainloop()
