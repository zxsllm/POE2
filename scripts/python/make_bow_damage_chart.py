from pathlib import Path
import csv
import re

from bs4 import BeautifulSoup
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[2]
HTML_FILE = ROOT / "data" / "raw" / "poe2db" / "Bows.html"
CSV_FILE = ROOT / "data" / "processed" / "reports" / "bow" / "bows_damage.csv"
PNG_FILE = ROOT / "reports" / "bow" / "assets" / "poe2_bows_avg_physical_damage.png"


def extract_bows(html_path: Path):
    soup = BeautifulSoup(html_path.read_text(encoding="utf-8"), "html.parser")
    section = soup.find(id="BowsItem")
    if section is None:
        raise RuntimeError("Could not find #BowsItem section in HTML")

    bows = []
    item_cols = section.select("div.row.row-cols-1.row-cols-lg-2.g-2 > div.col")
    for col in item_cols:
        names = [
            a.get_text(" ", strip=True)
            for a in col.select("a.whiteitem.Bow")
            if a.get_text(" ", strip=True)
        ]
        name = names[0] if names else None
        damage_el = col.select_one("span.colourPhysicalDamage")
        if not name or damage_el is None:
            continue

        damage_match = re.search(r"(\d+)\s*-\s*(\d+)", damage_el.get_text(strip=True))
        if damage_match is None:
            continue

        requirement_el = col.select_one("div.requirements")
        requirement_text = requirement_el.get_text(" ", strip=True) if requirement_el else ""
        level_match = re.search(r"Level\s+(\d+)", requirement_text)
        level = int(level_match.group(1)) if level_match else 1

        min_damage, max_damage = map(int, damage_match.groups())
        avg_damage = (min_damage + max_damage) / 2
        bows.append(
            {
                "level": level,
                "name": name,
                "physical_damage": f"{min_damage}-{max_damage}",
                "min_physical_damage": min_damage,
                "max_physical_damage": max_damage,
                "avg_physical_damage": avg_damage,
            }
        )

    return sorted(bows, key=lambda row: (row["level"], row["avg_physical_damage"], row["name"]))


def write_csv(rows, csv_path: Path):
    fieldnames = [
        "level",
        "name",
        "physical_damage",
        "min_physical_damage",
        "max_physical_damage",
        "avg_physical_damage",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def draw_chart(rows, png_path: Path):
    levels = [row["level"] for row in rows]
    averages = [row["avg_physical_damage"] for row in rows]

    plt.style.use("seaborn-v0_8-whitegrid")
    fig, ax = plt.subplots(figsize=(22, 12), dpi=150)
    ax.plot(levels, averages, color="#c48a3a", linewidth=2.2, marker="o", markersize=5)

    duplicate_index = {}
    for index, row in enumerate(rows):
        same_level_index = duplicate_index.get(row["level"], 0)
        duplicate_index[row["level"]] = same_level_index + 1
        offset_x = (-18, 18, 0)[same_level_index % 3]
        offset_y = 10 if index % 2 == 0 else -16
        ax.annotate(
            row["name"],
            (row["level"], row["avg_physical_damage"]),
            textcoords="offset points",
            xytext=(offset_x, offset_y),
            ha="center",
            va="bottom" if offset_y > 0 else "top",
            fontsize=8,
            color="#222222",
            bbox={"boxstyle": "round,pad=0.18", "fc": "white", "ec": "none", "alpha": 0.75},
        )

    ax.set_title("POE2 Bows: Average Physical Damage by Required Level", fontsize=16, pad=18)
    ax.set_xlabel("Required Level", fontsize=12)
    ax.set_ylabel("Average Physical Damage", fontsize=12)
    ax.set_xticks(sorted(set(levels)))
    ax.tick_params(axis="x", labelrotation=45)
    ax.margins(x=0.04, y=0.12)

    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)

    fig.tight_layout()
    fig.savefig(png_path, bbox_inches="tight")
    plt.close(fig)


def main():
    rows = extract_bows(HTML_FILE)
    if not rows:
        raise RuntimeError("No Bows Item rows found")
    write_csv(rows, CSV_FILE)
    draw_chart(rows, PNG_FILE)
    print(f"Wrote {CSV_FILE}")
    print(f"Wrote {PNG_FILE}")


if __name__ == "__main__":
    main()
