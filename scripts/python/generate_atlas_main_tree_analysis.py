from __future__ import annotations

import csv
import html
from collections import Counter
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
NODE_CSV = ROOT / "data" / "processed" / "passive_tree" / "poe2_atlas_passive_nodes.csv"
REPORT_FILE = ROOT / "reports" / "atlas" / "poe2_atlas_main_tree_analysis.html"

EXCLUDED_GENERIC_ID_PREFIXES = (
    "AtlasAbyss",
    "AtlasBreach",
    "AtlasDelirium",
    "AtlasExpedition",
    "AtlasIncursion",
    "AtlasRitual",
)

CN_NAME = {
    "The Journey Ahead": "前路选择",
    "The Journey Ahead: Pack Size": "前路选择：怪群规模",
    "The Journey Ahead: Effectiveness": "前路选择：怪物效能",
    "The Journey Ahead: Rarity": "前路选择：物品稀有度",
    "The Chosen Path": "选定之路",
    "The Chosen Path: Essences": "选定之路：精华",
    "The Chosen Path: Rogue Exiles": "选定之路：盗贼流放者",
    "The Chosen Path: Summoning Circles": "选定之路：召唤法阵",
    "The Chosen Path: Shrines": "选定之路：神龛",
    "The Chosen Path: Strongboxes": "选定之路：保险箱",
    "The Chosen Path: Azmeri Spirits": "选定之路：阿兹莫里灵体",
    "Essence Dowsing": "精华探测",
    "Crystalline Patterns": "晶化纹路",
    "Corrupted Lattices": "腐化晶格",
    "Unseen Rivers": "暗流",
    "Sacred Sap": "圣洁树液",
    "Evolving Throngs": "进化群体",
    "Nemesis Rising": "宿敌崛起",
    "Divined Blessing": "神授祝福",
    "Fabled Showdown": "传说对决",
    "Overlord's Domain": "霸主领域",
    "Overlord's Influence": "霸主影响",
    "Blood on the Stones": "石上之血",
    "Legendary Duels": "传奇决斗",
    "Well-equipped Opponents": "装备精良的对手",
    "Strongbox Type Selector": "保险箱类型选择",
    "Craftsman's Creed": "工匠信条",
    "History of the Faridun": "法里敦史记",
    "History of the Ezomytes": "伊佐麦史记",
    "History of the Vaal": "瓦尔史记",
    "Unstable Energies": "不稳定能量",
    "Corrupted Infusion": "腐化灌注",
    "Ecological Shift": "生态转移",
    "Atop the World": "世界之巅",
    "Industrial Improvements": "工业改良",
    "Local Knowledge": "地方知识",
    "Lucky Pillage": "幸运劫掠",
    "Constant Crossroads": "恒常歧路",
    "Fortunate Path": "幸运路径",
    "Valuable Paths": "高价值路径",
    "Grueling Journey": "艰苦旅程",
    "Enigmatic Intensification": "谜样强化",
    "Precursor Influence": "先驱影响",
    "Remnants of Power": "力量残余",
    "Controlled Climates": "可控气候",
    "Reverse Transcription": "反向转录",
    "Curiously Durable Stone": "异常耐用的石板",
    "Eons of Contamination": "污染纪元",
    "Eons of Domination": "支配纪元",
    "Crystalline Growths": "晶化生长",
    "Resonant Lattice": "共振晶格",
    "Inexplicable Alchemy": "不可解的炼金",
    "Likely Ambush": "可能伏击",
    "High-Value Thefts": "高价值盗取",
    "Hidden Compartments": "隐藏隔层",
    "Enchanted Locks": "附魔锁具",
    "Inlaid Inscriptions": "镶嵌铭文",
    "Royal Craftsmanship": "王室工艺",
    "Places of Worship": "礼拜之所",
    "Favoured Disciple": "受宠门徒",
    "Seasonal Blessing": "季节祝福",
    "Gathered Masses": "聚集群众",
    "Curious Spirits": "好奇灵体",
    "Wanted Poster": "通缉令",
    "Dressed in Fineries": "华服装束",
    "Escalating Rivalry": "升级的竞争",
    "Competitive Archaeology": "竞争性考古",
    "Guiding Light": "指引之光",
    "Grip of the Wilds": "荒野之握",
    "Viridi's Sacrifice": "维里迪的牺牲",
    "Worthy Hunter": "合格猎手",
    "Hunt the Apex": "狩猎巅峰",
    "Challenging Foe": "强敌",
    "Overheard Summons": "窃听召唤",
    "Runic Flare": "符文闪耀",
    "Expanding Hordes": "扩张兽群",
    "Bountiful Bloodlines": "丰饶血脉",
    "Infused Flesh": "灌注血肉",
    "Befit the Challenge": "匹配挑战",
    "Twin Threats": "双重威胁",
    "No Simple Battles": "没有简单战斗",
    "Adaptive Biology": "适应性生物学",
    "Mutating Monsters": "突变怪物",
    "To the Strong Go the Spoils": "强者得战利品",
    "Fit for a King": "王者之配",
    "Hard-Won Treasures": "血战宝藏",
    "Pathkeepers": "路径守卫",
    "Brutal Lessons": "残酷教训",
    "Cataclysm's Wake": "灾变余波",
    "Organised Forces": "有组织的军势",
    "Overlord's Hoard": "霸主宝库",
    "Ancient Relics": "远古遗物",
    "Lost Techniques": "失落技艺",
    "Modular Servant": "模块化仆从",
    "Witness to History": "历史见证",
    "Central Terraformer": "中央塑地机",
}

TERM_GLOSSARY = [
    ("Waystone", "地图石", "开图消耗品，决定地图等级和显式词缀，是地图风险与奖励的第一层载体。"),
    ("Tablet", "石板", "通过塔或区域影响地图，提供区域级规则和额外词缀。"),
    ("Precursor Tower", "先驱塔", "揭示周边区域并承载 Tablet 规划，决定你能如何改造一片地图。"),
    ("Biome", "生物群系/地形", "Desert、Forest、Grass、Mountain、Swamp、Water 等地形标签，影响节点触发。"),
    ("City Areas", "城市区域", "Faridun、Ezomyte、Vaal 等城市地图，能被改造为额外 Biome。"),
    ("Powerful Map Boss", "强力地图首领", "被升级或特殊标记的地图 Boss，常作为额外内容和高价值掉落的聚合点。"),
    ("Monster Modifier", "怪物词缀", "怪物身上的额外能力。主树经常用更多词缀换取更高稀有度或收益。"),
    ("Effectiveness", "效能", "怪物或 Boss 的强度系数，通常代表更难、更危险。"),
    ("Rarity", "稀有度", "提高掉落物稀有等级或高价值物品出现倾向。"),
    ("Quantity", "数量", "提高掉落总量或特定资源数量。"),
    ("Azmeri Spirit", "阿兹莫里灵体", "会影响、附身或强化怪物的地图内容，可和 Boss、神龛、保险箱互动。"),
    ("Essence", "精华", "地图内可定向工艺资源，主树提供出现率、类型、腐化和完美精华路线。"),
    ("Strongbox", "保险箱", "可被词缀、稀有度、类型和守卫怪群强化的地图容器奖励。"),
    ("Shrine", "神龛", "给玩家或 Boss 提供 Buff，也能成为怪群、灵体和首领奖励的连接点。"),
    ("Rogue Exile", "盗贼流放者", "装备驱动型独特敌人，主树可定向其装备类型与掉落。"),
    ("Summoning Circle", "召唤法阵", "召唤 Boss 或怪群的地图内容，可把附近地图 Boss 升级为 Powerful Map Boss。"),
    ("Corruption", "腐化", "提高风险和不确定性，常和 Waystone、Essence、Powerful Boss、Nexus 绑定。"),
]

