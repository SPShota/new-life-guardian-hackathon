#!/usr/bin/env python3
"""Bear Guardian pipeline.

PDFからのクマ目撃情報取得と、CSV/HTML生成までの軽量MVP。
共存の観点で「避ける・近づけない」を支援する目的。
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd
import requests

try:
    import pdfplumber  # type: ignore
except Exception:  # pragma: no cover - optional dependency guard
    pdfplumber = None

try:
    import folium  # type: ignore
except Exception:  # pragma: no cover - optional dependency guard
    folium = None

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
OUTPUTS_DIR = BASE_DIR / "outputs"
SAMPLE_CSV = DATA_DIR / "sample_sightings.csv"
PDF_URL = "https://www.city.nagano.nagano.jp/documents/3071/kuma20251031.pdf"
PDF_NAME = "kuma20251031.pdf"


def fetch_pdf(url: str = PDF_URL, dest: Path | None = None) -> Path:
    """Download PDF to raw directory."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    dest = dest or RAW_DIR / PDF_NAME
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    dest.write_bytes(resp.content)
    print(f"[fetch] saved PDF -> {dest}")
    return dest


def _parse_tables(pdf_path: Path) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    if pdfplumber is None:
        print("[parse] pdfplumber 未インストール。サンプルデータにフォールバックします。")
        return records

    with pdfplumber.open(pdf_path) as pdf:
        for page_idx, page in enumerate(pdf.pages):
            tables = page.extract_tables() or []
            for table in tables:
                for row in table:
                    cells = [(cell or "").strip() for cell in row]
                    if len([c for c in cells if c]) < 2:
                        continue
                    record: Dict[str, Any] = {}
                    # 期待: 日付 / 時刻 / 地域 / 詳細 の順で格納されているケースが多い
                    if len(cells) >= 1:
                        record["date"] = cells[0]
                    if len(cells) >= 2:
                        record["time"] = cells[1]
                    if len(cells) >= 3:
                        record["area"] = cells[2]
                    if len(cells) >= 4:
                        record["details"] = cells[3]
                    record["source"] = f"pdf_p{page_idx+1}"
                    records.append(record)
    return records


def parse_pdf(pdf_path: Path | None = None, sample_path: Path = SAMPLE_CSV) -> Path:
    """Parse PDF into structured CSV. Fallback to bundled sample."""
    pdf_path = pdf_path or RAW_DIR / PDF_NAME
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    output = PROCESSED_DIR / "sightings.csv"

    records: List[Dict[str, Any]] = []
    if pdf_path.exists():
        try:
            records = _parse_tables(pdf_path)
        except Exception as exc:  # pragma: no cover - defensive
            print(f"[parse] PDF parse failed, fallback to sample. reason={exc}")
            records = []
    else:
        print("[parse] PDF not found. Using sample data.")

    if not records:
        df = pd.read_csv(sample_path)
    else:
        df = pd.DataFrame.from_records(records)
        # 簡易正規化: 欠損列を追加し、lat/lonは未知なら空に
        for col in ("lat", "lon", "details"):
            if col not in df.columns:
                df[col] = ""
        if "source" not in df.columns:
            df["source"] = "pdf"

    df.to_csv(output, index=False, quoting=csv.QUOTE_NONNUMERIC)
    print(f"[parse] structured CSV -> {output}")
    return output


def generate_map(csv_path: Path | None = None) -> Path:
    """Generate a simple folium map with sighting markers."""
    csv_path = csv_path or PROCESSED_DIR / "sightings.csv"
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    if folium is None:
        raise RuntimeError("folium が必要です。pip install -r requirements.txt を実行してください")

    if not csv_path.exists():
        raise FileNotFoundError(f"sightings CSV not found: {csv_path}")

    df = pd.read_csv(csv_path)
    if "lat" not in df.columns or "lon" not in df.columns:
        raise ValueError("CSVにlat/lon列が必要です。サンプルデータを利用してください。")

    sighting_rows = df.dropna(subset=["lat", "lon"])
    if sighting_rows.empty:
        raise ValueError("緯度経度付きのデータがありません。")

    center = [sighting_rows["lat"].mean(), sighting_rows["lon"].mean()]
    m = folium.Map(location=center, zoom_start=12, control_scale=True)

    for _, row in sighting_rows.iterrows():
        popup = f"{row.get('date', '')} {row.get('time', '')}\n{row.get('area', '')}\n{row.get('details', '')}"
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=7,
            color="#d9480f",
            fill=True,
            fill_color="#f76707",
            fill_opacity=0.8,
            popup=popup,
        ).add_to(m)

    map_path = OUTPUTS_DIR / "sightings_map.html"
    m.save(str(map_path))
    print(f"[map] map created -> {map_path}")
    return map_path


