import pandas as pd
import numpy as np 
import importer

def real_duration(df):
    labels = df[df["label"] == "sync_tap"]
    start = labels.iloc[0]["start_s"]
    end = labels.iloc[-1]["start_s"]
    return end - start

def detect_claps(df):
    df["magnitude"] = np.sqrt(df["acc_x"] ** 2 + df["acc_y"] ** 2 + df["acc_z"] ** 2)
    treshhold = 8
    df["is_peak"] = df["magnitude"] > treshhold
    print(df[df["is_peak"]==True])



#print(real_duration(pd.read_csv(r"data\S01_test_20261030_121144_activityTracker(in).csv")))
detect_claps(importer.converter(r"data\6033722_0000000000.csv", "ax6"))