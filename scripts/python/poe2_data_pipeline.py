from __future__ import annotations

import argparse
import csv
import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"

POE2DB_BASE = "https://poe2db.tw/us/"
POE2DB_MODIFIERS_URL = urljoin(POE2DB_BASE, "Modifiers")
PATH_OF_CRAFTING_BASE = "https://pathofcrafting.net/"
PATH_OF_CRAFTING_MODIFIERS = urljoin(PATH_OF_CRAFTING_BASE, "data/modifiers.json")

USER_AGENT = "Mozilla/5.0 (compatible; POE2LocalResearch/1.0; +local-report-script)"
REQUEST_DELAY_SECONDS = 0.35

STATIC_MODIFIER_PAGES = [
    "Claws",
    "Daggers",
    "Wands",
    "One_Hand_Swords",
    "One_Hand_Axes",
    "One_Hand_Maces",
    "Sceptres",
    "Spears",
    "Flails",
    "Bows",
    "Staves",
    "Two_Hand_Swords",
    "Two_Hand_Axes",
    "Two_Hand_Maces",
    "Quarterstaves",
    "Crossbows",
    "Traps",
    "Talismans",
    "Amulets",
    "Rings",
    "Belts",
    "Gloves_str",
    "Gloves_dex",
    "Gloves_int",
    "Gloves_str_dex",
    "Gloves_str_int",
    "Gloves_dex_int",
    "Boots_str",
    "Boots_dex",
    "Boots_int",
    "Boots_str_dex",
    "Boots_str_int",
    "Boots_dex_int",
    "Body_Armours_str",
    "Body_Armours_dex",
    "Body_Armours_int",
    "Body_Armours_str_dex",
    "Body_Armours_str_int",
    "Body_Armours_dex_int",
    "Body_Armours_str_dex_int",
    "Helmets_str",
    "Helmets_dex",
    "Helmets_int",
    "Helmets_str_dex",
    "Helmets_str_int",
    "Helmets_dex_int",
    "Quivers",
    "Shields_str",
    "Shields_str_dex",
    "Shields_str_int",
    "Bucklers",
    "Foci",
    "Ruby",
    "Emerald",
    "Sapphire",
    "Time-Lost_Ruby",
    "Time-Lost_Emerald",
    "Time-Lost_Sapphire",
    "Life_Flasks",
    "Mana_Flasks",
    "Charms",
    "Urn_Relic",
    "Amphora_Relic",
    "Vase_Relic",
    "Seal_Relic",
    "Coffer_Relic",
    "Tapestry_Relic",
    "Incense_Relic",
    "Breach_Tablet",
    "Expedition_Tablet",
    "Delirium_Tablet",
    "Ritual_Tablet",
    "Irradiated_Tablet",
    "Overseer_Tablet",
    "Abyss_Tablet",
    "Temple_Tablet",
    "Waystones_low_tier",
    "Waystones_mid_tier",
    "Waystones_top_tier",
]


@dataclass(frozen=True)
class DownloadResult:
    url: str
    path: Path
    fetched: bool


def ensure_dirs() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def safe_filename(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_")


def request_text(url: str) -> str:
    response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=45)
    response.raise_for_status()
    return response.text


def download_text(url: str, path: Path, refresh: bool = False) -> DownloadResult:
    if path.exists() and not refresh:
        return DownloadResult(url=url, path=path, fetched=False)

    text = request_text(url)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    time.sleep(REQUEST_DELAY_SECONDS)
    return DownloadResult(url=url, path=path, fetched=True)


def download_json(url: str, path: Path, refresh: bool = False) -> DownloadResult:
    if path.exists() and not refresh:
        return DownloadResult(url=url, path=path, fetched=False)

    response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=45)
    response.raise_for_status()
    data = response.json()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    time.sleep(REQUEST_DELAY_SECONDS)
    return DownloadResult(url=url, path=path, fetched=True)


def bracket_extract_json_object(text: str, marker: str) -> dict[str, Any] | None:
    marker_index = text.find(marker)
    if marker_index < 0:
        return None

    start = text.find("{", marker_index)
    if start < 0:
        return None

    level = 0
    in_string = False
    escaped = False
    end = None
    for index in range(start, len(text)):
        char = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
        elif char == "{":
            level += 1
        elif char == "}":
            level -= 1
            if level == 0:
                end = index + 1
                break

    if end is None:
        return None

    return json.loads(text[start:end])


def html_to_text(value: Any) -> str:
    if value is None:
        return ""
    soup = BeautifulSoup(str(value), "html.parser")
    text = soup.get_text(" ", strip=True)
    return normalize_text(text)


def normalize_text(text: str) -> str:
    return (
        text.replace("\u00a0", " ")
        .replace("бк", "-")
        .replace("—", "-")
        .replace("–", "-")
        .replace("  ", " ")
        .strip()
    )


