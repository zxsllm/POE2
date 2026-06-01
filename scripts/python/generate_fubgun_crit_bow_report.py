from __future__ import annotations

import csv
import html
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = ROOT / "data" / "processed"
PRICE_DIR = PROCESSED_DIR / "prices" / "poe_ninja"
PRICE_TYPE_DIR = PRICE_DIR / "by_type"
MODS_DIR = PROCESSED_DIR / "mods"
ITEMS_DIR = PROCESSED_DIR / "items"
REPORT_FILE = ROOT / "reports" / "bow" / "fubgun_crit_bow_report.html"
MOD_ILVL = 80
CRAFT_OF_EXILE_DESECRATED_PREFIX_WEIGHT = 8.0
CRAFT_OF_EXILE_DESECRATED_SUFFIX_WEIGHT = 9.0


CN = {
    "Obliterator Bow": "湮灭之弓",
    "Orb of Transmutation": "蜕变石",
    "Orb of Augmentation": "增幅石",
    "Greater Orb of Transmutation": "高阶蜕变石",
    "Greater Orb of Augmentation": "高阶增幅石",
    "Perfect Orb of Transmutation": "完美蜕变石",
    "Perfect Orb of Augmentation": "完美增幅石",
    "Greater Essence of Seeking": "高阶追寻精髓",
    "Greater Essence of Abrasion": "高阶磨蚀精髓",
    "Exalted Orb": "崇高石",
    "Greater Exalted Orb": "高阶崇高石",
    "Perfect Exalted Orb": "完美崇高石",
    "Omen of Sinistral Exaltation": "左向崇高预兆",
    "Omen of Dextral Exaltation": "右向崇高预兆",
    "Omen of Greater Exaltation": "高阶崇高预兆",
    "Omen of Light": "光明预兆",
    "Omen of Catalysing Exaltation": "催化崇高预兆",
    "Omen of Sinistral Necromancy": "左向死灵预兆",
    "Omen of Dextral Necromancy": "右向死灵预兆",
    "Omen of Abyssal Echoes": "深渊回响预兆",
    "Preserved Jawbone": "保存完好的颚骨",
    "Ancient Jawbone": "远古颚骨",
    "Artificer's Orb": "工匠石",
    "Greater Iron Rune": "高阶铁符文",
    "Perfect Iron Rune": "完美铁符文",
    "Countess Seske's Rune of Archery": "瑟丝克伯爵夫人的箭术符文",
}


TARGET_LABELS = {
    "phys_pct_135": "135%+ increased Physical Damage / 135%+ 物理百分比",
    "phys_pct_155": "155%+ increased Physical Damage / 155%+ 物理百分比",
    "flat_phys_t3": "T3+ Adds Physical Damage / T3+ 物理点伤",
    "flat_phys_t2": "T2+ Adds Physical Damage / T2+ 物理点伤",
    "element_t3": "T3+ Elemental Damage / T3+ 元素点伤",
    "crit_multi_t3": "T3+ Critical Damage Bonus / T3+ 暴击伤害加成",
    "crit_chance_t3": "T3+ Critical Hit Chance / T3+ 暴击率",
    "projectile_skills": "+# to Level of all Projectile Skills / +# 投射物技能等级",
    "additional_arrows": "#% Surpassing chance to fire an additional Arrow / #% 超越概率发射额外箭矢",
    "effective_prefix": "有效前缀：除命中值和武器元素攻击伤害外的前缀",
    "effective_suffix": "有效后缀：暴伤、投射物等级、额外箭、攻速、暴击率",
}


TARGET_CODE = {
    "phys_pct_135": "P135",
    "phys_pct_155": "P155",
    "flat_phys_t3": "F3",
    "flat_phys_t2": "F2",
}


MANUAL_PRICES = {
    "normal_base_ex": 7.0,
    "phys_pct_135_154_magic_base_div": 9.0,
    "phys_pct_155_magic_base_div": 14.0,
    "flat_phys_t3_magic_base_ex": 4.0,
    "flat_phys_t2_magic_base_ex": 10.0,
    "trash_magic_bow_ex": None,
    "one_suffix_magic_base_ex": None,
}


