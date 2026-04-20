#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import re
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _write_text(path: Path, text: str) -> None:
    _ensure_dir(path.parent)
    path.write_text(text, encoding="utf-8")


def _safe_write_json(path: Path, data: Dict[str, Any]) -> None:
    def _json_safe(obj: Any) -> Any:
        if obj is None or isinstance(obj, (str, int, float, bool)):
            return obj
        if isinstance(obj, Path):
            return str(obj)
        if isinstance(obj, dict):
            return {str(k): _json_safe(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple, set)):
            return [_json_safe(x) for x in obj]
        try:
            json.dumps(obj)
            return obj
        except Exception:
            try:
                return str(obj)
            except Exception:
                return None

    _ensure_dir(path.parent)
    path.write_text(
        json.dumps(_json_safe(data), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _normalize_sheet_selector(raw: Optional[str]) -> Union[int, str, None]:
    if raw is None:
        return None
    raw = str(raw).strip()
    if raw == "":
        return None
    if raw.isdigit():
        return int(raw)
    return raw


def _load_table(input_path: Path, sheet_selector: Optional[str] = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    ext = input_path.suffix.lower()

    if ext == ".csv":
        df = pd.read_csv(input_path)
        meta = {
            "source_type": "csv",
            "sheet_name": None,
            "sheet_selector": None,
            "available_sheets": None,
        }
        return df, meta

    if ext == ".xlsx":
        xls = pd.ExcelFile(input_path)
        available_sheets = list(xls.sheet_names)

        selector = _normalize_sheet_selector(sheet_selector)
        if selector is None:
            selector = 0

        if isinstance(selector, int):
            if selector < 0 or selector >= len(available_sheets):
                raise ValueError(
                    f"Sheet index {selector} out of range for workbook with {len(available_sheets)} sheets: {available_sheets}"
                )
            resolved_sheet_name = available_sheets[selector]
            df = pd.read_excel(input_path, sheet_name=selector)
        else:
            if selector not in available_sheets:
                raise ValueError(
                    f"Sheet name '{selector}' not found. Available sheets: {available_sheets}"
                )
            resolved_sheet_name = selector
            df = pd.read_excel(input_path, sheet_name=selector)

        meta = {
            "source_type": "xlsx",
            "sheet_name": resolved_sheet_name,
            "sheet_selector": selector,
            "available_sheets": available_sheets,
        }
        return df, meta

    raise ValueError(f"Unsupported file type: {ext}")


def _maybe_parse_datetime(series: pd.Series) -> pd.Series:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        return pd.to_datetime(series, errors="coerce")


def _classify_column(series: pd.Series) -> str:
    s = series.dropna()
    if s.empty:
        return "unknown"

    parsed_dt = _maybe_parse_datetime(s)
    if parsed_dt.notna().mean() >= 0.8:
        return "datetime"

    parsed_num = pd.to_numeric(s, errors="coerce")
    if parsed_num.notna().mean() >= 0.8:
        return "numeric"

    nunique = s.astype(str).nunique(dropna=True)
    if nunique <= max(20, min(100, len(s) // 5)):
        return "categorical"

    return "text"


def _infer_schema(
    df: pd.DataFrame,
    source_file: str,
    source_type: str,
    sheet_name: Optional[str],
    available_sheets: Optional[List[str]] = None,
    sheet_selector: Optional[Union[int, str]] = None,
) -> Dict[str, Any]:
    columns_meta = []
    numeric_columns: List[str] = []
    categorical_columns: List[str] = []
    datetime_columns: List[str] = []
    possible_id_columns: List[str] = []

    for col in df.columns:
        series = df[col]
        inferred = _classify_column(series)
        col_name = str(col)

        if inferred == "numeric":
            numeric_columns.append(col_name)
        elif inferred == "categorical":
            categorical_columns.append(col_name)
        elif inferred == "datetime":
            datetime_columns.append(col_name)

        non_null = series.dropna()
        nunique = int(non_null.astype(str).nunique()) if not non_null.empty else 0

        if nunique == len(non_null) and len(non_null) > 0 and len(non_null) >= max(5, int(len(df) * 0.7)):
            possible_id_columns.append(col_name)

        columns_meta.append({
            "name": col_name,
            "type": inferred,
            "non_null_count": int(series.notna().sum()),
            "missing_count": int(series.isna().sum()),
            "unique_count": nunique,
        })

    return {
        "source_file": source_file,
        "source_type": source_type,
        "sheet_name": sheet_name,
        "sheet_selector": sheet_selector,
        "available_sheets": available_sheets,
        "sheet_count": len(available_sheets) if available_sheets else None,
        "row_count": int(len(df)),
        "column_count": int(len(df.columns)),
        "columns": columns_meta,
        "numeric_columns": numeric_columns,
        "categorical_columns": categorical_columns,
        "datetime_columns": datetime_columns,
        "possible_id_columns": possible_id_columns,
    }


def _series_top_values(series: pd.Series, top_k: int = 5) -> List[Dict[str, Any]]:
    vc = series.astype(str).value_counts(dropna=True).head(top_k)
    return [{"value": str(idx), "count": int(val)} for idx, val in vc.items()]


def _numeric_stats(series: pd.Series) -> Optional[Dict[str, Any]]:
    values = pd.to_numeric(series, errors="coerce").dropna()
    if values.empty:
        return None
    return {
        "count": int(values.count()),
        "min": float(values.min()),
        "max": float(values.max()),
        "mean": float(values.mean()),
        "median": float(values.median()),
        "std": float(values.std()) if values.count() > 1 else 0.0,
    }


def _datetime_stats(series: pd.Series) -> Optional[Dict[str, Any]]:
    values = _maybe_parse_datetime(series).dropna()
    if values.empty:
        return None
    return {
        "count": int(values.count()),
        "min": str(values.min()),
        "max": str(values.max()),
    }


def _build_summary_stats(df: pd.DataFrame, schema: Dict[str, Any]) -> Dict[str, Any]:
    column_stats: Dict[str, Any] = {}

    for col_meta in schema["columns"]:
        name = col_meta["name"]
        inferred = col_meta["type"]
        series = df[name]

        entry: Dict[str, Any] = {
            "type": inferred,
            "missing_count": int(series.isna().sum()),
            "missing_ratio": float(series.isna().mean()) if len(series) else 0.0,
        }

        if inferred == "numeric":
            entry["numeric_stats"] = _numeric_stats(series)
        elif inferred == "categorical":
            entry["top_values"] = _series_top_values(series)
        elif inferred == "datetime":
            entry["datetime_stats"] = _datetime_stats(series)

        column_stats[name] = entry

    return {
        "row_count": int(len(df)),
        "column_count": int(len(df.columns)),
        "duplicate_row_count": int(df.duplicated().sum()),
        "total_missing_cells": int(df.isna().sum().sum()),
        "column_stats": column_stats,
    }


def _write_previews(df: pd.DataFrame, bundle_dir: Path) -> List[Dict[str, Any]]:
    previews_dir = bundle_dir / "assets" / "previews"
    _ensure_dir(previews_dir)

    head_path = previews_dir / "head.csv"
    sampled_path = previews_dir / "sampled_rows.csv"
    column_summary_path = previews_dir / "column_summary.md"

    head_n = min(20, len(df))
    df.head(head_n).to_csv(head_path, index=False)

    if len(df) <= 50:
        sampled_df = df.copy()
    else:
        sample_n = min(50, len(df))
        sampled_df = df.sample(n=sample_n, random_state=42)
    sampled_df.to_csv(sampled_path, index=False)

    lines = ["# Column Summary", ""]
    for col in df.columns:
        series = df[col]
        lines.append(
            f"- {col}: non_null={int(series.notna().sum())}, "
            f"missing={int(series.isna().sum())}, "
            f"unique={int(series.astype(str).nunique(dropna=True))}"
        )
    _write_text(column_summary_path, "\n".join(lines))

    return [
        {"type": "head", "path": str(head_path)},
        {"type": "sampled_rows", "path": str(sampled_path)},
        {"type": "column_summary", "path": str(column_summary_path)},
    ]


def _save_line_chart(df: pd.DataFrame, x_col: str, y_col: str, out_path: Path) -> bool:
    data = pd.DataFrame({
        x_col: _maybe_parse_datetime(df[x_col]),
        y_col: pd.to_numeric(df[y_col], errors="coerce"),
    }).dropna()
    if data.empty:
        return False

    data = data.sort_values(x_col)
    plt.figure(figsize=(8, 4.5))
    plt.plot(data[x_col], data[y_col])
    plt.xlabel(x_col)
    plt.ylabel(y_col)
    plt.title(f"{y_col} over {x_col}")
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()
    return True


def _save_bar_chart(df: pd.DataFrame, x_col: str, y_col: str, out_path: Path) -> bool:
    temp = pd.DataFrame({
        x_col: df[x_col].astype(str),
        y_col: pd.to_numeric(df[y_col], errors="coerce"),
    }).dropna()
    if temp.empty:
        return False

    grouped = temp.groupby(x_col, dropna=True)[y_col].mean().sort_values(ascending=False).head(12)
    if grouped.empty:
        return False

    plt.figure(figsize=(8, 4.5))
    grouped.plot(kind="bar")
    plt.xlabel(x_col)
    plt.ylabel(f"mean({y_col})")
    plt.title(f"{y_col} by {x_col}")
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()
    return True


def _save_hist_chart(df: pd.DataFrame, y_col: str, out_path: Path) -> bool:
    values = pd.to_numeric(df[y_col], errors="coerce").dropna()
    if values.empty:
        return False

    plt.figure(figsize=(8, 4.5))
    plt.hist(values, bins=min(30, max(10, int(math.sqrt(len(values))))))
    plt.xlabel(y_col)
    plt.ylabel("count")
    plt.title(f"Distribution of {y_col}")
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()
    return True


def _generate_basic_charts(df: pd.DataFrame, schema: Dict[str, Any], bundle_dir: Path) -> List[Dict[str, Any]]:
    charts_dir = bundle_dir / "assets" / "charts"
    _ensure_dir(charts_dir)

    charts: List[Dict[str, Any]] = []
    idx = 1

    datetime_cols = schema["datetime_columns"]
    numeric_cols = schema["numeric_columns"]
    categorical_cols = schema["categorical_columns"]

    if datetime_cols and numeric_cols:
        x_col = datetime_cols[0]
        y_col = numeric_cols[0]
        out = charts_dir / f"chart_{idx:03d}.png"
        if _save_line_chart(df, x_col, y_col, out):
            charts.append({
                "id": f"chart_{idx:03d}",
                "type": "line",
                "path": str(out),
                "columns": [x_col, y_col],
                "summary": f"{y_col} over {x_col}",
            })
            idx += 1

    if categorical_cols and numeric_cols and idx <= 3:
        x_col = categorical_cols[0]
        y_col = numeric_cols[0]
        out = charts_dir / f"chart_{idx:03d}.png"
        if _save_bar_chart(df, x_col, y_col, out):
            charts.append({
                "id": f"chart_{idx:03d}",
                "type": "bar",
                "path": str(out),
                "columns": [x_col, y_col],
                "summary": f"{y_col} by {x_col}",
            })
            idx += 1

    if numeric_cols and idx <= 3:
        y_col = numeric_cols[min(1, len(numeric_cols) - 1)]
        out = charts_dir / f"chart_{idx:03d}.png"
        if _save_hist_chart(df, y_col, out):
            charts.append({
                "id": f"chart_{idx:03d}",
                "type": "histogram",
                "path": str(out),
                "columns": [y_col],
                "summary": f"Distribution of {y_col}",
            })
            idx += 1

    return charts


def _build_asset_ref(preview_or_chart: Dict[str, Any], bundle_dir: Path) -> str:
    rel = Path(preview_or_chart["path"]).relative_to(bundle_dir)
    kind = preview_or_chart.get("type", "asset")

    lines = [
        "[AssetRef]",
        f"type: {kind}",
    ]

    if "id" in preview_or_chart:
        lines.append(f"id: {preview_or_chart['id']}")

    lines.append(f"path: {rel.as_posix()}")

    summary = preview_or_chart.get("summary")
    if summary:
        lines.append(f"summary: {summary}")

    if kind in {"line", "bar", "histogram"}:
        lines.append("instruction: Inspect this chart before writing grounded.md if it contains key trends, comparisons, or distributions.")
    else:
        lines.append("instruction: Inspect this asset before writing grounded.md if it helps verify schema, example rows, or data patterns.")

    lines.append("[/AssetRef]")
    return "\n".join(lines)


def _build_extracted_markdown(
    schema: Dict[str, Any],
    summary_stats: Dict[str, Any],
    previews: List[Dict[str, Any]],
    charts: List[Dict[str, Any]],
    bundle_dir: Path,
) -> str:
    lines: List[str] = []
    lines.append("# Extracted Table Evidence")
    lines.append("")
    lines.append("## 1. Source")
    lines.append(f"- File name: {schema['source_file']}")
    lines.append(f"- File type: {schema['source_type']}")
    if schema.get("sheet_name"):
        lines.append(f"- Sheet name: {schema['sheet_name']}")
    if schema.get("available_sheets"):
        lines.append(f"- Available sheets: {', '.join(schema['available_sheets'])}")
    lines.append("")
    lines.append("## 2. Table Shape")
    lines.append(f"- Row count: {schema['row_count']}")
    lines.append(f"- Column count: {schema['column_count']}")
    lines.append("")
    lines.append("## 3. Columns")
    for col in schema["columns"]:
        lines.append(f"- {col['name']}: {col['type']} (missing={col['missing_count']}, unique={col['unique_count']})")
    lines.append("")
    lines.append("## 4. Summary Statistics")
    lines.append(f"- Duplicate rows: {summary_stats['duplicate_row_count']}")
    lines.append(f"- Total missing cells: {summary_stats['total_missing_cells']}")
    for name, stats in summary_stats["column_stats"].items():
        if stats["type"] == "numeric" and stats.get("numeric_stats"):
            ns = stats["numeric_stats"]
            lines.append(
                f"- {name}: numeric, "
                f"min={ns['min']:.4g}, max={ns['max']:.4g}, "
                f"mean={ns['mean']:.4g}, median={ns['median']:.4g}"
            )
        elif stats["type"] == "categorical" and stats.get("top_values"):
            top = ", ".join(f"{x['value']} ({x['count']})" for x in stats["top_values"])
            lines.append(f"- {name}: categorical, top values = {top}")
        elif stats["type"] == "datetime" and stats.get("datetime_stats"):
            ds = stats["datetime_stats"]
            lines.append(f"- {name}: datetime, range = {ds['min']} to {ds['max']}")
    lines.append("")
    lines.append("## 5. Referenced Assets")
    assets = previews + charts
    if not assets:
        lines.append("No preview or chart assets were generated.")
    else:
        for asset in assets:
            lines.append(_build_asset_ref(asset, bundle_dir))
            lines.append("")
    if not charts:
        lines.append("Execution note: no chart assets were generated automatically in this run. This alone does not imply a data-quality issue.")
    return "\n".join(lines).strip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a table-grounding extraction bundle.")
    parser.add_argument("input_path", help="Path to .xlsx or .csv")
    parser.add_argument("bundle_dir", help="Output bundle directory")
    parser.add_argument("--sheet", default=None, help="Optional sheet selector for xlsx: sheet name or zero-based index")
    args = parser.parse_args()

    input_path = Path(args.input_path).resolve()
    bundle_dir = Path(args.bundle_dir).resolve()
    _ensure_dir(bundle_dir)

    df, src_meta = _load_table(input_path, sheet_selector=args.sheet)

    df.columns = [str(c).strip() for c in df.columns]

    schema = _infer_schema(
        df=df,
        source_file=input_path.name,
        source_type=src_meta["source_type"],
        sheet_name=src_meta.get("sheet_name"),
        available_sheets=src_meta.get("available_sheets"),
        sheet_selector=src_meta.get("sheet_selector"),
    )
    summary_stats = _build_summary_stats(df, schema)
    previews = _write_previews(df, bundle_dir)
    charts = _generate_basic_charts(df, schema, bundle_dir)

    asset_index = {
        "source_file": input_path.name,
        "source_type": src_meta["source_type"],
        "sheet_name": src_meta.get("sheet_name"),
        "sheet_selector": src_meta.get("sheet_selector"),
        "available_sheets": src_meta.get("available_sheets"),
        "previews": previews,
        "charts": charts,
    }

    extracted_md = _build_extracted_markdown(schema, summary_stats, previews, charts, bundle_dir)
    _write_text(bundle_dir / "extracted.md", extracted_md)

    _safe_write_json(bundle_dir / "schema.json", schema)
    _safe_write_json(bundle_dir / "summary_stats.json", summary_stats)
    _safe_write_json(bundle_dir / "asset_index.json", asset_index)

    extracted_meta = {
        "source_file": input_path.name,
        "source_type": src_meta["source_type"],
        "sheet_name": src_meta.get("sheet_name"),
        "sheet_selector": src_meta.get("sheet_selector"),
        "available_sheets": src_meta.get("available_sheets"),
        "original_path": str(input_path),
        "row_count": int(len(df)),
        "column_count": int(len(df.columns)),
        "chart_count": int(len(charts)),
        "preview_count": int(len(previews)),
        "grounded_note_generated_by_script": False,
    }
    _safe_write_json(bundle_dir / "extracted_meta.json", extracted_meta)


if __name__ == "__main__":
    main()
