import os
from typing import Literal
import pandas as pd
from openmovement.process import OmConvert


def convert_to_and_save_csv(filepath: str) -> str:
    base = os.path.splitext(filepath)[0]
    csv_path = base + ".csv"
    options = {"csv_file": csv_path}

    om = OmConvert()
    om.execute(filepath, options)
    print("Saved to your working directory.")

    return csv_path


def create_df(filepath: str, columns: list[str], has_header: bool = False) -> pd.DataFrame | None:
    file_end = os.path.splitext(filepath)[1].lower()

    if file_end in (".wav", ".cwa"):
        filepath = convert_to_and_save_csv(filepath)
    elif file_end != ".csv":
        print("File cannot be converted. Consider using a .csv, .cwa or .wav file.")
        return None

    header_arg = 0 if has_header else None
    return pd.read_csv(filepath, header=header_arg, names=columns)


def converter(filepath: str, device: Literal["ax6", "mbient"] = "ax6") -> pd.DataFrame | None:
    columns_ax6 = ["timestamp", "acc_x", "acc_y", "acc_z", "gyro_x", "gyro_y", "gyro_z"]
    columns_mbient = ["epoch", "ms", "acc_x", "acc_y", "acc_z", "gyro_x", "gyro_y", "gyro_z"]

    if device == "ax6":
        df = create_df(filepath, columns_ax6, has_header=False)
        if df is not None:
            df[["date", "timestamp"]] = df["timestamp"].str.split(" ", expand=True)
            df = df[["date", *columns_ax6]]
            return df

    elif device == "mbient":
        df = create_df(filepath, columns_mbient, has_header=True)  # ggf. False, falls kein Header
        if df is not None:
            df["epoch"] = df["epoch"].astype(str).str.replace("Z", "")
            df[["date", "timestamp"]] = df["epoch"].str.split("T", expand=True)
            df = df[["date", "timestamp", *columns_mbient[1:]]]  # ohne "epoch"
            return df
    else:
        print("Please enter a valid device ('ax6' or 'mbient')")
        return None


if __name__ == "__main__":
    filepath = os.path.join("data", "6033722_0000000000.csv")
    df = converter(filepath, "ax6")