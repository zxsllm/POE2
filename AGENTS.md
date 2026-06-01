# POE2 项目规则

这些规则适用于本仓库内的弓打造报告、价格模型和后续修错。

## 数据与价格

- 所有 poe.ninja 能查到的材料，必须从 `data/processed/prices/poe_ninja/by_type/*.csv` 快照取价。
- 手动价格只用于 poe.ninja 无法直接索引的交易物品，例如白底、指定词缀魔法底、半成品魔法底。
- 刷新价格只能更新快照数据或手动输入，不应改计算模型。

## 目录规范

- 根目录只保留项目级文件，例如 `AGENTS.md`、`.gitignore`、项目说明文件；不要把脚本、报告、截图直接生成到根目录。
- Python 脚本统一放在 `scripts/python/`。
- Windows 辅助脚本和计划任务入口统一放在 `scripts/windows/`。
- HTML 报告按装备部位生成到 `reports/<slot>/`，例如弓报告固定放在 `reports/bow/`。
- 报告截图、图表和其他报告资产按装备部位生成到 `reports/<slot>/assets/`，例如弓资产固定放在 `reports/bow/assets/`。
- 原始抓取数据统一放在 `data/raw/`；这里保存网页、接口 JSON、站点脚本等原文，不能直接作为报告计算入口。
- poe.ninja 原始接口响应固定放在 `data/raw/poe_ninja/`；研究页面结构用的 HTML/JS 固定放在 `data/raw/poe_ninja/site_research/`；清洗后的价格表固定放在 `data/processed/prices/poe_ninja/by_type/`，每个类型一个 CSV。
- poe.ninja 价格快照摘要固定放在 `data/processed/prices/poe_ninja/summary.json`。
- PoE2DB 清洗后的全量词缀表固定放在 `data/processed/mods/poe2db_mods.csv`。
- PoE2DB 清洗后的全量基底表固定放在 `data/processed/items/poe2db_base_items.csv`。
- Path of Crafting 清洗后的词缀表固定放在 `data/processed/mods/pathofcrafting/modifiers.csv`。
- 清洗流程的摘要/元数据固定放在 `data/processed/metadata/`。
- 报告专用的中间表固定放在 `data/processed/reports/<slot>/`，例如弓伤害图表数据放在 `data/processed/reports/bow/`。
- 不要同时保存同一批清洗数据的 CSV 和 JSON；清洗后的规范格式默认使用 CSV，只有摘要/元数据使用 JSON。
- 不要保存可由全量表直接过滤出来的重复子集，例如不要另存 `poe2db_bow_mods.csv` 或 `poe2db_bow_bases.csv`；弓报告运行时从全量词缀/基底表过滤。
- YouTube 字幕和清洗文本固定放在 `data/youtube_transcripts/`。
- 常用交易站搜索链接固定放在 `poe2-trade/`，每个链接同时维护 `.url` 快捷方式和 `README.md` 索引说明。
- 自动任务日志固定放在 `data/logs/`，该目录不进 git。
- 新增脚本时必须用 `Path(__file__).resolve().parents[2]` 或等价方式定位项目根目录，避免依赖当前工作目录。
- 新增生成物时，优先复用以上目录；如果必须新增目录，先更新本节说明。

## 起步模型

- 不能把“直接买某个魔法底”写死为任一路线起点。
- 所有路线必须先进入统一起步状态候选池，再按目标状态选择最便宜或最适合的候选。
- 起步池至少比较：白底、普通/高阶/完美蜕变增幅、直接买物理百分比魔法底、直接买物理点伤魔法底、一词后缀底增幅赌前缀、3:1 垃圾魔法弓回收。

## 报告结构

- 修错时必须改原段落、原计算或原数据模型，不允许追加“更正块”堆叠。
- 报告只保留必要信息：路径、状态、转移、概率、公式、造价、成本占比、停手/继续条件。
- 所有核心材料和词缀必须保留中英文对照。

## 机制假设

- 普通蜕变/增幅无最低词缀等级限制；高阶蜕变/增幅最低词缀等级按 44；完美蜕变/增幅按 70。
- 深渊三选一概率使用 `1 - (1 - p)^3`；深渊回响六选使用 `1 - (1 - p)^6`。
- `Preserved Jawbone` 与 `Ancient Jawbone` 分开计算；`Ancient Jawbone` 只用于高价值中间态或接近毕业封口。
- `Omen of Catalysing Exaltation / 催化崇高预兆` 只在物品有 Catalyst Quality 时进入路线。

## 打造原语

这些是写报告和改模型时默认使用的基础操作。若游戏版本或实测结果与这里冲突，先改本节和计算模型，再改报告。

- 词缀槽位分为前缀和后缀；稀有装备最多 6 条随机词缀，通常最多 3 前缀 + 3 后缀。
- 魔法物品通常最多 2 条随机词缀；交易站或游戏显示中可能还会出现固定词、品质、符文、污染或特殊来源词，不要把它们直接当成普通随机词缀池。
- 词缀是否能出现同时受物品等级、装备类型、词缀域、前后缀槽位、最低词缀等级和权重影响；计算概率时必须先过滤掉超过当前物品等级或不在当前工艺最低词缀等级范围内的词缀。
- `Orb of Transmutation / 蜕变石`：普通物品变为魔法物品，并生成 1 条随机词缀。
- `Orb of Augmentation / 增幅石`：给仍有空位的魔法物品增加 1 条随机词缀。
- `Regal Orb / 富豪石`：魔法物品升级为稀有物品，保留原词缀并增加 1 条随机词缀。
- `Exalted Orb / 崇高石`：给仍有空位的稀有物品增加 1 条随机词缀；失败定义不是“没加词”，而是加到了不符合路线目标的词，通常需要重买或重做前置状态。
- 高阶/完美蜕变、增幅、富豪、崇高会按各自最低词缀等级过滤词缀池；本项目当前模型中高阶按 44、完美按 70 处理。
- `Omen of Greater Exaltation / 高阶崇高预兆`：用于让下一次崇高类操作增加额外词缀；和定向预兆的叠加关系若未实测，报告必须标记为待验证假设。
- `Omen of Sinistral Exaltation / 左向崇高预兆` 与 `Omen of Dextral Exaltation / 右向崇高预兆`：分别按项目约定视作定向前缀和定向后缀；使用前必须确认目标槽位有空位。
- 深渊封口是可循环工艺：揭示失败后，若模型假设可用 `Omen of Light / 光明预兆` 剥离深渊词，则失败成本应计入循环，不应按炸底重买计算。
- 深渊三选一和深渊回响六选都要把可出现的 Base 普通词缀与深渊专属词分开建模；若专属词权重未知，报告必须说明数据缺口，不得假装精算。
- 任何路线的“有效词”必须先在路线定义中列清楚；计算多次崇高成功率时，按路线定义判断是“至少一条有效”还是“每条新增都有效”。