TYPE_GLOSSARY = [
    ("keystone", "核心点/关键点", "通常改变规则或打开一个选择器；很多 keystone 后面会接多个可选分支。"),
    ("notable", "显著点/大点", "比小点更强的奖励节点；在选择器下方也常用 notable 表示具体选项。"),
    ("choice_option", "选择选项", "选择器的具体选项，通常代表互斥方向或当前策略开关。"),
    ("small", "小点", "路径或小数值成长节点；本报告主要展示 keystone、notable 和 choice_option。"),
]

STAT_CN = {
    "Select between Pack Size, Effectiveness or Rarity": "在怪群规模、怪物效能或物品稀有度之间选择",
    "8% increased Rarity of Items found | 5% increased Quantity of Items found": "找到物品的稀有度提高 8% | 找到物品的数量提高 5%",
    "10% increased Quantity of Waystones found": "找到的 Waystone 数量提高 10%",
    "100% increased Rarity of Waystones found": "找到的 Waystone 稀有度提高 100%",
    "50% increased Rarity of Waystones found": "找到的 Waystone 稀有度提高 50%",
    "2% increased effect of Explicit Modifiers on your Waystones for each Explicit Modifier": "Waystone 每有 1 条显式词缀，其显式词缀效果提高 2%",
    "Waystones have 25% more effect of Prefix Modifiers or 25% more effect of Suffix Modifiers when opening Maps": "开图时，Waystone 的前缀词缀效果提高 25% 更多，或后缀词缀效果提高 25% 更多",
    "Corrupted Waystones are Corrupted an additional time when used to traverse a Map": "使用腐化 Waystone 开图时，该 Waystone 额外腐化一次",
    "3% increased effect of Explicit Modifiers on your Waystones for each Tablet affecting Map area": "每个影响该地图区域的 Tablet，使你的 Waystone 显式词缀效果提高 3%",
    "10% chance for Waystones found in your Maps to be Rare and Corrupted": "你地图中找到的 Waystone 有 10% 几率为稀有并已腐化",
    "2% increased Rarity of Items Dropped by Monsters per Explicit Modifier on the Map": "地图每有 1 条显式词缀，怪物掉落物品的稀有度提高 2%",
    "33% increased Precursor Tower reveal radius": "Precursor Tower 揭示半径提高 33%",
    "30% increased Quantity of Tablets found": "找到的 Tablet 数量提高 30%",
    "20% chance for double effect of Explicit Modifiers on Tablets": "Tablet 的显式词缀有 20% 几率双倍效果",
    "5% increased effect of Explicit Modifiers on Tablets for each Tablet affecting Map area": "每个影响该地图区域的 Tablet，使 Tablet 显式词缀效果提高 5%",
    "Your Tablets may be upgraded to Rare and have +1 Maximum Modifier": "你的 Tablet 可能升级为稀有，并且最大词缀数 +1",
    "8% chance to not consume Tablet uses when opening Maps": "开图时有 8% 几率不消耗 Tablet 使用次数",
    "Irradiated Precursor Tablets may now be found": "现在可以找到 Irradiated Precursor Tablets",
    "Overseer Precursor Tablets can drop from Powerful Map Bosses": "Powerful Map Boss 可以掉落 Overseer Precursor Tablets",
    "Faridun Cities are also considered to be another Biome": "Faridun Cities 也会被视为另一种 Biome",
    "Ezomyte Cities are also considered to be another Biome": "Ezomyte Cities 也会被视为另一种 Biome",
    "Vaal Cities are also considered to be another Biome": "Vaal Cities 也会被视为另一种 Biome",
    "An additional Tablet may be used on City Maps": "City Maps 可以额外使用 1 个 Tablet",
    "Desert Biome Maps have 40% increased chance to drop Baryas and Inscribed Ultimatums | Mountain Biome Maps have 40% increased chance to drop Gold | Grass Biome Maps have 40% increased chance to drop Socket Currency | Forest Biome Maps have 40% increased chance to drop Jewels | Swamp and Water Biome Maps have 40% increased chance to drop Basic Currency": "Desert Biome 地图掉落 Barya 和 Inscribed Ultimatum 的几率提高 40% | Mountain Biome 地图掉落 Gold 的几率提高 40% | Grass Biome 地图掉落 Socket Currency 的几率提高 40% | Forest Biome 地图掉落 Jewel 的几率提高 40% | Swamp 与 Water Biome 地图掉落 Basic Currency 的几率提高 40%",
    "1 Rare Monster in Swamp Areas has 15% chance to be replaced by a random Map Boss": "Swamp Areas 中 1 个稀有怪有 15% 几率被随机 Map Boss 替代",
    "Essences found in Desert Areas have 50% increased chance to be Perfect Essences": "Desert Areas 中找到的 Essence 成为 Perfect Essence 的几率提高 50%",
    "6% increased Pack Size in Grass Areas": "Grass Areas 中怪群规模提高 6%",
    "Shrines in Water Areas are Worshipped by an additional Pack of Monsters": "Water Areas 中的 Shrine 会额外被 1 群怪物供奉",
    "Your Maps have 100% increased chance to contain Essences": "你的地图包含 Essence 的几率提高 100%",
    "30% increased chance to find Perfect Essences | 30% chance for minions of Essence Monsters to be Empowered": "找到 Perfect Essence 的几率提高 30% | Essence Monster 的随从有 30% 几率被 Empowered",
    "40% increased chance of Strongboxes": "Strongbox 出现几率提高 40%",
    "Strongboxes have 15% chance to be openable twice": "Strongbox 有 15% 几率可以开启两次",
    "Your Maps have 100% increased chance to contain Shrines": "你的地图包含 Shrine 的几率提高 100%",
    "Shrines are Worshipped by an additional Pack of Monsters": "Shrine 会额外被 1 群怪物供奉",
    "40% increased chance of Rogue Exiles": "Rogue Exile 出现几率提高 40%",
    "Rogue Exiles have 100% increased chance to drop Exceptional Items": "Rogue Exile 掉落 Exceptional Items 的几率提高 100%",
    "40% increased chance of Azmeri Spirits": "Azmeri Spirit 出现几率提高 40%",
    "50% increased maximum empowerment of Azmeri Spirits": "Azmeri Spirit 的最大 empowerment 提高 50%",
    "Summoning Circle Bosses have a 25% chance to have an additional Monster Modifier": "Summoning Circle Boss 有 25% 几率拥有 1 个额外 Monster Modifier",
    "10% chance to upgrade the boss of a nearby Map into a Powerful Map Boss when completing Summoning Circles": "完成 Summoning Circle 时，有 10% 几率将附近地图的 Boss 升级为 Powerful Map Boss",
    "10% increased Magic Pack Size": "Magic Pack Size 提高 10%",
    "20% increased Magic Monsters": "Magic Monsters 数量提高 20%",
    "Magic Monster Packs have 5% chance to have an additional Modifier": "Magic Monster Packs 有 5% 几率拥有 1 个额外 Modifier",
    "5% increased Rarity of Items Dropped by Magic Monsters per Monster Modifier": "Magic Monster 每有 1 个 Monster Modifier，其掉落物品稀有度提高 5%",
    "1 Rare Monster per Area is Duplicated": "每个区域有 1 个 Rare Monster 被复制",
    "Rare Monsters have at least 3 Monster Modifiers": "Rare Monsters 至少拥有 3 个 Monster Modifiers",
    "+1 to maximum Monster Modifiers on Rare Monsters | Rare Monsters have 10% increased chance of Monster Modifiers": "Rare Monsters 的最大 Monster Modifiers 数量 +1 | Rare Monsters 获得 Monster Modifiers 的几率提高 10%",
    "2% increased Rarity of Items Dropped by Monsters per Monster Modifier": "怪物每有 1 个 Monster Modifier，其掉落物品稀有度提高 2%",
    "Select a bonus for Rare Monsters": "为 Rare Monsters 选择一项加成",
    "15% increased Rarity of Items dropped by Map Bosses": "Map Bosses 掉落物品的稀有度提高 15%",
    "15% increased Quantity of Items dropped by Map Bosses": "Map Bosses 掉落物品的数量提高 15%",
    "10% increased Quantity of Waystones dropped by Map Bosses": "Map Bosses 掉落的 Waystone 数量提高 10%",
    "Map Bosses grant 50% increased Experience": "Map Bosses 给予的经验提高 50%",
    "Add additional content to areas with Powerful Map Bosses": "向拥有 Powerful Map Bosses 的区域添加额外内容",
    "Areas with Powerful Map Bosses have 20% chance to contain Corruption when entered": "进入拥有 Powerful Map Bosses 的区域时，该区域有 20% 几率包含 Corruption",
    "Non-Irradiated Areas with Powerful Map Bosses have +1 Level": "拥有 Powerful Map Bosses 的非 Irradiated 区域等级 +1",
    "Overseer Precursor Tablets also provide 20% increased Rarity of Items Dropped to the Map Boss": "Overseer Precursor Tablets 还会使 Map Boss 掉落物品的稀有度提高 20%",
    "25% increased Rarity of Items dropped by the Arbiter": "Arbiter 掉落物品的稀有度提高 25%",
    "Pinnacle Bosses have 20% chance to drop an additional Unique item": "Pinnacle Bosses 有 20% 几率额外掉落 1 件 Unique item",
    "6% increased Pack Size": "怪群规模提高 6%",
    "15% increased Effectiveness of Monsters in your Maps": "你地图中怪物的 Effectiveness 提高 15%",
    "10% increased Rarity of Items found": "找到物品的稀有度提高 10%",
    "100% increased chance of a certain content type": "某一种内容类型的出现几率提高 100%",
    "100% increased chance of Essences": "Essence 出现几率提高 100%",
    "100% increased chance of Rogue Exiles": "Rogue Exile 出现几率提高 100%",
    "100% increased chance of Summoning Circles": "Summoning Circle 出现几率提高 100%",
    "100% increased chance of Shrines": "Shrine 出现几率提高 100%",
    "100% increased chance of Strongboxes": "Strongbox 出现几率提高 100%",
    "100% increased chance of Azmeri Spirits": "Azmeri Spirit 出现几率提高 100%",
    "100% increased chance to find certain Essence types": "找到特定 Essence 类型的几率提高 100%",
    "100% increased chance for Essences found in your Maps to add Life modifiers": "你地图中找到的 Essence 添加 Life modifiers 的几率提高 100%",
    "100% increased chance for Essences found in your Maps to add Mana modifiers": "你地图中找到的 Essence 添加 Mana modifiers 的几率提高 100%",
    "100% increased chance for Essences found in your Maps to add Armour, Evasion and Energy Shield modifiers": "你地图中找到的 Essence 添加 Armour、Evasion 和 Energy Shield modifiers 的几率提高 100%",
    "100% increased chance for Essences found in your Maps to add Physical modifiers": "你地图中找到的 Essence 添加 Physical modifiers 的几率提高 100%",
    "100% increased chance for Essences found in your Maps to add Fire modifiers": "你地图中找到的 Essence 添加 Fire modifiers 的几率提高 100%",
    "100% increased chance for Essences found in your Maps to add Cold modifiers": "你地图中找到的 Essence 添加 Cold modifiers 的几率提高 100%",
    "100% increased chance for Essences found in your Maps to add Lightning modifiers": "你地图中找到的 Essence 添加 Lightning modifiers 的几率提高 100%",
    "100% increased chance for Essences found in your Maps to add Chaos modifiers": "你地图中找到的 Essence 添加 Chaos modifiers 的几率提高 100%",
    "100% increased chance for Essences found in your Maps to add Attack modifiers": "你地图中找到的 Essence 添加 Attack modifiers 的几率提高 100%",
    "100% increased chance for Essences found in your Maps to add Caster modifiers": "你地图中找到的 Essence 添加 Caster modifiers 的几率提高 100%",
    "100% increased chance for Essences found in your Maps to add Speed modifiers": "你地图中找到的 Essence 添加 Speed modifiers 的几率提高 100%",
    "100% increased chance for Essences found in your Maps to add Attribute modifiers": "你地图中找到的 Essence 添加 Attribute modifiers 的几率提高 100%",
    "100% increased chance for Essences found in your Maps to add Critical modifiers": "你地图中找到的 Essence 添加 Critical modifiers 的几率提高 100%",
    "100% increased chance for Essences found in your Maps to add Rarity modifiers": "你地图中找到的 Essence 添加 Rarity modifiers 的几率提高 100%",
    "100% increased chance for Essences found in your Maps to add Ally modifiers": "你地图中找到的 Essence 添加 Ally modifiers 的几率提高 100%",
    "Select a bonus when Corrupting Essence Monsters": "腐化 Essence Monsters 时选择一项加成",
    "Corrupting Essence Monsters cannot immediately release them and will always change their Essences": "腐化 Essence Monsters 不会立刻释放它们，并且总会改变它们的 Essences",
    "Corrupted Essence Monsters have 25% chance to be Duplicated when released": "Corrupted Essence Monsters 释放时有 25% 几率被复制",
    "Corrupting Essence Monsters Corrupts them an additional time": "腐化 Essence Monsters 会使其额外腐化一次",
    "When Corrupting Rare Essence Monsters immediately releases them they are instead immediately killed": "当腐化 Rare Essence Monsters 本应立刻释放它们时，改为立刻击杀它们",
    "100% increased chance to encounter certain Azmeri Spirits | Does not impact chance to encounter Sacred Spirits": "遇到特定 Azmeri Spirits 的几率提高 100% | 不影响遇到 Sacred Spirits 的几率",
    "100% increased chance for Azmeri Spirits to be Primal Spirits": "Azmeri Spirits 成为 Primal Spirits 的几率提高 100%",
    "100% increased chance for Azmeri Spirits to be Wild Spirits": "Azmeri Spirits 成为 Wild Spirits 的几率提高 100%",
    "100% increased chance for Azmeri Spirits to be Vivid Spirits": "Azmeri Spirits 成为 Vivid Spirits 的几率提高 100%",
    "Select a Sacred or Empowered Azmeri Spirits Bonus": "选择一项 Sacred 或 Empowered Azmeri Spirits 加成",
    "25% increased chance for Azmeri Spirits in your Maps to be Sacred Spirits": "你地图中的 Azmeri Spirits 成为 Sacred Spirits 的几率提高 25%",
    "When a Monster is Possessed by a Sacred Spirit it is also Possessed by another random Spirit": "当怪物被 Sacred Spirit 附身时，也会被另一个随机 Spirit 附身",
    "50% increased Azmeri Spirit empowerment when defeating Spirit-Influenced Monsters": "击败 Spirit-Influenced Monsters 时，Azmeri Spirit empowerment 提高 50%",
    "Select a bonus for Magic Packs": "为 Magic Packs 选择一项加成",
    "Magic Monster Packs have 15% chance to have an additional Modifier": "Magic Monster Packs 有 15% 几率拥有 1 个额外 Modifier",
    "15% increased Effectiveness of Rare Monsters in your Maps": "你地图中 Rare Monsters 的 Effectiveness 提高 15%",
    "Rare Monsters have 30% increased chance of Monster Modifiers": "Rare Monsters 获得 Monster Modifiers 的几率提高 30%",
    "Rare Monster Packs in your Maps have a 50% increased chance to have an Additional Rare Monster": "你地图中的 Rare Monster Packs 拥有额外 Rare Monster 的几率提高 50%",
    "10% increased Rarity of Items Dropped by Rare Monsters": "Rare Monsters 掉落物品的稀有度提高 10%",
    "100% increased chance to encounter certain Shrines": "遇到特定 Shrines 的几率提高 100%",
    "100% increased chance for Shrines to be Seeking Shrines": "Shrines 成为 Seeking Shrines 的几率提高 100%",
    "100% increased chance for Shrines to be Enlightening Shrines": "Shrines 成为 Enlightening Shrines 的几率提高 100%",
    "100% increased chance for Shrines to be Gloom Shrines": "Shrines 成为 Gloom Shrines 的几率提高 100%",
    "Gain a Shrine bonus for Map Bosses": "为 Map Bosses 获得一个 Shrine 相关加成",
    "25% chance Shrine Buffs are reapplied when entering the Boss arena": "进入 Boss arena 时，Shrine Buffs 有 25% 几率重新施加",
    "25% chance Shrine Buffs are instead applied to the Boss when activated, granting an additional reward": "激活 Shrine 时，Shrine Buffs 有 25% 几率改为施加给 Boss，并给予额外奖励",
    "Areas with Powerful Map Bosses contain an additional Essence": "拥有 Powerful Map Bosses 的区域包含额外 1 个 Essence",
    "Areas with Powerful Map Bosses contain an additional Summoning Circle": "拥有 Powerful Map Bosses 的区域包含额外 1 个 Summoning Circle",
    "Areas with Powerful Map Bosses contain an additional Rogue Exile": "拥有 Powerful Map Bosses 的区域包含额外 1 个 Rogue Exile",
    "Areas with Powerful Map Bosses contain an additional Strongbox": "拥有 Powerful Map Bosses 的区域包含额外 1 个 Strongbox",
    "Areas with Powerful Map Bosses contain an additional Shrine": "拥有 Powerful Map Bosses 的区域包含额外 1 个 Shrine",
    "Areas with Powerful Map Bosses contain an additional Azmeri Spirit": "拥有 Powerful Map Bosses 的区域包含额外 1 个 Azmeri Spirit",
    "Summoning Circles summon packs or a more powerful Boss": "Summoning Circles 会召唤怪群或更强大的 Boss",
    "Summoning Circle Bosses are Powerful": "Summoning Circle Bosses 是 Powerful",
    "Summoning Circle Runes are guarded by 2 Packs of Random Monsters": "Summoning Circle Runes 由 2 群随机怪物守卫",
    "Rogue Exiles have 100% increased chance to have certain types of uniques": "Rogue Exiles 拥有特定类型 Unique 装备的几率提高 100%",
    "Rogue Exiles have 100% increased chance to have equipped Unique Weapons": "Rogue Exiles 装备 Unique Weapons 的几率提高 100%",
    "Rogue Exiles have 100% increased chance to have equipped Unique Armour": "Rogue Exiles 装备 Unique Armour 的几率提高 100%",
    "Rogue Exiles have 100% increased chance to have equipped Unique Jewellery": "Rogue Exiles 装备 Unique Jewellery 的几率提高 100%",
    "Rogue Exiles have 100% increased chance to wear Items requiring Strength": "Rogue Exiles 穿戴需要 Strength 的物品的几率提高 100%",
    "Rogue Exiles have 100% increased chance to wear Items requiring Dexterity": "Rogue Exiles 穿戴需要 Dexterity 的物品的几率提高 100%",
    "Rogue Exiles have 100% increased chance to wear Items requiring Intelligence": "Rogue Exiles 穿戴需要 Intelligence 的物品的几率提高 100%",
    "Strongboxes in your Maps have 150% increased chance to be Cartographer's Strongboxes": "你地图中的 Strongboxes 成为 Cartographer's Strongboxes 的几率提高 150%",
    "Strongboxes in your Maps have 150% increased chance to be Researcher's Strongboxes": "你地图中的 Strongboxes 成为 Researcher's Strongboxes 的几率提高 150%",
    "Strongboxes in your Maps have 150% increased chance to be Ornate Strongboxes": "你地图中的 Strongboxes 成为 Ornate Strongboxes 的几率提高 150%",
    "Blacksmith's, Armourer's and Basic Strongboxes can roll additional Prefix Modifiers that cause dropped items to require Strength if possible": "Blacksmith's、Armourer's 和 Basic Strongboxes 可以额外掷出前缀词缀，使掉落物品在可能时需要 Strength",
    "Blacksmith's, Armourer's and Basic Strongboxes can roll additional Prefix Modifiers that cause dropped items to require Dexterity if possible": "Blacksmith's、Armourer's 和 Basic Strongboxes 可以额外掷出前缀词缀，使掉落物品在可能时需要 Dexterity",
    "Blacksmith's, Armourer's and Basic Strongboxes can roll additional Prefix Modifiers that cause dropped items to require Intelligence if possible": "Blacksmith's、Armourer's 和 Basic Strongboxes 可以额外掷出前缀词缀，使掉落物品在可能时需要 Intelligence",
    "Faridun Cities are also considered Desert Areas": "Faridun Cities 也被视为 Desert Areas",
    "Faridun Cities are also considered Mountain Areas": "Faridun Cities 也被视为 Mountain Areas",
    "Ezomyte Cities are also considered Grass Areas": "Ezomyte Cities 也被视为 Grass Areas",
    "Ezomyte Cities are also considered Swamp Areas": "Ezomyte Cities 也被视为 Swamp Areas",
    "Vaal Cities are also considered Forest Areas": "Vaal Cities 也被视为 Forest Areas",
    "Vaal Cities are also considered Water Areas": "Vaal Cities 也被视为 Water Areas",
}

