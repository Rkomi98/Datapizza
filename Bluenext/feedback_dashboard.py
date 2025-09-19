#!/usr/bin/env python3
"""Generate a before/after dashboard on AI adoption survey results."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

FAMILIARITY_COL = "Quanto sei familiare con le terminologie di AI, GenAI, e Machine Learning?"
FREQUENCY_COL = "Con quale frequenza usi strumenti AI?"
FREQUENCY_SCALE = {
    "ho provato qualche volta, ma non li uso": 1,
    "almeno una volta a settimana": 2,
    "almeno una volta al giorno": 3,
}
TOOL_COLUMNS_PRE = {
    "ChatGPT": "ChatGPT",
    "Gemini": "Gemini",
    "Copilot Chat": "Copilot Chat",
    "Copilot dentro Office": "Copilot dentro Office",
    "Copilot dentro Visual Studio": "Copilot dentro Visual Studio",
}
TOOL_COLUMNS_POST = {
    "ChatGPT": "Quali strumenti AI hai usato?.ChatGPT",
    "Gemini": "Quali strumenti AI hai usato?.Gemini",
    "Copilot Chat": "Quali strumenti AI hai usato?.Copilot Chat",
    "Copilot dentro Office": "Quali strumenti AI hai usato?.Copilot dentro Office",
    "Copilot dentro Visual Studio": "Quali strumenti AI hai usato?.Copilot dentro Visual Studio",
}
TOOL_NAMES = list(TOOL_COLUMNS_PRE.keys())
USAGE_SCALE = {
    "mai usato": 0,
    "uso sporadico": 1,
    "uso frequente": 2,
}
FREQUENCY_ORDERED = {
    "Ho provato qualche volta, ma non li uso": 1,
    "Almeno una volta a settimana": 2,
    "Almeno una volta al giorno": 3,
}
LIKERT_SCALE = {
    "Per niente": 1,
    "Voglio pensarci meglio": 2,
    "Abbastanza": 3,
    "Del tutto": 4,
}
ATTITUDE_SCALE = {
    "sono un po' preoccupato/a e vorrei più informazioni": 1,
    "sono neutrale, dipenderà da come verranno implementati": 2,
    "sono curioso/a ma ho alcune riserve": 3,
    "sono entusiasta e non vedo l'ora di utilizzarli": 4,
}
ATTITUDE_COL = "Dopo il corso, quale affermazione descrive meglio il tuo atteggiamento verso l'introduzione di strumenti AI in azienda?"
POST_METRIC_COLUMNS = {
    "Applicazione strumenti nel lavoro": "Per ciascun aspetto seguente, indica il tuo livello di accordo (1 = Per niente, 4 = Moltissimo).Quanto ti senti in grado di applicare gli strumenti/metodi nel lavoro quotidiano?",
    "Chiarezza argomenti": "Per ciascun aspetto seguente, indica il tuo livello di accordo (1 = Per niente, 4 = Moltissimo).Hai trovato chiari gli argomenti trattati?",
    "Attività pratiche utili": "Per ciascun aspetto seguente, indica il tuo livello di accordo (1 = Per niente, 4 = Moltissimo).Le attività pratiche ti hanno aiutato a comprendere i concetti?",
    "Coinvolgimento durante le sessioni": "Per ciascun aspetto seguente, indica il tuo livello di accordo (1 = Per niente, 4 = Moltissimo).Quanto ti sei sentito coinvolto durante le sessioni?",
    "Collaborazione tra colleghi": "Per ciascun aspetto seguente, indica il tuo livello di accordo (1 = Per niente, 4 = Moltissimo).Il percorso ha favorito la collaborazione con i colleghi?",
    "Qualità risultati migliorata": "Quanto sei d'accordo con le seguenti affermazioni riguardo l’impatto dell’AI sul tuo lavoro (1 = Per niente, 4 = Moltissimo):.La qualità/accuratezza dei risultati con l'AI è migliorata dopo il corso.",
}
SATISFACTION_COL = "Soddisfazione complessiva rispetto al percorso formativo"


@dataclass
class PostOverview:
    """Aggregate insights computed on the post-course dataset only."""

    attitude_distribution: pd.DataFrame
    metric_summary: pd.DataFrame
    satisfaction_mean: float
    satisfaction_distribution: pd.DataFrame


@dataclass
class PreparedData:
    """Holds cleaned datasets and the merged comparison table."""

    merged: pd.DataFrame
    familiarity_delta: pd.DataFrame
    frequency_delta: pd.DataFrame
    tool_delta: pd.DataFrame
    post_overview: PostOverview
    scale_summary: pd.DataFrame


def normalise_name(series: pd.Series) -> pd.Series:
    """Create a merge-friendly key from any name-like column."""
    return (
        series.fillna("")
        .astype(str)
        .str.strip()
        .str.replace(r"\s+", " ", regex=True)
        .str.lower()
    )


def extract_display_name(row: pd.Series) -> str:
    """Prefer the post-course name, otherwise fall back to pre-course."""
    for candidate in ("display_name_post", "display_name_pre"):
        value = row.get(candidate)
        if isinstance(value, str) and value.strip():
            return value
    return ""


def pick_name_column(df: pd.DataFrame) -> pd.Series:
    """Pick the most informative name column available."""
    name_candidates = [
        c for c in df.columns if "nome e cognome" in c.lower()
    ]
    if name_candidates:
        return df[name_candidates[0]]
    if "Nome" in df.columns:
        return df["Nome"]
    raise KeyError("Nessuna colonna trovata per Nome e Cognome")


def extract_numeric_prefix(series: pd.Series) -> pd.Series:
    """Extract numeric prefix from Likert-style answers like '4 - Moltissimo'."""
    return pd.to_numeric(
        series.astype(str).str.extract(r"(\d+)", expand=False), errors="coerce"
    )


def compute_post_overview(post_df: pd.DataFrame) -> PostOverview:
    """Aggregate post-course responses for high-level dashboard sections."""
    if ATTITUDE_COL in post_df.columns:
        attitude_counts = (
            post_df[ATTITUDE_COL]
            .fillna("")
            .astype(str)
            .str.strip()
            .replace("", pd.NA)
            .dropna()
            .value_counts()
            .rename_axis("attitude")
            .reset_index(name="count")
        )
        total = attitude_counts["count"].sum()
        if total:
            attitude_counts["percentage"] = attitude_counts["count"] / total * 100
    else:
        attitude_counts = pd.DataFrame(columns=["attitude", "count", "percentage"])

    metric_records: list[dict[str, object]] = []
    for label, column in POST_METRIC_COLUMNS.items():
        if column not in post_df.columns:
            continue
        numeric = extract_numeric_prefix(post_df[column])
        if numeric.dropna().empty:
            continue
        metric_records.append(
            {
                "metric": label,
                "mean": numeric.mean(),
                "median": numeric.median(),
                "n": int(numeric.dropna().shape[0]),
            }
        )
    metric_summary = pd.DataFrame(metric_records)

    satisfaction_series = post_df.get(SATISFACTION_COL)
    if satisfaction_series is not None:
        satisfaction_numeric = pd.to_numeric(satisfaction_series, errors="coerce")
        satisfaction_mean = float(satisfaction_numeric.mean()) if not satisfaction_numeric.dropna().empty else float("nan")
        satisfaction_distribution = (
            satisfaction_numeric.dropna().value_counts().sort_index().rename_axis("score").reset_index(name="count")
        )
        total_s = satisfaction_distribution["count"].sum()
        if total_s:
            satisfaction_distribution["percentage"] = satisfaction_distribution["count"] / total_s * 100
    else:
        satisfaction_mean = float("nan")
        satisfaction_distribution = pd.DataFrame(columns=["score", "count", "percentage"])

    return PostOverview(
        attitude_distribution=attitude_counts,
        metric_summary=metric_summary,
        satisfaction_mean=satisfaction_mean,
        satisfaction_distribution=satisfaction_distribution,
    )


def compute_scale_summary(pre_raw: pd.DataFrame, post_raw: pd.DataFrame) -> pd.DataFrame:
    """Collect min/max scale information for the key survey questions."""

    records: list[dict[str, object]] = []

    def record(
        dataset: str,
        column_label: str,
        labels: pd.Series,
        *,
        numeric: pd.Series | None = None,
        mapping: dict[str, int] | None = None,
        case_insensitive: bool = False,
    ) -> None:
        clean_labels = labels.dropna()
        if clean_labels.empty:
            return

        numeric_series: pd.Series
        if numeric is not None:
            numeric_series = numeric.loc[clean_labels.index]
        elif mapping is not None:
            normalised = (
                clean_labels.astype(str)
                .str.strip()
            )
            if case_insensitive:
                normalised = normalised.str.lower()
            numeric_series = normalised.map(mapping)
        else:
            numeric_series = pd.to_numeric(clean_labels, errors="coerce")

        numeric_series = numeric_series.dropna()
        if numeric_series.empty:
            return

        min_idx = numeric_series.idxmin()
        max_idx = numeric_series.idxmax()
        records.append(
            {
                "dataset": dataset,
                "column": column_label,
                "min_score": numeric_series.loc[min_idx],
                "min_label": clean_labels.loc[min_idx],
                "max_score": numeric_series.loc[max_idx],
                "max_label": clean_labels.loc[max_idx],
                "n": int(clean_labels.shape[0]),
            }
        )

    # Familiarità e frequenza
    record(
        "pre",
        "Familiarità AI",
        pre_raw[FAMILIARITY_COL],
    )
    record(
        "post",
        "Familiarità AI",
        post_raw[FAMILIARITY_COL],
    )
    record(
        "pre",
        "Frequenza uso AI",
        pre_raw[FREQUENCY_COL],
        mapping=FREQUENCY_ORDERED,
    )
    record(
        "post",
        "Frequenza uso AI",
        post_raw[FREQUENCY_COL],
        mapping=FREQUENCY_ORDERED,
    )

    # Atteggiamento
    pre_att_col = "Quale affermazione descrive meglio il tuo atteggiamento verso l'introduzione di strumenti AI in azienda?"
    post_att_col = ATTITUDE_COL
    if pre_att_col in pre_raw.columns:
        record(
            "pre",
            "Atteggiamento verso introduzione AI",
            pre_raw[pre_att_col],
            mapping=ATTITUDE_SCALE,
            case_insensitive=True,
        )
    if post_att_col in post_raw.columns:
        record(
            "post",
            "Atteggiamento verso introduzione AI",
            post_raw[post_att_col],
            mapping=ATTITUDE_SCALE,
            case_insensitive=True,
        )

    # Impatto pre
    pre_impact_columns = [
        "L'AI può aiutarmi a velocizzare e semplificare il mio lavoro",
        "L'AI può ridurre lo stress lavorativo automatizzando compiti noiosi o ripetitivi",
        "L'AI avrà un impatto significativo sul mio lavoro",
        "L'AI avrà un impatto significativo sulla società",
        "C'è il rischio di \"perdere capacità\" se le affidiamo all'AI",
    ]
    for col in pre_impact_columns:
        if col in pre_raw.columns:
            record("pre", col, pre_raw[col], mapping=LIKERT_SCALE)

    # Impatto post (Likert testuale)
    post_impact_columns = {
        "Impatto sul lavoro": "Quanto sei d'accordo con le seguenti affermazioni?.L'AI avrà un impatto significativo sul mio lavoro",
        "Impatto sulla società": "Quanto sei d'accordo con le seguenti affermazioni?.L'AI avrà un impatto significativo sulla società",
        "Rischio perdita capacità": "Quanto sei d'accordo con le seguenti affermazioni?.C'è il rischio di \"perdere capacità\" se le affidiamo all'AI",
    }
    for label, col in post_impact_columns.items():
        if col in post_raw.columns:
            record("post", label, post_raw[col], mapping=LIKERT_SCALE)

    # Metriche post (1-4 encoded as "n - label")
    for label, col in POST_METRIC_COLUMNS.items():
        if col not in post_raw.columns:
            continue
        labels = post_raw[col]
        numeric = extract_numeric_prefix(labels)
        record("post", label, labels, numeric=numeric)

    additional_post_metrics = {
        "Attività più rapide": "Quanto sei d'accordo con le seguenti affermazioni riguardo l’impatto dell’AI sul tuo lavoro (1 = Per niente, 4 = Moltissimo):.Completo le mie attività più rapidamente grazie all’AI.",
        "Qualità migliorata": "Quanto sei d'accordo con le seguenti affermazioni riguardo l’impatto dell’AI sul tuo lavoro (1 = Per niente, 4 = Moltissimo):.La qualità/accuratezza dei risultati con l'AI è migliorata dopo il corso.",
        "Idee creative": "Quanto sei d'accordo con le seguenti affermazioni riguardo l’impatto dell’AI sul tuo lavoro (1 = Per niente, 4 = Moltissimo):.L’AI mi aiuta a generare idee creative.",
        "Decisioni più rapide": "Quanto sei d'accordo con le seguenti affermazioni riguardo l’impatto dell’AI sul tuo lavoro (1 = Per niente, 4 = Moltissimo):.L’AI mi supporta nel prendere decisioni in modo più rapido.",
        "Carico mentale ridotto": "Quanto sei d'accordo con le seguenti affermazioni riguardo l’impatto dell’AI sul tuo lavoro (1 = Per niente, 4 = Moltissimo):.L’AI ha alleggerito il mio carico mentale nelle attività quotidiane.",
        "Uso più fluido": "Quanto sei d'accordo con le seguenti affermazioni riguardo l’impatto dell’AI sul tuo lavoro (1 = Per niente, 4 = Moltissimo):.Dopo il corso, l’utilizzo dell’AI nei miei task individuali è più fluido.",
        "Competenze pratiche": "Quanto sei d'accordo con le seguenti affermazioni riguardo l’impatto dell’AI sul tuo lavoro (1 = Per niente, 4 = Moltissimo):.Il corso mi ha fornito competenze pratiche per usare efficacemente l’AI.",
        "Problem solving": "Quanto sei d'accordo con le seguenti affermazioni riguardo l’impatto dell’AI sul tuo lavoro (1 = Per niente, 4 = Moltissimo):.Mi sento più capace di risolvere problemi complessi grazie agli strumenti ",
        "Collaborazione efficace": "Quanto sei d'accordo con le seguenti affermazioni riguardo l’impatto dell’AI sul tuo lavoro (1 = Per niente, 4 = Moltissimo):.L’AI mi aiuta a collaborare in modo più efficace con i colleghi.",
        "Esplorazione nuove applicazioni": "Quanto sei d'accordo con le seguenti affermazioni riguardo l’impatto dell’AI sul tuo lavoro (1 = Per niente, 4 = Moltissimo):.Il corso mi ha motivato ad esplorare nuove applicazioni dell’AI nel mio ru",
    }
    for label, col in additional_post_metrics.items():
        if col not in post_raw.columns:
            continue
        labels = post_raw[col]
        numeric = extract_numeric_prefix(labels)
        record("post", label, labels, numeric=numeric)

    if SATISFACTION_COL in post_raw.columns:
        record("post", "Soddisfazione complessiva", post_raw[SATISFACTION_COL])

    summary = pd.DataFrame.from_records(records)
    if not summary.empty:
        summary = summary.sort_values(["column", "dataset"])
    return summary


def clean_dataset(
    df: pd.DataFrame, suffix: str, tool_columns: dict[str, str]
) -> pd.DataFrame:
    """Standardise key fields needed for the merge."""
    cleaned = df.copy()
    name_series = pick_name_column(cleaned)
    familiarity_raw = cleaned[FAMILIARITY_COL]
    frequency_raw = cleaned[FREQUENCY_COL]
    cleaned[f"name_key_{suffix}"] = normalise_name(name_series)
    cleaned = cleaned[cleaned[f"name_key_{suffix}"].ne("")].copy()
    cleaned[f"display_name_{suffix}"] = (
        name_series.fillna("")
        .astype(str)
        .str.strip()
        .str.replace(r"\s+", " ", regex=True)
    )
    cleaned = cleaned.drop_duplicates(subset=f"name_key_{suffix}", keep="last")
    cleaned[f"{FAMILIARITY_COL}_{suffix}"] = pd.to_numeric(
        familiarity_raw, errors="coerce"
    )
    cleaned[f"{FREQUENCY_COL}_{suffix}_score"] = (
        frequency_raw
        .fillna("")
        .astype(str)
        .str.strip()
        .str.lower()
        .map(FREQUENCY_SCALE)
    )
    cleaned[f"{FREQUENCY_COL}_{suffix}_label"] = (
        frequency_raw
        .fillna("")
        .astype(str)
        .str.strip()
    )
    for tool, column in tool_columns.items():
        if column not in cleaned.columns:
            continue
        raw = cleaned[column]
        cleaned[f"{tool}_{suffix}_label"] = (
            raw.fillna("")
            .astype(str)
            .str.strip()
        )
        cleaned[f"{tool}_{suffix}_score"] = (
            raw.fillna("")
            .astype(str)
            .str.strip()
            .str.lower()
            .map(USAGE_SCALE)
        )
    drop_candidates = [FAMILIARITY_COL, FREQUENCY_COL, *tool_columns.values()]
    cleaned = cleaned.drop(columns=[c for c in drop_candidates if c in cleaned.columns])
    return cleaned


def prepare_data(pre_path: Path, post_path: Path) -> PreparedData:
    pre_raw = pd.read_csv(pre_path, encoding="utf-8-sig")
    post_raw = pd.read_csv(post_path, encoding="utf-8-sig")

    post_overview = compute_post_overview(post_raw)
    scale_summary = compute_scale_summary(pre_raw, post_raw)

    pre = clean_dataset(pre_raw, "pre", TOOL_COLUMNS_PRE)
    post = clean_dataset(post_raw, "post", TOOL_COLUMNS_POST)

    merged = (
        pre.merge(
            post,
            left_on="name_key_pre",
            right_on="name_key_post",
            how="outer",
            suffixes=("_pre", "_post"),
        )
        .copy()
    )

    merged["display_name"] = merged.apply(extract_display_name, axis=1)

    merged["familiarity_pre"] = merged[f"{FAMILIARITY_COL}_pre"]
    merged["familiarity_post"] = merged[f"{FAMILIARITY_COL}_post"]
    merged["familiarity_delta"] = (
        merged["familiarity_post"] - merged["familiarity_pre"]
    )

    merged["frequency_label_pre"] = merged[f"{FREQUENCY_COL}_pre_label"]
    merged["frequency_label_post"] = merged[f"{FREQUENCY_COL}_post_label"]
    merged["frequency_score_pre"] = merged[f"{FREQUENCY_COL}_pre_score"]
    merged["frequency_score_post"] = merged[f"{FREQUENCY_COL}_post_score"]
    merged["frequency_delta"] = (
        merged["frequency_score_post"] - merged["frequency_score_pre"]
    )

    for tool in TOOL_NAMES:
        merged[f"{tool}_delta"] = (
            merged.get(f"{tool}_post_score") - merged.get(f"{tool}_pre_score")
        )

    familiarity_delta = merged.dropna(
        subset=["display_name", "familiarity_pre", "familiarity_post"]
    )[["display_name", "familiarity_pre", "familiarity_post", "familiarity_delta"]]

    frequency_delta = merged.dropna(
        subset=["display_name", "frequency_score_pre", "frequency_score_post"]
    )[
        [
            "display_name",
            "frequency_label_pre",
            "frequency_label_post",
            "frequency_delta",
        ]
    ]

    tool_records: list[dict[str, object]] = []
    for _, row in merged.iterrows():
        name = row.get("display_name", "")
        if not isinstance(name, str) or not name.strip():
            continue
        for tool in TOOL_NAMES:
            pre_score = row.get(f"{tool}_pre_score")
            post_score = row.get(f"{tool}_post_score")
            if pd.isna(pre_score) or pd.isna(post_score):
                continue
            tool_records.append(
                {
                    "display_name": name,
                    "tool": tool,
                    "usage_pre": row.get(f"{tool}_pre_label"),
                    "usage_post": row.get(f"{tool}_post_label"),
                    "delta": post_score - pre_score,
                }
            )

    tool_delta = pd.DataFrame(tool_records)

    return PreparedData(
        merged,
        familiarity_delta,
        frequency_delta,
        tool_delta,
        post_overview,
        scale_summary,
    )


def build_familiarity_chart(data: pd.DataFrame) -> go.Figure:
    fig = px.bar(
        data.sort_values("familiarity_delta", ascending=False),
        x="display_name",
        y="familiarity_delta",
        text="familiarity_delta",
        color="familiarity_delta",
        color_continuous_scale=["#d62728", "#ffeda0", "#2ca02c"],
        title="Delta di familiarit\u00e0 con AI (post - pre)",
        labels={"display_name": "Partecipante", "familiarity_delta": "Delta"},
    )
    fig.add_hline(y=0, line_dash="dash", line_color="#444")
    fig.update_traces(texttemplate="%{text:.1f}", textposition="outside")
    fig.update_layout(
        xaxis_tickangle=-35,
        coloraxis_showscale=False,
        margin=dict(t=60, r=30, b=120, l=40),
        yaxis=dict(zeroline=False, title="Variazione"),
    )
    return fig


def build_frequency_chart(data: pd.DataFrame) -> go.Figure:
    if data.empty:
        return go.Figure()
    fig = px.bar(
        data.sort_values("frequency_delta", ascending=False),
        x="display_name",
        y="frequency_delta",
        text="frequency_delta",
        color="frequency_delta",
        color_continuous_scale=["#d62728", "#ffeda0", "#2ca02c"],
        title="Delta di frequenza d'uso strumenti AI (post - pre)",
        labels={"display_name": "Partecipante", "frequency_delta": "Delta"},
    )
    fig.add_hline(y=0, line_dash="dash", line_color="#444")
    fig.update_traces(texttemplate="%{text:+.0f}", textposition="outside")
    fig.update_layout(
        xaxis_tickangle=-35,
        coloraxis_showscale=False,
        margin=dict(t=60, r=30, b=120, l=40),
        yaxis=dict(zeroline=False, title="Variazione (scala 1-3)"),
    )
    return fig


def build_attitude_chart(data: pd.DataFrame) -> go.Figure:
    if data.empty:
        return go.Figure()
    fig = px.pie(
        data,
        names="attitude",
        values="count",
        title="Atteggiamento verso l'introduzione dell'AI (post)",
        hole=0.35,
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    fig.update_layout(margin=dict(t=60, r=30, b=30, l=30))
    return fig


def build_post_metric_chart(data: pd.DataFrame) -> go.Figure:
    if data.empty:
        return go.Figure()
    ordered = data.sort_values("mean", ascending=True)
    fig = px.bar(
        ordered,
        x="mean",
        y="metric",
        orientation="h",
        text="mean",
        color="mean",
        color_continuous_scale=["#d62728", "#ffeda0", "#2ca02c"],
        title="Valutazione media (1-4) sugli aspetti del percorso",
        labels={"mean": "Media", "metric": "Aspetto"},
    )
    fig.update_traces(texttemplate="%{text:.2f}", textposition="outside")
    fig.update_layout(
        xaxis=dict(range=[1, 4], title="Media"),
        coloraxis_showscale=False,
        margin=dict(t=60, r=30, b=40, l=100),
    )
    return fig


def build_satisfaction_indicator(mean_score: float, data: pd.DataFrame) -> go.Figure:
    if pd.isna(mean_score):
        return go.Figure()
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=mean_score,
            title={"text": "Soddisfazione media (1-5)"},
            number={"suffix": "/5", "valueformat": ".2f"},
            gauge={
                "axis": {"range": [1, 5]},
                "bar": {"color": "#2ca02c"},
                "steps": [
                    {"range": [1, 2], "color": "#fddbc7"},
                    {"range": [2, 3.5], "color": "#fee8c8"},
                    {"range": [3.5, 5], "color": "#c7e9c0"},
                ],
            },
        )
    )
    total = data["count"].sum() if not data.empty else 0
    if total:
        breakdown = ", ".join(
            f"{int(row['score'])}: {row['percentage']:.0f}%" for _, row in data.iterrows()
        )
        fig.add_annotation(
            text=f"Distribuzione ({total} risposte): {breakdown}",
            align="left",
            x=0.5,
            y=-0.25,
            xref="paper",
            yref="paper",
            showarrow=False,
        )
    fig.update_layout(margin=dict(t=80, r=30, b=100, l=30))
    return fig


def build_tool_delta_chart(data: pd.DataFrame) -> go.Figure:
    if data.empty:
        return go.Figure()
    summary = (
        data.groupby("tool", as_index=False)["delta"].mean()
        .sort_values("delta", ascending=False)
    )
    fig = px.bar(
        summary,
        x="tool",
        y="delta",
        text="delta",
        color="delta",
        color_continuous_scale=["#d62728", "#ffeda0", "#2ca02c"],
        title="Delta medio di utilizzo per strumento (post - pre)",
        labels={"tool": "Strumento", "delta": "Delta medio"},
    )
    fig.add_hline(y=0, line_dash="dash", line_color="#444")
    fig.update_traces(texttemplate="%{text:+.2f}", textposition="outside")
    fig.update_layout(
        coloraxis_showscale=False,
        margin=dict(t=60, r=30, b=80, l=40),
        yaxis=dict(zeroline=False, title="Variazione media (scala 0-2)"),
    )
    return fig


def build_tool_delta_table(data: pd.DataFrame) -> go.Figure:
    if data.empty:
        return go.Figure()
    table_data = data.sort_values(["tool", "display_name"])
    header = [
        "Strumento",
        "Nome",
        "Uso pre",
        "Uso post",
        "Delta",
    ]
    cells = [
        table_data["tool"],
        table_data["display_name"],
        table_data["usage_pre"],
        table_data["usage_post"],
        table_data["delta"].map(lambda v: f"{v:+.0f}" if pd.notna(v) else ""),
    ]
    fig = go.Figure(
        data=[
            go.Table(
                header=dict(values=header, fill_color="#1f77b4", font=dict(color="white")),
                cells=dict(values=cells, align="center"),
            )
        ]
    )
    fig.update_layout(margin=dict(t=30, r=10, b=10, l=10))
    return fig


def build_scale_summary_table(summary: pd.DataFrame) -> go.Figure:
    if summary.empty:
        return go.Figure()
    ordered = summary.sort_values(["column", "dataset"])
    header = [
        "Variabile",
        "Dataset",
        "Valore minimo",
        "Scala min",
        "Valore massimo",
        "Scala max",
        "Risposte",
    ]
    cells = [
        ordered["column"],
        ordered["dataset"],
        ordered["min_label"],
        ordered["min_score"].map(lambda v: f"{v:g}" if pd.notna(v) else ""),
        ordered["max_label"],
        ordered["max_score"].map(lambda v: f"{v:g}" if pd.notna(v) else ""),
        ordered["n"],
    ]
    fig = go.Figure(
        data=[
            go.Table(
                header=dict(values=header, fill_color="#1f77b4", font=dict(color="white")),
                cells=dict(values=cells, align="center"),
            )
        ]
    )
    fig.update_layout(margin=dict(t=30, r=10, b=10, l=10))
    return fig


def build_results_table(data: pd.DataFrame) -> go.Figure:
    display_cols = [
        "display_name",
        "familiarity_pre",
        "familiarity_post",
        "familiarity_delta",
        "frequency_label_pre",
        "frequency_label_post",
        "frequency_delta",
    ]
    table_data = data.dropna(subset=["display_name"])[display_cols]
    table_data = table_data.sort_values("display_name")

    header = [
        "Nome",
        "Familiarit\u00e0 pre",
        "Familiarit\u00e0 post",
        "Delta familiarit\u00e0",
        "Frequenza pre",
        "Frequenza post",
        "Delta frequenza",
    ]

    cells = [table_data[col] for col in table_data.columns]

    fig = go.Figure(
        data=[
            go.Table(
                header=dict(values=header, fill_color="#1f77b4", font=dict(color="white")),
                cells=dict(values=cells, align="center"),
            )
        ]
    )
    fig.update_layout(margin=dict(t=30, r=10, b=10, l=10))
    return fig


def render_dashboard(figures: Iterable[go.Figure], output_path: Path) -> None:
    valid_figs = [fig for fig in figures if len(fig.data) > 0]
    if not valid_figs:
        valid_figs = list(figures)
    parts = [fig.to_html(full_html=False, include_plotlyjs="cdn") for fig in valid_figs]
    html = f"""