def listify(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return "|".join(html_to_text(item) for item in value)
    return html_to_text(value)


def discover_modifier_pages(refresh: bool = False) -> list[str]:
    result = download_text(POE2DB_MODIFIERS_URL, RAW_DIR / "poe2db" / "Modifiers.html", refresh)
    soup = BeautifulSoup(result.path.read_text(encoding="utf-8"), "html.parser")
    discovered: list[str] = []
    for link in soup.select("a[href]"):
        href = link.get("href", "").strip()
        text = link.get_text(" ", strip=True)
        if href.startswith("/us/"):
            href = href.removeprefix("/us/")
        href = href.split("#", 1)[0].strip("/")
        if not href or href.startswith(("http", "#")):
            continue
        if text in {"Modifiers", "Quality", "Liquid Emotions", "Corrupted", "Desecrated Modifiers"}:
            continue
        if re.search(r"(Weapons|Jewellery|Gloves|Boots|Armours|Helmets|Off-hand|Jewels|Flasks|Relics|Tablet|Waystones)$", text):
            continue
        if href not in discovered and href in STATIC_MODIFIER_PAGES:
            discovered.append(href)
    for page in STATIC_MODIFIER_PAGES:
        if page not in discovered:
            discovered.append(page)
    return discovered


def fetch_poe2db_pages(pages: list[str], refresh: bool = False) -> list[DownloadResult]:
    results = []
    for page in pages:
        url = urljoin(POE2DB_BASE, page)
        path = RAW_DIR / "poe2db" / f"{safe_filename(page)}.html"
        try:
            results.append(download_text(url, path, refresh))
        except requests.HTTPError as error:
            print(f"  skipped {url}: {error}")
    return results


def parse_modsview(path: Path) -> dict[str, Any] | None:
    html = path.read_text(encoding="utf-8")
    return bracket_extract_json_object(html, "new ModsView(")


def flatten_poe2db_mods(raw_data: dict[str, Any]) -> list[dict[str, Any]]:
    baseitem = raw_data.get("baseitem", {})
    item_class = html_to_text(baseitem.get("link_name")) or baseitem.get("href", "")
    rows: list[dict[str, Any]] = []
    ignored = {"baseitem", "config", "gen", "opt"}

    for source_group, mods in raw_data.items():
        if source_group in ignored or not isinstance(mods, list):
            continue
        for mod in mods:
            if not isinstance(mod, dict):
                continue
            rows.append(
                {
                    "item_class": item_class,
                    "item_class_href": baseitem.get("href", ""),
                    "source_group": source_group,
                    "name": html_to_text(mod.get("Name")),
                    "level": mod.get("Level", ""),
                    "generation_type": mod.get("ModGenerationTypeID", ""),
                    "families": "|".join(mod.get("ModFamilyList", []) or []),
                    "drop_chance": mod.get("DropChance", ""),
                    "text": html_to_text(mod.get("str")),
                    "tags": listify(mod.get("mod_no")),
                    "fossil_tags": "|".join(mod.get("fossil_no", []) or []),
                    "spawn_tags": "|".join(mod.get("spawn_no", []) or []),
                    "adds_tags": "|".join(mod.get("adds_no", []) or []),
                    "code": mod.get("Code", ""),
                    "type": mod.get("type", ""),
                    "is_perfect": mod.get("IsPerfect", ""),
                    "hover": mod.get("hover", ""),
                }
            )
    return rows


def parse_base_items(path: Path) -> list[dict[str, Any]]:
    html = path.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")
    rows: list[dict[str, Any]] = []

    for card in soup.select("div.col"):
        links = [link for link in card.select("a.whiteitem") if link.get_text(" ", strip=True)]
        link = links[0] if links else None
        if not link:
            continue

        name = link.get_text(" ", strip=True)
        if not name:
            continue

        properties: dict[str, str] = {}
        for prop in card.select("div.property"):
            text = normalize_text(prop.get_text(" ", strip=True))
            if ":" in text:
                key, value = text.split(":", 1)
                properties[normalize_text(key)] = normalize_text(value)

        requirement_text = ""
        requirement = card.select_one("div.requirements")
        if requirement:
            requirement_text = normalize_text(requirement.get_text(" ", strip=True).replace("Requires:", ""))

        implicits = [
            normalize_text(node.get_text(" ", strip=True))
            for node in card.select("div.implicitMod")
            if normalize_text(node.get_text(" ", strip=True))
        ]

        level_match = re.search(r"Level\s+(\d+)", requirement_text)
        dex_match = re.search(r"(\d+)\s+Dex", requirement_text)
        physical_match = re.search(r"(\d+)\s*-\s*(\d+)", properties.get("Physical Damage", ""))

        min_phys = max_phys = avg_phys = ""
        if physical_match:
            min_phys = int(physical_match.group(1))
            max_phys = int(physical_match.group(2))
            avg_phys = (min_phys + max_phys) / 2

        rows.append(
            {
                "name": name,
                "href": link.get("href", ""),
                "page": path.stem,
                "physical_damage": properties.get("Physical Damage", ""),
                "min_physical_damage": min_phys,
                "max_physical_damage": max_phys,
                "avg_physical_damage": avg_phys,
                "critical_hit_chance": properties.get("Critical Hit Chance", ""),
                "attacks_per_second": properties.get("Attacks per Second", ""),
                "requirements": requirement_text,
                "required_level": int(level_match.group(1)) if level_match else "",
                "required_dex": int(dex_match.group(1)) if dex_match else "",
                "implicit": " | ".join(implicits),
            }
        )

    return rows


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


def write_json(data: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def build_outputs(poe2db_pages: list[str]) -> dict[str, int]:
    all_mods: list[dict[str, Any]] = []
    all_bases: list[dict[str, Any]] = []
    parsed_pages = 0

    for page in poe2db_pages:
        path = RAW_DIR / "poe2db" / f"{safe_filename(page)}.html"
        if not path.exists():
            continue
        raw_data = parse_modsview(path)
        if raw_data:
            all_mods.extend(flatten_poe2db_mods(raw_data))
            parsed_pages += 1
        all_bases.extend(parse_base_items(path))

    write_json(all_mods, PROCESSED_DIR / "poe2db_mods.json")
    write_csv(all_mods, PROCESSED_DIR / "poe2db_mods.csv")
    write_json(all_bases, PROCESSED_DIR / "poe2db_base_items.json")
    write_csv(all_bases, PROCESSED_DIR / "poe2db_base_items.csv")

    bow_mods = [row for row in all_mods if row["item_class_href"] == "Bows"]
    bow_bases = [row for row in all_bases if row["page"] == "Bows"]
    write_json(bow_mods, PROCESSED_DIR / "poe2db_bow_mods.json")
    write_csv(bow_mods, PROCESSED_DIR / "poe2db_bow_mods.csv")
    write_json(bow_bases, PROCESSED_DIR / "poe2db_bow_bases.json")
    write_csv(bow_bases, PROCESSED_DIR / "poe2db_bow_bases.csv")

    poc_path = RAW_DIR / "pathofcrafting" / "modifiers.json"
    poc_count = 0
    if poc_path.exists():
        poc_mods = json.loads(poc_path.read_text(encoding="utf-8"))
        poc_count = len(poc_mods)
        write_csv(poc_mods, PROCESSED_DIR / "pathofcrafting_modifiers.csv")

    summary = {
        "poe2db_pages": len(poe2db_pages),
        "poe2db_pages_with_mods": parsed_pages,
        "poe2db_mod_rows": len(all_mods),
        "poe2db_base_item_rows": len(all_bases),
        "poe2db_bow_mod_rows": len(bow_mods),
        "poe2db_bow_base_rows": len(bow_bases),
        "pathofcrafting_modifier_rows": poc_count,
    }
    write_json(summary, PROCESSED_DIR / "summary.json")
    return summary


def fetch_pathofcrafting(refresh: bool = False) -> list[DownloadResult]:
    results = [
        download_text(
            PATH_OF_CRAFTING_BASE,
            RAW_DIR / "pathofcrafting" / "index.html",
            refresh,
        ),
        download_json(
            PATH_OF_CRAFTING_MODIFIERS,
            RAW_DIR / "pathofcrafting" / "modifiers.json",
            refresh,
        ),
    ]

    index = (RAW_DIR / "pathofcrafting" / "index.html").read_text(encoding="utf-8")
    for asset in sorted(set(re.findall(r'(?:src|href)="(/assets/[^"]+)"', index))):
        results.append(
            download_text(
                urljoin(PATH_OF_CRAFTING_BASE, asset),
                RAW_DIR / "pathofcrafting" / safe_filename(asset.lstrip("/")),
                refresh,
            )
        )
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch and normalize PoE2DB and Path of Crafting data.")
    parser.add_argument("--refresh", action="store_true", help="Re-download cached raw files.")
    parser.add_argument("--skip-fetch", action="store_true", help="Only parse existing raw files.")
    parser.add_argument(
        "--pages",
        nargs="*",
        default=None,
        help="Limit PoE2DB pages, e.g. Bows Quivers. Defaults to all known modifier pages.",
    )
    args = parser.parse_args()

    ensure_dirs()
    pages = args.pages or discover_modifier_pages(refresh=args.refresh and not args.skip_fetch)

    if not args.skip_fetch:
        print(f"Fetching Path of Crafting data...")
        poc_results = fetch_pathofcrafting(refresh=args.refresh)
        print(f"  {sum(result.fetched for result in poc_results)} files downloaded/cached")

        print(f"Fetching {len(pages)} PoE2DB pages...")
        poe_results = fetch_poe2db_pages(pages, refresh=args.refresh)
        print(f"  {sum(result.fetched for result in poe_results)} files downloaded/cached")

    summary = build_outputs(pages)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
