import matplotlib.pyplot as plt
import pandas as pd
import importer


def plot_accelerometer(df, ax):
    ax.plot(df['timestamp'], df['acc_x'], label='acc_x')
    ax.plot(df['timestamp'], df['acc_y'], label='acc_y')
    ax.plot(df['timestamp'], df['acc_z'], label='acc_z')
    ax.set_xlabel('Timestamp')
    ax.set_ylabel('Accelerometer Values')
    ax.set_title('Accelerometer Data')
    ax.legend()


def plot_gyroscope(df, ax):
    ax.plot(df['timestamp'], df['gyro_x'], label='gyro_x')
    ax.plot(df['timestamp'], df['gyro_y'], label='gyro_y')
    ax.plot(df['timestamp'], df['gyro_z'], label='gyro_z')
    ax.set_xlabel('Timestamp')
    ax.set_ylabel('Gyroscope Values')
    ax.set_title('Gyroscope Data')
    ax.legend()


if __name__ == "__main__":
    df = importer.converter("data/6033722_0000000000.csv", "ax6")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    plot_accelerometer(df, ax1)
    plot_gyroscope(df, ax2)

    fig.tight_layout()
    plt.show()