from __future__ import annotations

import argparse
import csv
import html
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests


ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw" / "poe2wiki"
POE2DB_RAW_DIR = ROOT / "data" / "raw" / "poe2db"
PROCESSED_DIR = ROOT / "data" / "processed" / "passive_tree"
METADATA_DIR = ROOT / "data" / "processed" / "metadata"

POE2WIKI_API = "https://www.poe2wiki.net/api.php"
POE2DB_ATLAS_PAGE = "https://poe2db.tw/Atlas_passive_skill"
USER_AGENT = "Mozilla/5.0 (compatible; POE2LocalResearch/1.0; +local-atlas-passive-script)"

PASSIVE_FIELDS = [
    "_pageName=page_name",
    "id",
    "int_id",
    "name",
    "main_page",
    "atlas_sub_tree",
    "frame",
    "icon",
    "is_in_game",
    "is_atlas_passive",
    "is_keystone",
    "is_notable",
    "is_starting_node",
    "is_multiple_choice",
    "is_multiple_choice_option",
    "is_icon_only",
    "is_jewel_socket",
    "is_attribute",
    "is_free",
    "skill_points",
    "weapon_set_points",
    "buff_id",
    "stat_text_raw",
    "stat_text",
    "flavour_text",
    "reminder_text",
    "connections",
]


def ensure_dirs() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    POE2DB_RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    METADATA_DIR.mkdir(parents=True, exist_ok=True)


def request_json(params: dict[str, Any]) -> dict[str, Any]:
    response = requests.get(
        POE2WIKI_API,
        params=params,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


def request_text(url: str) -> str:
    response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=60)
    response.raise_for_status()
    return response.text


def fetch_cargo_rows(refresh: bool = False) -> list[dict[str, Any]]:
    raw_path = RAW_DIR / "poe2_atlas_passive_skills.json"
    if raw_path.exists() and not refresh:
        return json.loads(raw_path.read_text(encoding="utf-8"))

    rows: list[dict[str, Any]] = []
    offset = 0
    limit = 500
    while True:
        payload = request_json(
            {
                "action": "cargoquery",
                "format": "json",
                "tables": "passive_skills",
                "fields": ",".join(PASSIVE_FIELDS),
                "where": "is_atlas_passive=1",
                "order_by": "atlas_sub_tree,id",
                "limit": limit,
                "offset": offset,
            }
        )
        batch = [item.get("title", {}) for item in payload.get("cargoquery", [])]
        rows.extend(batch)
        if len(batch) < limit:
            break
        offset += limit

    raw_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    return rows


def fetch_poe2db_page(refresh: bool = False) -> None:
    raw_path = POE2DB_RAW_DIR / "Atlas_passive_skill.html"
    if raw_path.exists() and not refresh:
        return
    raw_path.write_text(request_text(POE2DB_ATLAS_PAGE), encoding="utf-8")


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    text = html.unescape(str(value))
    return text.replace("<br>", " | ").replace("<br />", " | ").replace("\r", "").replace("\n", " ").strip()


def bool_text(value: Any) -> str:
    if value in (True, "1", 1):
        return "true"
    if value in (False, "0", 0):
        return "false"
    return ""


def node_type(row: dict[str, Any]) -> str:
    if row.get("is starting node") == "1":
        return "start"
    if row.get("is keystone") == "1":
        return "keystone"
    if row.get("is notable") == "1":
        return "notable"
    if row.get("is multiple choice") == "1":
        return "choice"
    if row.get("is multiple choice option") == "1":
        return "choice_option"
    if row.get("is jewel socket") == "1":
        return "jewel_socket"
    if row.get("is icon only") == "1":
        return "icon_only"
    return "small"


