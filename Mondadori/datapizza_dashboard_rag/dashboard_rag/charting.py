from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from .catalog import DatasetEntry


@dataclass
class ChartSpec:
    title: str
    caption: str
    figure: go.Figure


def build_kpis(entry: DatasetEntry, analysis_df: pd.DataFrame) -> List[Tuple[str, str]]:
    if entry.kind == "sankey":
        return [
            ("Flusso totale", f"{int(analysis_df['value'].sum()):,}".replace(",", ".")),
            ("Nodi sorgente", str(analysis_df["source"].nunique())),
            ("Nodi target", str(analysis_df["target"].nunique())),
        ]

    if entry.kind == "scatter":
        return [
            ("Revenue totale", f"{int(analysis_df['revenue_eur'].sum()):,} EUR".replace(",", ".")),
            ("CPM medio", f"{analysis_df['cpm_medio_eur'].mean():.2f}"),
            ("Fill rate medio", f"{analysis_df['fill_rate_pct'].mean():.1f}%"),
        ]

    if entry.kind == "bar_chart_race":
        latest = analysis_df.loc[analysis_df["mese_dt"] == analysis_df["mese_dt"].max()]
        leader = latest.sort_values("revenue_cumulativa_eur", ascending=False).iloc[0]
        return [
            ("Ultimo periodo", str(latest["mese"].iloc[0])),
            ("Leader", str(leader["testata"])),
            ("Revenue leader", f"{int(leader['revenue_cumulativa_eur']):,} EUR".replace(",", ".")),
        ]

    if entry.kind == "slope":
        best_delta = analysis_df.sort_values("delta_vs_previous", ascending=False).iloc[0]
        return [
            ("Testate", str(analysis_df["testata"].nunique())),
            ("Periodi", str(analysis_df["trimestre"].nunique())),
            ("Best delta", f"{best_delta['testata']} ({int(best_delta['delta_vs_previous']):,} EUR)".replace(",", ".")),
        ]

    return [
        ("Righe", str(len(analysis_df))),
        ("Colonne", str(len(analysis_df.columns))),
        ("Numeriche", str(len(analysis_df.select_dtypes(include="number").columns))),
    ]


def build_insights(entry: DatasetEntry, analysis_df: pd.DataFrame) -> List[str]:
    if entry.kind == "sankey":
        top_edge = analysis_df.sort_values("value", ascending=False).iloc[0]
        top_target = analysis_df.groupby("target", as_index=False)["value"].sum().sort_values("value", ascending=False).iloc[0]
        return [
            f"Il flusso più rilevante è `{top_edge['source']} -> {top_edge['target']}` con valore {int(top_edge['value'])}.",
            f"Il nodo target più alimentato è `{top_target['target']}` con totale {int(top_target['value'])}.",
        ]

    if entry.kind == "scatter":
        top = analysis_df.sort_values("revenue_eur", ascending=False).iloc[0]
        revenue_by_month = analysis_df.groupby("mese", as_index=False)["revenue_eur"].sum().sort_values("revenue_eur", ascending=False).iloc[0]
        return [
            f"La combinazione più redditizia è `{top['testata']}` in `{top['mese']}` con {int(top['revenue_eur'])} EUR.",
            f"Il mese con il fatturato aggregato più alto è `{revenue_by_month['mese']}`.",
        ]

    if entry.kind == "bar_chart_race":
        latest = analysis_df.loc[analysis_df["mese_dt"] == analysis_df["mese_dt"].max()].sort_values(
            "revenue_cumulativa_eur", ascending=False
        )
        leader = latest.iloc[0]
        follower = latest.iloc[1]
        return [
            f"Nell'ultimo mese guida `{leader['testata']}` con {int(leader['revenue_cumulativa_eur'])} EUR cumulati.",
            f"Il distacco sul secondo `{follower['testata']}` è di {int(leader['revenue_cumulativa_eur'] - follower['revenue_cumulativa_eur'])} EUR.",
        ]

    if entry.kind == "slope":
        deltas = analysis_df.groupby("testata", as_index=False)["delta_vs_previous"].sum().sort_values("delta_vs_previous", ascending=False)
        best = deltas.iloc[0]
        worst = deltas.iloc[-1]
        return [
            f"La crescita migliore appartiene a `{best['testata']}` con delta totale {int(best['delta_vs_previous'])} EUR.",
            f"La crescita più debole appartiene a `{worst['testata']}` con delta totale {int(worst['delta_vs_previous'])} EUR.",
        ]

    return [
        "Il dataset non corrisponde a uno schema predefinito, quindi la dashboard usa grafici generici.",
        "La chat RAG resta disponibile anche per CSV generici.",
    ]


