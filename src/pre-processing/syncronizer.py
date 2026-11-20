from pathlib import Path
import warnings

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import importer


DEFAULT_JOINTS = ("left_wrist", "right_wrist", "torso", "right_thigh")
ACC_COLS = ("acc_x_g", "acc_y_g", "acc_z_g")
GYRO_COLS = ("gyro_x_dps", "gyro_y_dps", "gyro_z_dps")


def real_duration(df):
    labels = df[df["label"] == "sync_flip"]
    start = labels.iloc[0]["start_s"]
    end = labels.iloc[-1]["start_s"]
    return end - start


def detect_flip(
    df,
    window=50,
    lie_samples=250,
    time_col="epoch_ms",
    min_distance=300,
    n_flips=2,
    return_debug=False,
):
    df = df.reset_index(drop=True)
    z = df["acc_z_g"]

    # 1. Fenster über z -> Sequenz aus 1 (liegt +1g), -1 (liegt -1g), 0 (Bewegung/sonst)
    roll_mean = z.rolling(window, center=True).mean()
    roll_std = z.rolling(window, center=True).std()

    seq = np.where(
        (np.abs(roll_mean - 1.0) < 0.05) & (roll_std < 0.03),
        1,
        np.where((np.abs(roll_mean + 1.0) < 0.05) & (roll_std < 0.03), -1, 0),
    )

    # 2. Stufen-Kernel [1, ..., 1, -1, ..., -1] über die Sequenz schieben
    # Ohne abs(): nur Wechsel von +1 (z positiv) auf -1 (z negativ) ergeben positive Scores
    kernel = np.concatenate([np.ones(lie_samples), -np.ones(lie_samples)])
    scores = np.correlate(seq, kernel, mode="same")

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


