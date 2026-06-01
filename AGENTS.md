# POE2 项目规则

这些规则适用于本仓库内的弓打造报告、价格模型和后续修错。

## 数据与价格

- 所有 poe.ninja 能查到的材料，必须从 `data/processed/poe_ninja_prices.csv` 或 `data/processed/poe_ninja_prices.json` 快照取价。
- 手动价格只用于 poe.ninja 无法直接索引的交易物品，例如白底、指定词缀魔法底、半成品魔法底。
- 刷新价格只能更新快照数据或手动输入，不应改计算模型。

## 目录规范

- 根目录只保留项目级文件，例如 `AGENTS.md`、`.gitignore`、项目说明文件；不要把脚本、报告、截图直接生成到根目录。
- Python 脚本统一放在 `scripts/python/`。
- Windows 辅助脚本和计划任务入口统一放在 `scripts/windows/`。
- HTML 报告统一生成到 `reports/`。
- 报告截图、图表和其他报告资产统一生成到 `reports/assets/`。
- 原始抓取数据统一放在 `data/raw/`；清洗后的表和快照统一放在 `data/processed/`。
- poe.ninja 按分类拆分的价格 CSV 固定放在 `data/processed/poe_ninja_prices_by_type/`。
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
- 四条路线必须引用统一起步模块，不能各自写死不同起点。
- Fubgun 示例应归为“接近毕业”，不能标为“完美毕业”。
- 所有核心材料和词缀必须保留中英文对照。

## 机制假设

- 普通蜕变/增幅无最低词缀等级限制；高阶蜕变/增幅最低词缀等级按 44；完美蜕变/增幅按 70。
- 深渊三选一概率使用 `1 - (1 - p)^3`；深渊回响六选使用 `1 - (1 - p)^6`。
- `Preserved Jawbone` 与 `Ancient Jawbone` 分开计算；`Ancient Jawbone` 只用于高价值中间态或接近毕业封口。
- `Omen of Catalysing Exaltation / 催化崇高预兆` 只在物品有 Catalyst Quality 时进入路线。
