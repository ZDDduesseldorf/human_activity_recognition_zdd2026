from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def plot_activity(
    label: str,
    csv_path: str | Path | None = None,
    joints: tuple[str, ...] = ("left_wrist", "right_wrist", "torso", "right_thigh"),
    show: bool = True,
):
    """Plot x/y/z acceleration for an activity label (e.g. walking or squats).

    Pass a single segment CSV or a folder containing segment CSVs. By default,
    use data/activity/<label> relative to the project root. Each segment
    gets one figure with one subplot per joint; time starts at segment start.
    Return the figures so callers can save or further customize them.
    """
    if not label or label in (".", "..") or any(char in label for char in "/\\"):
        raise ValueError("Das Label muss ein einzelner Aktivitaetsname sein.")
    path = (
        Path(csv_path)
        if csv_path is not None
        else Path(__file__).resolve().parents[2] / "data" / "activity" / label
    )
    if not path.exists():
        raise FileNotFoundError(f"Keine Daten fuer das Label '{label}' unter {path} gefunden.")
    files = sorted(path.glob("*.csv")) if path.is_dir() else [path]
    if not files:
        raise FileNotFoundError(f"Keine CSVs fuer das Label '{label}' in {path} gefunden.")
    if not joints:
        raise ValueError("Mindestens ein Gelenk muss angegeben werden.")

    figures = []
    for file in files:
        df = pd.read_csv(file)
        required = ["time_s", *(f"{joint}_acc_{axis}_g" for joint in joints for axis in "xyz")]
        missing = [column for column in required if column not in df.columns]
        if missing:
            raise ValueError(f"Fehlende Spalten in {file.name}: {', '.join(missing)}")
        if df.empty:
            raise ValueError(f"Keine Messdaten in {file.name} vorhanden.")

        time_s = df["time_s"] - df["time_s"].iloc[0]
        fig, axes = plt.subplots(len(joints), 1, figsize=(14, 3 * len(joints)), sharex=True, squeeze=False)
        for ax, joint in zip(axes[:, 0], joints):
            for axis in "xyz":
                ax.plot(time_s, df[f"{joint}_acc_{axis}_g"], label=axis, linewidth=0.8)
            ax.set_title(joint.replace("_", " "))
            ax.set_ylabel("Beschleunigung [g]")
            ax.legend(loc="upper right")
            ax.grid(True, alpha=0.3)
        axes[-1, 0].set_xlabel("Zeit seit Segmentstart [s]")
        fig.suptitle(f"{label.replace('_', ' ').title()} – {file.stem}")
        fig.tight_layout()
        figures.append(fig)

    if show:
        plt.show()
    return figures


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Beschleunigungsdaten einer Aktivitaet plotten.")
    parser.add_argument("label", nargs="?", default="walking", help="Aktivitaetslabel, z. B. walking oder squats")
    args = parser.parse_args()
    plot_activity(args.label)


