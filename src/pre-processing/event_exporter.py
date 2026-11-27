"""Export combined sensor recordings and corresponding event labels."""

from pathlib import Path
from typing import Iterable

import pandas as pd

DEFAULT_EXCLUDED_EVENTS = ("sync_flip", "sync_flip_back")


def find_labels_csv(trial_id: str, data_root: str | Path = "data") -> Path:
    """Locate the *_labels.csv file for a given trial_id inside data/."""
    root = Path(data_root)
    direct = root / f"{trial_id}_labels.csv"
    if direct.is_file():
        return direct

    matches = sorted(root.rglob(f"{trial_id}_labels.csv"))
    if not matches:
        raise FileNotFoundError(
            f"Keine Label-CSV für '{trial_id}' in '{root}' gefunden."
        )
    return matches[0]


def shift_times_to_sync_flip(
    labels_df: pd.DataFrame,
    sync_label: str = "sync_flip",
) -> pd.DataFrame:
    """Shift start_s (and end_s if present) so that the first sync_flip is at t = 0 s."""
    df = labels_df.copy()
    sync_rows = df[df["label"] == sync_label]
    if sync_rows.empty:
        raise ValueError(f"Kein '{sync_label}'-Eintrag in der Label-CSV gefunden.")

    sync_start_s = float(sync_rows["start_s"].iloc[0])
    df["start_s"] = (df["start_s"] - sync_start_s).round(6)
    if "end_s" in df.columns:
        df["end_s"] = (df["end_s"] - sync_start_s).round(6)
    return df


def extract_event_labels(
    labels_df: pd.DataFrame,
    exclude_labels: Iterable[str] = DEFAULT_EXCLUDED_EVENTS,
    timezone: str = "Europe/Berlin",
    df_start_epoch_ms: float | None = None,
    align_to_sync_flip: bool = True,
) -> pd.DataFrame:
    """Filter event rows from the label DataFrame and add epoch timestamps."""
    working_df = shift_times_to_sync_flip(labels_df) if align_to_sync_flip else labels_df
    events = working_df[working_df["type"] == "event"].copy()

    if exclude_labels:
        events = events[~events["label"].isin(exclude_labels)].copy()

    if events.empty:
        cols = ["trial_id", "subject", "label", "start_s", "start_time", "epoch_ms"]
        if df_start_epoch_ms is not None:
            cols.append("relative_time_s")
        return pd.DataFrame(columns=cols)

    timestamps = pd.to_datetime(events["start_time"])
    if timestamps.dt.tz is None:
        timestamps = timestamps.dt.tz_localize(timezone)
    events["epoch_ms"] = timestamps.map(lambda t: int(round(t.timestamp() * 1000)))

    output_cols = ["trial_id", "subject", "label", "start_s", "start_time", "epoch_ms"]
    if df_start_epoch_ms is not None:
        events["relative_time_s"] = (events["epoch_ms"] - df_start_epoch_ms) / 1000.0
        output_cols.append("relative_time_s")

    available_cols = [col for col in output_cols if col in events.columns]
    return events[available_cols].reset_index(drop=True)


def save_event_data(
    sensor_df: pd.DataFrame,
    labels: pd.DataFrame | str | Path | None = None,
    trial_id: str | None = None,
    data_root: str | Path = "data",
    data_dir: str | Path = Path("data") / "event" / "data",
    label_dir: str | Path = Path("data") / "event" / "labels",
    time_col: str = "epoch_ms",
    exclude_labels: Iterable[str] = DEFAULT_EXCLUDED_EVENTS,
    timezone: str = "Europe/Berlin",
    align_to_sync_flip: bool = True,
) -> tuple[Path, Path]:
    """Save the cleaned sensor DataFrame and its filtered event labels as CSV files.

    Args:
        sensor_df: Cleaned, time-synchronized sensor DataFrame for one recording.
        labels: Label DataFrame or path to the trial's labels CSV. If omitted,
            `<trial_id>_labels.csv` is automatically searched inside `data_root`.
        trial_id: Recording ID used for filenames (and to auto-find the labels CSV).
            If omitted, read from the `trial_id` column of `labels`.
        data_root: Root data folder searched when `labels` is None (default: data).
        data_dir: Existing target folder for the full sensor CSV (default: data/event/data).
        label_dir: Existing target folder for the event label CSV (default: data/event/labels).
        time_col: Name of the epoch timestamp column in sensor_df (if present).
        exclude_labels: Event labels to drop (default: sync_flip, sync_flip_back).
        timezone: Timezone for naive start_time strings in the labels CSV.

    Returns:
        Tuple of (saved_data_path, saved_label_path).
    """
    if labels is None:
        if trial_id is None:
            raise ValueError("Entweder 'labels' oder 'trial_id' muss angegeben werden.")
        labels = find_labels_csv(trial_id, data_root=data_root)

    labels_df = pd.read_csv(labels) if isinstance(labels, (str, Path)) else labels.copy()

    if trial_id is None:
        if "trial_id" in labels_df.columns and not labels_df.empty:
            trial_id = str(labels_df["trial_id"].iloc[0])
        else:
            raise ValueError("trial_id must be provided if not present in labels.")

    df_start_epoch_ms = None
    if time_col in sensor_df.columns and not sensor_df.empty:
        df_start_epoch_ms = float(sensor_df[time_col].iloc[0])

    event_labels_df = extract_event_labels(
        labels_df,
        exclude_labels=exclude_labels,
        timezone=timezone,
        df_start_epoch_ms=df_start_epoch_ms,
        align_to_sync_flip=align_to_sync_flip,
    )

    data_dir_path = Path(data_dir)
    label_dir_path = Path(label_dir)
    if not data_dir_path.is_dir():
        raise FileNotFoundError(f"Zielordner für Sensordaten existiert nicht: {data_dir_path}")
    if not label_dir_path.is_dir():
        raise FileNotFoundError(f"Zielordner für Event-Labels existiert nicht: {label_dir_path}")

    data_path = data_dir_path / f"{trial_id}.csv"
    label_path = label_dir_path / f"{trial_id}_events.csv"

    sensor_df.to_csv(data_path, index=False)
    event_labels_df.to_csv(label_path, index=False)

    return data_path, label_path


if __name__ == "__main__":
    sample_trial_id = "20261117_P03_S03_SC01"
    sample_sensor_df = pd.read_csv(
        Path("data") / sample_trial_id / f"{sample_trial_id}_left_wrist_acc.csv"
    )

    saved_data, saved_labels = save_event_data(sample_sensor_df, trial_id=sample_trial_id)
    print(f"Sensordaten gespeichert: {saved_data}")
    print(f"Event-Labels gespeichert: {saved_labels}")
    print(pd.read_csv(saved_labels))
