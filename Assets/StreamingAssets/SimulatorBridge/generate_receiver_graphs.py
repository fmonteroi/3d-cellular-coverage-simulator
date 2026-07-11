"""Generates PNG result graphs from receiver CSV files exported by Unity."""

import argparse
import csv
import os

import matplotlib

# Allows Matplotlib to create images without opening a window
matplotlib.use("Agg")

import matplotlib.pyplot as plt


def read_csv(csv_path):
    """Reads the receiver samples stored by Unity."""
    data = {"time": [],"distance": [],"prx": [],"snr": []}

    with open(csv_path, newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)

        for row in reader:
            data["time"].append(float(row["timeSeconds"]))
            data["distance"].append(float(row["distanceMeters"]))
            data["prx"].append(float(row["prxDbm"]))
            data["snr"].append(float(row["snrDb"]))

    return data


def save_prx_distance_graph(data, receiver_name, output_directory):
    """Generates the received power versus distance graph."""
    output_path = os.path.join(output_directory,receiver_name + "_prx_distance.png",)

    plt.figure(figsize=(10, 6))

    plt.scatter(data["distance"], data["prx"], s=2,color="royalblue")

    plt.title(receiver_name + " - Received Power vs Distance")
    plt.xlabel("Distance to transmitter (m)")
    plt.ylabel("Received power (dBm)")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()


def save_snr_distance_graph(data, receiver_name, output_directory):
    """Generates the SNR versus distance graph."""
    output_path = os.path.join(output_directory, receiver_name + "_snr_distance.png")

    plt.figure(figsize=(10, 6))

    plt.scatter(data["distance"],data["snr"],s=2,color="seagreen")

    plt.title(receiver_name + " - SNR vs Distance")
    plt.xlabel("Distance to transmitter (m)")
    plt.ylabel("SNR (dB)")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()


def calculate_coverage_percentage(data, threshold):
    """Calculates the percentage of measured time above the threshold."""
    if len(data["time"]) < 2:
        return 0.0

    covered_time = 0.0
    total_time = 0.0

    for i in range(len(data["time"]) - 1):
        interval = data["time"][i + 1] - data["time"][i]

        if interval <= 0.0:
            continue

        total_time += interval

        if data["snr"][i] >= threshold:
            covered_time += interval

    if total_time <= 0.0:
        return 0.0

    return covered_time / total_time * 100.0


def save_snr_time_graph(data, receiver_name, excellent_threshold, good_threshold, poor_threshold, output_directory):
    """Generates the SNR versus time graph and shows coverage."""
    
    output_path = os.path.join(output_directory, receiver_name + "_snr_time.png")

    coverage = calculate_coverage_percentage(data, poor_threshold)

    plt.figure(figsize=(10, 6))

    plt.plot(data["time"],data["snr"],color="royalblue",linewidth=1.5,label="SNR")

    plt.axhline(y=excellent_threshold,color="green",linestyle="--",linewidth=1.5,label="Excellent / Good boundary")
    plt.axhline(y=good_threshold,color="gold",linestyle="--",linewidth=1.5,label="Good / Fair boundary")
    plt.axhline(y=poor_threshold,color="red",linestyle="--",linewidth=1.5,label="Fair / Poor & coverage boundary")

    plt.text(
        0.02,
        0.95,
        "Coverage: {:.2f}%".format(coverage),
        transform=plt.gca().transAxes,
        verticalalignment="top",
        bbox={
            "facecolor": "white",
            "alpha": 0.8,
            "edgecolor": "gray",
        }
    )

    plt.title(receiver_name + " - SNR vs Time")
    plt.xlabel("Time (s)")
    plt.ylabel("SNR (dB)")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()


def main():
    """Parses command line arguments and generates the selected graphs."""
    parser = argparse.ArgumentParser(description="Generate mobile receiver graphs.")

    parser.add_argument("--csv", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--receiver", required=True)
    
    parser.add_argument("--excellent-threshold",type=float,required=True)
    parser.add_argument("--good-threshold",type=float,required=True)
    parser.add_argument("--poor-threshold",type=float,required=True)

    parser.add_argument("--prx-distance",action="store_true")
    parser.add_argument("--snr-distance",action="store_true")
    parser.add_argument("--snr-time",action="store_true")

    args = parser.parse_args()

    if not os.path.isfile(args.csv):
        raise FileNotFoundError("CSV file not found: " + args.csv)

    os.makedirs(args.output, exist_ok=True)

    data = read_csv(args.csv)

    if len(data["time"]) == 0:
        raise ValueError("The CSV file does not contain receiver samples.")

    if args.prx_distance:
        save_prx_distance_graph(data,args.receiver,args.output)

    if args.snr_distance:
        save_snr_distance_graph(data,args.receiver, args.output)

    if args.snr_time:
        save_snr_time_graph(data, args.receiver, args.excellent_threshold, args.good_threshold, args.poor_threshold, args.output)


if __name__ == "__main__":
    main()
