import pandas as pd
import matplotlib.pyplot as plt



filepath1_acc = r"./data/test_measurement/MetaWear-cartesian-2026-11-13-13-30-06-59bb.csv"
metadata_filepath = r"./data/test_measurement/S02_20261113_121713_labels.csv"

df_sensor1_acc = pd.read_csv(filepath1_acc)
metadata = pd.read_csv(metadata_filepath)

zeit = (pd.to_datetime(metadata["start_time"]).dt.tz_localize("Europe/Berlin"))
metadata["epoch"] = [int(t.timestamp() * 1000) for t in zeit]

sync_tap = metadata[metadata.label == "sync_flip"]
squats = metadata[metadata.label == "squats"]

sync_tap_time_beginning = sync_tap["epoch"].iloc[0]
sync_tap_time_end = sync_tap["epoch"].iloc[-1]
squats_time = squats["epoch"].iloc[0]

print("TIMES: ", sync_tap_time_beginning, squats_time)


#breich = df_sensor1_acc[df_sensor1_acc["epoch"] <= squats_time].copy()
bereich = df_sensor1_acc.copy()

sensor_start = df_sensor1_acc["epoch"].iloc[0]
zeit_s = (bereich["epoch"] - sensor_start) / 1000

betrag = (bereich["x"]**2 + bereich["y"]**2 + bereich["z"]**2)**0.5

plt.plot(zeit_s, betrag)#df_sensor1_acc["z"])
plt.axvline(
    (sync_tap_time_beginning - sensor_start) / 1000,
   color="red",
    linestyle="--",
    label="Tap-Markierung aus Metadaten"
)
plt.axvline(
    (sync_tap_time_end - sensor_start) / 1000,
        color="red",
        linestyle="--",
        label="Tap-Markierung aus Metadaten"
)
plt.xlabel("Sekunden seit Sensorstart")
plt.ylabel("Beschleunigungsbetrag")
plt.legend()
plt.show()

# was hier noch fehlt: Ausschlag berechnen, zeeitlichen Unterschied bestimmen 
# eigentlichen Ausschlag und zeitlichen Ausschlag neutralisiere

# für  synchronization zwischen sensoren: für jeden Sensor
# auschlag finden die epoche davon und dann diese epoche auf 0 setzen indem:
# wir einfach das df cutten?
# dann um zu überprüfen ob es korrekt ist einmal das intervall zwischen
# diesem Startwert und dem Squat anfang berechnen und unter den Sensoren vergleichen


# große Tabelle mit filename, personen ID, session id, label etc. als csv oder npz
# 
