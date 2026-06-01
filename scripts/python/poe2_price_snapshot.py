from __future__ import annotations

import csv
import json
import argparse
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests


ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw" / "poe_ninja"
PRICE_DIR = ROOT / "data" / "processed" / "prices" / "poe_ninja"
TYPE_CSV_DIR = PRICE_DIR / "by_type"

LEAGUE = "Runes of Aldur"
LEAGUE_URL = "runesofaldur"
BASE_URL = "https://poe.ninja"
TYPES = [
    "Currency",
    "Essences",
    "Runes",
    "Ritual",
    "Abyss",
    "Fragments",
]
USER_AGENT = "Mozilla/5.0 (compatible; POE2LocalResearch/1.0; +local-price-script)"


def fetch_overview(type_name: str) -> dict[str, Any]:
    url = f"{BASE_URL}/poe2/api/economy/exchange/current/overview"
    response = requests.get(
        url,
        params={"league": LEAGUE, "type": type_name},
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
        timeout=45,
    )
    response.raise_for_status()
    return response.json()


def normalize_rows(type_name: str, data: dict[str, Any], snapshot_time: str) -> list[dict[str, Any]]:
    items = {item["id"]: item for item in data.get("items", [])}
    lines = {line["id"]: line for line in data.get("lines", [])}
    rates = data.get("core", {}).get("rates", {})
    divine_per_exalted = float(rates.get("divine") or 0)
    chaos_per_exalted = float(rates.get("chaos") or 0)

    rows: list[dict[str, Any]] = []
    for item_id, item in items.items():
        line = lines.get(item_id, {})
        # poe.ninja PoE2 exchange overview currently reports primaryValue in
        # Exalted Orb units; core.rates gives secondary conversions per exalt.
        exalted_value = float(line.get("primaryValue") or 0)
        rows.append(
            {
                "snapshot_time_utc": snapshot_time,
                "league": LEAGUE,
                "type": type_name,
                "id": item_id,
                "name": item.get("name", ""),
                "category": item.get("category", ""),
                "details_id": item.get("detailsId", ""),
                "divine_value": exalted_value * divine_per_exalted if divine_per_exalted else "",
                "exalted_value": exalted_value,
                "chaos_value": exalted_value * chaos_per_exalted if chaos_per_exalted else "",
                "max_volume_currency": line.get("maxVolumeCurrency", ""),
                "max_volume_rate": line.get("maxVolumeRate", ""),
                "volume_primary_value": line.get("volumePrimaryValue", ""),
                "sparkline_total_change": (line.get("sparkline") or {}).get("totalChange", ""),
            }
        )
    return rows


def write_csv(rows: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def snapshot_once() -> dict[str, Any]:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PRICE_DIR.mkdir(parents=True, exist_ok=True)
    TYPE_CSV_DIR.mkdir(parents=True, exist_ok=True)

    snapshot_time = datetime.now(timezone.utc).isoformat(timespec="seconds")
    raw_summary: dict[str, Any] = {
        "snapshot_time_utc": snapshot_time,
        "league": LEAGUE,
        "league_url": LEAGUE_URL,
        "source": f"{BASE_URL}/poe2/economy/{LEAGUE_URL}/currency",
        "types": TYPES,
    }

    for type_name in TYPES:
        data = fetch_overview(type_name)
        (RAW_DIR / f"{type_name}.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        rows = normalize_rows(type_name, data, snapshot_time)
        type_csv = TYPE_CSV_DIR / f"{type_name}.csv"
        write_csv(rows, type_csv)
        raw_summary[type_name] = {
            "items": len(data.get("items", [])),
            "lines": len(data.get("lines", [])),
            "rows": len(rows),
            "csv": str(type_csv.relative_to(ROOT)),
        }
        print(f"{type_name}: {len(rows)} rows")

    (PRICE_DIR / "summary.json").write_text(
        json.dumps(raw_summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Wrote per-type CSVs under {TYPE_CSV_DIR}")
    return raw_summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch poe.ninja PoE2 prices into CSV/JSON snapshots.")
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Keep running and refresh snapshots every interval.",
    )
    parser.add_argument(
        "--interval-seconds",
        type=int,
        default=3600,
        help="Refresh interval when --watch is set. Defaults to 3600 seconds.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.watch:
        snapshot_once()
        return

    interval = max(args.interval_seconds, 60)
    while True:
        started = datetime.now(timezone.utc).isoformat(timespec="seconds")
        print(f"[{started}] Starting poe.ninja price snapshot")
        try:
            snapshot_once()
        except Exception as exc:
            print(f"[{datetime.now(timezone.utc).isoformat(timespec='seconds')}] Snapshot failed: {exc}")
        print(f"Sleeping {interval} seconds")
        time.sleep(interval)


if __name__ == "__main__":
    main()
