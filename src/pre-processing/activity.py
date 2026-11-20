import pandas as pd
from pathlib import Path
import os

feature_df_path = r"..\human_activity_recognition_zdd2026\data\test_measurement\S02_20261113_121713_labels.csv"
feature_df = pd.read_csv(
    feature_df_path,
    delimiter = ","
)

s2_acc_data_path = r"..\human_activity_recognition_zdd2026\data\test_measurement\S02_acc.csv"
s2_acc_data = pd.read_csv(
    s2_acc_data_path,
    delimiter= ","
)
activity_label = [
    "walking"
]

print(s2_acc_data.head())


def extract_activity(
    df: pd.DataFrame,
    activity: str,
    start_time: float,
    end_time: float,
    save_path: str,
    time_col: str = "epoch",
):
    '''Extract activities from acclerometer data and save it in the activity folder''' 
    segment = df[(df[time_col] >= start_time) & (df[time_col] <= end_time)]

    if segment.empty:
        print(f"No Data found between {start_time} and {end_time}")
        return None

    out_dir = os.path.join(save_path, activity)
    os.makedirs(out_dir, exist_ok=True)

    out_file = os.path.join(out_dir, f"{activity}_{start_time:.0f}_{end_time:.0f}.csv")
    segment.to_csv(out_file, index=False)

    print(f"{len(segment)} Samples saved in: {out_file}")
    return segment    