CATEGORY_DEFS = [
    {
        "id": "baseline",
        "title_en": "Map baseline rewards",
        "title_cn": "地图基础收益",
        "design": "This layer makes every map better even when the player is not targeting a dedicated mechanic.",
        "design_cn": "这一层负责让所有地图自然变肥：更多怪、更高数量、更高稀有度、更好的 Waystone 维持。",
        "nodes": ["The Journey Ahead", "Lucky Pillage", "Constant Crossroads", "Fortunate Path", "Valuable Paths", "Grueling Journey"],
    },
    {
        "id": "waystone",
        "title_en": "Waystone and map modifier layer",
        "title_cn": "Waystone 与地图词缀层",
        "design": "Waystones are treated as a risk dial. The tree raises modifier effect, corruption depth and reward pressure.",
        "design_cn": "Waystone 不只是门票，而是风险倍率旋钮。主树通过词缀效果、腐化和稀有度把地图强度推高。",
        "nodes": ["Unstable Energies", "Corrupted Infusion", "Enigmatic Intensification", "The High Road", "Risk and Reward", "Valuable Paths"],
    },
    {
        "id": "tablet",
        "title_en": "Tablet and Precursor Tower planning",
        "title_cn": "Tablet 与 Precursor Tower 规划",
        "design": "This layer turns mapping from a single-map action into regional planning around towers, tablets and overlapping effects.",
        "design_cn": "这一层把刷图从单张地图行为改成区域规划：塔揭示区域，石板叠加规则，地图因此被改造。",
        "nodes": ["Atop the World", "Precursor Influence", "Remnants of Power", "Controlled Climates", "Reverse Transcription", "Curiously Durable Stone", "Eons of Contamination", "Eons of Domination"],
    },
    {
        "id": "biome",
        "title_en": "Biome and City ecology",
        "title_cn": "Biome 与 City 生态",
        "design": "Map geography matters. Different biomes and cities become different production environments.",
        "design_cn": "地图地理身份会影响收益：沙漠、森林、草地、山地、沼泽、水域与城市各自偏向不同内容。",
        "nodes": ["History of the Faridun", "History of the Ezomytes", "History of the Vaal", "Industrial Improvements", "Local Knowledge", "Boss of the Bog", "Arid Stability", "Bounty of the Fields", "Cult of the Rains"],
    },
    {
        "id": "content",
        "title_en": "Generic map content",
        "title_cn": "通用地图内容",
        "design": "These are non-dedicated mechanics that live inside the main tree: Essence, Strongbox, Shrine, Rogue Exile, Azmeri Spirit and Summoning Circle.",
        "design_cn": "这些不是 Abyss/Breach 等专属树，而是主树内置的刷图口味：精华、保险箱、神龛、盗贼流放者、阿兹莫里灵体、召唤法阵。",
        "nodes": ["Crystalline Growths", "Resonant Lattice", "Likely Ambush", "Hidden Compartments", "Places of Worship", "Gathered Masses", "Wanted Poster", "Dressed in Fineries", "Guiding Light", "Grip of the Wilds", "Challenging Foe", "Runic Flare"],
    },
    {
        "id": "monster",
        "title_en": "Monster risk and reward",
        "title_cn": "怪物风险与收益",
        "design": "The tree converts stronger magic and rare monsters into loot pressure through modifiers, duplication, pack size and effectiveness.",
        "design_cn": "这层把更强的魔法怪和稀有怪转化为收益：更多词缀、更大怪群、复制、效能与按词缀计算的稀有度。",
        "nodes": ["Expanding Hordes", "Bountiful Bloodlines", "Infused Flesh", "Befit the Challenge", "Twin Threats", "No Simple Battles", "Adaptive Biology", "Mutating Monsters", "To the Strong Go the Spoils", "Nemesis Rising"],
    },
    {
        "id": "boss",
        "title_en": "Boss, Powerful Boss and Pinnacle compression",
        "title_cn": "Boss、强力 Boss 与巅峰压缩",
        "design": "Bosses become reward concentrators. Extra content, corruption, tablets and unique rewards are pushed into boss maps.",
        "design_cn": "Boss 不再只是地图结尾，而是收益压缩点。主树把额外内容、腐化、Tablet 和高价值掉落导向 Boss 地图。",
        "nodes": ["Fit for a King", "Hard-Won Treasures", "Pathkeepers", "Brutal Lessons", "Overlord's Domain", "Overlord's Influence", "Cataclysm's Wake", "Organised Forces", "Overlord's Hoard", "Ancient Relics", "Witness to History"],
    },
]