def normalize_nodes(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for row in rows:
        connections = clean_text(row.get("connections"))
        stat_text_raw = clean_text(row.get("stat text raw"))
        normalized.append(
            {
                "id": clean_text(row.get("id")),
                "int_id": clean_text(row.get("int id")),
                "name": clean_text(row.get("name")),
                "page_name": clean_text(row.get("page name")),
                "main_page": clean_text(row.get("main page")),
                "atlas_sub_tree": clean_text(row.get("atlas sub tree")) or "Generic",
                "type": node_type(row),
                "frame": clean_text(row.get("frame")),
                "icon": clean_text(row.get("icon")),
                "stat_text_raw": stat_text_raw,
                "stat_text": clean_text(row.get("stat text")),
                "flavour_text": clean_text(row.get("flavour text")),
                "reminder_text": clean_text(row.get("reminder text")),
                "connections": connections,
                "connection_count": len([item for item in connections.split(",") if item.strip()]),
                "skill_points": clean_text(row.get("skill points")),
                "weapon_set_points": clean_text(row.get("weapon set points")),
                "buff_id": clean_text(row.get("buff id")),
                "is_in_game": bool_text(row.get("is in game")),
                "is_atlas_passive": bool_text(row.get("is atlas passive")),
                "is_keystone": bool_text(row.get("is keystone")),
                "is_notable": bool_text(row.get("is notable")),
                "is_starting_node": bool_text(row.get("is starting node")),
                "is_multiple_choice": bool_text(row.get("is multiple choice")),
                "is_multiple_choice_option": bool_text(row.get("is multiple choice option")),
                "is_icon_only": bool_text(row.get("is icon only")),
                "is_jewel_socket": bool_text(row.get("is jewel socket")),
                "is_attribute": bool_text(row.get("is attribute")),
                "is_free": bool_text(row.get("is free")),
            }
        )
    return normalized


def normalize_edges(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    node_names = {node["id"]: node["name"] for node in nodes}
    edges: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for node in nodes:
        from_id = node["id"]
        for target in node["connections"].split(","):
            to_id = target.strip()
            if not to_id:
                continue
            edge_key = tuple(sorted((from_id, to_id)))
            if edge_key in seen:
                continue
            seen.add(edge_key)
            edges.append(
                {
                    "from_id": from_id,
                    "from_name": node_names.get(from_id, ""),
                    "to_id": to_id,
                    "to_name": node_names.get(to_id, ""),
                }
            )
    return edges


def write_csv(rows: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def count_by(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        key = row.get(field) or "(blank)"
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def build_outputs(refresh: bool = False) -> dict[str, Any]:
    raw_rows = fetch_cargo_rows(refresh=refresh)
    fetch_poe2db_page(refresh=refresh)

    nodes = normalize_nodes(raw_rows)
    edges = normalize_edges(nodes)
    write_csv(nodes, PROCESSED_DIR / "poe2_atlas_passive_nodes.csv")
    write_csv(edges, PROCESSED_DIR / "poe2_atlas_passive_edges.csv")

    summary = {
        "snapshot_time_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": "poe2wiki Cargo passive_skills table, filtered by is_atlas_passive=1",
        "source_api": POE2WIKI_API,
        "poe2db_reference_page": POE2DB_ATLAS_PAGE,
        "node_rows": len(nodes),
        "edge_rows": len(edges),
        "sub_tree_counts": count_by(nodes, "atlas_sub_tree"),
        "node_type_counts": count_by(nodes, "type"),
        "outputs": {
            "raw_json": str((RAW_DIR / "poe2_atlas_passive_skills.json").relative_to(ROOT)),
            "poe2db_html": str((POE2DB_RAW_DIR / "Atlas_passive_skill.html").relative_to(ROOT)),
            "nodes_csv": str((PROCESSED_DIR / "poe2_atlas_passive_nodes.csv").relative_to(ROOT)),
            "edges_csv": str((PROCESSED_DIR / "poe2_atlas_passive_edges.csv").relative_to(ROOT)),
        },
        "known_gap": "This source includes passive text and connections, but not official atlas tree coordinates.",
    }
    (METADATA_DIR / "poe2_atlas_passive_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch and normalize PoE2 Atlas passive tree data.")
    parser.add_argument("--refresh", action="store_true", help="Re-download poe2wiki and PoE2DB raw data.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ensure_dirs()
    summary = build_outputs(refresh=args.refresh)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
