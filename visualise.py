import matplotlib.pyplot as plt
import pandas as pd
import importer


def plot_data(df):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    ax1.plot(df['timestamp'], df['acc_x'], label='acc_x')
    ax1.plot(df['timestamp'], df['acc_y'], label='acc_y')
    ax1.plot(df['timestamp'], df['acc_z'], label='acc_z')
    ax1.set_xlabel('Timestamp')
    ax1.set_ylabel('Accelerometer Values')
    ax1.set_title('Accelerometer Data')
    ax2.legend()
    ax2.plot(df['timestamp'], df['gyro_x'], label='gyro_x')
    ax2.plot(df['timestamp'], df['gyro_y'], label='gyro_y')
    ax2.plot(df['timestamp'], df['gyro_z'], label='gyro_z')
    ax2.set_xlabel('Timestamp')
    ax2.set_ylabel('Gyroscope Values')
    ax2.set_title('Gyroscope Data')
    ax2.legend()
    fig.tight_layout()
    plt.show()
    





if __name__ == "__main__":
    df = importer.converter("data/6033722_0000000000.csv", "ax6")
    plot_data(df)