<!DOCTYPE html>
<html lang=\"it\">
<head>
  <meta charset=\"utf-8\" />
  <title>Dashboard miglioramento popolazione</title>
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <style>
    body {{ font-family: Arial, sans-serif; margin: 30px; background: #f5f7fa; color: #222; }}
    h1 {{ margin-bottom: 0.5em; }}
    section {{ margin-bottom: 40px; background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); }}
  </style>
</head>
<body>
  <h1>Impatto del corso sugli strumenti AI</h1>
  <p>Delta calcolato come valore dopo il corso meno valore prima del corso.</p>
  {''.join(f'<section>{fragment}</section>' for fragment in parts)}
</body>
</html>
"""
    output_path.write_text(html, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Crea dashboard prima/dopo per il corso AI.")
    parser.add_argument(
        "--pre",
        type=Path,
        default=Path("Feedback corso inizio.csv"),
        help="CSV con le risposte prima del corso.",
    )
    parser.add_argument(
        "--post",
        type=Path,
        default=Path("Feedback corso fine.csv"),
        help="CSV con le risposte dopo il corso.",
    )
    parser.add_argument(
        "--html-out",
        type=Path,
        default=Path("dashboard_feedback.html"),
        help="File HTML di output per la dashboard.",
    )
    parser.add_argument(
        "--csv-out",
        type=Path,
        default=None,
        help="(Opzionale) Esporta la tabella dei delta in CSV.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data = prepare_data(args.pre, args.post)

    familiarity_fig = build_familiarity_chart(data.familiarity_delta)
    frequency_fig = build_frequency_chart(data.frequency_delta)
    attitude_fig = build_attitude_chart(data.post_overview.attitude_distribution)
    metrics_fig = build_post_metric_chart(data.post_overview.metric_summary)
    satisfaction_fig = build_satisfaction_indicator(
        data.post_overview.satisfaction_mean,
        data.post_overview.satisfaction_distribution,
    )
    tool_fig = build_tool_delta_chart(data.tool_delta)
    table_fig = build_results_table(data.merged)
    tool_table_fig = build_tool_delta_table(data.tool_delta)
    scale_table_fig = build_scale_summary_table(data.scale_summary)

    figures: list[go.Figure] = [familiarity_fig, frequency_fig]
    figures.append(metrics_fig)
    if len(scale_table_fig.data) > 0:
        figures.append(scale_table_fig)
    if len(attitude_fig.data) > 0:
        figures.append(attitude_fig)
    if len(satisfaction_fig.data) > 0:
        figures.append(satisfaction_fig)
    if not data.tool_delta.empty:
        figures.append(tool_fig)
    figures.append(table_fig)
    if not data.tool_delta.empty:
        figures.append(tool_table_fig)

    render_dashboard(figures, args.html_out)

    if args.csv_out is not None:
        export_cols = [
            "display_name",
            "familiarity_pre",
            "familiarity_post",
            "familiarity_delta",
            "frequency_label_pre",
            "frequency_label_post",
            "frequency_delta",
        ]
        for tool in TOOL_NAMES:
            export_cols.extend(
                [
                    f"{tool}_pre_label",
                    f"{tool}_post_label",
                    f"{tool}_delta",
                ]
            )
        data.merged.dropna(subset=["display_name"])[export_cols].sort_values(
            "display_name"
        ).to_csv(args.csv_out, index=False)

    familiarity_mean_pre = data.familiarity_delta["familiarity_pre"].mean()
    familiarity_mean_post = data.familiarity_delta["familiarity_post"].mean()
    familiarity_mean_delta = familiarity_mean_post - familiarity_mean_pre

    print("Andamento medio familiarit\u00e0 AI")
    print(f"  Prima: {familiarity_mean_pre:.2f}")
    print(f"  Dopo:  {familiarity_mean_post:.2f}")
    print(f"  Delta: {familiarity_mean_delta:+.2f}")

    if not data.frequency_delta.empty:
        freq_mean_pre = data.frequency_delta["frequency_delta"].add(
            data.frequency_delta["frequency_label_pre"].map(lambda _: 0), fill_value=0
        )
        # Re-compute with the score columns to avoid type juggling.
        freq_mean_pre = data.merged["frequency_score_pre"].mean()
        freq_mean_post = data.merged["frequency_score_post"].mean()
        if pd.notna(freq_mean_pre) and pd.notna(freq_mean_post):
            freq_mean_delta = freq_mean_post - freq_mean_pre
            print("Andamento medio frequenza uso AI (scala 1-3)")
            print(f"  Prima: {freq_mean_pre:.2f}")
            print(f"  Dopo:  {freq_mean_post:.2f}")
            print(f"  Delta: {freq_mean_delta:+.2f}")

    if not data.tool_delta.empty:
        tool_summary = (
            data.tool_delta.groupby("tool")["delta"].mean().sort_values(ascending=False)
        )
        print("Delta medio per strumento (scala 0-2)")
        for tool, delta in tool_summary.items():
            print(f"  {tool}: {delta:+.2f}")

    if not data.post_overview.metric_summary.empty:
        print("Valutazione media aspetti post-corso (scala 1-4)")
        for _, row in data.post_overview.metric_summary.sort_values("mean", ascending=False).iterrows():
            print(f"  {row['metric']}: {row['mean']:.2f} (n={row['n']})")

    if not data.post_overview.attitude_distribution.empty:
        print("Distribuzione atteggiamento post-corso")
        for _, row in data.post_overview.attitude_distribution.iterrows():
            print(f"  {row['attitude']}: {int(row['count'])} ({row['percentage']:.1f}%)")

    if pd.notna(data.post_overview.satisfaction_mean):
        total_s = int(data.post_overview.satisfaction_distribution["count"].sum()) if not data.post_overview.satisfaction_distribution.empty else 0
        print("Soddisfazione complessiva (scala 1-5)")
        print(f"  Media: {data.post_overview.satisfaction_mean:.2f} su 5 (n={total_s})")

    print(f"Dashboard salvata in: {args.html_out.resolve()}")
    if args.csv_out:
        print(f"Tabella dettagli salvata in: {args.csv_out.resolve()}")


if __name__ == "__main__":
    main()