def write_digest(csv_path: Path | None = None) -> Path:
    """Create a text digest for quick sharing."""
    csv_path = csv_path or PROCESSED_DIR / "sightings.csv"
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    df = pd.read_csv(csv_path)
    latest = df.head(0)
    try:
        latest = df.sort_values(by=["date", "time"], ascending=False)
    except Exception:
        latest = df

    lines = ["New Life Guardian - クマ回避ダイジェスト", ""]
    if not latest.empty:
        head = latest.iloc[0]
        lines.append(f"最新: {head.get('date','?')} {head.get('time','?')} @ {head.get('area','?')}")
        lines.append(f"内容: {head.get('details','')}".strip())

    hotspot = (
        df.groupby("area")["date"].count().sort_values(ascending=False).head(3)
        if "area" in df.columns and not df.empty
        else pd.Series()
    )
    if not hotspot.empty:
        lines.append("")
        lines.append("頻出エリア TOP3:")
        for area, cnt in hotspot.items():
            lines.append(f"- {area}: {cnt}件")

    lines.append("")
    lines.append("推奨アクション (共存重視):")
    lines.append("- 早朝/夕方の人通り少ないルートは避ける")
    lines.append("- 鈴・笛・ライトで存在を知らせる (威嚇しない)")
    lines.append("- 目撃エリア100m以内ではゴミや餌付けをしない")

    digest_path = OUTPUTS_DIR / "digest.txt"
    digest_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[digest] wrote {digest_path}")
    return digest_path


def run_pipeline(args: argparse.Namespace) -> None:
    pdf_path = fetch_pdf() if args.fetch else RAW_DIR / PDF_NAME
    csv_path = parse_pdf(pdf_path=pdf_path)
    map_path = None
    if args.make_map:
        map_path = generate_map(csv_path=csv_path)
    if args.digest:
        write_digest(csv_path=csv_path)
    if map_path:
        print(f"[done] open map: {map_path}")


def main(argv: List[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Bear Guardian data pipeline")
    sub = parser.add_subparsers(dest="command")

    p_fetch = sub.add_parser("fetch", help="PDFをダウンロード")
    p_fetch.set_defaults(func=lambda a: fetch_pdf())

    p_parse = sub.add_parser("parse", help="PDFを構造化CSVに変換")
    p_parse.add_argument("--pdf", type=Path, default=None, help="解析対象PDF")
    p_parse.set_defaults(func=lambda a: parse_pdf(pdf_path=a.pdf))

    p_map = sub.add_parser("map", help="foliumで地図HTMLを生成")
    p_map.add_argument("--csv", type=Path, default=None, help="入力CSV")
    p_map.set_defaults(func=lambda a: generate_map(csv_path=a.csv))

    p_digest = sub.add_parser("digest", help="テキストダイジェスト生成")
    p_digest.add_argument("--csv", type=Path, default=None, help="入力CSV")
    p_digest.set_defaults(func=lambda a: write_digest(csv_path=a.csv))

    p_all = sub.add_parser("pipeline", help="fetch->parse->map->digest をまとめて実行")
    p_all.add_argument("--no-fetch", dest="fetch", action="store_false", help="PDFダウンロードをスキップ")
    p_all.add_argument("--no-map", dest="make_map", action="store_false", help="地図生成をスキップ")
    p_all.add_argument("--no-digest", dest="digest", action="store_false", help="ダイジェスト生成をスキップ")
    p_all.set_defaults(fetch=True, make_map=True, digest=True, func=run_pipeline)

    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return
    args.func(args)


if __name__ == "__main__":
    main()
