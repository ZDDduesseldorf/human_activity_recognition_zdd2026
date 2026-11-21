"""End-to-end preprocessing pipeline: sync sensors, export events and activity segments."""

from pathlib import Path
import sys

import pandas as pd

from activity import extract_activity
from event_exporter import save_event_data, shift_times_to_sync_flip
from syncronizer import DEFAULT_JOINTS, load_trial, synchronize_trial


def process_trial(
    trial_dir: str | Path,
    output_root: str | Path = "data",
    target_hz: float = 50.0,
    joint_names: tuple[str, ...] = DEFAULT_JOINTS,
    max_duration_diff_s: float = 5.0,
    max_gap_s: float = 0.25,
) -> dict:
    """Synchronize one trial folder and export event + activity datasets.

    Creates the following structure under `output_root`:
        <output_root>/
            event/
                data/<trial_id>.csv
                labels/<trial_id>_events.csv
            activity/
                <activity_name>/<trial_id>_<activity_name>_<start>_<end>.csv
    """
    trial_path = Path(trial_dir)
    trial_id = trial_path.name
    out_root = Path(output_root)

    event_data_dir = out_root / "event" / "data"
    event_label_dir = out_root / "event" / "labels"
    activity_dir = out_root / "activity"

    event_data_dir.mkdir(parents=True, exist_ok=True)
    event_label_dir.mkdir(parents=True, exist_ok=True)
    activity_dir.mkdir(parents=True, exist_ok=True)

    # 1. Sensordaten + Labels laden und auf gemeinsames Zeitraster (ab 0.0 s am 1. sync_flip) synchronisieren
    joints, df_labels = load_trial(trial_path, joint_names=joint_names)
    df_synced = synchronize_trial(
        joints,
        df_labels,
        target_hz=target_hz,
        max_duration_diff_s=max_duration_diff_s,
        max_gap_s=max_gap_s,
    )

    # 2. Gesamtaufnahme + auf sync_flip=0s verschobene Event-Labels exportieren
    event_data_path, event_label_path = save_event_data(
        df_synced,
        labels=df_labels,
        trial_id=trial_id,
        data_dir=event_data_dir,
        label_dir=event_label_dir,
    )

    # 3. Aktivitäten anhand der auf sync_flip=0s verschobenen Labels ausschneiden und speichern
    shifted_labels = shift_times_to_sync_flip(df_labels)
    activities = shifted_labels[shifted_labels["type"] == "activity"].dropna(subset=["start_s", "end_s"])

    saved_activities = 0
    for _, row in activities.iterrows():
        seg = extract_activity(
            df_synced,
            activity=str(row["label"]),
            start_time=float(row["start_s"]),
            end_time=float(row["end_s"]),
            save_path=activity_dir,
            time_col="time_s",
            trial_id=trial_id,
        )
        if seg is not None:
            saved_activities += 1

    print(
        f"[{trial_id}] Fertig: {df_synced.shape[0]} Samples x {df_synced.shape[1]} Spalten | "
        f"Events -> {event_label_path} | {saved_activities} Aktivitäts-Segmente -> {activity_dir}"
    )

    return {
        "trial_id": trial_id,
        "shape": df_synced.shape,
        "event_data_path": event_data_path,
        "event_label_path": event_label_path,
        "activity_dir": activity_dir,
        "saved_activities": saved_activities,
    }


def find_trial_dirs(data_root: str | Path = "data") -> list[Path]:
    """Find all trial folders containing `<folder_name>_labels.csv`."""
    root = Path(data_root)
    return sorted(
        p for p in root.iterdir()
        if p.is_dir() and (p / f"{p.name}_labels.csv").is_file()
    )


def process_all_trials(
    data_root: str | Path = "data",
    output_root: str | Path = "data",
    target_hz: float = 50.0,
) -> list[dict]:
    """Run `process_trial` on every valid trial folder inside `data_root`."""
    trial_dirs = find_trial_dirs(data_root)
    if not trial_dirs:
        print(f"Keine Trial-Ordner mit '<trial_id>_labels.csv' in '{data_root}' gefunden.")
        return []

    results = []
    for trial_dir in trial_dirs:
        results.append(process_trial(trial_dir, output_root=output_root, target_hz=target_hz))
    return results


if __name__ == "__main__":
    if len(sys.argv) > 1:
        process_trial(sys.argv[1])
    else:
        process_all_trials()
