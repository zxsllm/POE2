from __future__ import annotations

import csv
import html
import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = ROOT / "data" / "processed"
REPORT_FILE = ROOT / "reports" / "poe2_bow_crafting_report.html"
CHART_FILE = ROOT / "reports" / "assets" / "poe2_bows_avg_physical_damage.png"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def num(value: Any, default: float = 0) -> float:
    try:
        if value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def draw_bow_chart(bases: list[dict[str, str]]) -> None:
    rows = [row for row in bases if row.get("avg_physical_damage")]
    rows.sort(key=lambda row: (num(row.get("required_level")), num(row.get("avg_physical_damage")), row.get("name", "")))

    levels = [num(row["required_level"]) for row in rows]
    averages = [num(row["avg_physical_damage"]) for row in rows]

    plt.style.use("seaborn-v0_8-whitegrid")
    fig, ax = plt.subplots(figsize=(22, 12), dpi=150)
    ax.plot(levels, averages, color="#c48a3a", linewidth=2.2, marker="o", markersize=5)

    duplicate_index: dict[float, int] = {}
    for index, row in enumerate(rows):
        level = num(row["required_level"])
        same_level_index = duplicate_index.get(level, 0)
        duplicate_index[level] = same_level_index + 1
        offset_x = (-20, 20, 0)[same_level_index % 3]
        offset_y = 11 if index % 2 == 0 else -18
        ax.annotate(
            row["name"],
            (level, num(row["avg_physical_damage"])),
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
    fig.savefig(CHART_FILE, bbox_inches="tight")
    plt.close(fig)


def top_bases(bases: list[dict[str, str]]) -> list[dict[str, str]]:
    priority = {
        "Gemini Bow": 100,
        "Warmonger Bow": 95,
        "Obliterator Bow": 90,
        "Guardian Bow": 86,
        "Fanatic Bow": 80,
        "Ironwood Shortbow": 70,
    }
    rows = []
    for row in bases:
        score = priority.get(row["name"], num(row.get("avg_physical_damage")))
        copied = dict(row)
        copied["score"] = str(score)
        rows.append(copied)
    return sorted(rows, key=lambda row: num(row["score"]), reverse=True)[:8]


def find_mods(mods: list[dict[str, str]], keywords: list[str], limit: int = 14) -> list[dict[str, str]]:
    matched = []
    lowered = [keyword.lower() for keyword in keywords]
    for row in mods:
        blob = " ".join([row.get("name", ""), row.get("text", ""), row.get("families", ""), row.get("source_group", "")]).lower()
        if any(keyword in blob for keyword in lowered):
            matched.append(row)
    matched.sort(key=lambda row: (row.get("source_group", ""), num(row.get("level")), row.get("name", "")))
    return matched[:limit]


def render_base_rows(rows: list[dict[str, str]]) -> str:
    lines = []
    for row in rows:
        lines.append(
            "<tr>"
            f"<td><strong>{esc(row['name'])}</strong></td>"
            f"<td>Lv {esc(row.get('required_level', ''))}<br>{esc(row.get('physical_damage', ''))}<br>{esc(row.get('attacks_per_second', ''))} APS</td>"
            f"<td>{esc(row.get('implicit', '')) or '-'}</td>"
            f"<td>{base_advice(row)}</td>"
            "</tr>"
        )
    return "\n".join(lines)


def base_advice(row: dict[str, str]) -> str:
    name = row["name"]
    if name == "Gemini Bow":
        return "额外箭机会，优先 ilvl 81+；暴击/攻速/高物理底可加价。"
    if name == "Warmonger Bow":
        return "通用高物理、高攻速，无负面，最适合批量物理弓。"
    if name == "Obliterator Bow":
        return "白板均伤高但有射程负面，只在底价便宜时做。"
    if name == "Guardian Bow":
        return "连锁清图卖点，适合清图向买家。"
    if name == "Fanatic Bow":
        return "隐藏混沌点伤，偏毒/混沌路线。"
    return "按当日成品价倒推，不要高价收冷门底。"


def render_mod_rows(rows: list[dict[str, str]]) -> str:
    lines = []
    for row in rows:
        lines.append(
            "<tr>"
            f"<td>{esc(row.get('source_group', ''))}</td>"
            f"<td>{esc(row.get('name', ''))}</td>"
            f"<td>Lv {esc(row.get('level', ''))}</td>"
            f"<td>{esc(row.get('text', ''))}</td>"
            f"<td>{esc(row.get('drop_chance', ''))}</td>"
            "</tr>"
        )
    return "\n".join(lines)


MATERIAL_CN = {
    "Orb of Augmentation": "增幅石",
    "Orb of Transmutation": "蜕变石",
    "Greater Orb of Transmutation": "高阶蜕变石",
    "Greater Orb of Augmentation": "高阶增幅石",
    "Perfect Orb of Transmutation": "完美蜕变石",
    "Perfect Orb of Augmentation": "完美增幅石",
    "Greater Essence of Abrasion": "高阶磨蚀精髓",
    "Greater Essence of Seeking": "高阶追寻精髓",
    "Perfect Essence of Battle": "完美战斗精髓",
    "Perfect Essence of Haste": "完美迅捷精髓",
    "Omen of Sinistral Necromancy": "左向死灵预兆",
    "Omen of the Liege": "君主预兆",
    "Omen of Greater Exaltation": "高阶崇高预兆",
    "Omen of Abyssal Echoes": "深渊回响预兆",
    "Greater Exalted Orb": "高阶崇高石",
    "Perfect Exalted Orb": "完美崇高石",
    "Ancient Jawbone": "远古颚骨",
    "Preserved Jawbone": "保存完好的颚骨",
    "Artificer's Orb": "工匠石 / 打孔石",
    "Greater Iron Rune": "高阶铁符文",
    "Countess Seske's Rune of Archery": "瑟丝克伯爵夫人的箭术符文",
    "Perfect Iron Rune": "完美铁符文",
    "Architect's Orb": "建筑师石",
    "Chaos Orb": "混沌石",
    "Greater Chaos Orb": "高阶混沌石",
    "Exalted Orb": "崇高石",
    "Orb of Annulment": "剥离石",
    "Blacksmith's Whetstone": "铁匠磨刀石",
}


CRAFT_RECIPES = [
    {
        "name": "0.5 非暴击弓：高物理转元素底",
        "source": "0.5 Ice Shot Deadeye，May 31 2026。中文理解：先拿到高物理百分比魔法底，再用高阶磨蚀精髓补物理点伤，后面转成高物理+元素点伤的非暴击弓。",
        "steps": [
            {
                "label": "起手：直接买合格魔法底，或从 normal 自己打",
                "materials": [],
                "manual": "当前输入价：normal ilvl>75 Obliterator Bow = 8E；>=135% increased Physical Damage 的 Magic Obliterator Bow = 10div。按下面“基底起手方案”表决定。",
            },
            {
                "label": "固定补物理点伤，并把魔法弓升成稀有",
                "materials": [("Greater Essence of Abrasion", 1)],
                "note": "高阶磨蚀精髓 / Greater Essence of Abrasion：给弓固定加物理点伤。非暴击路线优先这个。",
            },
            {
                "label": "用深渊/预兆补高额点伤前缀",
                "materials": [("Omen of Sinistral Necromancy", 1), ("Ancient Jawbone", 1)],
                "note": "左向死灵预兆 + 远古颚骨：目标是揭示高额点伤，冰点伤最好。价格很贵，这一步决定是否值得继续。",
            },
            {
                "label": "补最后 2 个词缀",
                "materials": [("Greater Exalted Orb", 2), ("Omen of Greater Exaltation", 2)],
                "note": "高阶崇高石 + 高阶崇高预兆：尽量补可卖词缀。命中差就按半成品止损。",
            },
            {
                "label": "补孔与高阶铁符文",
                "materials": [("Artificer's Orb", 2), ("Greater Iron Rune", 2)],
                "optional": True,
                "note": "工匠石打孔，高阶铁符文加物理伤害。已有孔则扣掉对应工匠石。",
            },
        ],
    },
    {
        "name": "0.5 暴击弓：Crit Swap 起步",
        "source": "0.5 Ice Shot Deadeye，May 31 2026。中文理解：前半段仍要高物理百分比底，但第二步不补物理点伤，改用高阶追寻精髓拿暴击词缀，给 Crit Swap 用。",
        "steps": [
            {
                "label": "起手：直接买合格魔法底，或从 normal 自己打",
                "materials": [],
                "manual": "当前输入价同上：normal 底 8E；>=135% 物理百分比魔法底 10div。暴击路线也先要这个底。",
            },
            {
                "label": "固定补暴击词缀",
                "materials": [("Greater Essence of Seeking", 1)],
                "note": "高阶追寻精髓 / Greater Essence of Seeking：攻略说会给 T3 暴击，用于 Crit Swap。",
            },
            {
                "label": "用深渊/预兆补高额点伤前缀",
                "materials": [("Omen of Sinistral Necromancy", 1), ("Ancient Jawbone", 1)],
                "note": "优先高物理点伤；强元素点伤也能卖，但要看构筑需求。",
            },
            {
                "label": "补最后 2 个词缀",
                "materials": [("Greater Exalted Orb", 2), ("Omen of Greater Exaltation", 2)],
            },
            {
                "label": "补孔与高阶铁符文",
                "materials": [("Artificer's Orb", 2), ("Greater Iron Rune", 2)],
                "optional": True,
            },
        ],
    },
]

MARKET_ASSUMPTIONS = {
    "normal_obliterator_bow_exalted": 8.0,
    "phys_135_magic_obliterator_bow_divine": 10.0,
}


def load_prices() -> tuple[list[dict[str, str]], dict[str, dict[str, str]]]:
    path = PROCESSED_DIR / "poe_ninja_prices.csv"
    if not path.exists():
        return [], {}
    rows = read_csv(path)
    by_name = {row["name"].lower(): row for row in rows}
    return rows, by_name


def exalted_per_divine(prices_by_name: dict[str, dict[str, str]]) -> float:
    divine = prices_by_name.get("Divine Orb".lower())
    if divine:
        value = num(divine.get("exalted_value"))
        if value:
            return value
    exalted = prices_by_name.get("Exalted Orb".lower())
    value = num(exalted.get("divine_value")) if exalted else 0
    return 1 / value if value else 50.0


def material_label(name: str) -> str:
    cn = MATERIAL_CN.get(name, "")
    return f"{esc(cn)}<br><code>{esc(name)}</code>" if cn else f"<code>{esc(name)}</code>"


def format_value(value: float) -> str:
    if value == 0:
        return "0"
    if value >= 100:
        return f"{value:.1f}"
    if value >= 10:
        return f"{value:.2f}"
    if value >= 1:
        return f"{value:.3f}"
    return f"{value:.4f}"


def price_values(price: dict[str, str] | None, quantity: float) -> tuple[float | None, float | None, float | None]:
    if not price:
        return None, None, None
    divine = num(price.get("divine_value")) * quantity
    exalted = num(price.get("exalted_value")) * quantity
    chaos = num(price.get("chaos_value")) * quantity
    return divine, exalted, chaos


def render_material_price_table(prices_by_name: dict[str, dict[str, str]]) -> str:
    names = [
        "Orb of Transmutation",
        "Orb of Augmentation",
        "Greater Orb of Transmutation",
        "Greater Orb of Augmentation",
        "Perfect Orb of Transmutation",
        "Perfect Orb of Augmentation",
        "Greater Essence of Abrasion",
        "Greater Essence of Seeking",
        "Omen of Sinistral Necromancy",
        "Ancient Jawbone",
        "Omen of Greater Exaltation",
        "Greater Exalted Orb",
        "Perfect Exalted Orb",
        "Perfect Essence of Battle",
        "Perfect Essence of Haste",
        "Omen of the Liege",
        "Omen of Abyssal Echoes",
        "Artificer's Orb",
        "Greater Iron Rune",
        "Blacksmith's Whetstone",
    ]
    rows = []
    for name in names:
        price = prices_by_name.get(name.lower())
        if not price:
            rows.append(f"<tr><td>{material_label(name)}</td><td colspan=\"3\">poe.ninja 当前分类未返回</td></tr>")
            continue
        rows.append(
            "<tr>"
            f"<td>{material_label(name)}</td>"
            f"<td>{format_value(num(price.get('exalted_value')))} ex</td>"
            f"<td>{format_value(num(price.get('divine_value')))} div</td>"
            f"<td>{format_value(num(price.get('chaos_value')))} chaos</td>"
            "</tr>"
        )
    return "\n".join(rows)


def render_cost_tables(prices_by_name: dict[str, dict[str, str]]) -> str:
    direct_base_div = MARKET_ASSUMPTIONS["phys_135_magic_obliterator_bow_divine"]
    direct_base_ex = direct_base_div * exalted_per_divine(prices_by_name)
    direct_base_chaos = direct_base_div * num((prices_by_name.get("Divine Orb".lower()) or {}).get("chaos_value"))
    sections = []
    for recipe in CRAFT_RECIPES:
        cumulative_ex = 0.0
        cumulative_div = 0.0
        cumulative_chaos = 0.0
        rows = []
        for index, step in enumerate(recipe["steps"], start=1):
            materials = step.get("materials", [])
            step_ex = 0.0
            step_div = 0.0
            step_chaos = 0.0
            material_bits = []
            missing = False
            uses_direct_base = not materials and "起手" in step["label"]
            for material_name, quantity in materials:
                price = prices_by_name.get(material_name.lower())
                divine, exalted, chaos = price_values(price, float(quantity))
                quantity_text = format_value(float(quantity)).rstrip("0").rstrip(".")
                material_bits.append(f"{quantity_text} x {material_label(material_name)}")
                if divine is None or exalted is None or chaos is None:
                    missing = True
                    continue
                step_div += divine
                step_ex += exalted
                step_chaos += chaos

            if not step.get("optional"):
                if uses_direct_base:
                    step_ex += direct_base_ex
                    step_div += direct_base_div
                    step_chaos += direct_base_chaos
                cumulative_ex += step_ex
                cumulative_div += step_div
                cumulative_chaos += step_chaos

            if step.get("manual"):
                material_bits.append(f"<span class=\"muted\">{esc(step['manual'])}</span>")

            note = step.get("note", "")
            optional_text = "（可选）" if step.get("optional") else ""
            cost_text = f"{format_value(step_ex)} ex / {format_value(step_div)} div / {format_value(step_chaos)} chaos" if uses_direct_base else "需手动估价" if not materials else (
                "价格缺失" if missing else f"{format_value(step_ex)} ex / {format_value(step_div)} div / {format_value(step_chaos)} chaos"
            )
            cumulative_text = "不计入必做累计" if step.get("optional") else f"{format_value(cumulative_ex)} ex / {format_value(cumulative_div)} div"
            rows.append(
                "<tr>"
                f"<td>{index}. {esc(step['label'])} {optional_text}</td>"
                f"<td>{'<br>'.join(material_bits) if material_bits else '-'}</td>"
                f"<td>{cost_text}</td>"
                f"<td>{cumulative_text}</td>"
                f"<td>{esc(note)}</td>"
                "</tr>"
            )

        sections.append(
            f"""
    <h3>{esc(recipe["name"])}</h3>
    <p class="muted">{esc(recipe["source"])}</p>
    <table>
      <thead><tr><th>步骤</th><th>材料（中文 / English）</th><th>本步材料成本</th><th>必做累计</th><th>说明</th></tr></thead>
      <tbody>{''.join(rows)}</tbody>
    </table>
    <p><strong>必做材料小计：</strong>{format_value(cumulative_ex)} ex / {format_value(cumulative_div)} div / {format_value(cumulative_chaos)} chaos。<span class="muted">未包含弓底买入价、失败重做的基底损耗、成品降价空间。</span></p>
"""
        )
    return "\n".join(sections)


def pdps(
    percent_phys: float,
    flat_min: float = 0,
    flat_max: float = 0,
    quality: float = 0,
    rune_percent: float = 0,
    aps: float = 1.1,
    base_min: float = 62,
    base_max: float = 115,
) -> float:
    multiplier = 1 + (percent_phys + quality + rune_percent) / 100
    avg_hit = ((base_min + flat_min) + (base_max + flat_max)) / 2 * multiplier
    return avg_hit * aps


def render_dps_tables() -> str:
    phys_tiers = [
        ("Cruel / 残暴", "135-154%", (135 + 154) / 2),
        ("Tyrannical / 暴君", "155-169%", (155 + 169) / 2),
        ("Merciless / 无情", "170-179%", (170 + 179) / 2),
    ]
    flat_abrasion = ((16 + 24) / 2, (28 + 42) / 2)
    high_flat = ((26 + 39) / 2, (44 + 66) / 2)
    quality = 20
    two_greater_iron = 36

    noncrit_rows = []
    crit_rows = []
    for tier_name, tier_range, percent in phys_tiers:
        base_pdps = pdps(percent)
        noncrit_after_essence = pdps(percent, *flat_abrasion)
        noncrit_after_high_flat = pdps(percent, *flat_abrasion)
        noncrit_final = pdps(percent, *flat_abrasion, quality=quality, rune_percent=two_greater_iron)
        crit_after_seeking = pdps(percent)
        crit_after_high_flat = pdps(percent, *high_flat)
        crit_final = pdps(percent, *high_flat, quality=quality, rune_percent=two_greater_iron)
        noncrit_rows.append(
            "<tr>"
            f"<td>{esc(tier_name)}<br>{esc(tier_range)}</td>"
            f"<td>{format_value(base_pdps)}</td>"
            f"<td>{format_value(noncrit_after_essence)}</td>"
            f"<td>{format_value(noncrit_after_high_flat)}</td>"
            f"<td>{format_value(noncrit_final)}</td>"
            "</tr>"
        )
        crit_rows.append(
            "<tr>"
            f"<td>{esc(tier_name)}<br>{esc(tier_range)}</td>"
            f"<td>{format_value(base_pdps)}</td>"
            f"<td>{format_value(crit_after_seeking)}</td>"
            f"<td>{format_value(crit_after_high_flat)}</td>"
            f"<td>{format_value(crit_final)}</td>"
            "</tr>"
        )

    return f"""
  <section>
    <h2>每一步平均 pDPS</h2>
    <p class="muted">基础按 <code>Obliterator Bow</code> 白板 <code>62-115</code>、攻速 <code>1.1</code> 计算。同 T 级取区间平均。这里算的是物理 DPS / pDPS，不把火冰电点伤计入；如果深渊/预兆补出元素点伤，市场仍会看 eDPS/总 DPS，但和 pDPS 不是同一个数。</p>
    <h3>非暴击弓：高物理转元素底</h3>
    <table>
      <thead><tr><th>%物理前缀</th><th>买入魔法底</th><th>+ 高阶磨蚀精髓<br>16-24 / 28-42 物理点伤</th><th>深渊/预兆后<br>此处不计元素点伤</th><th>+20% 品质 + 2 个高阶铁符文</th></tr></thead>
      <tbody>{''.join(noncrit_rows)}</tbody>
    </table>
    <h3>暴击弓：Crit Swap</h3>
    <table>
      <thead><tr><th>%物理前缀</th><th>买入魔法底</th><th>+ 高阶追寻精髓<br>补暴击，不加 pDPS</th><th>若补到 Flaring 物理点伤<br>26-39 / 44-66</th><th>+20% 品质 + 2 个高阶铁符文</th></tr></thead>
      <tbody>{''.join(crit_rows)}</tbody>
    </table>
  </section>
"""


def row_family_key(row: dict[str, str]) -> str:
    return row.get("families") or f"{row.get('generation_type')}::{row.get('name')}::{row.get('text')}"


def eligible_normal_mods(
    bow_mods: list[dict[str, str]],
    max_level: int,
    min_mod_level: int,
) -> list[dict[str, str]]:
    by_family: dict[str, list[dict[str, str]]] = {}
    for row in bow_mods:
        if row.get("source_group") != "normal":
            continue
        if int(num(row.get("level"))) > max_level:
            continue
        if row.get("generation_type") not in {"1", "2"}:
            continue
        by_family.setdefault(row_family_key(row), []).append(row)

    eligible: list[dict[str, str]] = []
    for family_rows in by_family.values():
        high_rows = [row for row in family_rows if int(num(row.get("level"))) >= min_mod_level]
        if high_rows:
            eligible.extend(high_rows)
        else:
            # Greater/Perfect orbs keep low-level one-off mod families rather than deleting
            # a modifier type entirely. Use the highest tier in that family as the local fallback.
            eligible.append(max(family_rows, key=lambda row: int(num(row.get("level")))))
    return eligible


def bow_prefix_weight_model(
    bow_mods: list[dict[str, str]],
    min_ilvl: int,
    include_merciless: bool,
    min_mod_level: int,
) -> dict[str, float]:
    max_level = 999 if include_merciless else 81
    prefix_weight = 0.0
    suffix_weight = 0.0
    target_weight = 0.0
    target_rows = []
    for row in eligible_normal_mods(bow_mods, max_level, min_mod_level):
        level = int(num(row.get("level")))
        weight = num(row.get("drop_chance"))
        if row.get("generation_type") == "1":
            prefix_weight += weight
        elif row.get("generation_type") == "2":
            suffix_weight += weight
            continue
        else:
            continue
        text = row.get("text", "")
        if "increased Physical Damage" not in text or "Accuracy" in text:
            continue
        match = re_search_phys_range(text)
        if match and match[0] >= 135:
            target_weight += weight
            target_rows.append((row.get("name", ""), level, weight, text))

    probability = target_weight / prefix_weight if prefix_weight else 0
    return {
        "prefix_weight": prefix_weight,
        "suffix_weight": suffix_weight,
        "target_weight": target_weight,
        "probability": probability,
        "expected_attempts": 1 / probability if probability else 0,
        "target_rows": target_rows,
        "min_ilvl": min_ilvl,
        "min_mod_level": min_mod_level,
    }


def re_search_phys_range(text: str) -> tuple[int, int] | None:
    import re

    match = re.search(r"\((\d+)\s*-\s*(\d+)\)\s*%\s*increased Physical Damage", text)
    if not match:
        return None
    return int(match.group(1)), int(match.group(2))


def render_reset_model(bow_mods: list[dict[str, str]], prices_by_name: dict[str, dict[str, str]]) -> str:
    ex_per_div = exalted_per_divine(prices_by_name)

    normal_base_ex = MARKET_ASSUMPTIONS["normal_obliterator_bow_exalted"]
    bought_phys_div = MARKET_ASSUMPTIONS["phys_135_magic_obliterator_bow_divine"]
    bought_phys_ex = bought_phys_div * ex_per_div

    orb_options = [
        ("普通", "Orb of Transmutation", "Orb of Augmentation", 0),
        ("高阶", "Greater Orb of Transmutation", "Greater Orb of Augmentation", 44),
        ("完美", "Perfect Orb of Transmutation", "Perfect Orb of Augmentation", 70),
    ]
    rows = []
    for ilvl_label, min_ilvl, include_merciless in [
        ("ilvl 75-81", 75, False),
        ("ilvl 82+", 82, True),
    ]:
        for option_label, trans_name, aug_name, min_mod_level in orb_options:
            transmute = prices_by_name.get(trans_name.lower())
            aug = prices_by_name.get(aug_name.lower())
            transmute_ex = num(transmute.get("exalted_value")) if transmute else 0
            aug_ex = num(aug.get("exalted_value")) if aug else 0
            model = bow_prefix_weight_model(bow_mods, min_ilvl, include_merciless, min_mod_level)
            attempts = model["expected_attempts"]
            total_weight = model["prefix_weight"] + model["suffix_weight"]
            suffix_first_probability = model["suffix_weight"] / total_weight if total_weight else 0
            first_target_probability = model["target_weight"] / total_weight if total_weight else 0
            augment_hit_probability = model["target_weight"] / model["prefix_weight"] if model["prefix_weight"] else 0
            combined_probability = first_target_probability + suffix_first_probability * augment_hit_probability
            attempts = 1 / combined_probability if combined_probability else 0
            expected_ex = attempts * (normal_base_ex + transmute_ex + suffix_first_probability * aug_ex)
            expected_div = expected_ex / ex_per_div if ex_per_div else 0
            target_names = ", ".join(f"{name}(w={weight:g})" for name, _level, weight, _text in model["target_rows"])
            rows.append(
                "<tr>"
                f"<td>{esc(ilvl_label)}<br>{esc(option_label)}蜕变/增幅<br><code>{esc(trans_name)}</code><br><code>{esc(aug_name)}</code></td>"
                f"<td>{esc('>=' + str(min_mod_level) + ' 级' if min_mod_level else '无限制')}</td>"
                f"<td>{format_value(model['target_weight'])} / {format_value(total_weight)}<br>{esc(target_names)}</td>"
                f"<td>{format_value(combined_probability * 100)}%</td>"
                f"<td>{format_value(attempts)} 次</td>"
                f"<td>{format_value(expected_ex)} ex / {format_value(expected_div)} div</td>"
                f"<td>{format_value(bought_phys_ex)} ex / {format_value(bought_phys_div)} div</td>"
                "</tr>"
            )

    return f"""
    <h3>基底起手方案：直接买，还是用蜕变/增幅自己打？</h3>
    <p>你给的市场输入：<code>normal, ilvl &gt; 75 Obliterator Bow = 8E</code>；<code>带一条 %Physical Damage &gt;=135% 的 Magic Obliterator Bow = 10div</code>。下面按 PoE2DB 弓前缀权重估算，目标只算纯 <code>% increased Physical Damage</code>，不把混合物理/命中算入。</p>
    <div class="callout">权重来源说明：当前脚本使用 PoE2DB 的 <code>Bows#ModifiersCalc</code>。与 Craft of Exile 对比，弓前缀总权重在 ilvl 82+ 时同为 <code>44755</code>，所以物理百分比前缀的结论一致；后缀总权重不完全一致，主要差在 <code>+ Level of all Projectile Skills</code> 和物理偷取高阶权重。后续如果要精算补后缀命中率，要单独指定用 PoE2DB 还是 Craft of Exile。</div>
    <table>
      <thead><tr><th>方案</th><th>新增词缀最低等级</th><th>目标权重 / 总权重</th><th>单底成功率</th><th>期望重开次数</th><th>从 normal 自己打的期望成本</th><th>直接买合格魔法底</th></tr></thead>
      <tbody>{''.join(rows)}</tbody>
    </table>
    <div class="callout">结论：这一步不是固定成本，而是失败重开成本。按你给的 8E normal 底和 10div 合格魔法底，当前更推荐直接买 <code>>=135% phys</code> 魔法底。自己用蜕变/增幅只适合捡到底、低价批量收底，或者你能接受很大的波动。</div>
    {render_perfect_orb_note(bow_mods, prices_by_name)}
"""


def simple_min_level_pool(
    bow_mods: list[dict[str, str]],
    min_mod_level: int,
    target_min_phys: int,
    max_level: int = 82,
) -> tuple[float, float, float]:
    prefix = 0.0
    suffix = 0.0
    target = 0.0
    for row in bow_mods:
        if row.get("source_group") != "normal" or row.get("generation_type") not in {"1", "2"}:
            continue
        level = int(num(row.get("level")))
        if level > max_level or level < min_mod_level:
            continue
        weight = num(row.get("drop_chance"))
        if row.get("generation_type") == "1":
            prefix += weight
            text = row.get("text", "")
            target_range = re_search_phys_range(text)
            if target_range and target_range[0] >= target_min_phys and "Accuracy" not in text:
                target += weight
        else:
            suffix += weight
    return prefix, suffix, target


def render_perfect_orb_note(bow_mods: list[dict[str, str]], prices_by_name: dict[str, dict[str, str]]) -> str:
    ex_per_div = exalted_per_divine(prices_by_name)
    base_ex = MARKET_ASSUMPTIONS["normal_obliterator_bow_exalted"]
    direct_magic_ex = MARKET_ASSUMPTIONS["phys_135_magic_obliterator_bow_divine"] * ex_per_div
    greater_trans_ex = num((prices_by_name.get("Greater Orb of Transmutation".lower()) or {}).get("exalted_value"))
    greater_aug_ex = num((prices_by_name.get("Greater Orb of Augmentation".lower()) or {}).get("exalted_value"))
    perfect_trans_ex = num((prices_by_name.get("Perfect Orb of Transmutation".lower()) or {}).get("exalted_value"))
    perfect_aug_ex = num((prices_by_name.get("Perfect Orb of Augmentation".lower()) or {}).get("exalted_value"))

    greater_prefix, greater_suffix, greater_target = simple_min_level_pool(bow_mods, 44, 135, 82)
    perfect_prefix, perfect_suffix, perfect_target = simple_min_level_pool(bow_mods, 70, 155, 82)

    prefix, suffix, target = perfect_prefix, perfect_suffix, perfect_target
    total = prefix + suffix
    p_trans = target / total if total else 0
    p_aug = target / prefix if prefix else 0
    avg_trans = 1 / p_trans if p_trans else 0
    avg_aug = 1 / p_aug if p_aug else 0
    trans_cost_ex = avg_trans * (base_ex + perfect_trans_ex)
    aug_only_ex = avg_aug * perfect_aug_ex
    suffix_break_even_vs_direct = direct_magic_ex / avg_aug - perfect_aug_ex if avg_aug else 0
    suffix_break_even_vs_trans = trans_cost_ex / avg_aug - perfect_aug_ex if avg_aug else 0

    greater_p_aug = greater_target / greater_prefix if greater_prefix else 0
    greater_avg_aug = 1 / greater_p_aug if greater_p_aug else 0
    greater_aug_only_ex = greater_avg_aug * greater_aug_ex
    greater_suffix_break_even_vs_direct = direct_magic_ex / greater_avg_aug - greater_aug_ex if greater_avg_aug else 0

    perfect_suffix_break_even_vs_direct = suffix_break_even_vs_direct
    return f"""
    <h3>完美蜕变 vs 完美增幅：目标不是同一个</h3>
    <p>下面除弓底外全部使用 poe.ninja 快照价。完美蜕变石 / <code>Perfect Orb of Transmutation</code> 和完美增幅石 / <code>Perfect Orb of Augmentation</code> 的新增词缀最低等级都是 70，所以不会出 <code>Cruel 135-154% increased Physical Damage</code>，目标变成 <code>Tyrannical 155-169%</code> + <code>Merciless 170-179%</code>。按 PoE2DB 权重，目标权重是 <code>{format_value(target)}</code>，不是 100。</p>
    <table>
      <thead><tr><th>方案</th><th>池子</th><th>命中率</th><th>平均次数</th><th>平均成本</th><th>判断</th></tr></thead>
      <tbody>
        <tr><td>完美蜕变直接赌</td><td>前缀 {format_value(prefix)} + 后缀 {format_value(suffix)} = {format_value(total)}</td><td>{format_value(p_trans * 100)}%</td><td>{format_value(avg_trans)} 次</td><td>{format_value(trans_cost_ex)} ex / {format_value(trans_cost_ex / ex_per_div)} div</td><td>用 8E 白底 + 快照完美蜕变 {format_value(perfect_trans_ex)}E 计算，成本高于直接买 10div 合格底。</td></tr>
        <tr><td>完美增幅补前缀</td><td>只抽前缀 {format_value(prefix)}</td><td>{format_value(p_aug * 100)}%</td><td>{format_value(avg_aug)} 次</td><td>只算增幅：{format_value(aug_only_ex)} ex；另加 {format_value(avg_aug)} 把一词后缀底</td><td>目标更高，是 155%+ 物理百分比；只有当一词后缀魔法底足够便宜时成立。</td></tr>
      </tbody>
    </table>
    <h3>一词后缀魔法底：用高阶/完美增幅赌前缀是否更赚？</h3>
    <table>
      <thead><tr><th>增幅方案</th><th>目标</th><th>只抽前缀池</th><th>命中率</th><th>平均次数</th><th>只算增幅成本</th><th>一词后缀底临界价</th></tr></thead>
      <tbody>
        <tr><td>高阶增幅石<br><code>Greater Orb of Augmentation</code></td><td>135%+ 物理百分比<br>Cruel + Tyrannical + Merciless<br>0.5 最低词缀等级 44</td><td>{format_value(greater_prefix)}</td><td>{format_value(greater_p_aug * 100)}%</td><td>{format_value(greater_avg_aug)} 次</td><td>{format_value(greater_aug_only_ex)} ex</td><td>低于约 {format_value(greater_suffix_break_even_vs_direct)}E，才比 10div 直接买合格底便宜。</td></tr>
        <tr><td>完美增幅石<br><code>Perfect Orb of Augmentation</code></td><td>155%+ 物理百分比<br>Tyrannical + Merciless</td><td>{format_value(perfect_prefix)}</td><td>{format_value(p_aug * 100)}%</td><td>{format_value(avg_aug)} 次</td><td>{format_value(aug_only_ex)} ex</td><td>低于约 {format_value(perfect_suffix_break_even_vs_direct)}E，才比 10div 直接买合格底便宜。</td></tr>
      </tbody>
    </table>
    <div class="callout">回答你的问题：是的，如果能低价买到只有一条后缀、没有前缀的 Magic Obliterator Bow，用高阶增幅或完美增幅赌物理百分比前缀可能更划算。按当前快照价，高阶增幅对 <code>135%+</code> 的临界价约 {format_value(greater_suffix_break_even_vs_direct)}E；完美增幅对 <code>155%+</code> 的临界价约 {format_value(perfect_suffix_break_even_vs_direct)}E。高于这个价，直接买 10div 合格物理魔法底更稳。</div>
"""


def render_report() -> None:
    summary = read_json(PROCESSED_DIR / "summary.json")
    bow_bases = read_csv(PROCESSED_DIR / "poe2db_bow_bases.csv")
    bow_mods = read_csv(PROCESSED_DIR / "poe2db_bow_mods.csv")
    prices, prices_by_name = load_prices()
    price_snapshot_time = prices[0]["snapshot_time_utc"] if prices else "未抓取"

    draw_bow_chart(bow_bases)

    relevant_mods = find_mods(
        bow_mods,
        [
            "physical damage",
            "attack speed",
            "critical",
            "additional arrow",
            "level of all attack",
            "onslaught",
            "extra physical",
        ],
        limit=22,
    )

    html_text = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>PoE2 0.5 弓赚钱打造报告</title>
  <style>
    body {{ margin:0; font-family:"Microsoft YaHei","Segoe UI",Arial,sans-serif; background:#101014; color:#ede7d7; line-height:1.6; }}
    main {{ max-width:1220px; margin:0 auto; padding:28px 22px 56px; }}
    h1 {{ margin:0 0 10px; font-size:44px; color:#fff6df; line-height:1.12; }}
    h2 {{ margin:34px 0 14px; font-size:24px; color:#fff1cd; }}
    h3 {{ margin:22px 0 10px; color:#fff1cd; }}
    a {{ color:#85aee6; }}
    code {{ color:#ffe0a3; background:#24202a; padding:1px 5px; border-radius:5px; }}
    .muted {{ color:#b9b2a2; }}
    .meta {{ display:flex; flex-wrap:wrap; gap:8px; margin:14px 0 22px; }}
    .pill {{ border:1px solid #34384a; background:#151720; padding:6px 10px; border-radius:999px; font-size:13px; }}
    .grid {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:14px; }}
    .card {{ border:1px solid #34384a; background:#181922; border-radius:8px; padding:16px; }}
    .callout {{ border-left:4px solid #d7a94f; background:#1b1a1c; padding:14px 16px; margin:14px 0; border-radius:0 8px 8px 0; }}
    table {{ width:100%; border-collapse:collapse; margin:10px 0 18px; overflow-wrap:anywhere; }}
    th,td {{ border:1px solid #34384a; padding:10px 12px; vertical-align:top; text-align:left; }}
    th {{ background:#20212b; color:#fff0cf; }}
    td {{ background:#151721; }}
    img {{ max-width:100%; border-radius:8px; background:#f6f1e8; }}
    .flow {{ overflow-x:auto; border:1px solid #34384a; background:#13151d; border-radius:8px; padding:12px; }}
    svg text {{ font-family:"Microsoft YaHei","Segoe UI",Arial,sans-serif; fill:#f2ead8; font-size:14px; }}
    .node {{ fill:#202330; stroke:#4b5066; stroke-width:1.3; }}
    .gold {{ fill:#3a2b15; stroke:#d7a94f; }}
    .green {{ fill:#1e3326; stroke:#7fbf8b; }}
    .blue {{ fill:#1b2c45; stroke:#85aee6; }}
    .red {{ fill:#3a1d21; stroke:#d77a73; }}
    .arrow {{ stroke:#d7a94f; stroke-width:2; fill:none; marker-end:url(#arrowhead); }}
    @media (max-width:860px) {{ .grid {{ grid-template-columns:1fr; }} h1 {{ font-size:32px; }} }}
  </style>
</head>
<body>
<main>
  <h1>PoE2 0.5 新赛季弓赚钱打造报告</h1>
  <p class="muted">这份报告由脚本生成，数据来自本地缓存的 PoE2DB 词缀库与 Path of Crafting 公开 modifiers.json。核心策略仍然是批量买入好魔法底，用固定精髓补物理，再按 pDPS、攻速、暴击、技能等级和额外箭分层卖。</p>
  <div class="meta">
    <span class="pill">PoE2DB 词缀：{summary.get("poe2db_mod_rows", 0)}</span>
    <span class="pill">弓词缀：{summary.get("poe2db_bow_mod_rows", 0)}</span>
    <span class="pill">弓基底：{summary.get("poe2db_bow_base_rows", 0)}</span>
    <span class="pill">Path of Crafting：{summary.get("pathofcrafting_modifier_rows", 0)}</span>
    <span class="pill">poe.ninja 快照：{esc(price_snapshot_time)}</span>
  </div>

  <section class="grid">
    <div class="card"><strong>最稳路线</strong><p>收 <code>Magic</code> 弓底，要求已有 <code>% increased Physical Damage</code> 或好后缀，再用 <code>Greater Essence of Abrasion</code> 补固定物理点伤。</p></div>
    <div class="card"><strong>热门买家</strong><p>0.5 弓流派会持续吃高物理 DPS、攻速、暴击、额外箭、攻击技能等级。</p></div>
    <div class="card"><strong>止损原则</strong><p>成品价减成本不足 25%-35% 毛利不做；低预算货优先周转，不用 Perfect Essence 硬救。</p></div>
  </section>

  <section>
    <h2>poe.ninja 材料价格快照</h2>
    <p class="muted">来源：<a href="https://poe.ninja/poe2/economy/runesofaldur/currency">poe.ninja Runes of Aldur currency</a>，脚本同时抓取 Currency、Essences、Runes、Ritual/Omens、Abyss、Fragments。价格是快照，不是成交保证。</p>
    <div class="callout">蜕变/增幅三档机制：普通没有最低词缀等级；0.5 后高阶新增词缀至少 44 级；完美新增词缀至少 70 级。对本目标 <code>>=135% increased Physical Damage</code> 来说，高阶能保留 Cruel(135-154%, 60级) 和 Tyrannical(155-169%, 75级)，ilvl 82+ 还可出 Merciless(170-179%, 82级)；完美会排除 Cruel，只保留 Tyrannical/Merciless。所以完美不是必然更划算。</div>
    <table>
      <thead><tr><th>材料</th><th>约合 Exalted</th><th>约合 Divine</th><th>约合 Chaos</th></tr></thead>
      <tbody>
        {render_material_price_table(prices_by_name)}
      </tbody>
    </table>
  </section>

  <section>
    <h2>按攻略逐步造价估算</h2>
    <div class="callout">基底与成品售价无法从 poe.ninja 通货页得到，需要去交易站查。这里计算的是材料成本；判断能不能做，必须再加上“弓底价格”和至少 10%-20% 的降价空间。</div>
    {render_reset_model(bow_mods, prices_by_name)}
    {render_cost_tables(prices_by_name)}
  </section>

  {render_dps_tables()}

  <section>
    <h2>可重复执行命令</h2>
    <pre><code>python scripts/python/poe2_data_pipeline.py --refresh
python scripts/python/generate_bow_report.py</code></pre>
    <p>只更新报告、不重新抓网页时：</p>
    <pre><code>python scripts/python/poe2_data_pipeline.py --skip-fetch
python scripts/python/generate_bow_report.py</code></pre>
  </section>

  <section>
    <h2>数据文件</h2>
    <ul>
      <li><code>data/raw/poe2db/*.html</code>：PoE2DB 原始页面缓存。</li>
      <li><code>data/raw/pathofcrafting/modifiers.json</code>：Path of Crafting 公开核心词缀库。</li>
      <li><code>data/processed/poe2db_mods.csv</code>：PoE2DB 全部解析词缀。</li>
      <li><code>data/processed/poe2db_bow_mods.csv</code>：弓词缀池。</li>
      <li><code>data/processed/poe2db_bow_bases.csv</code>：弓基底。</li>
      <li><code>data/processed/pathofcrafting_modifiers.csv</code>：模拟器词缀库扁平表。</li>
    </ul>
  </section>
</main>
</body>
</html>
"""
    REPORT_FILE.write_text(html_text, encoding="utf-8")
    print(f"Wrote {REPORT_FILE}")
    print(f"Wrote {CHART_FILE}")


if __name__ == "__main__":
    render_report()