CHOICE_GROUPS = [
    {
        "title_en": "The Journey Ahead",
        "title_cn": "前路选择",
        "core": "The Journey Ahead",
        "role_cn": "最基础的地图生产参数：怪群规模、怪物强度、或物品稀有度。",
        "role_en": "The basic map-production dial: more packs, stronger monsters, or more item rarity.",
        "options": ["The Journey Ahead: Pack Size", "The Journey Ahead: Effectiveness", "The Journey Ahead: Rarity"],
    },
    {
        "title_en": "The Chosen Path",
        "title_cn": "选定之路",
        "core": "The Chosen Path",
        "role_cn": "主树最重要的通用内容偏向：决定当前地图更容易遇到哪类非专属内容。",
        "role_en": "The most important generic-content selector. It biases which non-dedicated content appears more often.",
        "options": ["The Chosen Path: Essences", "The Chosen Path: Rogue Exiles", "The Chosen Path: Summoning Circles", "The Chosen Path: Shrines", "The Chosen Path: Strongboxes", "The Chosen Path: Azmeri Spirits"],
    },
    {
        "title_en": "Essence Dowsing",
        "title_cn": "精华探测",
        "core": "Essence Dowsing",
        "role_cn": "把精华从随机工艺资源变成定向工艺资源。",
        "role_en": "Turns Essence from a random crafting resource into a targeted crafting resource.",
        "options": ["Essence Dowsing: Body", "Essence Dowsing: Mind", "Essence Dowsing: Enhancement", "Essence Dowsing: Abrasion", "Essence Dowsing: Flames", "Essence Dowsing: Ice", "Essence Dowsing: Electricity", "Essence Dowsing: Ruin"],
    },
    {
        "title_en": "Crystalline Patterns",
        "title_cn": "晶化纹路",
        "core": "Crystalline Patterns",
        "role_cn": "另一组精华类型定向，覆盖攻击、施法、速度、属性、暴击、稀有度和召唤相关方向。",
        "role_en": "A second Essence-type selector covering attack, caster, speed, attribute, critical, rarity and ally directions.",
        "options": ["Crystalline Patterns: Battle", "Crystalline Patterns: Sorcery", "Crystalline Patterns: Alacrity", "Crystalline Patterns: Infinite", "Crystalline Patterns: Seeking", "Crystalline Patterns: Opulence", "Crystalline Patterns: Command"],
    },
    {
        "title_en": "Corrupted Lattices",
        "title_cn": "腐化晶格",
        "core": "Corrupted Lattices",
        "role_cn": "腐化精华怪时的风险控制：稳定改精华、复制、加深腐化，或直接处理危险稀有怪。",
        "role_en": "Risk control when corrupting Essence monsters: stable conversion, duplication, deeper corruption, or killing dangerous rares.",
        "options": ["Corrupted Lattices: Stable Prison", "Corrupted Lattices: Duplication", "Corrupted Lattices: Deepened Corruption", "Corrupted Lattices: Ruptured Flesh"],
    },
    {
        "title_en": "Unseen Rivers",
        "title_cn": "暗流",
        "core": "Unseen Rivers",
        "role_cn": "定向阿兹莫里灵体类型，但不影响 Sacred Spirits。",
        "role_en": "Biases Azmeri Spirit type without changing Sacred Spirit chance.",
        "options": ["Unseen Rivers: Primal", "Unseen Rivers: Wild", "Unseen Rivers: Vivid"],
    },
    {
        "title_en": "Sacred Sap",
        "title_cn": "圣洁树液",
        "core": "Sacred Sap",
        "role_cn": "在更多 Sacred、复合附身、或更高 Empowerment 之间选择。",
        "role_en": "Chooses between more Sacred Spirits, mixed possession, or higher empowerment.",
        "options": ["Sacred Sap: Purified", "Sacred Sap: Commingled", "Sacred Sap: Distilled"],
    },
    {
        "title_en": "Evolving Throngs",
        "title_cn": "进化群体",
        "core": "Evolving Throngs",
        "role_cn": "魔法怪群的二选一：更大规模，或更多额外词缀。",
        "role_en": "Magic pack selector: larger packs or more additional modifiers.",
        "options": ["Evolving Throngs: Adaptation", "Evolving Throngs: Swarm"],
    },
    {
        "title_en": "Nemesis Rising",
        "title_cn": "宿敌崛起",
        "core": "Nemesis Rising",
        "role_cn": "稀有怪路线核心：强度、词缀、额外稀有怪、或稀有怪掉落稀有度。",
        "role_en": "Rare-monster selector: effectiveness, modifiers, additional rares, or rare-monster item rarity.",
        "options": ["Nemesis Rising: Effectiveness", "Nemesis Rising: Monster Modifiers", "Nemesis Rising: Additional Rare Monster", "Nemesis Rising: Rarity"],
    },
    {
        "title_en": "Divined Blessing",
        "title_cn": "神授祝福",
        "core": "Divined Blessing",
        "role_cn": "定向特定神龛类型。",
        "role_en": "Biases toward a selected Shrine type.",
        "options": ["Divined Blessing: Seeking Shrine", "Divined Blessing: Enlightening Shrine", "Divined Blessing: Gloom Shrine"],
    },
    {
        "title_en": "Fabled Showdown",
        "title_cn": "传说对决",
        "core": "Fabled Showdown",
        "role_cn": "Boss 战神龛选择：玩家拿 Buff 更安全，或让 Boss 拿 Buff 换额外奖励。",
        "role_en": "Boss-shrine selector: player safety via buff reapplication, or boss empowerment for extra reward.",
        "options": ["Favour the Hero", "Favour the Villain"],
    },
    {
        "title_en": "Overlord's Domain",
        "title_cn": "霸主领域",
        "core": "Overlord's Domain",
        "role_cn": "把 Essence、Summoning Circle 或 Rogue Exile 添加到 Powerful Map Boss 区域。",
        "role_en": "Adds Essence, Summoning Circle or Rogue Exile to areas with Powerful Map Bosses.",
        "options": ["Overlord's Domain: Essence", "Overlord's Domain: Summoning Circle", "Overlord's Domain: Rogue Exile"],
    },
    {
        "title_en": "Overlord's Influence",
        "title_cn": "霸主影响",
        "core": "Overlord's Influence",
        "role_cn": "把 Strongbox、Shrine 或 Azmeri Spirit 添加到 Powerful Map Boss 区域。",
        "role_en": "Adds Strongbox, Shrine or Azmeri Spirit to areas with Powerful Map Bosses.",
        "options": ["Overlord's Influence: Strongbox", "Overlord's Influence: Shrine", "Overlord's Influence: Azmeri Spirit"],
    },
    {
        "title_en": "Blood on the Stones",
        "title_cn": "石上之血",
        "core": "Blood on the Stones",
        "role_cn": "召唤法阵走 Boss 强化，或走符文守卫怪群密度。",
        "role_en": "Summoning Circle selector: stronger bosses or additional guardian packs around runes.",
        "options": ["Blood on the Stones: Bosses", "Blood on the Stones: Guardians"],
    },
    {
        "title_en": "Rogue Exile equipment selectors",
        "title_cn": "盗贼流放者装备选择",
        "core": "Legendary Duels",
        "role_cn": "把 Rogue Exile 变成定向装备掉落源：武器、防具、首饰，以及力量/敏捷/智慧需求方向。",
        "role_en": "Turns Rogue Exiles into targeted item sources: weapon, armour, jewellery, and attribute requirements.",
        "options": ["Legendary Duels: Renowned Weapons", "Legendary Duels: Renowned Armours", "Legendary Duels: Renowned Jewelry", "Well-equipped Opponents: Strength", "Well-equipped Opponents: Dexterity", "Well-equipped Opponents: Intelligence"],
    },
    {
        "title_en": "Strongbox selectors",
        "title_cn": "保险箱选择",
        "core": "Strongbox Type Selector",
        "role_cn": "一层选择箱子类型，一层选择装备属性倾向。",
        "role_en": "One layer selects strongbox type; another biases item attribute requirements.",
        "options": ["Cartographer's Plunder", "Researcher's Plunder", "Noble's Plunder", "Craftsman's Creed: Strength of Arm", "Craftsman's Creed: Skill of Hand", "Craftsman's Creed: Sharpness of Mind", "Craftsman's Creed: Starkness of Heart"],
    },
    {
        "title_en": "City history selectors",
        "title_cn": "城市史记选择",
        "core": "History of the Faridun",
        "role_cn": "把城市额外视为某种 Biome，让城市节点与地形节点叠加触发。",
        "role_en": "Makes cities count as an additional biome, allowing city bonuses and biome bonuses to stack.",
        "options": ["History of the Faridun: Vastiri Woes", "History of the Faridun: Mutewind Alliance", "History of the Ezomytes: Eastern Phaaryl", "History of the Ezomytes: Northern Ezomyr", "History of the Vaal: Reign of the First Queen", "History of the Vaal: Grand Waterways"],
    },
]


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def read_nodes() -> list[dict[str, str]]:
    with NODE_CSV.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def main_tree_nodes(nodes: list[dict[str, str]]) -> list[dict[str, str]]:
    rows = []
    for row in nodes:
        if row.get("atlas_sub_tree") != "Generic":
            continue
        node_id = row.get("id", "")
        if node_id.startswith(EXCLUDED_GENERIC_ID_PREFIXES):
            continue
        rows.append(row)
    return rows


