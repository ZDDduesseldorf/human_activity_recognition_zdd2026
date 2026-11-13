import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import importer


def real_duration(df):
    labels = df[df["label"] == "sync_flip"]
    start = labels.iloc[0]["start_s"]
    end = labels.iloc[-1]["start_s"]
    return end - start


def detect_flip(
    df,
    window=50,
    lie_samples=250,
    time_col="epoch",
    min_distance=300,
    n_flips=4,
    return_debug=False,
):
    df = df.reset_index(drop=True)
    z = df["z"]

    # 1. Fenster über z -> Sequenz aus 1 (liegt +1g), -1 (liegt -1g), 0 (Bewegung/sonst)
    roll_mean = z.rolling(window, center=True).mean()
    roll_std = z.rolling(window, center=True).std()

    seq = np.where(
        (np.abs(roll_mean - 1.0) < 0.05) & (roll_std < 0.03),
        1,
        np.where((np.abs(roll_mean + 1.0) < 0.05) & (roll_std < 0.03), -1, 0),
    )

    # 2. Stufen-Kernel [1, ..., 1, -1, ..., -1] über die Sequenz schieben
    kernel = np.concatenate([np.ones(lie_samples), -np.ones(lie_samples)])
    scores = np.abs(np.correlate(seq, kernel, mode="same"))

    # 3. Die n_flips höchsten Peaks mit Mindestabstand finden
    masked_scores = scores.copy()
    peak_indices = []
    for _ in range(n_flips):
        idx = int(np.argmax(masked_scores))
        if masked_scores[idx] <= 0:
            break
        peak_indices.append(idx)
        masked_scores[max(0, idx - min_distance) : min(len(scores), idx + min_distance + 1)] = -1

    peak_indices = sorted(peak_indices)
    events = [float(df.loc[idx, time_col]) for idx in peak_indices]

    print("Gefundene Zeitpunkte:", events, "Scores:", [float(scores[i]) for i in peak_indices])

    if return_debug:
        return events, seq, scores, peak_indices
    return events


def fake_duration(df):
    flips = detect_flip(df)
    print(flips)
    if len(flips) < 2:
        return None
    return (flips[-1] - flips[0]) / 1000


def compare(dfr, dff):
    return real_duration(dfr), fake_duration(dff)


def plot_flips(df_acc, df_labels, window=50, lie_samples=250, min_distance=300, n_flips=4):
    df_acc = df_acc.reset_index(drop=True)
    t_start = df_acc["epoch"].iloc[0]
    t_s = (df_acc["epoch"] - t_start) / 1000.0

    events, seq, scores, peak_indices = detect_flip(
        df_acc,
        window=window,
        lie_samples=lie_samples,
        time_col="epoch",
        min_distance=min_distance,
        n_flips=n_flips,
        return_debug=True,
    )

    # Gespeicherte sync_flip-Labels über start_time / end_time in Sekunden seit Sensorstart umrechnen
    flips_label = df_labels[df_labels["label"] == "sync_flip"].copy()
    start_epochs = pd.Series(
        [t.timestamp() * 1000 for t in pd.to_datetime(flips_label["start_time"]).dt.tz_localize("Europe/Berlin")]
    )
    end_epochs = pd.Series(
        [t.timestamp() * 1000 for t in pd.to_datetime(flips_label["end_time"]).dt.tz_localize("Europe/Berlin")]
    )
    label_starts_s = (start_epochs - t_start) / 1000.0
    label_ends_s = (end_epochs - t_start) / 1000.0

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), sharex=True)

    # Plot 1: z-Achse + erkannte Flips + gespeicherte Labels
    ax1.plot(t_s, df_acc["z"], label="z (g)", color="steelblue", linewidth=0.8)
    for i, idx in enumerate(peak_indices):
        ax1.axvline(
            t_s.iloc[idx],
            color="red",
            linestyle="--",
            linewidth=1.5,
            label="Erkannter Flip" if i == 0 else None,
        )
    for i, (ls, le) in enumerate(zip(label_starts_s, label_ends_s)):
        ax1.axvspan(
            ls,
            le,
            color="green",
            alpha=0.25,
            label="Gespeicherter sync_flip (Labels)" if i == 0 else None,
        )
    ax1.set_ylabel("z-Beschleunigung [g]")
    ax1.set_title("Flip-Erkennung vs. gespeicherte Labels")
    ax1.legend(loc="upper right")
    ax1.grid(True, alpha=0.3)

    # Plot 2: Sequenz (1 / 0 / -1) + Kernel-Score
    ax2.plot(t_s, seq, label="Sequenz (1 / 0 / -1)", color="darkorange", linewidth=0.9)
    ax2_twin = ax2.twinx()
    ax2_twin.plot(t_s, scores, label="Kernel-Score", color="purple", alpha=0.6, linewidth=0.9)
    for idx in peak_indices:
        ax2_twin.plot(t_s.iloc[idx], scores[idx], "ro")

    ax2.set_xlabel("Zeit seit Sensorstart [s]")
    ax2.set_ylabel("Sequenz")
    ax2_twin.set_ylabel("Kernel-Score")
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    temp_r = pd.read_csv(r"C:\Users\rafae\Downloads\S03_20261113_134625.csv")
    temp_f = pd.read_csv(r"C:\Users\rafae\Downloads\20261113_02_03_SENSOR02_left_hand_acc.csv")
    print("Vergleich (real, fake):", compare(temp_r, temp_f))
    plot_flips(temp_f, temp_r)
