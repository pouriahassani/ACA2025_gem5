import os
import glob
import argparse
import matplotlib.pyplot as plt

def extract_stats(path):
    stats = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if len(line.split()) < 2:
                continue
            key, value = line.split()[:2]
            try:
                stats[key] = float(value)
            except ValueError:
                continue
    return stats

def main():
    parser = argparse.ArgumentParser(description="Plot gem5 stats by key.")
    parser.add_argument("stat_key", type=str, nargs="?", help="Stat key to plot (e.g. system.cpu.ipc)")
    parser.add_argument("--path_dir", type=str, default=".", help="Directory containing stats files")
    parser.add_argument("--list_keys", action="store_true", help="List available stat keys and exit")
    args = parser.parse_args()

    path_files = os.path.join(args.path_dir, "stats_*.txt")
    files = sorted(glob.glob(path_files))

    if not files:
        print(f"❌ No stats files found in: {args.path_dir}")
        return

    all_stats = []
    for fpath in files:
        stats = extract_stats(fpath)
        stats["__file__"] = os.path.basename(fpath)
        all_stats.append(stats)

    if args.list_keys:
        all_keys = sorted(set().union(*[s.keys() for s in all_stats if s]))
        print("✅ Available stat keys:")
        for k in all_keys:
            print(" ", k)
        return

    key = args.stat_key
    if not key:
        print("❌ You must specify a stat key or use --list_keys.")
        return

    values = []
    labels = []
    for s in all_stats:
        if key in s:
            values.append(s[key])
            labels.append(s["__file__"])
        else:
            print(f"⚠️ Stat key '{key}' not found in {s['__file__']}")

    if not values:
        print(f"❌ Stat key not found in any files: {key}")
        return

    plt.figure(figsize=(10,6))
    plt.bar(labels, values)
    plt.title(f"{key} across configurations")
    plt.ylabel(key)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    out_name = f"plot_{key.replace('.', '_')}.png"
    plt.savefig(out_name)
    print(f"✅ Plot saved to {out_name}")

if __name__ == "__main__":
    main()
