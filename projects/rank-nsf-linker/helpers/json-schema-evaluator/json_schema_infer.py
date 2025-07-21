import argparse
import json
from pathlib import Path
from collections import defaultdict
from genson import SchemaBuilder


def infer_schema_and_stats(json_dir, schema_out, stats_out):
    builder = SchemaBuilder()
    field_counts = defaultdict(int)
    total_files = 0
    json_files = list(Path(json_dir).rglob("*.json"))

    if not json_files:
        print(f"[!] No JSON files found in: {json_dir}")
        return

    for file in json_files:
        try:
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)
                builder.add_object(data)
                total_files += 1

                if isinstance(data, dict):
                    for key in data.keys():
                        field_counts[key] += 1
        except Exception as e:
            print(f"[!] Skipping {file.name}: {e}")

    # Write schema
    with open(schema_out, "w", encoding="utf-8") as f:
        json.dump(json.loads(builder.to_json()), f, indent=2)
    print(f"[✓] Schema saved to {schema_out}")

    # Write stats
    with open(stats_out, "w", encoding="utf-8") as f:
        f.write("field,occurrences,percentage\n")
        for field, count in sorted(field_counts.items(), key=lambda x: -x[1]):
            percent = round((count / total_files) * 100, 2)
            f.write(f"{field},{count},{percent}%\n")
    print(f"[✓] Field occurrence stats saved to {stats_out}")
    print(f"[✓] Processed {total_files} JSON files.")


if __name__ == "__main__":
    # python3 json_schema_infer.py --dir /Users/saif.islam/code/open-concept-lab/rank-nsf-linker/data/nsfdata/2025/ --schema-out out_schema.json --stats-out out_stats.csv
    parser = argparse.ArgumentParser(
        description="Infer JSON schema and field stats from a directory of JSON files."
    )
    parser.add_argument("--dir", required=True, help="Directory containing JSON files")
    parser.add_argument(
        "--schema-out",
        default="schema.json",
        help="Output file path for the inferred schema",
    )
    parser.add_argument(
        "--stats-out",
        default="field_stats.csv",
        help="Output CSV for field occurrence statistics",
    )

    args = parser.parse_args()
    infer_schema_and_stats(args.dir, args.schema_out, args.stats_out)
