import argparse
from pathlib import Path

import pandas as pd

ROLE_COL = "Qual è la tua posizione lavorativa?"
EXPERIENCE_COL = "seniority"
RAL_COL = "Qual è la tua RAL attuale?"
CLUSTER_COL = "Fascia esperienza"


def compute_ral_stats(dataset_path: Path) -> pd.DataFrame:
    """Return min, max, mean, median of RAL per role and experience cluster."""
    df = pd.read_csv(dataset_path)

    relevant = df[[ROLE_COL, EXPERIENCE_COL, RAL_COL]].copy()
    relevant[RAL_COL] = pd.to_numeric(relevant[RAL_COL], errors="coerce")

    cluster_order = ["0-1 anni", "2-5 anni", ">5 anni"]
    seniority_to_cluster = {
        "Entry Level (0-1 years)": "0-1 anni",
        "Junior (1-2.5 years)": "2-5 anni",
        "Mid-Level (2.5-5 years)": "2-5 anni",
        "Senior (5-7 years)": ">5 anni",
        "Expert (7+ years)": ">5 anni",
    }
    relevant[CLUSTER_COL] = relevant[EXPERIENCE_COL].map(seniority_to_cluster)
    relevant[CLUSTER_COL] = pd.Categorical(
        relevant[CLUSTER_COL], categories=cluster_order, ordered=True
    )

    filtered = relevant.dropna(subset=[ROLE_COL, RAL_COL, CLUSTER_COL])
    stats = (
        filtered.groupby([ROLE_COL, CLUSTER_COL], observed=True)[RAL_COL]
        .agg(["min", "max", "mean", "median"])
        .reset_index()
        .sort_values([ROLE_COL, CLUSTER_COL])
    )
    stats[["mean", "median"]] = stats[["mean", "median"]].round(2)

    return stats


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Calcola min, max, media e mediana della RAL per ruolo e cluster di esperienza",
    )
    parser.add_argument(
        "--input",
        default="Data/df_cleaned.csv",
        help="Percorso al file CSV sorgente (default: Data/df_cleaned.csv)",
    )
    parser.add_argument(
        "--output",
        help="Percorso opzionale per salvare i risultati come CSV",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    dataset_path = Path(args.input)

    if not dataset_path.exists():
        raise FileNotFoundError(f"File non trovato: {dataset_path}")

    stats = compute_ral_stats(dataset_path)

    if args.output:
        stats.to_csv(args.output, index=False)
    else:
        print(stats.to_string(index=False))


if __name__ == "__main__":
    main()