@dataclass
class Candidate:
    code: str
    target: str
    method: str
    materials: str
    cost_per_try: float | None
    probability: float | None
    average_cost: float | None
    direct_compare: str
    route_fit: str
    verdict: str = "备选"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def read_csv_dir(path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for csv_path in sorted(path.glob("*.csv")):
        rows.extend(read_csv(csv_path))
    return rows


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def num(value: Any, default: float = 0.0) -> float:
    try:
        if value in ("", None):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def fmt(value: float | None, suffix: str = "") -> str:
    if value is None:
        return "需手动输入"
    if value == 0:
        return f"0{suffix}"
    if abs(value) >= 100:
        return f"{value:.1f}{suffix}"
    if abs(value) >= 10:
        return f"{value:.2f}{suffix}"
    if abs(value) >= 1:
        return f"{value:.3f}{suffix}"
    return f"{value:.4f}{suffix}"


def money(value: float | None) -> str:
    if value is None:
        return "需手动输入"
    return f"{fmt(value)}E"


def pct(probability: float | None) -> str:
    if probability is None:
        return "条件公式"
    if probability <= 0:
        return "0%"
    return f"{probability * 100:.3f}%"


def tries(probability: float | None) -> str:
    if probability is None:
        return "条件公式"
    if probability <= 0:
        return "不可命中"
    return f"{1 / probability:.1f}"


def load_prices() -> tuple[list[dict[str, str]], dict[str, dict[str, str]]]:
    rows = read_csv_dir(PRICE_TYPE_DIR)
    return rows, {row["name"].lower(): row for row in rows}


def cost(prices: dict[str, dict[str, str]], *names: str) -> float:
    return sum(num((prices.get(name.lower()) or {}).get("exalted_value")) for name in names)


def exalted_per_divine(prices: dict[str, dict[str, str]]) -> float:
    divine = prices.get("divine orb")
    if divine and num(divine.get("exalted_value")):
        return num(divine.get("exalted_value"))
    exalted = prices.get("exalted orb")
    divine_value = num(exalted.get("divine_value")) if exalted else 0
    return 1 / divine_value if divine_value else 50.0


def label(name: str) -> str:
    cn = CN.get(name)
    return f"{esc(name)} / {esc(cn)}" if cn else esc(name)


def price_line(name: str, prices: dict[str, dict[str, str]]) -> str:
    row = prices.get(name.lower())
    if not row:
        return f"<tr><td><code>{label(name)}</code></td><td colspan=\"3\">快照未找到</td></tr>"
    return (
        "<tr>"
        f"<td><code>{label(name)}</code></td>"
        f"<td>{fmt(num(row.get('exalted_value')))}E</td>"
        f"<td>{fmt(num(row.get('divine_value')))}div</td>"
        f"<td>{fmt(num(row.get('chaos_value')))}c</td>"
        "</tr>"
    )


def family_key(row: dict[str, str]) -> str:
    return row.get("families") or f"{row.get('generation_type')}:{row.get('name')}:{row.get('text')}"


def mod_pool(
    bow_mods: list[dict[str, str]],
    generation_type: str | None = None,
    min_mod_level: int = 0,
    ilvl: int = MOD_ILVL,
    excluded_families: set[str] | None = None,
) -> list[dict[str, str]]:
    excluded_families = excluded_families or set()
    rows = []
    for row in bow_mods:
        if row.get("source_group") != "normal":
            continue
        if row.get("generation_type") not in {"1", "2"}:
            continue
        if generation_type and row.get("generation_type") != generation_type:
            continue
        if int(num(row.get("level"))) > ilvl:
            continue
        if int(num(row.get("level"))) < min_mod_level:
            continue
        if family_key(row) in excluded_families:
            continue
        if num(row.get("drop_chance")) <= 0:
            continue
        rows.append(row)
    return rows


def weight(rows: list[dict[str, str]]) -> float:
    return sum(num(row.get("drop_chance")) for row in rows)


def target_rows(rows: list[dict[str, str]], target: str) -> list[dict[str, str]]:
    matched = []
    for row in rows:
        family = row.get("families")
        level = int(num(row.get("level")))
        if target == "phys_pct_135" and family == "LocalPhysicalDamagePercent" and level >= 60:
            matched.append(row)
        elif target == "phys_pct_155" and family == "LocalPhysicalDamagePercent" and level >= 75:
            matched.append(row)
        elif target == "flat_phys_t3" and family == "PhysicalDamage" and level >= 60:
            matched.append(row)
        elif target == "flat_phys_t2" and family == "PhysicalDamage" and level >= 75:
            matched.append(row)
        elif target == "element_t3" and family in {"FireDamage", "ColdDamage", "LightningDamage"} and level >= 60:
            matched.append(row)
        elif target == "crit_multi_t3" and family == "CriticalStrikeMultiplier" and level >= 44:
            matched.append(row)
        elif target == "crit_chance_t3" and family == "CriticalStrikeChanceIncrease" and level >= 44:
            matched.append(row)
        elif target == "attack_speed_t3" and family == "IncreasedAttackSpeed" and level >= 30:
            matched.append(row)
        elif target == "projectile_skills" and family == "IncreaseSocketedGemLevel":
            matched.append(row)
        elif target == "additional_arrows" and family == "AdditionalArrows":
            matched.append(row)
        elif target == "effective_prefix" and row.get("generation_type") == "1" and family not in {
            "IncreasedAccuracy",
            "IncreasedWeaponElementalDamagePercent",
        }:
            matched.append(row)
        elif target == "effective_suffix" and row.get("generation_type") == "2" and family in {
            "CriticalStrikeMultiplier",
            "IncreaseSocketedGemLevel",
            "AdditionalArrows",
            "IncreasedAttackSpeed",
            "CriticalStrikeChanceIncrease",
        }:
            matched.append(row)
    return matched


def target_rows_any(rows: list[dict[str, str]], targets: set[str]) -> list[dict[str, str]]:
    by_key: dict[str, dict[str, str]] = {}
    for target in targets:
        for row in target_rows(rows, target):
            by_key[f"{family_key(row)}:{row.get('level')}:{row.get('name')}"] = row
    return list(by_key.values())


def random_affix_pool(
    bow_mods: list[dict[str, str]],
    min_mod_level: int,
    excluded_families: set[str] | None = None,
) -> list[dict[str, str]]:
    return mod_pool(bow_mods, None, min_mod_level, excluded_families=excluded_families)


def two_random_mod_probabilities(
    bow_mods: list[dict[str, str]],
    min_mod_level: int,
    targets: set[str],
    excluded_families: set[str] | None = None,
) -> tuple[float, float]:
    pool = random_affix_pool(bow_mods, min_mod_level, excluded_families)
    total = weight(pool)
    if not total:
        return 0.0, 0.0
    useful_keys = {family_key(row) for row in target_rows_any(pool, targets)}
    at_least_one = 0.0
    at_least_two = 0.0
    for first in pool:
        first_w = num(first.get("drop_chance"))
        first_good = family_key(first) in useful_keys
        next_pool = random_affix_pool(
            bow_mods,
            min_mod_level,
            (excluded_families or set()) | {family_key(first)},
        )
        next_total = weight(next_pool)
        if not next_total:
            continue
        second_good_weight = sum(
            num(row.get("drop_chance")) for row in next_pool if family_key(row) in useful_keys
        )
        second_good = second_good_weight / next_total
        first_p = first_w / total
        if first_good:
            at_least_one += first_p
            at_least_two += first_p * second_good
        else:
            at_least_one += first_p * second_good
    return at_least_one, at_least_two


def two_random_mod_probabilities_with_required(
    bow_mods: list[dict[str, str]],
    min_mod_level: int,
    targets: set[str],
    required_target: str,
    excluded_families: set[str] | None = None,
) -> tuple[float, float]:
    pool = random_affix_pool(bow_mods, min_mod_level, excluded_families)
    total = weight(pool)
    if not total:
        return 0.0, 0.0
    useful_keys = {family_key(row) for row in target_rows_any(pool, targets)}
    required_keys = {family_key(row) for row in target_rows(pool, required_target)}
    at_least_one = 0.0
    success = 0.0
    for first in pool:
        first_key = family_key(first)
        first_w = num(first.get("drop_chance"))
        first_good = first_key in useful_keys
        first_required = first_key in required_keys
        next_pool = random_affix_pool(
            bow_mods,
            min_mod_level,
            (excluded_families or set()) | {first_key},
        )
        next_total = weight(next_pool)
        if not next_total:
            continue
        second_good_weight = sum(
            num(row.get("drop_chance")) for row in next_pool if family_key(row) in useful_keys
        )
        second_required_good_weight = sum(
            num(row.get("drop_chance"))
            for row in next_pool
            if family_key(row) in useful_keys and family_key(row) in required_keys
        )
        first_p = first_w / total
        if first_good:
            at_least_one += first_p
            if first_required:
                success += first_p * (second_good_weight / next_total)
            else:
                success += first_p * (second_required_good_weight / next_total)
        else:
            at_least_one += first_p * (second_good_weight / next_total)
    return at_least_one, success


def target_stats(
    bow_mods: list[dict[str, str]],
    target: str,
    generation_type: str,
    min_mod_level: int,
    excluded_families: set[str] | None = None,
) -> tuple[float, float, float]:
    rows = mod_pool(bow_mods, generation_type, min_mod_level, excluded_families=excluded_families)
    total = weight(rows)
    target_weight = weight(target_rows(rows, target))
    probability = target_weight / total if total else 0
    return probability, target_weight, total


def target_stats_any(
    bow_mods: list[dict[str, str]],
    targets: set[str],
    generation_type: str,
    min_mod_level: int,
    excluded_families: set[str] | None = None,
) -> tuple[float, float, float]:
    rows = mod_pool(bow_mods, generation_type, min_mod_level, excluded_families=excluded_families)
    total = weight(rows)
    target_weight = weight(target_rows_any(rows, targets))
    probability = target_weight / total if total else 0
    return probability, target_weight, total


def target_generation_type(target: str) -> str:
    return "2" if target in {"crit_multi_t3", "crit_chance_t3"} else "1"


def trans_aug_attempt(
    bow_mods: list[dict[str, str]],
    target: str,
    min_mod_level: int,
    trans_cost: float,
    aug_cost: float,
    normal_base_cost: float,
) -> tuple[float, float, float, float, float]:
    side = target_generation_type(target)
    other_side = "1" if side == "2" else "2"
    target_pool = mod_pool(bow_mods, side, min_mod_level)
    other_pool = mod_pool(bow_mods, other_side, min_mod_level)
    target_side_total = weight(target_pool)
    other_total = weight(other_pool)
    target_weight = weight(target_rows(target_pool, target))
    total_first_roll = target_side_total + other_total
    trans_hit = target_weight / total_first_roll if total_first_roll else 0
    trans_other_side = other_total / total_first_roll if total_first_roll else 0
    aug_hit = target_weight / target_side_total if target_side_total else 0
    success = trans_hit + trans_other_side * aug_hit
    cost_per_try = normal_base_cost + trans_cost + trans_other_side * aug_cost
    average = cost_per_try / success if success else 0
    return success, cost_per_try, average, target_weight, target_side_total


def augment_only(
    bow_mods: list[dict[str, str]],
    target: str,
    min_mod_level: int,
    aug_cost: float,
    suffix_base_cost: float | None,
) -> tuple[float, float, float | None, float, float]:
    target_pool = mod_pool(bow_mods, "1", min_mod_level)
    total = weight(target_pool)
    target_weight = weight(target_rows(target_pool, target))
    probability = target_weight / total if total else 0
    if suffix_base_cost is None or probability <= 0:
        average = None
    else:
        average = (suffix_base_cost + aug_cost) / probability
    return probability, aug_cost, average, target_weight, total


def random_magic_target_probability(
    bow_mods: list[dict[str, str]],
    target: str,
    min_mod_level: int,
) -> tuple[float, float, float, float, float]:
    prefix_pool = mod_pool(bow_mods, "1", min_mod_level)
    suffix_pool = mod_pool(bow_mods, "2", min_mod_level)
    prefix_total = weight(prefix_pool)
    suffix_total = weight(suffix_pool)
    target_weight = weight(target_rows(prefix_pool, target))
    prefix_probability = target_weight / prefix_total if prefix_total else 0.0
    one_affix_probability = target_weight / (prefix_total + suffix_total) if prefix_total + suffix_total else 0.0
    return prefix_probability, one_affix_probability, target_weight, prefix_total, suffix_total


def startup_candidates(
    bow_mods: list[dict[str, str]],
    prices: dict[str, dict[str, str]],
    ex_per_div: float,
) -> tuple[list[Candidate], dict[str, Candidate], dict[str, Any]]:
    normal_base = MANUAL_PRICES["normal_base_ex"]
    direct_phys_135 = MANUAL_PRICES["phys_pct_135_154_magic_base_div"] * ex_per_div
    direct_phys_155 = MANUAL_PRICES["phys_pct_155_magic_base_div"] * ex_per_div
    direct_flat_t3 = MANUAL_PRICES["flat_phys_t3_magic_base_ex"]
    direct_flat_t2 = MANUAL_PRICES["flat_phys_t2_magic_base_ex"]
    trash_magic_bow = MANUAL_PRICES["trash_magic_bow_ex"]
    suffix_base = MANUAL_PRICES["one_suffix_magic_base_ex"]
    s7_probability, s7_one_affix_probability, s7_target_weight, s7_prefix_total, s7_suffix_total = (
        random_magic_target_probability(bow_mods, "phys_pct_135", 0)
    )
    s7_per_try = trash_magic_bow * 3 if trash_magic_bow is not None else None
    s7_average = s7_per_try / s7_probability if s7_per_try is not None and s7_probability else None
    s7_break_even = direct_phys_135 * s7_probability / 3 if s7_probability else 0.0

    tiers = [
        ("S1", "普通蜕变/增幅", 0, "Orb of Transmutation", "Orb of Augmentation"),
        ("S2", "高阶蜕变/增幅", 44, "Greater Orb of Transmutation", "Greater Orb of Augmentation"),
        ("S3", "完美蜕变/增幅", 70, "Perfect Orb of Transmutation", "Perfect Orb of Augmentation"),
    ]

    candidates: list[Candidate] = [
        Candidate(
            "S0",
            "base",
            "直接买白底",
            "normal ilvl 75-80 Obliterator Bow / 白色湮灭之弓",
            normal_base,
            1.0,
            normal_base,
            "只是重开成本，不是路线入口",
            "全部路线",
            "重开基准",
        )
    ]

    target_routes = {
        "phys_pct_135": "路线 1、路线 3",
        "flat_phys_t3": "路线 2",
        "phys_pct_155": "高端备选",
        "flat_phys_t2": "路线 2 高端备选",
    }

    target_tiers = {
        "phys_pct_135": tiers[:2],
        "flat_phys_t3": tiers[:2],
        "phys_pct_155": tiers,
        "flat_phys_t2": [tiers[2]],
    }
    for target, available_tiers in target_tiers.items():
        for code, tier_label, min_level, trans_name, aug_name in available_tiers:
            trans_cost = cost(prices, trans_name)
            aug_cost = cost(prices, aug_name)
            probability, per_try, average, target_weight, total = trans_aug_attempt(
                bow_mods,
                target,
                min_level,
                trans_cost,
                aug_cost,
                normal_base,
            )
            candidates.append(
                Candidate(
                    f"{code}-{TARGET_CODE[target]}",
                    target,
                    f"{tier_label}从白底生成",
                    f"{label(trans_name)} + {label(aug_name)}",
                    per_try,
                    probability,
                    average,
                    f"目标权重 {fmt(target_weight)} / 前缀池 {fmt(total)}",
                    target_routes.get(target, "备选"),
                )
            )

    candidates.extend(
        [
            Candidate(
                "S7-P135",
                "phys_pct_135",
                "3:1 回收垃圾魔法弓",
                "3 x trash Magic Bow / 3 把垃圾魔法弓 -> 1 把随机未鉴定魔法弓",
                s7_per_try,
                s7_probability,
                s7_average,
                (
                    f"假设成品魔法弓含随机前缀：目标权重 {fmt(s7_target_weight)} / 前缀池 {fmt(s7_prefix_total)}；"
                    f"平均消耗 {fmt(3 / s7_probability)} 把垃圾魔法弓；"
                    f"单把垃圾弓低于 {fmt(s7_break_even)}E 才比直接买 135-154% 底便宜；"
                    f"若只按单随机词保守估算，概率 {pct(s7_one_affix_probability)}"
                ),
                "路线 1、路线 3 的垃圾底回收",
                "条件备选",
            ),
            Candidate(
                "S4-P135",
                "phys_pct_135",
                "直接买一词 135-154% 物理百分比魔法底",
                "135-154% phys Magic Obliterator Bow / 135-154% 物理百分比魔法湮灭之弓",
                direct_phys_135,
                1.0,
                direct_phys_135,
                "手动价 9div",
                "路线 1、路线 3",
            ),
            Candidate(
                "S4-P155",
                "phys_pct_155",
                "直接买一词 155%+ 物理百分比魔法底",
                "155%+ phys Magic Obliterator Bow / 155%+ 物理百分比魔法湮灭之弓",
                direct_phys_155,
                1.0,
                direct_phys_155,
                "手动价 14div",
                "路线 1、路线 3 高端备选",
            ),
            Candidate(
                "S5-F3",
                "flat_phys_t3",
                "直接买一词物理点伤魔法底",
                "T3+ flat phys Magic Obliterator Bow / T3+ 物理点伤魔法湮灭之弓",
                direct_flat_t3,
                1.0,
                direct_flat_t3,
                "手动价 4E",
                "路线 2",
            ),
            Candidate(
                "S5-F2",
                "flat_phys_t2",
                "直接买一词 T2+ 物理点伤魔法底",
                "T2+ flat phys Magic Obliterator Bow / T2+ 物理点伤魔法湮灭之弓",
                direct_flat_t2,
                1.0,
                direct_flat_t2,
                "手动价 10E",
                "路线 2 高端备选",
            ),
        ]
    )

    s6_rows = []
    for code, tier_label, min_level, aug_name, target in [
        ("S6G", "一词后缀底 + 高阶增幅", 44, "Greater Orb of Augmentation", "phys_pct_135"),
        ("S6P", "一词后缀底 + 完美增幅", 70, "Perfect Orb of Augmentation", "phys_pct_155"),
    ]:
        aug_cost = cost(prices, aug_name)
        probability, per_try, average, target_weight, total = augment_only(
            bow_mods,
            target,
            min_level,
            aug_cost,
            suffix_base,
        )
        direct_reference = direct_phys_155 if target == "phys_pct_155" else direct_phys_135
        break_even = direct_reference * probability - aug_cost if probability else 0
        candidates.append(
            Candidate(
                f"{code}-{TARGET_CODE[target]}",
                target,
                tier_label,
                f"一词后缀魔法底 + {label(aug_name)}",
                (suffix_base + aug_cost) if suffix_base is not None else None,
                probability,
                average,
                f"后缀底低于 {fmt(max(break_even, 0))}E 才比同目标直接买便宜；目标权重 {fmt(target_weight)} / 前缀池 {fmt(total)}",
                "路线 1、路线 3 的低价捡漏",
                "条件备选",
            )
        )
        s6_rows.append((code, probability, break_even))

    selectable = [
        c
        for c in candidates
        if c.target in {"phys_pct_135", "phys_pct_155", "flat_phys_t3", "flat_phys_t2"} and c.average_cost
    ]
    best_by_target: dict[str, Candidate] = {}
    compatible_targets = {
        "phys_pct_135": {"phys_pct_135", "phys_pct_155"},
        "flat_phys_t3": {"flat_phys_t3", "flat_phys_t2"},
        "phys_pct_155": {"phys_pct_155"},
        "flat_phys_t2": {"flat_phys_t2"},
    }
    for target, compatible in compatible_targets.items():
        rows = [c for c in selectable if c.target in compatible]
        if rows:
            best = min(rows, key=lambda item: item.average_cost or float("inf"))
            best_by_target[target] = best
            best.verdict = "高端推荐" if target in {"phys_pct_155", "flat_phys_t2"} else "推荐"
    for candidate in candidates:
        if candidate.verdict == "备选" and candidate.average_cost and candidate.target in best_by_target:
            if candidate.average_cost > (best_by_target[candidate.target].average_cost or 0) * 2:
                candidate.verdict = "不推荐"

    debug = {
        "direct_phys_135_ex": direct_phys_135,
        "direct_phys_155_ex": direct_phys_155,
        "direct_flat_t3_ex": direct_flat_t3,
        "direct_flat_t2_ex": direct_flat_t2,
        "normal_base_ex": normal_base,
        "s6_rows": s6_rows,
    }
    return candidates, best_by_target, debug


def choice_probability(single_probability: float, choices: int) -> float:
    return 1 - (1 - single_probability) ** choices


def two_prefix_probability(
    bow_mods: list[dict[str, str]],
    first_target: str,
    second_target: str,
    min_mod_level: int,
    excluded_families: set[str],
) -> float:
    rows = mod_pool(bow_mods, "1", min_mod_level, excluded_families=excluded_families)
    total = weight(rows)
    if not total:
        return 0
    probability = 0.0
    for first_name, second_name in ((first_target, second_target), (second_target, first_target)):
        for first in target_rows(rows, first_name):
            first_probability = num(first.get("drop_chance")) / total
            next_rows = mod_pool(
                bow_mods,
                "1",
                min_mod_level,
                excluded_families=excluded_families | {family_key(first)},
            )
            next_total = weight(next_rows)
            if next_total:
                probability += first_probability * weight(target_rows(next_rows, second_name)) / next_total
    return probability


def expected(per_try: float, probability: float) -> str:
    if probability <= 0:
        return "不可命中"
    return f"{fmt(per_try / probability)}E"


def retry_expected(attempt_cost: float, probability: float, reset_cost: float) -> float:
    if probability <= 0:
        return float("inf")
    return (attempt_cost + (1 - probability) * reset_cost) / probability


def render_startup_table(candidates: list[Candidate]) -> str:
    rows = []
    for c in candidates:
        row_class = ""
        if c.code in {"S4-P135", "S5-F3"}:
            row_class = ' class="best-base"'
        elif c.code in {"S4-P155", "S5-F2", "S7-P135"}:
            row_class = ' class="watch-base"'
        rows.append(
            f"<tr{row_class}>"
            f"<td><code>{esc(c.code)}</code></td>"
            f"<td>{esc(TARGET_LABELS.get(c.target, '白底重开'))}</td>"
            f"<td>{esc(c.method)}</td>"
            f"<td>{c.materials}</td>"
            f"<td>{money(c.cost_per_try)}</td>"
            f"<td>{pct(c.probability)}</td>"
            f"<td>{tries(c.probability)}</td>"
            f"<td>{money(c.average_cost)}</td>"
            f"<td>{esc(c.direct_compare)}</td>"
            f"<td>{esc(c.route_fit)}</td>"
            f"<td>{esc(c.verdict)}</td>"
            "</tr>"
        )
    return (
        "<table>"
        "<thead><tr><th>状态</th><th>目标起始状态</th><th>生成方式</th><th>材料</th><th>单次成本</th><th>成功率</th><th>平均次数</th><th>平均成本</th><th>临界比较</th><th>适用路线</th><th>选择</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody>"
        "</table>"
    )


def cost_share_table(title: str, rows: list[tuple[str, float, str]]) -> str:
    total = sum(value for _, value, _ in rows)
    body = []
    for name, value, note in rows:
        share = value / total * 100 if total else 0
        body.append(
            "<tr>"
            f"<td>{esc(name)}</td>"
            f"<td>{fmt(value)}E</td>"
            f"<td>{share:.1f}%</td>"
            f"<td>{esc(note)}</td>"
            "</tr>"
        )
    return (
        f"<h4>{esc(title)}</h4>"
        "<table><thead><tr><th>步骤</th><th>成本</th><th>占比</th><th>判断</th></tr></thead>"
        f"<tbody>{''.join(body)}</tbody>"
        f"<tfoot><tr><th>合计</th><th>{fmt(total)}E</th><th>100%</th><th></th></tr></tfoot></table>"
    )


def expected_material_table(title: str, rows: list[tuple[str, float, float, str]]) -> str:
    total = sum(total_cost for _, _, total_cost, _ in rows)
    body = []
    for name, quantity, total_cost, note in rows:
        share = total_cost / total * 100 if total else 0
        body.append(
            "<tr>"
            f"<td>{name}</td>"
            f"<td>{fmt(quantity)}</td>"
            f"<td>{money(total_cost)}</td>"
            f"<td>{share:.2f}%</td>"
            f"<td>{note}</td>"
            "</tr>"
        )
    return (
        f"<h4>{esc(title)}</h4>"
        "<table><thead><tr><th>成本项</th><th>期望消耗数量</th><th>期望成本</th><th>占比</th><th>说明</th></tr></thead>"
        f"<tbody>{''.join(body)}</tbody>"
        f"<tfoot><tr><th>合计</th><th></th><th>{money(total)}</th><th>100%</th><th></th></tr></tfoot></table>"
    )


def step_cost_table(title: str, rows: list[tuple[str, str, float, float, str]]) -> str:
    body = []
    for step, state, added_cost, cumulative_cost, note in rows:
        body.append(
            "<tr>"
            f"<td>{esc(step)}</td>"
            f"<td>{state}</td>"
            f"<td>{money(added_cost)}</td>"
            f"<td>{money(cumulative_cost)}</td>"
            f"<td>{note}</td>"
            "</tr>"
        )
    return (
        f"<h4>{esc(title)}</h4>"
        "<table><thead><tr><th>步骤</th><th>达到的状态</th><th>本步新增期望成本</th><th>累计期望成本</th><th>说明</th></tr></thead>"
        f"<tbody>{''.join(body)}</tbody></table>"
    )


def render_operation_table(title: str, rows: list[tuple[str, str, str, float, str, str, str]]) -> str:
    body = []
    for code, target, materials, per_try, probability, expected_cost, verdict in rows:
        body.append(
            "<tr>"
            f"<td><code>{esc(code)}</code></td>"
            f"<td>{target}</td>"
            f"<td>{materials}</td>"
            f"<td>{money(per_try)}</td>"
            f"<td>{probability}</td>"
            f"<td>{expected_cost}</td>"
            f"<td>{verdict}</td>"
            "</tr>"
        )
    return (
        f"<h4>{esc(title)}</h4>"
        "<table><thead><tr><th>操作</th><th>目标</th><th>材料</th><th>单次成本</th><th>成功率 / 公式</th><th>材料期望</th><th>判断</th></tr></thead>"
        f"<tbody>{''.join(body)}</tbody></table>"
    )


def render_route_candidate_table(title: str, rows: list[tuple[Any, ...]]) -> str:
    body = []
    for row in rows:
        target_state, method, materials, per_try, probability, compare, verdict = row[:7]
        expected_override = row[7] if len(row) > 7 else None
        row_class = ""
        if "推荐" in verdict or verdict == "主封口":
            row_class = ' class="best-route"'
        elif "备选" in verdict or "可选" in verdict:
            row_class = ' class="watch-route"'
        if expected_override is not None:
            expected_text = expected_override
        elif probability is None:
            expected_text = "不可精算"
        elif probability >= 1:
            expected_text = money(per_try)
        else:
            expected_text = expected(per_try, probability)
        body.append(
            f"<tr{row_class}>"
            f"<td>{target_state}</td>"
            f"<td>{method}</td>"
            f"<td>{materials}</td>"
            f"<td>{money(per_try)}</td>"
            f"<td>{pct(probability)}</td>"
            f"<td>{tries(probability)}</td>"
            f"<td>{expected_text}</td>"
            f"<td>{compare}</td>"
            f"<td>{verdict}</td>"
            "</tr>"
        )
    return (
        f"<h4>{esc(title)}</h4>"
        "<table><thead><tr><th>目标状态</th><th>生成方式</th><th>材料</th><th>单次成本</th><th>成功率</th><th>平均次数</th><th>平均成本</th><th>临界比较</th><th>选择</th></tr></thead>"
        f"<tbody>{''.join(body)}</tbody></table>"
    )


def render_cost_distribution(title: str, rows: list[tuple[str, str, float, str]]) -> str:
    body = []
    running = 0.0
    for stage, item, cost_value, note in rows:
        running += cost_value
        body.append(
            "<tr>"
            f"<td>{esc(stage)}</td>"
            f"<td>{item}</td>"
            f"<td>{money(cost_value)}</td>"
            f"<td>{money(running)}</td>"
            f"<td>{note}</td>"
            "</tr>"
        )
    return (
        f"<h4>{esc(title)}</h4>"
        "<table><thead><tr><th>阶段</th><th>做法 / 材料</th><th>本段成本</th><th>累计成本</th><th>说明</th></tr></thead>"
        f"<tbody>{''.join(body)}</tbody></table>"
    )


def render_price_distribution(title: str, rows: list[tuple[Any, ...]]) -> str:
    body = []
    for row in rows:
        scene, included, total_cost, probability, note = row[:5]
        expected_override = row[5] if len(row) > 5 else None
        if expected_override is not None:
            expected_text = expected_override
        elif probability is None:
            expected_text = "条件计算"
        elif probability >= 1:
            expected_text = money(total_cost)
        else:
            expected_text = expected(total_cost, probability)
        body.append(
            "<tr>"
            f"<td>{esc(scene)}</td>"
            f"<td>{included}</td>"
            f"<td>{money(total_cost)}</td>"
            f"<td>{pct(probability)}</td>"
            f"<td>{expected_text}</td>"
            f"<td>{note}</td>"
            "</tr>"
        )
    return (
        f"<h4>{esc(title)}</h4>"
        "<table><thead><tr><th>场景</th><th>包含步骤 / 材料</th><th>单次投入</th><th>成功率</th><th>无回收期望</th><th>说明</th></tr></thead>"
        f"<tbody>{''.join(body)}</tbody></table>"
    )


def render_route1_cost_breakdown(title: str, rows: list[tuple[str, str, str, str, str, str, str]]) -> str:
    body = []
    for scene, pre_loop, seal_loop, success_rate, reset_cost, expected_text, note in rows:
        body.append(
            "<tr>"
            f"<td>{esc(scene)}</td>"
            f"<td>{pre_loop}</td>"
            f"<td>{seal_loop}</td>"
            f"<td>{success_rate}</td>"
            f"<td>{reset_cost}</td>"
            f"<td>{expected_text}</td>"
            f"<td>{note}</td>"
            "</tr>"
        )
    return (
        f"<h4>{esc(title)}</h4>"
        "<table><thead><tr><th>场景</th><th>前置循环</th><th>封口循环</th><th>成功率</th><th>失败处理成本</th><th>累计期望</th><th>说明</th></tr></thead>"
        f"<tbody>{''.join(body)}</tbody></table>"
    )


def render_probability_rows(bow_mods: list[dict[str, str]]) -> str:
    rows = []
    checks = [
        ("phys_pct_135", "1", 0),
        ("phys_pct_135", "1", 44),
        ("phys_pct_155", "1", 70),
        ("flat_phys_t3", "1", 0),
        ("flat_phys_t3", "1", 44),
        ("flat_phys_t2", "1", 70),
        ("element_t3", "1", 0),
        ("crit_multi_t3", "2", 0),
        ("crit_multi_t3", "2", 44),
    ]
    for target, side, min_level in checks:
        probability, target_weight, total = target_stats(bow_mods, target, side, min_level)
        rows.append(
            "<tr>"
            f"<td>{esc(TARGET_LABELS[target])}</td>"
            f"<td>{'前缀' if side == '1' else '后缀'}</td>"
            f"<td>{min_level}</td>"
            f"<td>{fmt(target_weight)} / {fmt(total)}</td>"
            f"<td>{pct(probability)}</td>"
            "</tr>"
        )
    return "".join(rows)


def parse_added_physical_range(text: str) -> tuple[int, int, int, int] | None:
    match = re.search(
        r"Adds \((\d+) - (\d+)\) to \((\d+) - (\d+)\) Physical Damage",
        text,
    )
    if not match:
        return None
    return tuple(int(part) for part in match.groups())


def render_flat_phys_tier_table(bow_mods: list[dict[str, str]]) -> str:
    rows = []
    mods = [
        row
        for row in bow_mods
        if row.get("source_group") == "normal"
        and row.get("generation_type") == "1"
        and row.get("families") == "PhysicalDamage"
        and int(num(row.get("level"))) <= MOD_ILVL
    ]
    mods.sort(key=lambda row: int(num(row.get("level"))), reverse=True)
    for index, row in enumerate(mods, start=1):
        parsed = parse_added_physical_range(row.get("text", ""))
        if not parsed:
            continue
        min_low, min_high, max_low, max_high = parsed
        avg_low = (min_low + max_low) / 2
        avg_high = (min_high + max_high) / 2
        rows.append(
            "<tr>"
            f"<td>T{index}</td>"
            f"<td><code>{esc(row.get('name'))}</code></td>"
            f"<td>{esc(row.get('level'))}</td>"
            f"<td>{fmt(num(row.get('drop_chance')))}</td>"
            f"<td><code>{esc(row.get('text'))}</code></td>"
            f"<td>{min_low}-{min_high}</td>"
            f"<td>{max_low}-{max_high}</td>"
            f"<td>{fmt(avg_low)}-{fmt(avg_high)}</td>"
            f"<td>搜 >= {min_low}/{max_low} 可覆盖本档；想排除下一档以下，可提高到 >= {min_high}/{max_high}</td>"
            "</tr>"
        )
    return (
        "<table>"
        "<thead><tr><th>T级</th><th>英文名</th><th>词缀等级</th><th>权重</th><th>完整范围</th><th>前值范围</th><th>后值范围</th><th>平均点伤范围</th><th>交易搜索提示</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody>"
        "</table>"
    )


def render_state_table(route: str, states: list[tuple[str, str, str, str, str]]) -> str:
    body = []
    for code, valid_mods, empty_slots, actions, stop in states:
        body.append(
            "<tr>"
            f"<td><code>{esc(code)}</code></td>"
            f"<td>{valid_mods}</td>"
            f"<td>{esc(empty_slots)}</td>"
            f"<td>{actions}</td>"
            f"<td>{stop}</td>"
            "</tr>"
        )
    return (
        f"<h4>{esc(route)}状态列表</h4>"
        "<table><thead><tr><th>状态</th><th>已有有效词</th><th>空前缀/后缀</th><th>下一步</th><th>卖出/继续条件</th></tr></thead>"
        f"<tbody>{''.join(body)}</tbody></table>"
    )


def render_transition_table(rows: list[tuple[str, str, str, str, str, str]]) -> str:
    body = []
    for source, target, op, probability, cost_text, condition in rows:
        body.append(
            "<tr>"
            f"<td><code>{esc(source)}</code></td>"
            f"<td><code>{esc(target)}</code></td>"
            f"<td>{op}</td>"
            f"<td>{probability}</td>"
            f"<td>{cost_text}</td>"
            f"<td>{condition}</td>"
            "</tr>"
        )
    return (
        "<h4>状态转移</h4>"
        "<table><thead><tr><th>从</th><th>到</th><th>操作</th><th>概率 / 公式</th><th>造价</th><th>条件</th></tr></thead>"
        f"<tbody>{''.join(body)}</tbody></table>"
    )


def render_routes(
    bow_mods: list[dict[str, str]],
    prices: dict[str, dict[str, str]],
    best: dict[str, Candidate],
) -> str:
    seeking = cost(prices, "Greater Essence of Seeking")
    abrasion = cost(prices, "Greater Essence of Abrasion")
    exalt = cost(prices, "Exalted Orb")
    greater_exalt = cost(prices, "Greater Exalted Orb")
    perfect_exalt = cost(prices, "Perfect Exalted Orb")
    sin_ex = cost(prices, "Omen of Sinistral Exaltation")
    dex_ex = cost(prices, "Omen of Dextral Exaltation")
    greater_omen = cost(prices, "Omen of Greater Exaltation")
    light_omen = cost(prices, "Omen of Light")
    sin_necro = cost(prices, "Omen of Sinistral Necromancy")
    dex_necro = cost(prices, "Omen of Dextral Necromancy")
    preserved = cost(prices, "Preserved Jawbone")
    ancient = cost(prices, "Ancient Jawbone")
    echoes = cost(prices, "Omen of Abyssal Echoes")
    catalysing = cost(prices, "Omen of Catalysing Exaltation")

    phys_start = best["phys_pct_135"]
    flat_start = best["flat_phys_t3"]
    phys_cost = phys_start.average_cost or 0
    flat_cost = flat_start.average_cost or 0

    def material(name: str, value: float | None = None) -> str:
        price = cost(prices, name) if value is None else value
        return f"<code>{label(name)}</code> {money(price)}"

    def material_x(count: int, name: str, value: float | None = None) -> str:
        price = cost(prices, name) if value is None else value
        return f"<code>{count} x {label(name)}</code> {money(price * count)}"

    p_flat_greater, flat_w, flat_total = target_stats(
        bow_mods,
        "flat_phys_t3",
        "1",
        35,
        {"LocalPhysicalDamagePercent", "CriticalStrikeChanceIncrease"},
    )
    p_phys_greater, phys_w, phys_total = target_stats(
        bow_mods,
        "phys_pct_135",
        "1",
        35,
        {"PhysicalDamage", "CriticalStrikeChanceIncrease"},
    )
    p_phys_preserved_single = target_stats(bow_mods, "phys_pct_135", "1", 0)[0]
    p_phys_preserved = choice_probability(p_phys_preserved_single, 3)
    p_phys_preserved_echo = choice_probability(p_phys_preserved_single, 6)
    p_phys_ancient_single = target_stats(bow_mods, "phys_pct_135", "1", 40)[0]
    p_phys_ancient = choice_probability(p_phys_ancient_single, 3)
    p_phys_ancient_echo = choice_probability(p_phys_ancient_single, 6)
    p_flat_preserved = choice_probability(target_stats(bow_mods, "flat_phys_t3", "1", 0)[0], 3)
    p_flat_ancient = choice_probability(target_stats(bow_mods, "flat_phys_t3", "1", 40)[0], 3)
    p_element_preserved = choice_probability(target_stats(bow_mods, "element_t3", "1", 0)[0], 3)
    p_element_echo = choice_probability(target_stats(bow_mods, "element_t3", "1", 0)[0], 6)
    p_multi_normal = target_stats(bow_mods, "crit_multi_t3", "2", 0, {"CriticalStrikeChanceIncrease"})[0]
    p_multi_greater = target_stats(bow_mods, "crit_multi_t3", "2", 35, {"CriticalStrikeChanceIncrease"})[0]
    p_multi_perfect = target_stats(bow_mods, "crit_multi_t3", "2", 50, {"CriticalStrikeChanceIncrease"})[0]
    p_flat_normal = target_stats(
        bow_mods,
        "flat_phys_t3",
        "1",
        0,
        {"LocalPhysicalDamagePercent", "CriticalStrikeChanceIncrease"},
    )[0]
    p_flat_perfect = target_stats(
        bow_mods,
        "flat_phys_t3",
        "1",
        50,
        {"LocalPhysicalDamagePercent", "CriticalStrikeChanceIncrease"},
    )[0]
    p_phys_normal = target_stats(
        bow_mods,
        "phys_pct_135",
        "1",
        0,
        {"PhysicalDamage", "CriticalStrikeChanceIncrease"},
    )[0]
    p_phys_perfect = target_stats(
        bow_mods,
        "phys_pct_135",
        "1",
        50,
        {"PhysicalDamage", "CriticalStrikeChanceIncrease"},
    )[0]

    p_two_prefix = two_prefix_probability(
        bow_mods,
        "flat_phys_t3",
        "element_t3",
        35,
        {"LocalPhysicalDamagePercent", "CriticalStrikeChanceIncrease"},
    )
    p_two_reverse = two_prefix_probability(
        bow_mods,
        "phys_pct_135",
        "element_t3",
        35,
        {"PhysicalDamage", "CriticalStrikeChanceIncrease"},
    )

    useful_after_crit = {"effective_prefix", "effective_suffix"}
    useful_after_flat = {"effective_prefix", "effective_suffix"}
    useful_after_pdps = {"effective_prefix", "effective_suffix"}
    r1_excluded = {"LocalPhysicalDamagePercent", "CriticalStrikeChanceIncrease"}
    r2_excluded = {"PhysicalDamage", "LocalPhysicalDamagePercent", "CriticalStrikeChanceIncrease"}
    r3_excluded = {"LocalPhysicalDamagePercent", "PhysicalDamage"}
    r1_two_normal = two_random_mod_probabilities_with_required(
        bow_mods,
        0,
        useful_after_crit,
        "flat_phys_t3",
        r1_excluded,
    )
    r1_two_greater = two_random_mod_probabilities_with_required(
        bow_mods,
        35,
        useful_after_crit,
        "flat_phys_t3",
        r1_excluded,
    )
    r1_two_perfect = two_random_mod_probabilities_with_required(
        bow_mods,
        50,
        useful_after_crit,
        "flat_phys_t3",
        r1_excluded,
    )
    r1_two_no_flat_normal = two_random_mod_probabilities(
        bow_mods,
        0,
        useful_after_crit,
        r1_excluded | {"PhysicalDamage"},
    )
    r1_two_no_flat_greater = two_random_mod_probabilities(
        bow_mods,
        35,
        useful_after_crit,
        r1_excluded | {"PhysicalDamage"},
    )
    r1_two_no_flat_perfect = two_random_mod_probabilities(
        bow_mods,
        50,
        useful_after_crit,
        r1_excluded | {"PhysicalDamage"},
    )
    r2_two_normal = two_random_mod_probabilities(bow_mods, 0, useful_after_flat, r2_excluded)
    r2_two_greater = two_random_mod_probabilities(bow_mods, 35, useful_after_flat, r2_excluded)
    r2_two_perfect = two_random_mod_probabilities(bow_mods, 50, useful_after_flat, r2_excluded)
    r3_two_normal = two_random_mod_probabilities(bow_mods, 0, useful_after_pdps, r3_excluded)
    r3_two_greater = two_random_mod_probabilities(bow_mods, 35, useful_after_pdps, r3_excluded)
    r3_two_perfect = two_random_mod_probabilities(bow_mods, 50, useful_after_pdps, r3_excluded)
    _, r1_abyss_w, r1_abyss_total = target_stats_any(
        bow_mods,
        {"element_t3"},
        "1",
        0,
        {"LocalPhysicalDamagePercent", "PhysicalDamage"},
    )
    r1_abyss_single = r1_abyss_w / (r1_abyss_total + CRAFT_OF_EXILE_DESECRATED_PREFIX_WEIGHT)
    r1_abyss_three = choice_probability(r1_abyss_single, 3)
    r1_abyss_six = choice_probability(r1_abyss_single, 6)
    _, r1_abyss_ancient_w, r1_abyss_ancient_total = target_stats_any(
        bow_mods,
        {"element_t3"},
        "1",
        40,
        {"LocalPhysicalDamagePercent", "PhysicalDamage"},
    )
    r1_abyss_ancient_single = r1_abyss_ancient_w / (
        r1_abyss_ancient_total + CRAFT_OF_EXILE_DESECRATED_PREFIX_WEIGHT
    )
    r1_abyss_ancient_three = choice_probability(r1_abyss_ancient_single, 3)
    r1_abyss_ancient_six = choice_probability(r1_abyss_ancient_single, 6)
    _, r1_flat_abyss_w, r1_flat_abyss_total = target_stats(
        bow_mods,
        "flat_phys_t3",
        "1",
        0,
        {"LocalPhysicalDamagePercent"},
    )
    r1_flat_abyss_single = r1_flat_abyss_w / (
        r1_flat_abyss_total + CRAFT_OF_EXILE_DESECRATED_PREFIX_WEIGHT
    )
    r1_flat_abyss_three = choice_probability(r1_flat_abyss_single, 3)
    r1_flat_abyss_six = choice_probability(r1_flat_abyss_single, 6)
    _, r1_flat_abyss_ancient_w, r1_flat_abyss_ancient_total = target_stats(
        bow_mods,
        "flat_phys_t3",
        "1",
        40,
        {"LocalPhysicalDamagePercent"},
    )
    r1_flat_abyss_ancient_single = r1_flat_abyss_ancient_w / (
        r1_flat_abyss_ancient_total + CRAFT_OF_EXILE_DESECRATED_PREFIX_WEIGHT
    )
    r1_flat_abyss_ancient_three = choice_probability(r1_flat_abyss_ancient_single, 3)
    r1_flat_abyss_ancient_six = choice_probability(r1_flat_abyss_ancient_single, 6)
    _, r2_phys_abyss_w, r2_phys_abyss_total = target_stats(
        bow_mods,
        "phys_pct_135",
        "1",
        0,
        {"PhysicalDamage"},
    )
    r2_phys_abyss_single = r2_phys_abyss_w / (
        r2_phys_abyss_total + CRAFT_OF_EXILE_DESECRATED_PREFIX_WEIGHT
    )
    r2_phys_abyss_total_with_desecrated = (
        r2_phys_abyss_total + CRAFT_OF_EXILE_DESECRATED_PREFIX_WEIGHT
    )
    r2_phys_abyss_three = choice_probability(r2_phys_abyss_single, 3)
    r2_phys_abyss_six = choice_probability(r2_phys_abyss_single, 6)
    _, r2_phys_abyss_ancient_w, r2_phys_abyss_ancient_total = target_stats(
        bow_mods,
        "phys_pct_135",
        "1",
        40,
        {"PhysicalDamage"},
    )
    r2_phys_abyss_ancient_single = r2_phys_abyss_ancient_w / (
        r2_phys_abyss_ancient_total + CRAFT_OF_EXILE_DESECRATED_PREFIX_WEIGHT
    )
    r2_phys_abyss_ancient_total_with_desecrated = (
        r2_phys_abyss_ancient_total + CRAFT_OF_EXILE_DESECRATED_PREFIX_WEIGHT
    )
    r2_phys_abyss_ancient_three = choice_probability(r2_phys_abyss_ancient_single, 3)
    r2_phys_abyss_ancient_six = choice_probability(r2_phys_abyss_ancient_single, 6)
    _, r3_abyss_w, r3_abyss_total = target_stats_any(
        bow_mods,
        {"element_t3"},
        "1",
        0,
        {"LocalPhysicalDamagePercent", "PhysicalDamage"},
    )
    r3_abyss_single = r3_abyss_w / (r3_abyss_total + CRAFT_OF_EXILE_DESECRATED_PREFIX_WEIGHT)
    r3_abyss_three = choice_probability(r3_abyss_single, 3)
    r3_abyss_six = choice_probability(r3_abyss_single, 6)
    _, r3_abyss_ancient_w, r3_abyss_ancient_total = target_stats_any(
        bow_mods,
        {"element_t3"},
        "1",
        40,
        {"LocalPhysicalDamagePercent", "PhysicalDamage"},
    )
    r3_abyss_ancient_single = r3_abyss_ancient_w / (
        r3_abyss_ancient_total + CRAFT_OF_EXILE_DESECRATED_PREFIX_WEIGHT
    )
    r3_abyss_ancient_three = choice_probability(r3_abyss_ancient_single, 3)
    r3_abyss_ancient_six = choice_probability(r3_abyss_ancient_single, 6)

    normal_prefix_cost = exalt + sin_ex
    greater_prefix_cost = greater_exalt + sin_ex
    perfect_prefix_cost = perfect_exalt + sin_ex
    normal_suffix_cost = exalt + dex_ex
    greater_suffix_cost = greater_exalt + dex_ex
    preserved_prefix_cost = preserved
    preserved_prefix_echo_cost = preserved_prefix_cost + echoes
    ancient_prefix_cost = ancient
    ancient_prefix_echo_cost = ancient_prefix_cost + echoes
    r1_abyss_three_retry = retry_expected(preserved_prefix_cost, r1_abyss_three, light_omen)
    r1_abyss_six_retry = retry_expected(preserved_prefix_echo_cost, r1_abyss_six, light_omen)
    r1_abyss_ancient_three_retry = retry_expected(ancient_prefix_cost, r1_abyss_ancient_three, light_omen)
    r1_abyss_ancient_six_retry = retry_expected(ancient_prefix_echo_cost, r1_abyss_ancient_six, light_omen)
    r1_flat_abyss_three_retry = retry_expected(preserved_prefix_cost, r1_flat_abyss_three, light_omen)
    r1_flat_abyss_six_retry = retry_expected(preserved_prefix_echo_cost, r1_flat_abyss_six, light_omen)
    r1_flat_abyss_ancient_three_retry = retry_expected(
        ancient_prefix_cost,
        r1_flat_abyss_ancient_three,
        light_omen,
    )
    r1_flat_abyss_ancient_six_retry = retry_expected(
        ancient_prefix_echo_cost,
        r1_flat_abyss_ancient_six,
        light_omen,
    )
    r1_abyss_three_directed_retry = r1_abyss_three_retry + sin_necro
    r1_abyss_six_directed_retry = r1_abyss_six_retry + sin_necro
    r1_abyss_ancient_three_directed_retry = r1_abyss_ancient_three_retry + sin_necro
    r1_abyss_ancient_six_directed_retry = r1_abyss_ancient_six_retry + sin_necro
    r1_flat_abyss_ancient_six_directed_retry = r1_flat_abyss_ancient_six_retry + sin_necro
    r2_phys_abyss_three_retry = retry_expected(preserved_prefix_cost, r2_phys_abyss_three, light_omen)
    r2_phys_abyss_six_retry = retry_expected(preserved_prefix_echo_cost, r2_phys_abyss_six, light_omen)
    r2_phys_abyss_ancient_three_retry = retry_expected(
        ancient_prefix_cost,
        r2_phys_abyss_ancient_three,
        light_omen,
    )
    r2_phys_abyss_ancient_six_retry = retry_expected(
        ancient_prefix_echo_cost,
        r2_phys_abyss_ancient_six,
        light_omen,
    )
    r3_abyss_three_retry = retry_expected(preserved_prefix_cost, r3_abyss_three, light_omen)
    r3_abyss_six_retry = retry_expected(preserved_prefix_echo_cost, r3_abyss_six, light_omen)
    r3_abyss_ancient_three_retry = retry_expected(ancient_prefix_cost, r3_abyss_ancient_three, light_omen)
    r3_abyss_ancient_six_retry = retry_expected(ancient_prefix_echo_cost, r3_abyss_ancient_six, light_omen)
    p_phys_preserved_retry = retry_expected(preserved_prefix_cost, p_phys_preserved, light_omen)
    p_phys_preserved_echo_retry = retry_expected(preserved_prefix_echo_cost, p_phys_preserved_echo, light_omen)
    p_flat_preserved_retry = retry_expected(preserved_prefix_cost, p_flat_preserved, light_omen)
    p_element_preserved_retry = retry_expected(preserved_prefix_cost, p_element_preserved, light_omen)
    r1_base_essence_cost = phys_cost + seeking
    r2_base_essence_cost = flat_cost + seeking
    r3_base_abrasion_cost = phys_cost + abrasion
    r1_low_double_cost = greater_omen + exalt
    r1_greater_double_cost = greater_omen + greater_exalt
    r1_perfect_double_cost = greater_omen + perfect_exalt
    r2_low_double_cost = greater_omen + exalt
    r2_high_double_cost = greater_omen + greater_exalt
    r3_low_double_cost = greater_omen + exalt
    r3_high_double_cost = greater_omen + greater_exalt
    r3_perfect_double_cost = greater_omen + perfect_exalt
    r1_low_preloop_expected = (r1_base_essence_cost + r1_low_double_cost) / r1_two_normal[1]
    r1_greater_preloop_expected = (r1_base_essence_cost + r1_greater_double_cost) / r1_two_greater[1]
    r1_perfect_preloop_expected = (r1_base_essence_cost + r1_perfect_double_cost) / r1_two_perfect[1]
    r1_no_flat_low_preloop_expected = (r1_base_essence_cost + r1_low_double_cost) / r1_two_no_flat_normal[1]
    r1_no_flat_greater_preloop_expected = (r1_base_essence_cost + r1_greater_double_cost) / r1_two_no_flat_greater[1]
    r1_no_flat_perfect_preloop_expected = (r1_base_essence_cost + r1_perfect_double_cost) / r1_two_no_flat_perfect[1]
    r2_low_preloop_expected = (r2_base_essence_cost + r2_low_double_cost) / r2_two_normal[1]
    r2_high_preloop_expected = (r2_base_essence_cost + r2_high_double_cost) / r2_two_greater[1]
    r3_low_preloop_expected = (r3_base_abrasion_cost + r3_low_double_cost) / r3_two_normal[1]
    r3_high_preloop_expected = (r3_base_abrasion_cost + r3_high_double_cost) / r3_two_greater[1]
    r3_perfect_preloop_expected = (r3_base_abrasion_cost + r3_perfect_double_cost) / r3_two_perfect[1]
    r1_greater_attempts = 1 / r1_two_no_flat_greater[1] if r1_two_no_flat_greater[1] else 0
    r1_ancient_echo_attempts = (
        1 / r1_flat_abyss_ancient_six
        if r1_flat_abyss_ancient_six
        else 0
    )
    r1_ancient_echo_failures = (
        (1 - r1_flat_abyss_ancient_six) / r1_flat_abyss_ancient_six
        if r1_flat_abyss_ancient_six
        else 0
    )
    r1_base_component = phys_cost * r1_greater_attempts
    r1_seeking_component = seeking * r1_greater_attempts
    r1_greater_omen_component = greater_omen * r1_greater_attempts
    r1_greater_exalt_component = greater_exalt * r1_greater_attempts
    r1_ancient_component = ancient * r1_ancient_echo_attempts
    r1_echo_component = echoes * r1_ancient_echo_attempts
    r1_light_component = light_omen * r1_ancient_echo_failures
    r1_sin_necro_component = sin_necro
    r1_abyss_component = (
        r1_sin_necro_component
        + r1_ancient_component
        + r1_echo_component
        + r1_light_component
    )
    r1_optimal_total = (
        r1_base_component
        + r1_seeking_component
        + r1_greater_omen_component
        + r1_greater_exalt_component
        + r1_abyss_component
    )
    r1_force_flat_total = r1_greater_preloop_expected + r1_abyss_ancient_six_directed_retry
    r1_flat_finish_total = r1_no_flat_greater_preloop_expected + r1_flat_abyss_ancient_six_directed_retry
    r2_low_attempts = 1 / r2_two_normal[1] if r2_two_normal[1] else 0
    r2_best_total_expected = r2_low_preloop_expected + r2_phys_abyss_ancient_six_retry
    r2_ancient_echo_attempts = 1 / r2_phys_abyss_ancient_six if r2_phys_abyss_ancient_six else 0
    r2_ancient_echo_failures = (
        (1 - r2_phys_abyss_ancient_six) / r2_phys_abyss_ancient_six
        if r2_phys_abyss_ancient_six
        else 0
    )
    r3_low_attempts = 1 / r3_two_normal[1] if r3_two_normal[1] else 0
    r3_ancient_echo_attempts = 1 / r3_abyss_ancient_six if r3_abyss_ancient_six else 0
    r3_ancient_echo_failures = (
        (1 - r3_abyss_ancient_six) / r3_abyss_ancient_six
        if r3_abyss_ancient_six
        else 0
    )
    r3_base_component = phys_cost * r3_low_attempts
    r3_abrasion_component = abrasion * r3_low_attempts
    r3_greater_omen_component = greater_omen * r3_low_attempts
    r3_exalt_component = exalt * r3_low_attempts
    r3_ancient_component = ancient * r3_ancient_echo_attempts
    r3_echo_component = echoes * r3_ancient_echo_attempts
    r3_light_component = light_omen * r3_ancient_echo_failures
    r3_abyss_component = r3_ancient_component + r3_echo_component + r3_light_component
    r3_optimal_total = (
        r3_base_component
        + r3_abrasion_component
        + r3_greater_omen_component
        + r3_exalt_component
        + r3_abyss_component
    )
    desecrated_prefixes = [
        row
        for row in bow_mods
        if row.get("source_group") == "desecrated" and row.get("generation_type") == "1"
    ]
    desecrated_suffixes = [
        row
        for row in bow_mods
        if row.get("source_group") == "desecrated" and row.get("generation_type") == "2"
    ]
    greater_double_any = greater_exalt + greater_omen
    two_greater = greater_exalt * 2
    two_greater_prefix = greater_prefix_cost * 2
    greater_double_prefix = greater_exalt + greater_omen + sin_ex

    exalt_rows = []
    for tier_name, min_level, prefix_cost, suffix_cost in [
        ("普通崇高 / Exalted Orb", 0, normal_prefix_cost, normal_suffix_cost),
        ("高阶崇高 / Greater Exalted Orb", 35, greater_prefix_cost, greater_suffix_cost),
        ("完美崇高 / Perfect Exalted Orb", 50, perfect_prefix_cost, perfect_exalt + dex_ex),
    ]:
        p_flat = target_stats(
            bow_mods,
            "flat_phys_t3",
            "1",
            min_level,
            {"LocalPhysicalDamagePercent", "CriticalStrikeChanceIncrease"},
        )[0]
        p_phys = target_stats(
            bow_mods,
            "phys_pct_135",
            "1",
            min_level,
            {"PhysicalDamage", "CriticalStrikeChanceIncrease"},
        )[0]
        p_multi = target_stats(
            bow_mods,
            "crit_multi_t3",
            "2",
            min_level,
            {"CriticalStrikeChanceIncrease"},
        )[0]
        exalt_rows.append(
            "<tr>"
            f"<td>{esc(tier_name)}</td>"
            f"<td>{min_level}</td>"
            f"<td>{money(prefix_cost)} / {pct(p_flat)} / {expected(prefix_cost, p_flat)}</td>"
            f"<td>{money(prefix_cost)} / {pct(p_phys)} / {expected(prefix_cost, p_phys)}</td>"
            f"<td>{money(suffix_cost)} / {pct(p_multi)} / {expected(suffix_cost, p_multi)}</td>"
            "</tr>"
        )

    route1_price_distribution = render_route1_cost_breakdown(
        "路线 1 价格分布：高阶双加和深渊封口分开循环",
        [
            (
                "起步 + 暴击精髓",
                f"<code>{phys_start.code}</code> {money(phys_cost)} + {material('Greater Essence of Seeking', seeking)} = {money(r1_base_essence_cost)}",
                "未进入深渊",
                "100.000%",
                "无",
                money(r1_base_essence_cost),
                "第二步结束的确定成本：已有物理百分比前缀、暴击率后缀，以及精髓产生的随机词。",
            ),
            (
                "低端双加",
                f"前置固定 {money(r1_base_essence_cost)}；每轮 {material('Omen of Greater Exaltation', greater_omen)} + {material('Exalted Orb', exalt)} = {money(r1_low_double_cost)}",
                "未进入深渊",
                f"双加两条都有效且含 T3+ 物理点伤 {pct(r1_two_normal[1])}",
                "失败炸底，重买底并从精髓重做",
                f"{money(r1_low_preloop_expected)} = ({money(r1_base_essence_cost)} + {money(r1_low_double_cost)}) / {pct(r1_two_normal[1])}",
                "成功率=2 条随机词都有效，且其中至少 1 条必须是 T3+ 物理点伤；期望按整把从起步重新做计算。",
            ),
            (
                "高阶双加",
                f"前置固定 {money(r1_base_essence_cost)}；每轮 {material('Omen of Greater Exaltation', greater_omen)} + {material('Greater Exalted Orb', greater_exalt)} = {money(r1_greater_double_cost)}",
                "未进入深渊",
                f"双加两条都有效且含 T3+ 物理点伤 {pct(r1_two_greater[1])}",
                "失败炸底，重买底并从精髓重做",
                f"{money(r1_greater_preloop_expected)} = ({money(r1_base_essence_cost)} + {money(r1_greater_double_cost)}) / {pct(r1_two_greater[1])}",
                "成功率=2 条随机词都有效，且其中至少 1 条必须是 T3+ 物理点伤；高价值基底优先看这个。",
            ),
            (
                "完美双加",
                f"前置固定 {money(r1_base_essence_cost)}；每轮 {material('Omen of Greater Exaltation', greater_omen)} + {material('Perfect Exalted Orb', perfect_exalt)} = {money(r1_perfect_double_cost)}",
                "未进入深渊",
                f"双加两条都有效且含 T3+ 物理点伤 {pct(r1_two_perfect[1])}",
                "失败炸底，重买底并从精髓重做",
                f"{money(r1_perfect_preloop_expected)} = ({money(r1_base_essence_cost)} + {money(r1_perfect_double_cost)}) / {pct(r1_two_perfect[1])}",
                "只适合追高端；完美崇高的最低词缀等级按当前模型为 50。",
            ),
            (
                "高阶双加 + Preserved 封口",
                f"先完成高阶双加，前置期望 {money(r1_greater_preloop_expected)}",
                f"首次定向 {material('Omen of Sinistral Necromancy', sin_necro)}；每轮 {material('Preserved Jawbone', preserved)} = {money(preserved_prefix_cost)}；失败后 {material('Omen of Light', light_omen)}",
                f"双加 {pct(r1_two_greater[1])}；深渊三选 {pct(r1_abyss_three)}",
                f"深渊失败剥离 {money(light_omen)}",
                f"{money(r1_greater_preloop_expected + r1_abyss_three_directed_retry)} = {money(r1_greater_preloop_expected)} + {money(r1_abyss_three_directed_retry)}",
                "左向死灵只算首次定向；成功后深渊失败只剥离重试。",
            ),
            (
                "高阶双加 + Echo 封口",
                f"先完成高阶双加，前置期望 {money(r1_greater_preloop_expected)}",
                f"首次定向 {material('Omen of Sinistral Necromancy', sin_necro)}；每轮 {material('Preserved Jawbone', preserved)} + {material('Omen of Abyssal Echoes', echoes)} = {money(preserved_prefix_echo_cost)}；失败后 {material('Omen of Light', light_omen)}",
                f"双加 {pct(r1_two_greater[1])}；Echo 六选 {pct(r1_abyss_six)}",
                f"深渊失败剥离 {money(light_omen)}",
                f"{money(r1_greater_preloop_expected + r1_abyss_six_directed_retry)} = {money(r1_greater_preloop_expected)} + {money(r1_abyss_six_directed_retry)}",
                "左向死灵只算首次定向；Echo 六选失败同样用光明预兆剥离重试。",
            ),
            (
                "高阶双加 + Ancient 封口",
                f"先完成高阶双加，前置期望 {money(r1_greater_preloop_expected)}",
                f"首次定向 {material('Omen of Sinistral Necromancy', sin_necro)}；每轮 {material('Ancient Jawbone', ancient)} = {money(ancient_prefix_cost)}；失败后 {material('Omen of Light', light_omen)}",
                f"双加 {pct(r1_two_greater[1])}；Ancient 三选 {pct(r1_abyss_ancient_three)}",
                f"深渊失败剥离 {money(light_omen)}",
                f"{money(r1_greater_preloop_expected + r1_abyss_ancient_three_directed_retry)} = {money(r1_greater_preloop_expected)} + {money(r1_abyss_ancient_three_directed_retry)}",
                "Ancient 过滤低级词缀，单次贵但失败次数少。",
            ),
            (
                "高阶双加 + Ancient Echo 封口",
                f"先完成高阶双加，前置期望 {money(r1_greater_preloop_expected)}",
                f"首次定向 {material('Omen of Sinistral Necromancy', sin_necro)}；每轮 {material('Ancient Jawbone', ancient)} + {material('Omen of Abyssal Echoes', echoes)} = {money(ancient_prefix_echo_cost)}；失败后 {material('Omen of Light', light_omen)}",
                f"双加 {pct(r1_two_greater[1])}；Ancient Echo 六选 {pct(r1_abyss_ancient_six)}",
                f"深渊失败剥离 {money(light_omen)}",
                f"{money(r1_greater_preloop_expected + r1_abyss_ancient_six_directed_retry)} = {money(r1_greater_preloop_expected)} + {money(r1_abyss_ancient_six_directed_retry)}",
                "左向死灵只算首次定向；这是点伤前置分支里的最低封口期望。",
            ),
            (
                "高阶双加不含点伤 + Ancient Echo 洗点伤",
                f"先完成高阶双加但不要求物理点伤，前置期望 {money(r1_no_flat_greater_preloop_expected)}",
                f"首次定向 {material('Omen of Sinistral Necromancy', sin_necro)}；每轮 {material('Ancient Jawbone', ancient)} + {material('Omen of Abyssal Echoes', echoes)} = {money(ancient_prefix_echo_cost)}；失败后 {material('Omen of Light', light_omen)}",
                f"双加 {pct(r1_two_no_flat_greater[1])}；物理点伤六选 {pct(r1_flat_abyss_ancient_six)}",
                f"深渊失败剥离 {money(light_omen)}",
                f"{money(r1_flat_finish_total)} = {money(r1_no_flat_greater_preloop_expected)} + {money(r1_flat_abyss_ancient_six_directed_retry)}",
                "当前更便宜：双崇高不用强求物理点伤；左向死灵只算首次深渊定向。",
            ),
        ],
    )
    route1_timing_compare = render_route_candidate_table(
        "路线 1 物理点伤时机比较",
        [
            (
                "A：双崇高阶段出 T3+ 物理点伤",
                "双加两条都有效，且至少 1 条是 T3+ 物理点伤；最后深渊补 T3+ 元素",
                f"每轮前置 {phys_start.code} + {material('Greater Essence of Seeking', seeking)} + {material('Omen of Greater Exaltation', greater_omen)} + {material('Greater Exalted Orb', greater_exalt)}；封口首次加 {material('Omen of Sinistral Necromancy', sin_necro)}，循环用 {material('Ancient Jawbone', ancient)} + {material('Omen of Abyssal Echoes', echoes)}",
                r1_base_essence_cost + r1_greater_double_cost,
                r1_two_greater[1],
                f"前置 {money(r1_greater_preloop_expected)}；封口 {pct(r1_abyss_ancient_six)} / {money(r1_abyss_ancient_six_directed_retry)}",
                "备选",
                money(r1_force_flat_total),
            ),
            (
                "B：最后深渊洗 T3+ 物理点伤",
                "双加两条都有效但不要求物理点伤；最后深渊补 T3+ 物理点伤",
                f"每轮前置 {phys_start.code} + {material('Greater Essence of Seeking', seeking)} + {material('Omen of Greater Exaltation', greater_omen)} + {material('Greater Exalted Orb', greater_exalt)}；封口首次加 {material('Omen of Sinistral Necromancy', sin_necro)}，循环用 {material('Ancient Jawbone', ancient)} + {material('Omen of Abyssal Echoes', echoes)}",
                r1_base_essence_cost + r1_greater_double_cost,
                r1_two_no_flat_greater[1],
                f"前置 {money(r1_no_flat_greater_preloop_expected)}；封口 {pct(r1_flat_abyss_ancient_six)} / {money(r1_flat_abyss_ancient_six_directed_retry)}",
                "推荐",
                money(r1_flat_finish_total),
            ),
        ],
    )
    route1_step_costs = step_cost_table(
        "路线 1 最优路径分步骤成本：S4-P135 + 高阶双加不强求点伤 + Ancient Echo 洗点伤",
        [
            (
                "1. 基底",
                f"<code>{phys_start.code}</code>：135-154% 物理百分比魔法底",
                phys_cost,
                phys_cost,
                "本步只算第一次买入基底；双崇高失败导致的重买成本归到第 3 步。"
            ),
            (
                "2. 基底 + 暴击词",
                f"上一步 + <code>{label('Greater Essence of Seeking')}</code>",
                seeking,
                r1_base_essence_cost,
                "本步只算第一次打精髓；后续失败重做的精髓成本归到第 3 步。"
            ),
            (
                "3. 基底 + 暴击词 + 双崇高有效",
                f"上一步 + <code>{label('Omen of Greater Exaltation')}</code> + <code>{label('Greater Exalted Orb')}</code>",
                r1_no_flat_greater_preloop_expected - r1_base_essence_cost,
                r1_no_flat_greater_preloop_expected,
                f"双加两条都有效即可，但本分支不要求物理点伤；成功率 {pct(r1_two_no_flat_greater[1])}，失败炸底重做，平均总尝试 {fmt(r1_greater_attempts)} 次。"
            ),
            (
                "4. 深渊洗 T3+ 物理点伤",
                f"上一步 + 首次 <code>{label('Omen of Sinistral Necromancy')}</code> + <code>{label('Ancient Jawbone')}</code> + <code>{label('Omen of Abyssal Echoes')}</code>，失败用 <code>{label('Omen of Light')}</code>",
                r1_abyss_component,
                r1_optimal_total,
                f"六选估算 {pct(r1_flat_abyss_ancient_six)}；左向死灵只计 1 次，后续重洗不重复计入。"
            ),
        ],
    )
    route1_material_share = expected_material_table(
        "路线 1 最优路径物品期望消耗",
        [
            (f"<code>{phys_start.code}</code> 135-154% 物理百分比魔法底", r1_greater_attempts, r1_base_component, "双崇高失败会炸底，所以这里是最大成本项。"),
            (f"<code>{label('Greater Essence of Seeking')}</code>", r1_greater_attempts, r1_seeking_component, "每次重做基底都要重新打暴击精髓。"),
            (f"<code>{label('Omen of Greater Exaltation')}</code>", r1_greater_attempts, r1_greater_omen_component, "用于一次补 2 条随机词。"),
            (f"<code>{label('Greater Exalted Orb')}</code>", r1_greater_attempts, r1_greater_exalt_component, "与高阶崇高预兆配套。"),
            (f"<code>{label('Omen of Sinistral Necromancy')}</code>", 1.0, r1_sin_necro_component, "深渊定向前缀只计首次 1 个，后续重洗不重复计。"),
            (f"<code>{label('Ancient Jawbone')}</code>", r1_ancient_echo_attempts, r1_ancient_component, "进入深渊后平均尝试次数。"),
            (f"<code>{label('Omen of Abyssal Echoes')}</code>", r1_ancient_echo_attempts, r1_echo_component, "把三选一变六选一。"),
            (f"<code>{label('Omen of Light')}</code>", r1_ancient_echo_failures, r1_light_component, "深渊失败后剥离深渊词。"),
        ],
    )
    route1_ops = render_route_candidate_table(
        "路线 1 候选路径表：第二步确定，第三步以后按候选池比较",
        [
            (f"R1-BASE：{TARGET_LABELS['phys_pct_135']} 起步底", "统一起步模块推荐", f"<code>{phys_start.code}</code>：{phys_start.materials}", phys_cost, 1.0, "基底价格进入路线 1 总成本", "推荐"),
            ("R1-S1：物理百分比 + 暴击率 + 随机词", "确定步骤：精髓补暴击", material("Greater Essence of Seeking", seeking), seeking, 1.0, "第二步必做；本行是第二步最优解", "推荐"),
            ("R1-S2：随机补 2 词，2 条都有效，不强求物理点伤", "大幅提升预兆 + 高阶崇高，一次加 2 词", f"{material('Omen of Greater Exaltation', greater_omen)} + {material('Greater Exalted Orb', greater_exalt)}", greater_omen + greater_exalt, r1_two_no_flat_greater[1], f"前置期望 {money(r1_no_flat_greater_preloop_expected)}；后续深渊洗物理点伤", "推荐", money(r1_no_flat_greater_preloop_expected)),
            ("R1-S2：随机补 2 词，2 条都有效且含物理点伤", "2 个普通崇高直接连点", material_x(2, "Exalted Orb", exalt), exalt * 2, r1_two_normal[1], f"至少 1 条有效：{pct(r1_two_normal[0])}", "低端备选"),
            ("R1-S2：随机补 2 词，2 条都有效且含物理点伤", "大幅提升预兆 + 普通崇高，一次加 2 词", f"{material('Omen of Greater Exaltation', greater_omen)} + {material('Exalted Orb', exalt)}", greater_omen + exalt, r1_two_normal[1], f"同 2 个普通崇高；至少 1 条有效：{pct(r1_two_normal[0])}", "低端备选"),
            ("R1-S2：随机补 2 词，2 条都有效且含物理点伤", "2 个高阶崇高直接连点", material_x(2, "Greater Exalted Orb", greater_exalt), greater_exalt * 2, r1_two_greater[1], f"至少 1 条有效：{pct(r1_two_greater[0])}", "被下一项替代"),
            ("R1-S2：随机补 2 词，2 条都有效且含物理点伤", "大幅提升预兆 + 高阶崇高，一次加 2 词", f"{material('Omen of Greater Exaltation', greater_omen)} + {material('Greater Exalted Orb', greater_exalt)}", greater_omen + greater_exalt, r1_two_greater[1], f"同 2 个高阶崇高；至少 1 条有效：{pct(r1_two_greater[0])}", "点伤前置备选"),
            ("R1-S2：随机补 2 词，2 条都有效且含物理点伤", "大幅提升预兆 + 完美崇高，一次加 2 词", f"{material('Omen of Greater Exaltation', greater_omen)} + {material('Perfect Exalted Orb', perfect_exalt)}", greater_omen + perfect_exalt, r1_two_perfect[1], f"至少 1 条有效：{pct(r1_two_perfect[0])}", "很贵，追高端才看"),
            ("R1-S3：深渊补 T3+ 物理点伤", "左向定向 + Ancient Echo 六选，可循环重试", f"首次 {material('Omen of Sinistral Necromancy', sin_necro)} + 每轮 {material('Ancient Jawbone', ancient)} + {material('Omen of Abyssal Echoes', echoes)}；失败后 {material('Omen of Light', light_omen)} 剥离深渊词", ancient_prefix_echo_cost + sin_necro, r1_flat_abyss_ancient_six, "目标：T3+ 物理点伤；左向只计首次", "推荐", money(r1_flat_abyss_ancient_six_directed_retry)),
            ("R1-S3：深渊补 1 条有效前缀", "Preserved 三选一，可循环重试", f"{material('Preserved Jawbone', preserved)}；失败后 {material('Omen of Light', light_omen)} 剥离深渊词", preserved_prefix_cost, r1_abyss_three, "目标：T3+ 元素；物理点伤已由双崇高步骤保证", "低端封口", money(r1_abyss_three_retry)),
            ("R1-S3：深渊补 1 条有效前缀", "Preserved + Echo 六选，可循环重试", f"{material('Preserved Jawbone', preserved)} + {material('Omen of Abyssal Echoes', echoes)}；失败后 {material('Omen of Light', light_omen)} 剥离深渊词", preserved_prefix_echo_cost, r1_abyss_six, "目标：T3+ 元素；物理点伤已由双崇高步骤保证", "高价胚才看", money(r1_abyss_six_retry)),
            ("R1-S3：深渊补 1 条有效前缀", "Ancient 三选一，可循环重试", f"{material('Ancient Jawbone', ancient)}；失败后 {material('Omen of Light', light_omen)} 剥离深渊词", ancient_prefix_cost, r1_abyss_ancient_three, "Ancient 最低词缀等级 40；目标仍是 T3+ 元素", "高价胚", money(r1_abyss_ancient_three_retry)),
            ("R1-S3：深渊补 1 条有效前缀", "Ancient + Echo 六选，可循环重试", f"{material('Ancient Jawbone', ancient)} + {material('Omen of Abyssal Echoes', echoes)}；失败后 {material('Omen of Light', light_omen)} 剥离深渊词", ancient_prefix_echo_cost, r1_abyss_ancient_six, "分母已加入 Craft of Exile 弓深渊前缀权重", "点伤前置可选", money(r1_abyss_ancient_six_retry)),
        ],
    )
    route2_states = render_state_table(
        "路线 2：暴击物理点伤反做",
        [
            ("R2-S0", f"来自起步池 <code>{flat_start.code}</code>：{TARGET_LABELS['flat_phys_t3']}", "需要保留 1 个前缀空位", f"<code>{label('Greater Essence of Seeking')}</code>", "低成本入口；不需要先付高价物理百分比底。"),
            ("R2-S1", "<code>T3+ Physical Damage / T3+ 物理点伤</code> + <code>Critical Hit Chance / 暴击率</code> + 精髓随机词", "只继续有前缀空位的胚", "深渊定向洗 135%+ 物理百分比", "若随机词占满前缀或价值差，直接卖/跳过。"),
            ("R2-S2", "物理点伤 + 暴击率 + 135%+ 物理百分比", "三核心成立", "再补元素前缀或好后缀", "命中三核心后先估价，通常可以卖。"),
            ("R2-S3", "三核心 + 高元素/暴伤/攻速之一", "接近毕业", "只做高价值封口", "不把元素前缀算作路线 2 第三步成功。"),
        ],
    )
    route2_transitions = render_transition_table(
        [
            ("起步池", "R2-S0", "选择最低成本 T3+ 物理点伤候选", "由统一起步模块计算", f"{fmt(flat_cost)}E", "当前手动 4E 直接买通常是低成本基准。"),
            ("R2-S0", "R2-S1", f"<code>{label('Greater Essence of Seeking')}</code>", "精髓固定暴击率", f"{fmt(seeking)}E", "进入 2 词稀有。"),
            ("R2-S1", "R2-S2", f"<code>{label('Omen of Greater Exaltation')}</code> + <code>{label('Exalted Orb')}</code>", f"双加两条都有效 {pct(r2_two_normal[1])}", f"前置期望 {money(r2_low_preloop_expected)}", "先做会炸底的步骤；失败从点伤底重做。"),
            ("R2-S2", "R2-S3", f"<code>{label('Ancient Jawbone')}</code> + <code>{label('Omen of Abyssal Echoes')}</code>，失败后 <code>{label('Omen of Light')}</code> 剥离重试", f"最后补 135%+ 物理百分比，六选：1 - (1 - {pct(r2_phys_abyss_ancient_single)})^6 = {pct(r2_phys_abyss_ancient_six)}", f"重试期望 {money(r2_phys_abyss_ancient_six_retry)}", "深渊能无限洗，放在最后；分母加入 Craft of Exile 深渊前缀权重。"),
        ]
    )
    route2_price_distribution = render_route1_cost_breakdown(
        "路线 2 价格分布：物理百分比必须靠深渊循环",
        [
            (
                "起步 + 暴击精髓",
                f"<code>{flat_start.code}</code> {money(flat_cost)} + {material('Greater Essence of Seeking', seeking)} = {money(r2_base_essence_cost)}",
                "未进入深渊",
                "100.000%",
                "无",
                money(r2_base_essence_cost),
                "第二步结束的确定成本：已有物理点伤前缀、暴击率后缀，以及精髓产生的随机词；只继续有前缀空位的胚。"
            ),
            (
                "低端双加",
                f"前置固定 {money(r2_base_essence_cost)}；每轮 {material('Omen of Greater Exaltation', greater_omen)} + {material('Exalted Orb', exalt)} = {money(r2_low_double_cost)}",
                "未进入深渊",
                f"双加两条都有效 {pct(r2_two_normal[1])}",
                "失败炸底，重买点伤底并从精髓重做",
                f"{money(r2_low_preloop_expected)} = ({money(r2_base_essence_cost)} + {money(r2_low_double_cost)}) / {pct(r2_two_normal[1])}",
                "先做不可逆步骤；成功后才进入深渊物理百分比循环。"
            ),
            (
                "高阶双加",
                f"前置固定 {money(r2_base_essence_cost)}；每轮 {material('Omen of Greater Exaltation', greater_omen)} + {material('Greater Exalted Orb', greater_exalt)} = {money(r2_high_double_cost)}",
                "未进入深渊",
                f"双加两条都有效 {pct(r2_two_greater[1])}",
                "失败炸底，重买点伤底并从精髓重做",
                f"{money(r2_high_preloop_expected)} = ({money(r2_base_essence_cost)} + {money(r2_high_double_cost)}) / {pct(r2_two_greater[1])}",
                "高阶更贵；当前低端双加期望更低。"
            ),
            (
                "Preserved 定向物理百分比",
                f"先完成低端双加，前置期望 {money(r2_low_preloop_expected)}",
                f"每轮 {material('Preserved Jawbone', preserved)} = {money(preserved_prefix_cost)}；失败后 {material('Omen of Light', light_omen)}",
                f"三选 {pct(r2_phys_abyss_three)}",
                f"深渊失败剥离 {money(light_omen)}",
                f"{money(r2_low_preloop_expected + r2_phys_abyss_three_retry)} = {money(r2_low_preloop_expected)} + {money(r2_phys_abyss_three_retry)}",
                "最后一步只认 135%+ 物理百分比；失败不报废，分母加入 Craft of Exile 深渊前缀权重。"
            ),
            (
                "Preserved Echo 定向物理百分比",
                f"先完成低端双加，前置期望 {money(r2_low_preloop_expected)}",
                f"每轮 {material('Preserved Jawbone', preserved)} + {material('Omen of Abyssal Echoes', echoes)} = {money(preserved_prefix_echo_cost)}；失败后 {material('Omen of Light', light_omen)}",
                f"六选 {pct(r2_phys_abyss_six)}",
                f"深渊失败剥离 {money(light_omen)}",
                f"{money(r2_low_preloop_expected + r2_phys_abyss_six_retry)} = {money(r2_low_preloop_expected)} + {money(r2_phys_abyss_six_retry)}",
                "Echo 提高成功率；因为光明预兆很贵，期望低于普通 Preserved。"
            ),
            (
                "Ancient 定向物理百分比",
                f"先完成低端双加，前置期望 {money(r2_low_preloop_expected)}",
                f"每轮 {material('Ancient Jawbone', ancient)} = {money(ancient_prefix_cost)}；失败后 {material('Omen of Light', light_omen)}",
                f"Ancient 三选 {pct(r2_phys_abyss_ancient_three)}",
                f"深渊失败剥离 {money(light_omen)}",
                f"{money(r2_low_preloop_expected + r2_phys_abyss_ancient_three_retry)} = {money(r2_low_preloop_expected)} + {money(r2_phys_abyss_ancient_three_retry)}",
                "Ancient 过滤低级词缀，物理百分比占比上升。"
            ),
            (
                "Ancient Echo 定向物理百分比",
                f"先完成低端双加，前置期望 {money(r2_low_preloop_expected)}",
                f"每轮 {material('Ancient Jawbone', ancient)} + {material('Omen of Abyssal Echoes', echoes)} = {money(ancient_prefix_echo_cost)}；失败后 {material('Omen of Light', light_omen)}",
                f"Ancient Echo 六选 {pct(r2_phys_abyss_ancient_six)}",
                f"深渊失败剥离 {money(light_omen)}",
                f"{money(r2_best_total_expected)} = {money(r2_low_preloop_expected)} + {money(r2_phys_abyss_ancient_six_retry)}",
                "当前路线 2 最低期望；使用 Craft of Exile 外推深渊前缀权重。"
            ),
        ],
    )
    route2_ops = render_route_candidate_table(
        "路线 2 候选路径表：点伤底 + 暴击后，必须深渊补物理百分比",
        [
            (f"R2-BASE：{TARGET_LABELS['flat_phys_t3']} 起步底", "统一起步模块推荐", f"<code>{flat_start.code}</code>：{flat_start.materials}", flat_cost, 1.0, "基底价格进入路线 2 总成本", "推荐"),
            ("R2-S1：物理点伤 + 暴击率 + 随机词", "确定步骤：精髓补暴击", material("Greater Essence of Seeking", seeking), seeking, 1.0, "第二步必做；本行是第二步最优解", "推荐"),
            ("R2-S2：深渊前先补 2 条有效词", "大幅提升预兆 + 普通崇高，一次加 2 词", f"{material('Omen of Greater Exaltation', greater_omen)} + {material('Exalted Orb', exalt)}", greater_omen + exalt, r2_two_normal[1], f"深渊前置步骤；失败炸底重做，前置期望 {money(r2_low_preloop_expected)}", "低端推荐"),
            ("R2-S2：深渊前先补 2 条有效词", "大幅提升预兆 + 高阶崇高，一次加 2 词", f"{material('Omen of Greater Exaltation', greater_omen)} + {material('Greater Exalted Orb', greater_exalt)}", greater_omen + greater_exalt, r2_two_greater[1], f"深渊前置步骤；失败炸底重做，前置期望 {money(r2_high_preloop_expected)}", "高端备选"),
            ("R2-S2：深渊补 135%+ 物理百分比", "Preserved 三选一，可循环重试", f"{material('Preserved Jawbone', preserved)}；失败后 {material('Omen of Light', light_omen)} 剥离深渊词", preserved_prefix_cost, r2_phys_abyss_three, f"单抽权重 {fmt(r2_phys_abyss_w)} / {fmt(r2_phys_abyss_total_with_desecrated)}；失败不报废", "低端备选", money(r2_phys_abyss_three_retry)),
            ("R2-S2：深渊补 135%+ 物理百分比", "Preserved + Echo 六选，可循环重试", f"{material('Preserved Jawbone', preserved)} + {material('Omen of Abyssal Echoes', echoes)}；失败后 {material('Omen of Light', light_omen)} 剥离深渊词", preserved_prefix_echo_cost, r2_phys_abyss_six, "只认 135%+ 物理百分比；Echo 六选", "备选", money(r2_phys_abyss_six_retry)),
            ("R2-S2：深渊补 135%+ 物理百分比", "Ancient 三选一，可循环重试", f"{material('Ancient Jawbone', ancient)}；失败后 {material('Omen of Light', light_omen)} 剥离深渊词", ancient_prefix_cost, r2_phys_abyss_ancient_three, f"Ancient 权重 {fmt(r2_phys_abyss_ancient_w)} / {fmt(r2_phys_abyss_ancient_total_with_desecrated)}", "高价备选", money(r2_phys_abyss_ancient_three_retry)),
            ("R2-S3：最后深渊补 135%+ 物理百分比", "Ancient + Echo 六选，可循环重试", f"{material('Ancient Jawbone', ancient)} + {material('Omen of Abyssal Echoes', echoes)}；失败后 {material('Omen of Light', light_omen)} 剥离深渊词", ancient_prefix_echo_cost, r2_phys_abyss_ancient_six, "使用 Craft of Exile 外推深渊前缀权重", "高价推荐", money(r2_phys_abyss_ancient_six_retry)),
        ],
    )
    route2_share = expected_material_table(
        "路线 2 最优路径成本占比：Ancient Echo 洗 135%+ 物理百分比",
        [
            ("T3+ 物理点伤起步底", r2_low_attempts, flat_cost * r2_low_attempts, "双加失败会炸底，所以要重买点伤底。"),
            (f"<code>{label('Greater Essence of Seeking')}</code>", r2_low_attempts, seeking * r2_low_attempts, "每次重做基底都要重新打暴击精髓。"),
            (f"<code>{label('Omen of Greater Exaltation')}</code>", r2_low_attempts, greater_omen * r2_low_attempts, "深渊前先做双加。"),
            (f"<code>{label('Exalted Orb')}</code>", r2_low_attempts, exalt * r2_low_attempts, "与高阶崇高预兆配套。"),
            (f"<code>{label('Ancient Jawbone')}</code>", r2_ancient_echo_attempts, ancient * r2_ancient_echo_attempts, "深渊循环平均尝试次数。"),
            (f"<code>{label('Omen of Abyssal Echoes')}</code>", r2_ancient_echo_attempts, echoes * r2_ancient_echo_attempts, "每次 Ancient 封口配一个 Echo。"),
            (f"<code>{label('Omen of Light')}</code>", r2_ancient_echo_failures, light_omen * r2_ancient_echo_failures, "深渊失败后剥离重试。"),
        ],
    )
    route2_step_costs = step_cost_table(
        "路线 2 分步骤成本：点伤底反做物理百分比",
        [
            (
                "1. 基底",
                f"<code>{flat_start.code}</code>：T3+ 物理点伤魔法底",
                flat_cost,
                flat_cost,
                "直接买点伤底，不从高价物理百分比底起步。"
            ),
            (
                "2. 基底 + 暴击词",
                f"上一步 + <code>{label('Greater Essence of Seeking')}</code>",
                seeking,
                r2_base_essence_cost,
                "精髓固定暴击率；只继续有前缀空位的胚。"
            ),
            (
                "3. 深渊前双加有效",
                f"上一步 + <code>{label('Omen of Greater Exaltation')}</code> + <code>{label('Exalted Orb')}</code>",
                r2_low_preloop_expected - r2_base_essence_cost,
                r2_low_preloop_expected,
                f"双加两条都有效才进入深渊；成功率 {pct(r2_two_normal[1])}，失败炸底重做。"
            ),
            (
                "4. 最后深渊定向物理百分比",
                f"上一步 + <code>{label('Ancient Jawbone')}</code> + <code>{label('Omen of Abyssal Echoes')}</code>，失败用 <code>{label('Omen of Light')}</code>",
                r2_phys_abyss_ancient_six_retry,
                r2_best_total_expected,
                f"只认 135%+ 物理百分比；六选估算 {pct(r2_phys_abyss_ancient_six)}，失败可无限洗。"
            ),
        ],
    )

    route3_states = render_state_table(
        "路线 3：非暴击 pDPS 量产",
        [
            ("R3-S0", f"来自起步池 <code>{phys_start.code}</code>：{TARGET_LABELS['phys_pct_135']}", "2 前缀 / 2-3 后缀", f"<code>{label('Greater Essence of Abrasion')}</code>", "不强求暴击；暴击后缀出现也只算有效词之一。"),
            ("R3-S1", "<code>135%+ Physical Damage / 135%+ 物理百分比</code> + <code>Physical Damage / 物理点伤</code>", "1 前缀 / 3 后缀", "补元素、攻速、暴击、暴伤", "2 条物理前缀已经可卖，低价货优先周转。"),
            ("R3-S2", "双物理前缀 + 2 条有效词", "0-1 前缀 / 1-2 后缀", "大幅提升预兆 + 崇高继续补有效词", "3-4 条有效词为中间过渡，可按 pDPS/eDPS 定价。"),
            ("R3-S3", "双物理 + 元素 + 2 个好后缀", "0 前缀 / 0-1 后缀", "只做符文/品质补强", "接近毕业；完美毕业要求核心多为 T1/T2。"),
        ],
    )
    route3_transitions = render_transition_table(
        [
            ("起步池", "R3-S0", "选择最低成本 135%+ 物理百分比候选", "由统一起步模块计算", f"{fmt(phys_cost)}E", "与路线 1 共用起步池。"),
            ("R3-S0", "R3-S1", f"<code>{label('Greater Essence of Abrasion')}</code>", "精髓固定物理点伤", f"{fmt(abrasion)}E", "稳定形成双物理前缀。"),
            ("R3-S1", "R3-S2", f"<code>{label('Omen of Greater Exaltation')}</code> + 崇高", f"普通双加两条都有效 {pct(r3_two_normal[1])}；高阶 {pct(r3_two_greater[1])}", f"{money(greater_omen + exalt)} / {money(greater_omen + greater_exalt)}", "先用大幅提升找有效词；暴击后缀也算有效。"),
            ("R3-S2", "R3-S3", "深渊或继续崇高补最后有效词", f"深渊元素三选 {pct(r3_abyss_three)}；Echo 六选 {pct(r3_abyss_six)}", f"{fmt(preserved_prefix_cost)}E / {fmt(preserved_prefix_echo_cost)}E", "深渊放在后段，失败可光明剥离重试；分母加入 Craft of Exile 深渊前缀权重。"),
        ]
    )
    route3_step_costs = step_cost_table(
        "路线 3 最优路径分步骤成本：S4-P135 + 高阶磨蚀 + 低端双加 + Ancient Echo",
        [
            (
                "1. 基底",
                f"<code>{phys_start.code}</code>：135-154% 物理百分比魔法底",
                phys_cost,
                phys_cost,
                "与路线 1 共用统一起步池；本步只算第一次买入基底。"
            ),
            (
                "2. 基底 + 物理点伤",
                f"上一步 + <code>{label('Greater Essence of Abrasion')}</code>",
                abrasion,
                r3_base_abrasion_cost,
                "磨蚀精髓固定物理点伤；这条路线不强求暴击。"
            ),
            (
                "3. 双加两条有效",
                f"上一步 + <code>{label('Omen of Greater Exaltation')}</code> + <code>{label('Exalted Orb')}</code>",
                r3_low_preloop_expected - r3_base_abrasion_cost,
                r3_low_preloop_expected,
                f"双加两条都有效才继续；成功率 {pct(r3_two_normal[1])}，失败炸底重做。暴击后缀可算有效，但不是必需。"
            ),
            (
                "4. 深渊补 T3+ 元素",
                f"上一步 + <code>{label('Ancient Jawbone')}</code> + <code>{label('Omen of Abyssal Echoes')}</code>，失败用 <code>{label('Omen of Light')}</code>",
                r3_abyss_ancient_six_retry,
                r3_optimal_total,
                f"六选估算 {pct(r3_abyss_ancient_six)}；失败只剥离深渊词，不重买底。"
            ),
        ],
    )
    route3_material_share = expected_material_table(
        "路线 3 最优路径物品期望消耗",
        [
            (f"<code>{phys_start.code}</code> 135-154% 物理百分比魔法底", r3_low_attempts, r3_base_component, "双加失败会炸底，所以要重买基底。"),
            (f"<code>{label('Greater Essence of Abrasion')}</code>", r3_low_attempts, r3_abrasion_component, "每次重做基底都要重新打磨蚀精髓。"),
            (f"<code>{label('Omen of Greater Exaltation')}</code>", r3_low_attempts, r3_greater_omen_component, "用于一次补 2 条随机词。"),
            (f"<code>{label('Exalted Orb')}</code>", r3_low_attempts, r3_exalt_component, "低端量产用普通崇高配大幅提升预兆。"),
            (f"<code>{label('Ancient Jawbone')}</code>", r3_ancient_echo_attempts, r3_ancient_component, "进入深渊后平均尝试次数。"),
            (f"<code>{label('Omen of Abyssal Echoes')}</code>", r3_ancient_echo_attempts, r3_echo_component, "把三选一变六选一。"),
            (f"<code>{label('Omen of Light')}</code>", r3_ancient_echo_failures, r3_light_component, "深渊失败后剥离深渊词。"),
        ],
    )
    route3_price_distribution = render_route1_cost_breakdown(
        "路线 3 价格分布：不强求暴击，只要求双加有效",
        [
            (
                "起步 + 磨蚀精髓",
                f"<code>{phys_start.code}</code> {money(phys_cost)} + {material('Greater Essence of Abrasion', abrasion)} = {money(r3_base_abrasion_cost)}",
                "未进入深渊",
                "100.000%",
                "无",
                money(r3_base_abrasion_cost),
                "第二步结束的确定成本：已有物理百分比前缀、物理点伤前缀，以及精髓产生的随机词。"
            ),
            (
                "低端双加",
                f"前置固定 {money(r3_base_abrasion_cost)}；每轮 {material('Omen of Greater Exaltation', greater_omen)} + {material('Exalted Orb', exalt)} = {money(r3_low_double_cost)}",
                "未进入深渊",
                f"双加两条都有效 {pct(r3_two_normal[1])}",
                "失败炸底，重买底并从磨蚀精髓重做",
                f"{money(r3_low_preloop_expected)} = ({money(r3_base_abrasion_cost)} + {money(r3_low_double_cost)}) / {pct(r3_two_normal[1])}",
                "当前量产推荐；暴击后缀算有效，但不强求暴击。"
            ),
            (
                "高阶双加",
                f"前置固定 {money(r3_base_abrasion_cost)}；每轮 {material('Omen of Greater Exaltation', greater_omen)} + {material('Greater Exalted Orb', greater_exalt)} = {money(r3_high_double_cost)}",
                "未进入深渊",
                f"双加两条都有效 {pct(r3_two_greater[1])}",
                "失败炸底，重买底并从磨蚀精髓重做",
                f"{money(r3_high_preloop_expected)} = ({money(r3_base_abrasion_cost)} + {money(r3_high_double_cost)}) / {pct(r3_two_greater[1])}",
                "高阶更贵，当前不作为量产推荐。"
            ),
            (
                "低端双加 + Preserved 封口",
                f"先完成低端双加，前置期望 {money(r3_low_preloop_expected)}",
                f"每轮 {material('Preserved Jawbone', preserved)} = {money(preserved_prefix_cost)}；失败后 {material('Omen of Light', light_omen)}",
                f"深渊三选 {pct(r3_abyss_three)}",
                f"深渊失败剥离 {money(light_omen)}",
                f"{money(r3_low_preloop_expected + r3_abyss_three_retry)} = {money(r3_low_preloop_expected)} + {money(r3_abyss_three_retry)}",
                "低端封口；失败不报废。"
            ),
            (
                "低端双加 + Echo 封口",
                f"先完成低端双加，前置期望 {money(r3_low_preloop_expected)}",
                f"每轮 {material('Preserved Jawbone', preserved)} + {material('Omen of Abyssal Echoes', echoes)} = {money(preserved_prefix_echo_cost)}；失败后 {material('Omen of Light', light_omen)}",
                f"Echo 六选 {pct(r3_abyss_six)}",
                f"深渊失败剥离 {money(light_omen)}",
                f"{money(r3_low_preloop_expected + r3_abyss_six_retry)} = {money(r3_low_preloop_expected)} + {money(r3_abyss_six_retry)}",
                "Echo 降低封口期望，但仍高于 Ancient Echo。"
            ),
            (
                "低端双加 + Ancient Echo 封口",
                f"先完成低端双加，前置期望 {money(r3_low_preloop_expected)}",
                f"每轮 {material('Ancient Jawbone', ancient)} + {material('Omen of Abyssal Echoes', echoes)} = {money(ancient_prefix_echo_cost)}；失败后 {material('Omen of Light', light_omen)}",
                f"Ancient Echo 六选 {pct(r3_abyss_ancient_six)}",
                f"深渊失败剥离 {money(light_omen)}",
                f"{money(r3_optimal_total)} = {money(r3_low_preloop_expected)} + {money(r3_abyss_ancient_six_retry)}",
                "当前路线 3 最低期望；适合已有可卖双物理胚时封口。"
            ),
        ],
    )
    route3_ops = render_route_candidate_table(
        "路线 3 候选路径表：双物理后补有效词",
        [
            (f"R3-BASE：{TARGET_LABELS['phys_pct_135']} 起步底", "统一起步模块推荐", f"<code>{phys_start.code}</code>：{phys_start.materials}", phys_cost, 1.0, "基底价格进入路线 3 总成本", "推荐"),
            ("R3-S1：双物理前缀 + 随机词", "确定步骤：磨蚀精髓补物理点伤", material("Greater Essence of Abrasion", abrasion), abrasion, 1.0, "第二步必做；本行是第二步最优解", "推荐"),
            ("R3-S2：随机补 2 词，2 条都有效", "大幅提升预兆 + 普通崇高，一次加 2 词", f"{material('Omen of Greater Exaltation', greater_omen)} + {material('Exalted Orb', exalt)}", greater_omen + exalt, r3_two_normal[1], f"至少 1 条有效：{pct(r3_two_normal[0])}", "低端推荐"),
            ("R3-S2：随机补 2 词，2 条都有效", "大幅提升预兆 + 高阶崇高，一次加 2 词", f"{material('Omen of Greater Exaltation', greater_omen)} + {material('Greater Exalted Orb', greater_exalt)}", greater_omen + greater_exalt, r3_two_greater[1], f"至少 1 条有效：{pct(r3_two_greater[0])}", "高端备选"),
            ("R3-S2：随机补 2 词，2 条都有效", "大幅提升预兆 + 完美崇高，一次加 2 词", f"{material('Omen of Greater Exaltation', greater_omen)} + {material('Perfect Exalted Orb', perfect_exalt)}", greater_omen + perfect_exalt, r3_two_perfect[1], f"至少 1 条有效：{pct(r3_two_perfect[0])}", "很贵"),
            ("R3-S2：深渊补元素前缀", "Preserved 三选一，可循环重试", f"{material('Preserved Jawbone', preserved)}；失败后 {material('Omen of Light', light_omen)} 剥离深渊词", preserved_prefix_cost, r3_abyss_three, "目标：T3+ 元素；失败不报废", "低端封口", money(r3_abyss_three_retry)),
            ("R3-S2：深渊补元素前缀", "Preserved + Echo 六选，可循环重试", f"{material('Preserved Jawbone', preserved)} + {material('Omen of Abyssal Echoes', echoes)}；失败后 {material('Omen of Light', light_omen)} 剥离深渊词", preserved_prefix_echo_cost, r3_abyss_six, "目标：T3+ 元素；失败不报废", "高价胚才看", money(r3_abyss_six_retry)),
            ("R3-S2：深渊补元素前缀", "Ancient + Echo 六选，可循环重试", f"{material('Ancient Jawbone', ancient)} + {material('Omen of Abyssal Echoes', echoes)}；失败后 {material('Omen of Light', light_omen)} 剥离深渊词", ancient_prefix_echo_cost, r3_abyss_ancient_six, "目标：T3+ 元素；失败不报废", "推荐封口", money(r3_abyss_ancient_six_retry)),
        ],
    )
    formula_html = f"""
      <h4>概率公式</h4>
      <table>
        <thead><tr><th>机制</th><th>公式</th><th>本报告用法</th></tr></thead>
        <tbody>
          <tr><td>蜕变 + 可选增幅</td><td><code>P = P(蜕变直接命中) + P(蜕变出另一侧) x P(增幅命中目标侧)</code></td><td>统一起步池 S1-S3。</td></tr>
          <tr><td>随机补 2 词</td><td><code>P(2 条都有效) = sum(P(第一条有效) x P(第二条有效 | 第一条已剔除同族))</code></td><td>连续 2 个崇高和 <code>Omen of Greater Exaltation / 高阶崇高预兆</code> 都按 2 条随机词处理；主成功率要求 2 条都有效。</td></tr>
          <tr><td>深渊三选一</td><td><code>1 - (1 - p)^3</code></td><td>Preserved / Ancient 分开算。</td></tr>
          <tr><td>深渊回响六选</td><td><code>1 - (1 - p)^6</code></td><td>Echo 成本单独加入，不只看概率翻倍。</td></tr>
          <tr><td>深渊失败重试</td><td><code>期望 = (尝试成本 + (1 - p) x 光明预兆成本) / p</code></td><td>失败后用 <code>Omen of Light / 光明预兆</code> 剥离深渊词，回到同一个胚子继续洗。</td></tr>
          <tr><td>Ancient Jawbone</td><td><code>最低词缀等级 40</code></td><td>低级前缀被过滤，目标词权重占比上升，所以成功率高于 Preserved；但材料单价也更高。</td></tr>
          <tr><td>路线 1 双加成功</td><td><code>P = sum(P(第一条有效) x P(第二条有效 | 剔除同族))</code></td><td>额外要求两条都有效，且其中至少一条是 <code>T3+ Adds Physical Damage / T3+ 物理点伤</code>。</td></tr>
        </tbody>
      </table>
      <div class="callout">深渊封口现在按“只剩 1 个词缀空位”建模：Jawbone 必然占这个空位，所以不叠加左向/右向死灵预兆。失败后用 <code>Omen of Light / 光明预兆</code> 剥离这条深渊词并重试，因此深渊步骤是可循环期望，不像崇高失败那样必须重买底材。<code>Ancient Jawbone / 远古颚骨</code> 成功率更高，是因为它过滤掉 40 级以下低级词缀，使目标词在剩余前缀池中的权重占比上升。</div>
      <div class="callout">深渊专属权重来源：本地 PoE2DB 快照能列出弓的深渊专属词，前缀 {len(desecrated_prefixes)} 条、后缀 {len(desecrated_suffixes)} 条，但 <code>drop_chance</code> 为空/0。Craft of Exile 的 POE2 数据文件中，Bow 深渊专属前缀 8 条、后缀 9 条，单条权重均为 1；本报告把前缀总权重 {fmt(CRAFT_OF_EXILE_DESECRATED_PREFIX_WEIGHT)} 加入深渊前缀分母。该权重属于外部外推值，不是游戏客户端原始数据。</div>
      <div class="callout bad"><code>{label('Omen of Catalysing Exaltation')}</code> 只在物品有 <code>Catalyst Quality / 催化品质</code> 时进入路线。本地 <code>Obliterator Bow</code> 基底没有可催化字段，所以主路线不使用；当前快照价 {fmt(catalysing)}E。</div>
    """

    return f"""
    <section>
      <h2>三条路线状态机</h2>
      <div class="callout">候选表里的“成功率”是当前这一步的概率，不是整条路线最终成品率。随机补 2 词的主成功定义已改为 2 条都有效；“至少 1 条有效”只放在临界比较里。有效词翻译：<code>Critical Damage Bonus / 暴击伤害加成</code>、<code>Level of all Projectile Skills / 所有投射物技能等级</code>、<code>Surpassing chance to fire an additional Arrow / 超越概率发射额外箭矢</code>。路线 1 的价格分布另列“无回收期望”，它按从基底重做且失败不卖回收来估，实际成本会因半成品可卖而下降。</div>
      <div class="tabs">
        <input checked id="route-1" name="route-tab" type="radio">
        <input id="route-2" name="route-tab" type="radio">
        <input id="route-3" name="route-tab" type="radio">
        <div class="tab-labels">
          <label for="route-1">路线 1：物理百分比暴击</label>
          <label for="route-2">路线 2：点伤反做</label>
          <label for="route-3">路线 3：非暴击 pDPS</label>
        </div>
        <div class="tab-panel route-1-panel">{route1_timing_compare}{route1_step_costs}{route1_material_share}{route1_price_distribution}{route1_ops}</div>
        <div class="tab-panel route-2-panel">{route2_step_costs}{route2_share}{route2_price_distribution}{route2_ops}</div>
        <div class="tab-panel route-3-panel">{route3_step_costs}{route3_material_share}{route3_price_distribution}{route3_ops}</div>
      </div>
      {formula_html}
    </section>
    """


def render_desecrated_rows(bow_mods: list[dict[str, str]]) -> str:
    rows = []
    for row in bow_mods:
        if row.get("source_group") != "desecrated":
            continue
        side = "前缀" if row.get("generation_type") == "1" else "后缀"
        rows.append(
            "<tr>"
            f"<td>{side}</td>"
            f"<td>{esc(row.get('name'))}</td>"
            f"<td>{esc(row.get('families'))}</td>"
            f"<td>{esc(row.get('text'))}</td>"
            f"<td>{esc(row.get('drop_chance') or '0')}</td>"
            "</tr>"
        )
    return "".join(rows)


def render_report() -> None:
    prices, prices_by_name = load_prices()
    summary = read_json(PRICE_DIR / "summary.json")
    bow_mods = [
        row for row in read_csv(MODS_DIR / "poe2db_mods.csv")
        if row.get("item_class_href") == "Bows"
    ]
    bases = [
        row for row in read_csv(ITEMS_DIR / "poe2db_base_items.csv")
        if row.get("page") == "Bows"
    ]
    obliterator = next((row for row in bases if row.get("name") == "Obliterator Bow"), {})

    snapshot_time = summary.get("snapshot_time_utc") or (prices[0]["snapshot_time_utc"] if prices else "未抓取")
    ex_per_div = exalted_per_divine(prices_by_name)
    candidates, best, debug = startup_candidates(bow_mods, prices_by_name, ex_per_div)
    routes_html = render_routes(bow_mods, prices_by_name, best)

    phys_start = best["phys_pct_135"]
    flat_start = best["flat_phys_t3"]
    recommended_route = "路线 2：点伤反做" if (flat_start.average_cost or 0) + cost(prices_by_name, "Greater Essence of Seeking") < (phys_start.average_cost or 0) else "路线 1/3：物理百分比起步"

    required_price_names = [
        "Orb of Transmutation",
        "Orb of Augmentation",
        "Greater Orb of Transmutation",
        "Greater Orb of Augmentation",
        "Perfect Orb of Transmutation",
        "Perfect Orb of Augmentation",
        "Exalted Orb",
        "Greater Exalted Orb",
        "Perfect Exalted Orb",
        "Omen of Sinistral Exaltation",
        "Omen of Dextral Exaltation",
        "Omen of Greater Exaltation",
        "Omen of Light",
        "Omen of Sinistral Necromancy",
        "Omen of Dextral Necromancy",
        "Omen of Abyssal Echoes",
        "Omen of Catalysing Exaltation",
        "Preserved Jawbone",
        "Ancient Jawbone",
        "Greater Essence of Seeking",
        "Greater Essence of Abrasion",
        "Artificer's Orb",
        "Greater Iron Rune",
        "Countess Seske's Rune of Archery",
    ]
    missing = [name for name in required_price_names if name.lower() not in prices_by_name]
    missing_text = "无" if not missing else "、".join(missing)

    html_text = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>POE2 Obliterator Bow 打造状态机报告</title>
  <style>
    body {{ margin:0; font-family:"Microsoft YaHei","Segoe UI",Arial,sans-serif; background:#101114; color:#eee7d7; line-height:1.58; }}
    main {{ width:100%; max-width:none; box-sizing:border-box; margin:0; padding:24px 12px 52px; }}
    h1 {{ margin:0 0 8px; font-size:34px; line-height:1.18; color:#fff3d0; }}
    h2 {{ margin:32px 0 12px; font-size:23px; color:#fff3d0; }}
    h3 {{ margin:22px 0 10px; color:#fff3d0; }}
    h4 {{ margin:18px 0 8px; color:#f7deb2; }}
    code {{ color:#ffe0a3; background:#24202a; padding:1px 5px; border-radius:5px; }}
    table {{ width:100%; border-collapse:collapse; margin:10px 0 18px; table-layout:auto; overflow-wrap:break-word; }}
    th, td {{ border:1px solid #35384a; padding:9px 10px; text-align:left; vertical-align:top; }}
    th {{ background:#20212b; color:#fff0cf; }}
    td {{ background:#151721; }}
    tr.best-base td {{ background:#2b151b; border-top:3px solid #ff4d63; border-bottom:3px solid #ff4d63; }}
    tr.best-base td:first-child {{ border-left:3px solid #ff4d63; }}
    tr.best-base td:last-child {{ border-right:3px solid #ff4d63; }}
    tr.watch-base td {{ background:#261d16; border-top:2px solid #d78a40; border-bottom:2px solid #d78a40; }}
    tr.watch-base td:first-child {{ border-left:2px solid #d78a40; }}
    tr.watch-base td:last-child {{ border-right:2px solid #d78a40; }}
    tr.best-route td {{ background:#2b151b; border-top:3px solid #ff4d63; border-bottom:3px solid #ff4d63; }}
    tr.best-route td:first-child {{ border-left:3px solid #ff4d63; }}
    tr.best-route td:last-child {{ border-right:3px solid #ff4d63; }}
    tr.watch-route td {{ background:#261d16; border-top:2px solid #d78a40; border-bottom:2px solid #d78a40; }}
    tr.watch-route td:first-child {{ border-left:2px solid #d78a40; }}
    tr.watch-route td:last-child {{ border-right:2px solid #d78a40; }}
    .muted {{ color:#b9b2a2; }}
    .top {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:12px; margin:14px 0 18px; }}
    .box {{ border:1px solid #35384a; background:#181922; border-radius:8px; padding:13px; }}
    .box strong {{ display:block; color:#fff3d0; margin-bottom:5px; }}
    .callout {{ border-left:4px solid #d7a94f; background:#1b1a1c; padding:12px 14px; margin:13px 0; border-radius:0 8px 8px 0; }}
    .good {{ border-left-color:#7fbf8b; }}
    .bad {{ border-left-color:#d77a73; }}
    .tabs > input {{ position:absolute; opacity:0; pointer-events:none; }}
    .tab-labels {{ display:flex; flex-wrap:wrap; gap:8px; border-bottom:1px solid #35384a; }}
    .tab-labels label {{ cursor:pointer; background:#151721; border:1px solid #35384a; border-bottom:none; border-radius:8px 8px 0 0; padding:9px 12px; color:#d8d0be; font-weight:700; }}
    .tab-panel {{ display:none; border:1px solid #35384a; border-top:none; padding:14px; background:#12141d; }}
    #route-1:checked ~ .tab-labels label[for="route-1"],
    #route-2:checked ~ .tab-labels label[for="route-2"],
    #route-3:checked ~ .tab-labels label[for="route-3"] {{ background:#2a251a; color:#fff1cd; border-color:#d7a94f; }}
    #route-1:checked ~ .route-1-panel,
    #route-2:checked ~ .route-2-panel,
    #route-3:checked ~ .route-3-panel {{ display:block; }}
    code {{ white-space:nowrap; }}
    th:nth-child(1), td:nth-child(1),
    th:nth-child(5), td:nth-child(5),
    th:nth-child(6), td:nth-child(6),
    th:nth-child(7), td:nth-child(7),
    th:nth-child(8), td:nth-child(8),
    th:nth-child(11), td:nth-child(11) {{ white-space:nowrap; }}
    td:nth-child(5), td:nth-child(6), td:nth-child(7), td:nth-child(8) {{ font-variant-numeric:tabular-nums; }}
    @media (max-width:900px) {{ .top {{ grid-template-columns:1fr; }} h1 {{ font-size:28px; }} }}
  </style>
</head>
<body>
<main>
  <h1>POE2 Obliterator Bow 打造报告：统一起步池 + 状态机路线</h1>
  <section class="top">
    <div class="box"><strong>快照时间</strong><code>{esc(snapshot_time)}</code></div>
    <div class="box"><strong>手动价格输入</strong>白底 {fmt(MANUAL_PRICES['normal_base_ex'])}E；135-154% 物理魔法底 {fmt(MANUAL_PRICES['phys_pct_135_154_magic_base_div'])}div；155%+ 物理魔法底 {fmt(MANUAL_PRICES['phys_pct_155_magic_base_div'])}div；T3+ 物理点伤魔法底 {fmt(MANUAL_PRICES['flat_phys_t3_magic_base_ex'])}E；T2+ 物理点伤魔法底 {fmt(MANUAL_PRICES['flat_phys_t2_magic_base_ex'])}E；垃圾魔法弓 {money(MANUAL_PRICES['trash_magic_bow_ex'])}。</div>
    <div class="box"><strong>当前最便宜起步</strong>物理百分比：<code>{phys_start.code}</code> {fmt(phys_start.average_cost)}E；物理点伤：<code>{flat_start.code}</code> {fmt(flat_start.average_cost)}E。</div>
    <div class="box"><strong>当前推荐路线</strong>{esc(recommended_route)}。深渊封口只作为各路线最后一步，不再单独列为路线。</div>
  </section>

  <section>
    <h2>价格索引与手动输入</h2>
    <div class="callout">所有 ninja 能查到的材料都来自本地快照。缺失项：<code>{esc(missing_text)}</code>。手动价只用于交易站指定底子，当前未设置“一词后缀魔法底”价格，因此 S6 只显示临界价。</div>
    <table>
      <thead><tr><th>材料</th><th>Exalted</th><th>Divine</th><th>Chaos</th></tr></thead>
      <tbody>{''.join(price_line(name, prices_by_name) for name in required_price_names)}</tbody>
    </table>
  </section>

  <section>
    <h2>打造机制规则</h2>
    <table>
      <thead><tr><th>机制</th><th>本报告采用规则</th></tr></thead>
      <tbody>
        <tr><td>词缀池</td><td>按 <code>PoE2DB Bows</code> 普通词缀权重计算，物品等级按买入基底 <code>ilvl 75-80</code> 处理，概率模型使用上限 <code>ilvl {MOD_ILVL}</code>；超过 80 级的词缀不进入池。<code>Obliterator Bow / 湮灭之弓</code> 本地基底：{esc(obliterator.get('physical_damage', ''))} 物理、{esc(obliterator.get('attacks_per_second', ''))} APS、隐式 <code>{esc(obliterator.get('implicit', ''))}</code>。</td></tr>
        <tr><td>蜕变/增幅</td><td>普通最低词缀等级 0；高阶最低 44；完美最低 70。完美蜕变/增幅不能出 60 级 T3 物理百分比 <code>Cruel / 135-154%</code>，也不能出 60/65 级 T3 物理点伤；在 ilvl 80 上对应目标会升级为 <code>P155</code> 或 <code>F2</code>。起步池用 <code>P(蜕变命中) + P(蜕变出另一侧) x P(增幅命中)</code>。</td></tr>
        <tr><td>崇高与预兆</td><td><code>Omen of Sinistral Exaltation / 左向崇高预兆</code> 视作定向前缀；<code>Omen of Dextral Exaltation / 右向崇高预兆</code> 视作定向后缀。当前模型里完美崇高石最低词缀等级按 50，不等同于完美蜕变/增幅的 70，因此仍可能命中 60 级 T3；双加与定向同时触发列为待验证假设。</td></tr>
        <tr><td>深渊</td><td><code>Reveal desecrated modifiers may include base modifiers</code>，所以三选一可以出现 Base 普通词缀。三选一用 <code>1 - (1 - p)^3</code>，Echo 六选用 <code>1 - (1 - p)^6</code>。失败后用 <code>Omen of Light / 光明预兆</code> 剥离深渊词，可在同一胚子上重试。</td></tr>
        <tr><td>催化崇高预兆</td><td><code>Omen of Catalysing Exaltation / 催化崇高预兆</code> 只在物品有 <code>Catalyst Quality / 催化品质</code> 时进入路线；当前弓基底不进入主线。</td></tr>
      </tbody>
    </table>
  </section>

  <section>
    <h2>统一起步模块</h2>
    <div class="callout">状态 ID 是唯一的：<code>S0</code> 是白底重开基准；<code>S1/S2/S3</code> 表示普通/高阶/完美蜕变增幅；后缀 <code>P135</code> 表示目标 135%+ 物理百分比，<code>P155</code> 表示目标 155%+ 物理百分比，<code>F3</code> 表示目标 T3+ 物理点伤，<code>F2</code> 表示目标 T2+ 物理点伤。因为完美蜕变/增幅最低等级 70，起步池不会再列 <code>S3-P135</code> 或 <code>S3-F3</code>。</div>
    {render_startup_table(candidates)}
    <div class="callout good">路线 1 和路线 3 只读取 <code>{TARGET_LABELS['phys_pct_135']}</code> 的推荐起步状态；路线 2 只读取 <code>{TARGET_LABELS['flat_phys_t3']}</code> 的推荐起步状态。直接买底只是候选之一，不再是路线硬编码起点。</div>
  </section>

  {routes_html}

  <section>
    <h2>物理点伤 T 级范围</h2>
    <div class="callout">这张表用于交易站搜价。<code>Adds Physical Damage / 附加物理点伤</code> 的 T 级数值互相重叠，低 T 高 roll 可能高过高 T 低 roll，所以搜价时建议同时看前值和后值范围，不只看 T 级。</div>
    {render_flat_phys_tier_table(bow_mods)}
  </section>

  <section>
    <h2>状态分层</h2>
    <table>
      <thead><tr><th>层级</th><th>定义</th><th>处理</th></tr></thead>
      <tbody>
        <tr><td>中间过渡</td><td>2-3 条有效词，例如物理百分比 + 暴击率，或物理点伤 + 暴击率。</td><td>低成本筛选，可卖半成品；不使用 Ancient/Echo 硬救。</td></tr>
        <tr><td>接近毕业</td><td>4-5 条有效词，已经有双物理、暴击率、元素/暴伤等核心卖点。</td><td>Fubgun 那把归这里；可考虑 Ancient 或高阶定向封口。</td></tr>
        <tr><td>完美毕业</td><td>核心词多为 T1/T2，终局品质、插槽、符文补强完整。</td><td>只在高预期售价覆盖高成本时继续。</td></tr>
      </tbody>
    </table>
  </section>

  <section>
    <h2>深渊专属词候选</h2>
    <p class="muted">这些词在本地数据中多为权重 0，因此不参与 Base 权重池精算，只作为有效词候选列出。</p>
    <table>
      <thead><tr><th>方向</th><th>英文名</th><th>族</th><th>文本</th><th>权重</th></tr></thead>
      <tbody>{render_desecrated_rows(bow_mods)}</tbody>
    </table>
  </section>

  <section>
    <h2>可重复执行</h2>
    <pre><code>python scripts/python/generate_fubgun_crit_bow_report.py</code></pre>
  </section>
</main>
</body>
</html>
"""
    REPORT_FILE.write_text(html_text, encoding="utf-8")
    print(f"Wrote {REPORT_FILE}")
    print(
        "direct_phys_135_ex="
        f"{fmt(debug['direct_phys_135_ex'])}; "
        "direct_phys_155_ex="
        f"{fmt(debug['direct_phys_155_ex'])}; "
        f"direct_flat_t3_ex={fmt(debug['direct_flat_t3_ex'])}; "
        f"direct_flat_t2_ex={fmt(debug['direct_flat_t2_ex'])}"
    )


if __name__ == "__main__":
    render_report()
