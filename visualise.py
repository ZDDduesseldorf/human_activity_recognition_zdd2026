"""Plot accelerometer and gyroscope data from imported file."""
import matplotlib.pyplot as plt
import pandas as pd
import matplotlib.dates as mdates
import importer


def plot_data(df):
    """Plot accelerometer and gyroscope data over time."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(18, 8))
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    ax1.plot(df['timestamp'], df['acc_x'], label='acc_x', linewidth=0.5)
    ax1.plot(df['timestamp'], df['acc_y'], label='acc_y', linewidth=0.5)
    ax1.plot(df['timestamp'], df['acc_z'], label='acc_z', linewidth=0.5)
    ax1.set_xlabel('Timestamp')
    ax1.set_ylabel('Accelerometer Values')
    ax1.set_title('Accelerometer Data')
    ax2.legend()
    ax2.plot(df['timestamp'], df['gyro_x'], label='gyro_x', linewidth=0.5)
    ax2.plot(df['timestamp'], df['gyro_y'], label='gyro_y', linewidth=0.5)
    ax2.plot(df['timestamp'], df['gyro_z'], label='gyro_z', linewidth=0.5)
    ax2.set_xlabel('Timestamp')
    ax2.set_ylabel('Gyroscope Values')
    ax2.set_title('Gyroscope Data')
    ax2.legend()
    for ax in (ax1, ax2):
        locator = mdates.AutoDateLocator(maxticks=35,minticks=20)
        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(locator))
    fig.tight_layout()
    plt.show()
    


def main() -> None:
    """Load the example file and plot the first 10000 samples."""
    df = importer.converter("data/6033722_0000000000.csv", "ax6")
    if df is None:
        return 
    df=df.head(10000)
    plot_data(df)


if __name__ == "__main__":
    main()