from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests


ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw" / "poe2_skilltree"
PROCESSED_DIR = ROOT / "data" / "processed" / "passive_tree"
METADATA_DIR = ROOT / "data" / "processed" / "metadata"

REPOSITORY = "grindinggear/poe2-skilltree-export"
BRANCH = "main"
RAW_DATA_URL = f"https://raw.githubusercontent.com/{REPOSITORY}/{BRANCH}/data.json"
LATEST_RELEASE_URL = f"https://api.github.com/repos/{REPOSITORY}/releases/latest"
USER_AGENT = "Mozilla/5.0 (compatible; POE2LocalResearch/1.0; +local-skilltree-script)"


def ensure_dirs() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    METADATA_DIR.mkdir(parents=True, exist_ok=True)


def request_json(url: str) -> Any:
    response = requests.get(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


def fetch_json(url: str, path: Path, refresh: bool = False) -> Any:
    if path.exists() and not refresh:
        return json.loads(path.read_text(encoding="utf-8"))

    data = request_json(url)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data


def as_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float, str)):
        return str(value)
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def join_values(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return "|".join(as_text(item) for item in value)
    return as_text(value)


def write_csv(rows: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return

    fieldnames: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            if key not in seen:
                fieldnames.append(key)
                seen.add(key)

    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def node_type(node: dict[str, Any]) -> str:
    if node.get("isKeystone"):
        return "keystone"
    if node.get("isMastery"):
        return "mastery"
    if node.get("isNotable"):
        return "notable"
    if node.get("isJewelSocket"):
        return "jewel_socket"
    if node.get("isAscendancyStart"):
        return "ascendancy_start"
    if node.get("isGenericAttribute"):
        return "attribute"
    if node.get("ascendancyId"):
        return "ascendancy_small"
    if not node.get("name") and not node.get("stats"):
        return "connector"
    return "small"


def flatten_nodes(data: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    nodes = data.get("nodes", {})
    for node_key, node in nodes.items():
        if not isinstance(node, dict):
            continue

        known_keys = {
            "activeEffectImage",
            "ascendancyId",
            "edges",
            "flavourText",
            "grantedPassivePoints",
            "grantedSkill",
            "group",
            "icon",
            "id",
            "in",
            "isAscendancyStart",
            "isGenericAttribute",
            "isJewelSocket",
            "isKeystone",
            "isMastery",
            "isNotable",
            "keystonesInRadius",
            "name",
            "orbit",
            "orbitIndex",
            "out",
            "recipe",
            "reminderText",
            "skill",
            "stats",
            "x",
            "y",
        }
        granted_skill = node.get("grantedSkill") if isinstance(node.get("grantedSkill"), dict) else {}
        extra = {key: value for key, value in node.items() if key not in known_keys}

        rows.append(
            {
                "node_key": node_key,
                "skill": node.get("skill", ""),
                "id": node.get("id", ""),
                "name": node.get("name", ""),
                "type": node_type(node),
                "ascendancy_id": node.get("ascendancyId", ""),
                "group": node.get("group", ""),
                "orbit": node.get("orbit", ""),
                "orbit_index": node.get("orbitIndex", ""),
                "x": node.get("x", ""),
                "y": node.get("y", ""),
                "stats": join_values(node.get("stats")),
                "stat_count": len(node.get("stats") or []),
                "recipe": join_values(node.get("recipe")),
                "flavour_text": join_values(node.get("flavourText")),
                "reminder_text": join_values(node.get("reminderText")),
                "granted_passive_points": node.get("grantedPassivePoints", ""),
                "granted_skill_name": granted_skill.get("name", ""),
                "granted_skill_type_line": granted_skill.get("typeLine", ""),
                "granted_skill_base_type": granted_skill.get("baseType", ""),
                "is_notable": as_text(node.get("isNotable")),
                "is_keystone": as_text(node.get("isKeystone")),
                "is_mastery": as_text(node.get("isMastery")),
                "is_jewel_socket": as_text(node.get("isJewelSocket")),
                "is_ascendancy_start": as_text(node.get("isAscendancyStart")),
                "is_generic_attribute": as_text(node.get("isGenericAttribute")),
                "keystones_in_radius": join_values(node.get("keystonesInRadius")),
                "out": join_values(node.get("out")),
                "in": join_values(node.get("in")),
                "edges": join_values(node.get("edges")),
                "icon": node.get("icon", ""),
                "active_effect_image": node.get("activeEffectImage", ""),
                "extra_json": as_text(extra) if extra else "",
            }
        )
    return rows


def flatten_edges(data: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    nodes = data.get("nodes", {})
    for index, edge in enumerate(data.get("edges", [])):
        if not isinstance(edge, dict):
            continue
        from_key = as_text(edge.get("from"))
        to_key = as_text(edge.get("to"))
        rows.append(
            {
                "edge_index": index,
                "from_node": from_key,
                "to_node": to_key,
                "from_name": (nodes.get(from_key) or {}).get("name", "") if isinstance(nodes, dict) else "",
                "to_name": (nodes.get(to_key) or {}).get("name", "") if isinstance(nodes, dict) else "",
            }
        )
    return rows


def flatten_groups(data: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for group_key, group in data.get("groups", {}).items():
        if not isinstance(group, dict):
            continue
        rows.append(
            {
                "group_key": group_key,
                "x": group.get("x", ""),
                "y": group.get("y", ""),
                "orbits": join_values(group.get("orbits")),
                "nodes": join_values(group.get("nodes")),
                "node_count": len(group.get("nodes") or []),
            }
        )
    return rows


def flatten_classes(data: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for class_index, class_data in enumerate(data.get("classes", [])):
        if not isinstance(class_data, dict):
            continue
        rows.append(
            {
                "class_index": class_index,
                "kind": "base_class",
                "id": "",
                "name": class_data.get("name", ""),
                "base_class": class_data.get("name", ""),
                "base_str": class_data.get("base_str", ""),
                "base_dex": class_data.get("base_dex", ""),
                "base_int": class_data.get("base_int", ""),
                "image": class_data.get("image", ""),
                "offset_x": class_data.get("image_offset_x", ""),
                "offset_y": class_data.get("image_offset_y", ""),
                "flavour_text": "",
                "override_pairs": as_text(class_data.get("overridePairs")),
            }
        )
        for ascendancy in class_data.get("ascendancies") or []:
            if not isinstance(ascendancy, dict):
                continue
            rows.append(
                {
                    "class_index": class_index,
                    "kind": "ascendancy",
                    "id": ascendancy.get("id", ""),
                    "name": ascendancy.get("name", ""),
                    "base_class": class_data.get("name", ""),
                    "base_str": "",
                    "base_dex": "",
                    "base_int": "",
                    "image": ascendancy.get("image", ""),
                    "offset_x": ascendancy.get("offsetX", ""),
                    "offset_y": ascendancy.get("offsetY", ""),
                    "flavour_text": ascendancy.get("flavourText", ""),
                    "override_pairs": as_text(ascendancy.get("overridePairs")),
                }
            )
    return rows


def count_by(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        key = as_text(row.get(field)) or "(blank)"
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def build_outputs(data: dict[str, Any], release: dict[str, Any]) -> dict[str, Any]:
    node_rows = flatten_nodes(data)
    edge_rows = flatten_edges(data)
    group_rows = flatten_groups(data)
    class_rows = flatten_classes(data)

    write_csv(node_rows, PROCESSED_DIR / "poe2_skilltree_nodes.csv")
    write_csv(edge_rows, PROCESSED_DIR / "poe2_skilltree_edges.csv")
    write_csv(group_rows, PROCESSED_DIR / "poe2_skilltree_groups.csv")
    write_csv(class_rows, PROCESSED_DIR / "poe2_skilltree_classes.csv")

    summary = {
        "snapshot_time_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source_repository": REPOSITORY,
        "source_branch": BRANCH,
        "source_data_url": RAW_DATA_URL,
        "latest_release_tag": release.get("tag_name", ""),
        "latest_release_name": release.get("name", ""),
        "latest_release_published_at": release.get("published_at", ""),
        "latest_release_url": release.get("html_url", ""),
        "tree": data.get("tree", ""),
        "node_rows": len(node_rows),
        "edge_rows": len(edge_rows),
        "group_rows": len(group_rows),
        "class_rows": len(class_rows),
        "jewel_slot_count": len(data.get("jewelSlots") or []),
        "node_type_counts": count_by(node_rows, "type"),
        "ascendancy_node_counts": count_by(
            [row for row in node_rows if row.get("ascendancy_id")],
            "ascendancy_id",
        ),
        "outputs": {
            "nodes_csv": str((PROCESSED_DIR / "poe2_skilltree_nodes.csv").relative_to(ROOT)),
            "edges_csv": str((PROCESSED_DIR / "poe2_skilltree_edges.csv").relative_to(ROOT)),
            "groups_csv": str((PROCESSED_DIR / "poe2_skilltree_groups.csv").relative_to(ROOT)),
            "classes_csv": str((PROCESSED_DIR / "poe2_skilltree_classes.csv").relative_to(ROOT)),
            "raw_data_json": str((RAW_DIR / "data.json").relative_to(ROOT)),
            "release_json": str((RAW_DIR / "latest_release.json").relative_to(ROOT)),
        },
    }
    (METADATA_DIR / "poe2_skilltree_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch and normalize GGG PoE2 passive skill tree data.")
    parser.add_argument("--refresh", action="store_true", help="Re-download raw GitHub data.")
    parser.add_argument("--skip-fetch", action="store_true", help="Only parse existing raw files.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ensure_dirs()

    raw_data_path = RAW_DIR / "data.json"
    release_path = RAW_DIR / "latest_release.json"
    if args.skip_fetch:
        data = json.loads(raw_data_path.read_text(encoding="utf-8"))
        release = json.loads(release_path.read_text(encoding="utf-8")) if release_path.exists() else {}
    else:
        data = fetch_json(RAW_DATA_URL, raw_data_path, refresh=args.refresh)
        release = fetch_json(LATEST_RELEASE_URL, release_path, refresh=args.refresh)

    summary = build_outputs(data, release)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
