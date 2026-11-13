import pandas as pd
import matplotlib.pyplot as plt



filepath1_acc = r"./data/test_measurement/S02_acc.csv"
metadata_filepath = r"./data/test_measurement/P01_S01_20261110.csv"

df_sensor1_acc = pd.read_csv(filepath1_acc)
metadata = pd.read_csv(metadata_filepath)

zeit = (pd.to_datetime(metadata["start_time"]).dt.tz_localize("Europe/Berlin"))
metadata["epoch"] = [int(t.timestamp() * 1000) for t in zeit]

sync_tap = metadata[metadata.label == "sync_tap"]
squats = metadata[metadata.label == "squats"]

sync_tap_time = sync_tap["epoch"].iloc[0]
squats_time = squats["epoch"].iloc[0]


bereich = df_sensor1_acc[df_sensor1_acc["epoch"] <= squats_time].copy()

sensor_start = df_sensor1_acc["epoch"].iloc[0]
zeit_s = (bereich["epoch"] - sensor_start) / 1000

betrag = (bereich["x"]**2 + bereich["y"]**2 + bereich["z"]**2)**0.5

plt.plot(zeit_s, betrag)
plt.axvline(
    (sync_tap_time - sensor_start) / 1000,
    color="red",
    linestyle="--",
    label="Tap-Markierung aus Metadaten"
)
plt.xlabel("Sekunden seit Sensorstart")
plt.ylabel("Beschleunigungsbetrag")
plt.legend()
plt.show()

# was hier noch fehlt: Ausschlag berechnen, zeeitlichen Unterschied bestimmen 
# eigentlichen Ausschlag und zeitlichen Ausschlag neutralisieren



# für  synchronization zwischen sensoren: für jeden Sensor
# auschlag finden die epoche davon und dann diese epoche auf 0 setzen indem:
# wir einfach das df cutten?
# dann um zu überprüfen ob es korrekt ist einmal das intervall zwischen
# diesem Startwert und dem Squat anfang berechnen und unter den Sensoren vergleichen