def build_charts(entry: DatasetEntry, analysis_df: pd.DataFrame) -> List[ChartSpec]:
    if entry.kind == "sankey":
        labels = list(dict.fromkeys(list(analysis_df["source"]) + list(analysis_df["target"])))
        label_to_index = {label: index for index, label in enumerate(labels)}
        sankey = go.Figure(
            go.Sankey(
                node={"label": labels, "pad": 18, "thickness": 16},
                link={
                    "source": analysis_df["source"].map(label_to_index),
                    "target": analysis_df["target"].map(label_to_index),
                    "value": analysis_df["value"],
                },
            )
        )
        sankey.update_layout(margin=dict(l=10, r=10, t=40, b=10), height=520)

        totals = analysis_df.groupby("target", as_index=False)["value"].sum().sort_values("value", ascending=False)
        bars = px.bar(totals, x="target", y="value", color="target")
        bars.update_layout(showlegend=False, xaxis_title="Target", yaxis_title="Valore")

        return [
            ChartSpec("Sankey dei flussi", "Rappresentazione diretta delle relazioni tra nodi.", sankey),
            ChartSpec("Peso per target", "Somma dei flussi in ingresso per nodo target.", bars),
        ]

    if entry.kind == "scatter":
        scatter = px.scatter(
            analysis_df,
            x="cpm_medio_eur",
            y="fill_rate_pct",
            size="revenue_eur",
            color="testata",
            hover_name="testata",
            hover_data=["mese"],
        )
        scatter.update_layout(xaxis_title="CPM Medio (€)", yaxis_title="Fill Rate (%)")

        trend = analysis_df.groupby("mese_dt", as_index=False)["revenue_eur"].sum()
        line = px.line(trend, x="mese_dt", y="revenue_eur", markers=True)
        line.update_layout(xaxis_title="Mese", yaxis_title="Revenue (€)")

        return [
            ChartSpec("Scatter performance", "CPM vs fill rate, dimensione bolla proporzionale alla revenue.", scatter),
            ChartSpec("Trend revenue mensile", "Somma revenue aggregata per mese.", line),
        ]

    if entry.kind == "bar_chart_race":
        line = px.line(
            analysis_df,
            x="mese_dt",
            y="revenue_cumulativa_eur",
            color="testata",
            markers=True,
        )
        line.update_layout(xaxis_title="Mese", yaxis_title="Revenue cumulativa (€)")

        latest = analysis_df.loc[analysis_df["mese_dt"] == analysis_df["mese_dt"].max()].sort_values(
            "revenue_cumulativa_eur", ascending=False
        )
        bars = px.bar(latest, x="testata", y="revenue_cumulativa_eur", color="testata")
        bars.update_layout(showlegend=False, xaxis_title="Testata", yaxis_title="Revenue cumulativa (€)")

        return [
            ChartSpec("Andamento cumulativo", "Serie temporale per testata lungo i mesi disponibili.", line),
            ChartSpec("Ultimo snapshot", "Confronto tra testate nell'ultimo mese disponibile.", bars),
        ]

    if entry.kind == "slope":
        grouped = px.bar(analysis_df, x="testata", y="revenue_eur", color="trimestre", barmode="group")
        grouped.update_layout(xaxis_title="Testata", yaxis_title="Revenue (€)")

        delta = analysis_df.groupby("testata", as_index=False)["delta_vs_previous"].sum().sort_values("delta_vs_previous", ascending=False)
        delta_chart = px.bar(delta, x="testata", y="delta_vs_previous", color="delta_vs_previous", color_continuous_scale="RdYlGn")
        delta_chart.update_layout(xaxis_title="Testata", yaxis_title="Delta vs periodo precedente (€)")

        return [
            ChartSpec("Confronto per trimestre", "Barre affiancate per leggere il confronto tra periodi.", grouped),
            ChartSpec("Delta tra periodi", "Crescita o calo della revenue per testata.", delta_chart),
        ]

    numeric_columns = list(analysis_df.select_dtypes(include="number").columns)
    categorical_columns = [column for column in analysis_df.columns if column not in numeric_columns]
    charts: List[ChartSpec] = []

    if numeric_columns:
        histogram = px.histogram(analysis_df, x=numeric_columns[0])
        charts.append(ChartSpec("Distribuzione numerica", f"Istogramma della colonna `{numeric_columns[0]}`.", histogram))

    if numeric_columns and categorical_columns:
        summary = analysis_df.groupby(categorical_columns[0], as_index=False)[numeric_columns[0]].sum().sort_values(
            numeric_columns[0], ascending=False
        ).head(10)
        bar = px.bar(summary, x=categorical_columns[0], y=numeric_columns[0], color=categorical_columns[0])
        charts.append(ChartSpec("Top categorie", "Aggregazione sulle prime categorie disponibili.", bar))

    return charts

