import tkinter as tk
from tkinter import messagebox
from tkinter.scrolledtext import ScrolledText

def calculate_lays():
    # clear previous output
    output_txt.delete("1.0", tk.END)
    lines = input_txt.get("1.0", tk.END).strip().splitlines()

    # read & validate bankroll
    try:
        bank = float(balance_entry.get())
        if bank <= 0:
            raise ValueError
    except ValueError:
        messagebox.showerror("Input Error", "Please enter a positive number for your account balance.")
        return

    candidates = []

    # parse each line of your pasted table
    for line in lines:
        if "|" not in line:
            continue
        parts = [c.strip() for c in line.split("|")]
        # need at least: name | overall_score | live_odds
        if len(parts) < 3:
            continue

        name = parts[0]
        try:
            overall_score = float(parts[1])
            live_odds     = float(parts[2])
        except ValueError:
            # probably a header or malformed row
            continue

        if live_odds <= 1:
            continue

        # derive win‐prob from your "Overall Score" %
        p_model = overall_score / 100.0

        # back‐EV & lay‐EV
        ev_back = p_model * (live_odds - 1) - (1 - p_model)
        ev_lay  = -ev_back
        if ev_lay <= 0:
            # no positive edge to lay
            continue

        # full Kelly fraction for lay
        f_full = ev_lay / (live_odds - 1)
        # 25% Kelly
        f_25   = max(0, f_full) * 0.25

        # compute monetary stake & liability
        stake      = f_25 * bank
        liability  = stake * (live_odds - 1)

        candidates.append({
            "name":      name,
            "odds":      live_odds,
            "ev_lay":    ev_lay,
            "stake":     stake,
            "liability": liability
        })

    # sort all positive‐EV lays by edge (ev_lay) descending
    candidates.sort(key=lambda c: c["ev_lay"], reverse=True)

    # build the output
    output_txt.insert(tk.END,
        f"Bankroll: £{bank:.2f}\n"
        f"Applying 25% Kelly fraction per lay, listed by best edge:\n\n"
    )

    if not candidates:
        output_txt.insert(tk.END, "No positive‑EV lay opportunities found.\n")
    else:
        for c in candidates:
            output_txt.insert(tk.END,
                f"{c['name']}\n"
                f"  Odds:        {c['odds']:.2f}\n"
                f"  Lay EV:      +{c['ev_lay']:.3f} per £1\n"
                f"  Stake:       £{c['stake']:.2f}\n"
                f"  Liability:   £{c['liability']:.2f}\n\n"
            )


# Build the GUI
root = tk.Tk()
root.title("Odds Apex – Golf Lay Calculator")

tk.Label(root, text="Paste your pipe‑delimited table here:").grid(row=0, column=0, sticky="w", padx=4, pady=4)
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
