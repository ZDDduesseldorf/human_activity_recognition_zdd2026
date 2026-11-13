import matplotlib.pyplot as plt 
import pandas as pd 


df = pd.read_csv(r"./data/test_measurement/MetaWear-cartesian-2026-11-13-13-30-06-8882.csv")
betrag = (df["x"]**2 + df["y"]**2 + df["z"]**2)**0.5
z = df["z"]
plt.plot(df["elapsed_ms"], betrag)
plt.show()
