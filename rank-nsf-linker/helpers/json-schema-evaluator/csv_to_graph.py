import pandas as pd
import matplotlib.pyplot as plt
import argparse


def plot_field_occurrence(csv_file, output_image, top_n=20):
    df = pd.read_csv(csv_file)

    # Remove '%' sign and convert percentage to float
    df["percentage"] = df["percentage"].str.replace("%", "").astype(float)

    # Sort by occurrences
    df_sorted = df.sort_values(by="occurrences", ascending=False).head(top_n)

    # Plot
    plt.figure(figsize=(10, 8))
    plt.barh(df_sorted["field"], df_sorted["occurrences"], color="skyblue")
    plt.xlabel("Occurrences")
    plt.ylabel("Fields")
    plt.title(f"Top {top_n} Field Occurrences")
    plt.gca().invert_yaxis()
    plt.tight_layout()

    plt.savefig(output_image)
    print(f"[✓] Graph saved to {output_image}")


if __name__ == "__main__":
    # python3 csv_to_graph.py --csv out_stats.csv --out out_fields.png --top 30
    parser = argparse.ArgumentParser(
        description="Convert CSV field stats to bar chart."
    )
    parser.add_argument("--csv", required=True, help="Path to field_stats.csv")
    parser.add_argument(
        "--out", default="field_occurrence.png", help="Output image path"
    )
    parser.add_argument("--top", type=int, default=20, help="Top N fields to show")

    args = parser.parse_args()
    plot_field_occurrence(args.csv, args.out, args.top)