def plot_flips(df_acc, df_labels, window=50, lie_samples=250, min_distance=300, n_flips=2):
    df_acc = df_acc.reset_index(drop=True)
    t_start = df_acc["epoch_ms"].iloc[0]
    t_s = (df_acc["epoch_ms"] - t_start) / 1000.0

    events, seq, scores, peak_indices = detect_flip(
        df_acc,
        window=window,
        lie_samples=lie_samples,
        time_col="epoch_ms",
        min_distance=min_distance,
        n_flips=n_flips,
        return_debug=True,
    )

    # Gespeicherte sync_flip-Labels über start_time in Sekunden seit Sensorstart umrechnen
    flips_label = df_labels[df_labels["label"] == "sync_flip"].copy()
    start_epochs = pd.Series(
        [t.timestamp() * 1000 for t in pd.to_datetime(flips_label["start_time"]).dt.tz_localize("Europe/Berlin")]
    )
    label_starts_s = (start_epochs - t_start) / 1000.0

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), sharex=True)

    # Plot 1: z-Achse + erkannte Flips + gespeicherte Labels
    ax1.plot(t_s, df_acc["acc_z_g"], label="z (g)", color="steelblue", linewidth=0.8)
    for i, idx in enumerate(peak_indices):
        ax1.axvline(
            t_s.iloc[idx],
            color="red",
            linestyle="--",
            linewidth=1.5,
            label="Erkannter Flip" if i == 0 else None,
        )
    for i, ls in enumerate(label_starts_s):
        ax1.axvline(
            ls,
            color="green",
            linestyle="-",
            linewidth=1.5,
            alpha=0.8,
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


def _align_and_interpolate(
    df: pd.DataFrame,
    sensor_t1: float,
    sensor_t2: float,
    duration_s: float,
    target_t: np.ndarray,
    value_cols: tuple[str, ...],
    time_col: str = "epoch_ms",
    max_gap_s: float = 0.25,
) -> dict[str, np.ndarray]:
    """Mappt Sensor-Zeitstempel linear auf [0, duration_s] und interpoliert auf target_t."""
    clean = df[[time_col, *value_cols]].dropna(subset=[time_col]).sort_values(time_col)
    clean = clean.drop_duplicates(subset=time_col)

    t_sensor = clean[time_col].to_numpy(dtype=float)
    t_aligned = (t_sensor - sensor_t1) / (sensor_t2 - sensor_t1) * duration_s

    # Lücken größer als max_gap_s im Zielraster maskieren (keine Interpolation über Aussetzer)
    gap_mask = np.zeros(len(target_t), dtype=bool)
    if max_gap_s is not None and len(t_aligned) > 1:
        gap_starts = np.where(np.diff(t_aligned) > max_gap_s)[0]
        for idx in gap_starts:
            gap_mask |= (target_t > t_aligned[idx]) & (target_t < t_aligned[idx + 1])

    out: dict[str, np.ndarray] = {}
    for col in value_cols:
        vals = np.interp(target_t, t_aligned, clean[col].to_numpy(dtype=float), left=np.nan, right=np.nan)
        vals[gap_mask] = np.nan
        out[col] = vals
    return out


def synchronize_trial(
    joints: dict[str, tuple[pd.DataFrame | None, pd.DataFrame | None]],
    df_labels: pd.DataFrame,
    target_hz: float = 50.0,
    max_duration_diff_s: float = 5.0,
    max_gap_s: float = 0.25,
    time_col: str = "epoch_ms",
    acc_cols: tuple[str, ...] = ACC_COLS,
    gyro_cols: tuple[str, ...] = GYRO_COLS,
) -> pd.DataFrame:
    """Synchronisiert alle Gelenke (Acc + Gyro) zwischen den beiden sync_flips auf ein gemeinsames Zeitraster.

    - Startet bei time_s = 0.0 s (erster sync_flip) bis zur echten Dauer zwischen erstem und letztem sync_flip.
    - Pro Gelenk werden die Flips auf Acc erkannt und für Acc & Gyro dieses Gelenks verwendet.
    - Bei fehlenden/abgebrochenen Sensoren oder zu großer Dauer-Abweichung wird eine Warnung ausgegeben
      und die Spalten des Gelenks werden mit NaN gefüllt, damit das Spalten-Schema konstant bleibt.
    """
    flips_label = df_labels[df_labels["label"] == "sync_flip"]
    if len(flips_label) < 2:
        raise ValueError("df_labels muss mindestens zwei 'sync_flip'-Einträge enthalten.")

    duration_s = float(flips_label.iloc[-1]["start_s"]) - float(flips_label.iloc[0]["start_s"])
    if duration_s <= 0:
        raise ValueError(f"Ungültige Label-Dauer zwischen den sync_flips: {duration_s}s")

    n_samples = int(np.floor(duration_s * target_hz)) + 1
    target_t = np.arange(n_samples, dtype=float) / target_hz

    result: dict[str, np.ndarray] = {"time_s": target_t}
    nan_col = lambda: np.full(len(target_t), np.nan, dtype=float)

    for joint_name, (df_acc, df_gyro) in joints.items():
        if df_acc is None or df_acc.empty:
            warnings.warn(f"[{joint_name}] Keine Acc-Daten vorhanden. Spalten werden mit NaN gefüllt.")
            for col in (*acc_cols, *gyro_cols):
                result[f"{joint_name}_{col}"] = nan_col()
            continue

        events = detect_flip(df_acc, time_col=time_col)
        if len(events) < 2:
            warnings.warn(
                f"[{joint_name}] Weniger als 2 sync_flips erkannt ({len(events)}). Spalten werden mit NaN gefüllt."
            )
            for col in (*acc_cols, *gyro_cols):
                result[f"{joint_name}_{col}"] = nan_col()
            continue

        sensor_t1, sensor_t2 = events[0], events[-1]
        sensor_dur_s = (sensor_t2 - sensor_t1) / 1000.0
        dur_diff = abs(sensor_dur_s - duration_s)

        if dur_diff > max_duration_diff_s:
            warnings.warn(
                f"[{joint_name}] Dauer-Abweichung zu groß: Sensor={sensor_dur_s:.3f}s vs. "
                f"Labels={duration_s:.3f}s (Diff={dur_diff:.3f}s > {max_duration_diff_s}s). "
                f"Spalten werden mit NaN gefüllt."
            )
            for col in (*acc_cols, *gyro_cols):
                result[f"{joint_name}_{col}"] = nan_col()
            continue

        acc_interp = _align_and_interpolate(
            df_acc, sensor_t1, sensor_t2, duration_s, target_t, acc_cols, time_col=time_col, max_gap_s=max_gap_s
        )
        for col, vals in acc_interp.items():
            result[f"{joint_name}_{col}"] = vals

        if df_gyro is None or df_gyro.empty:
            warnings.warn(f"[{joint_name}] Keine Gyro-Daten vorhanden. Gyro-Spalten werden mit NaN gefüllt.")
            for col in gyro_cols:
                result[f"{joint_name}_{col}"] = nan_col()
        else:
            gyro_interp = _align_and_interpolate(
                df_gyro, sensor_t1, sensor_t2, duration_s, target_t, gyro_cols, time_col=time_col, max_gap_s=max_gap_s
            )
            for col, vals in gyro_interp.items():
                result[f"{joint_name}_{col}"] = vals

    return pd.DataFrame(result)


def load_trial(
    trial_dir: str | Path,
    joint_names: tuple[str, ...] = DEFAULT_JOINTS,
) -> tuple[dict[str, tuple[pd.DataFrame | None, pd.DataFrame | None]], pd.DataFrame]:
    """Lädt Labels sowie Acc/Gyro-CSVs aller Gelenke aus einem Trial-Ordner."""
    trial_path = Path(trial_dir)
    trial_id = trial_path.name
    df_labels = pd.read_csv(trial_path / f"{trial_id}_labels.csv")

    joints: dict[str, tuple[pd.DataFrame | None, pd.DataFrame | None]] = {}
    for joint in joint_names:
        acc_path = trial_path / f"{trial_id}_{joint}_acc.csv"
        gyro_path = trial_path / f"{trial_id}_{joint}_gyro.csv"
        df_acc = pd.read_csv(acc_path) if acc_path.exists() else None
        df_gyro = pd.read_csv(gyro_path) if gyro_path.exists() else None
        joints[joint] = (df_acc, df_gyro)

    return joints, df_labels


if __name__ == "__main__":
    joints, df_labels = load_trial(r"data\20261117_P03_S03_SC01")
    df_synced = synchronize_trial(joints, df_labels, target_hz=50.0)
    print("Synchronisiertes DataFrame:", df_synced.shape)
    print(df_synced.head())
    print("\nNaN-Anteil pro Spalte:")
    print(df_synced.isna().mean().round(4))