def index_by_name(nodes: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    by: dict[str, list[dict[str, str]]] = {}
    for row in nodes:
        by.setdefault(row.get("name", ""), []).append(row)
    return by


def cn(name: str) -> str:
    return CN_NAME.get(name, "")


def display_name(name: str) -> str:
    c = cn(name)
    return f"{esc(name)} <span class=\"muted\">/ {esc(c)}</span>" if c else esc(name)


def type_display(ntype: str) -> str:
    type_cn = {
        "keystone": "核心点",
        "notable": "显著点",
        "choice_option": "选择选项",
        "small": "小点",
    }
    label = type_cn.get(ntype, "未知")
    return f"<code>{esc(ntype)}</code><br><span class=\"muted\">{esc(label)}</span>"


def effect_cn(text: str) -> str:
    if not text:
        return "该节点在数据表中没有效果文本。"
    return STAT_CN.get(text, f"待补充人工翻译：{text}")


def render_effect_text(text: str) -> str:
    return esc(text).replace(" | ", "<br>")


def effect(row: dict[str, str] | None) -> str:
    if not row:
        return "<span class=\"missing\">数据表未找到 / Missing in CSV</span>"
    raw_text = row.get("stat_text_raw") or ""
    en_text = raw_text or "No stat text in CSV."
    zh_text = effect_cn(raw_text)
    return (
        f"<div class=\"effect-block\"><span class=\"effect-label\">EN</span>{render_effect_text(en_text)}</div>"
        f"<div class=\"effect-block zh\"><span class=\"effect-label\">中</span>{render_effect_text(zh_text)}</div>"
    )


def node_row(name: str, by_name: dict[str, list[dict[str, str]]]) -> str:
    rows = by_name.get(name, [])
    row = rows[0] if rows else None
    ntype = row.get("type", "") if row else ""
    return (
        "<tr>"
        f"<td class=\"node-name\">{display_name(name)}</td>"
        f"<td>{type_display(ntype)}</td>"
        f"<td>{effect(row)}</td>"
        "</tr>"
    )


def render_category(cat: dict[str, object], by_name: dict[str, list[dict[str, str]]]) -> str:
    rows = "".join(node_row(name, by_name) for name in cat["nodes"])
    return f"""
    <section class=\"card\" id=\"cat-{esc(cat['id'])}\">
      <h3>{esc(cat['title_en'])} <span>/ {esc(cat['title_cn'])}</span></h3>
      <p class=\"two-line\"><b>Design role:</b> {esc(cat['design'])}<br><b>设计作用：</b>{esc(cat['design_cn'])}</p>
      <table>
        <thead><tr><th>Node / 节点</th><th>Type</th><th>Effect / 效果</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </section>
    """


def render_choice_group(group: dict[str, object], by_name: dict[str, list[dict[str, str]]]) -> str:
    core = by_name.get(group["core"], [None])[0]
    option_rows = "".join(node_row(name, by_name) for name in group["options"])
    return f"""
    <section class=\"choice-card\" id=\"choice-{esc(str(group['title_en']).lower().replace(' ', '-').replace("'", ''))}\">
      <div class=\"choice-head\">
        <h3>{esc(group['title_en'])} <span>/ {esc(group['title_cn'])}</span></h3>
        <div class=\"badge\">Choice Point / 选择点</div>
      </div>
      <p><b>Core effect / 核心效果：</b>{effect(core)}</p>
      <p><b>Design role:</b> {esc(group['role_en'])}<br><b>设计作用：</b>{esc(group['role_cn'])}</p>
      <table>
        <thead><tr><th>Option / 选项</th><th>Type</th><th>Effect / 效果</th></tr></thead>
        <tbody>{option_rows}</tbody>
      </table>
    </section>
    """


def render_glossary() -> str:
    rows = []
    for en, zh, desc in TERM_GLOSSARY:
        rows.append(f"<tr><td><code>{esc(en)}</code></td><td>{esc(zh)}</td><td>{esc(desc)}</td></tr>")
    return "".join(rows)


def render_type_glossary() -> str:
    rows = []
    for ntype, zh, desc in TYPE_GLOSSARY:
        rows.append(f"<tr><td><code>{esc(ntype)}</code></td><td>{esc(zh)}</td><td>{esc(desc)}</td></tr>")
    return "".join(rows)


def render_stat_box(label: str, value: object, note: str = "") -> str:
    return f"""
    <div class=\"stat\">
      <div class=\"stat-value\">{esc(value)}</div>
      <div class=\"stat-label\">{esc(label)}</div>
      {f'<div class=\"stat-note\">{esc(note)}</div>' if note else ''}
    </div>
    """


def build_html(nodes: list[dict[str, str]]) -> str:
    generic_all = [n for n in nodes if n.get("atlas_sub_tree") == "Generic"]
    main = main_tree_nodes(nodes)
    by_name = index_by_name(main)
    counts = Counter(n.get("type", "unknown") for n in main)
    category_html = "".join(render_category(cat, by_name) for cat in CATEGORY_DEFS)
    choice_html = "".join(render_choice_group(group, by_name) for group in CHOICE_GROUPS)
    stat_html = "".join(
        [
            render_stat_box("Generic rows in CSV / CSV 中 Generic 行", len(generic_all)),
            render_stat_box("Main-tree rows used / 本报告采用主树行", len(main), "已排除专属玩法 ID 前缀"),
            render_stat_box("Keystones / 核心点", counts.get("keystone", 0)),
            render_stat_box("Notables / 显著点", counts.get("notable", 0)),
            render_stat_box("Choice options / 选择选项", counts.get("choice_option", 0)),
        ]
    )
    toc_cats = "".join(f"<li><a href=\"#cat-{esc(cat['id'])}\">{esc(cat['title_cn'])} / {esc(cat['title_en'])}</a></li>" for cat in CATEGORY_DEFS)
    toc_choices = "".join(f"<li>{esc(group['title_cn'])} / {esc(group['title_en'])}</li>" for group in CHOICE_GROUPS)
    return f"""<!doctype html>
<html lang=\"zh-CN\">
<head>
<meta charset=\"utf-8\">
<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
<title>PoE2 Atlas Main Passive Tree Analysis / 异界主树设计分析</title>
<style>
:root {{
  color-scheme: light;
  --bg: #f3efe5;
  --panel: #fffaf0;
  --ink: #211a12;
  --muted: #6e6252;
  --line: #d7c7ad;
  --accent: #9d5b1c;
  --accent2: #234e70;
  --soft: #f7ead4;
}}
* {{ box-sizing: border-box; }}
body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", Arial, sans-serif; color: var(--ink); background: radial-gradient(circle at top left, #fff8e8 0, var(--bg) 42%, #e7ddcc 100%); line-height: 1.65; }}
header {{ padding: 44px 6vw 28px; background: linear-gradient(135deg, #24160b, #6e3d12 60%, #9d5b1c); color: #fff7e8; }}
header h1 {{ margin: 0 0 10px; font-size: clamp(28px, 4vw, 48px); letter-spacing: .02em; }}
header p {{ margin: 7px 0; color: #f3ddbb; max-width: 1100px; }}
main {{ padding: 28px 6vw 60px; max-width: 1500px; margin: 0 auto; }}
section {{ scroll-margin-top: 24px; }}
.card, .choice-card, .note, .toc, .glossary {{ background: rgba(255, 250, 240, .92); border: 1px solid var(--line); border-radius: 18px; padding: 22px; box-shadow: 0 14px 30px rgba(65, 42, 12, .08); margin: 18px 0; }}
h2 {{ margin: 34px 0 14px; font-size: 28px; border-left: 6px solid var(--accent); padding-left: 12px; }}
h3 {{ margin: 0 0 10px; font-size: 21px; color: #3a2414; }}
h3 span, .muted {{ color: var(--muted); font-weight: 500; }}
.two-line {{ margin: 8px 0 18px; }}
.stat-grid {{ display: grid; grid-template-columns: repeat(5, minmax(140px, 1fr)); gap: 14px; margin-top: 22px; }}
.stat {{ background: rgba(255,255,255,.16); border: 1px solid rgba(255,255,255,.28); border-radius: 14px; padding: 14px; }}
.stat-value {{ font-size: 30px; font-weight: 800; color: #fff; }}
.stat-label {{ color: #ffefcf; font-size: 13px; }}
.stat-note {{ color: #e9cda6; font-size: 12px; }}
.grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 18px; }}
.toc ul {{ columns: 2; margin: 8px 0 0; padding-left: 22px; }}
a {{ color: #7a3f0a; }}
table {{ width: 100%; border-collapse: collapse; overflow: hidden; border-radius: 12px; background: #fffdf8; }}
th, td {{ border-bottom: 1px solid #eadbc4; vertical-align: top; padding: 10px 12px; }}
th {{ text-align: left; background: #ead8ba; color: #392511; position: sticky; top: 0; }}
tr:last-child td {{ border-bottom: 0; }}
code {{ background: #f1e3cf; border: 1px solid #dfc7a4; border-radius: 6px; padding: 1px 5px; font-family: ui-monospace, SFMono-Regular, Consolas, monospace; }}
.node-name {{ min-width: 260px; font-weight: 700; }}
.effect-block {{ margin: 0 0 8px; padding-left: 42px; position: relative; }}
.effect-block:last-child {{ margin-bottom: 0; }}
.effect-label {{ position: absolute; left: 0; top: 0; min-width: 28px; text-align: center; border-radius: 6px; background: #efe0c8; color: #4d3518; font-size: 11px; font-weight: 800; }}
.effect-block.zh {{ color: #2f4b2f; }}
.effect-block.zh .effect-label {{ background: #dfeeda; color: #275127; }}
.choice-head {{ display: flex; align-items: center; justify-content: space-between; gap: 12px; }}
.badge {{ display: inline-block; border-radius: 999px; background: #e4f0f6; color: var(--accent2); border: 1px solid #a8cadb; padding: 5px 11px; font-size: 12px; font-weight: 800; white-space: nowrap; }}
.missing {{ color: #a33; font-weight: 700; }}
.pill-list {{ display: flex; flex-wrap: wrap; gap: 8px; padding: 0; margin: 10px 0 0; list-style: none; }}
.pill-list li {{ background: var(--soft); border: 1px solid var(--line); border-radius: 999px; padding: 5px 10px; }}
footer {{ color: var(--muted); border-top: 1px solid var(--line); margin-top: 38px; padding-top: 18px; font-size: 13px; }}
@media (max-width: 1000px) {{ .grid, .stat-grid {{ grid-template-columns: 1fr; }} .toc ul {{ columns: 1; }} .node-name {{ min-width: unset; }} table {{ font-size: 14px; }} }}
</style>
</head>
<body>
<header>
  <h1>PoE2 Atlas Main Passive Tree Analysis<br>异界主树设计分析</h1>
  <p>Generated on {esc(date.today().isoformat())}. Source: <code>{esc(NODE_CSV.relative_to(ROOT))}</code></p>
  <p>Scope / 范围：只分析 <b>Generic 主树</b>。报告会排除 Abyss、Breach、Delirium、Expedition、Incursion、Ritual 等专属玩法树；同时排除少量虽然标记为 Generic、但 ID 前缀属于专属玩法的节点。</p>
  <div class=\"stat-grid\">{stat_html}</div>
</header>
<main>
  <section class=\"note\">
    <h2>Executive summary / 核心结论</h2>
    <p><b>English:</b> The main Atlas tree is not primarily a build tree. It is a mapping control surface. Most nodes provide permanent progression, while selected keystones act as switches for current farming strategy.</p>
    <p><b>中文：</b>主树不是传统意义上的角色构筑树，而是一个“开图控制台”。大多数节点负责长期成长；真正的策略变化集中在选择点：内容偏向、精华类型、灵体类型、怪物风险、Boss 聚合和城市地形叠加。</p>
    <ul class=\"pill-list\">
      <li>Progression / 长期成长</li>
      <li>Direction switches / 策略开关</li>
      <li>Regional planning / 区域规划</li>
      <li>Risk-to-reward / 风险换收益</li>
      <li>Boss compression / Boss 收益压缩</li>
    </ul>
  </section>

  <section class=\"toc\">
    <h2>Table of contents / 目录</h2>
    <div class=\"grid\">
      <div><h3>Taxonomy / 分类</h3><ul>{toc_cats}</ul></div>
      <div><h3>Choice points / 选择点</h3><ul>{toc_choices}</ul></div>
    </div>
  </section>

  <section class=\"glossary\">
    <h2>Node type / Type 字段是什么意思</h2>
    <p><b>English:</b> The <code>type</code> column comes from the cleaned passive node data and describes how the node behaves in the tree. In this report it is mostly used to distinguish rule-changing selectors, ordinary notable bonuses and selector options.</p>
    <p><b>中文：</b><code>type</code> 是清洗后的节点类型字段，用来说明这个节点在树上的功能。这里最常见的是 keystone、notable 和 choice_option：前者多为规则变化或选择器，中间是显著奖励点，后者是某个选择器下的具体选项。</p>
    <table>
      <thead><tr><th>type</th><th>中文</th><th>Meaning / 含义</th></tr></thead>
      <tbody>{render_type_glossary()}</tbody>
    </table>
  </section>

  <section class=\"glossary\">
    <h2>Terminology / 术语对照</h2>
    <table>
      <thead><tr><th>English</th><th>中文</th><th>Design meaning / 设计含义</th></tr></thead>
      <tbody>{render_glossary()}</tbody>
    </table>
  </section>

  <h2>1. Main-tree taxonomy / 主树分类</h2>
  {category_html}

  <h2>2. Choice points / 选择点详解</h2>
  <section class=\"note\">
    <p><b>English:</b> Because most progression nodes can eventually be allocated, the meaningful decisions are compressed into selector nodes. These are not just numerical upgrades; they decide what the next batch of maps is trying to produce.</p>
    <p><b>中文：</b>由于许多成长点理论上最终都能点满，真正的选择集中在选择节点上。它们不是简单数值加成，而是在决定当前这一轮刷图到底生产什么：精华、保险箱、Boss、稀有怪、神龛、灵体或城市地形叠加。</p>
  </section>
  {choice_html}

  <section class=\"note\">
    <h2>Design read / 设计解读</h2>
    <p><b>English:</b> The main tree keeps long-term completion friendly while preserving strategy through selectors. You may eventually collect most progression, but you still cannot set every target type, shrine type, essence type, rogue equipment type and boss-area content to every option at once.</p>
    <p><b>中文：</b>主树的设计是在“最终可成长”和“当前有策略”之间折中：普通节点给长期成长，选择点给当前方向。玩家可以逐步点满大量成长点，但不能同时把所有精华类型、神龛类型、Rogue 装备类型、Boss 区域内容和城市地形都调到所有方向。</p>
    <p><b>Practical implication / 实战含义：</b> 你的 Atlas Build 不只是点数路线，而是这些选择开关的组合。短期刷图时应该先决定目标产物，再调 The Chosen Path、Essence/Azmeri/Shrine/Rogue/Strongbox 选择点，以及 Powerful Boss 的内容聚合。</p>
  </section>

  <footer>
    <p>Generated by <code>scripts/python/generate_atlas_main_tree_analysis.py</code>. This report is data-backed by the cleaned Atlas passive node CSV and deliberately excludes dedicated mechanic sub-trees.</p>
  </footer>
</main>
</body>
</html>
"""


def main() -> None:
    nodes = read_nodes()
    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.write_text(build_html(nodes), encoding="utf-8")
    print(f"Wrote {REPORT_FILE}")


if __name__ == "__main__":
    main()
