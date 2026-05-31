## Mod設計書: scrap_zombie

### 目的
金属スクラップと融合した新規ゾンビ進化系統2種（Scrap Zombie → Scrap Hulk）を追加する。高アーマー・高ダメージ・低速度の特性を持つ。

### スコープ
- **含む:**
  - モンスター2種: `mon_zombie_scrap`（copy-from `mon_zombie_base`）, `mon_zombie_scrap_hulk`（copy-from `mon_zombie_scrap`）
  - モンスターグループ追加2件: `GROUP_ZOMBIE` への出現追加, `GROUP_ZOMBIE_UPGRADE` への進化追加
  - 死亡ドロップ2件: `mon_zombie_scrap_death_drops`, `mon_zombie_scrap_hulk_death_drops`
- **含まない:**
  - アイテム追加（ドロップは既存アイテムを流用）
  - レシピ追加
  - シナリオ変更

### ターゲットバージョン
- CDDA: 0.I RC

### 依存関係
- 依存mod: dda（必須）

### 使用予定ID一覧
| 種別 | ID | 説明 |
|---|---|---|
| MONSTER | `mon_zombie_scrap` | スクラップゾンビ（基本種） |
| MONSTER | `mon_zombie_scrap_hulk` | スクラップハルク（進化種） |
| item_group | `mon_zombie_scrap_death_drops` | スクラップゾンビの死亡ドロップ |
| item_group | `mon_zombie_scrap_hulk_death_drops` | スクラップハルクの死亡ドロップ |

### 参照ファイル（external/cdda/） — 要確認
- [ ] `external/cdda/data/json/monsters/zombie.json` — `mon_zombie_base` のベースステータス確認、hulk系統（`mon_zombie_hulk`）のステータスベンチマーク
- [ ] `external/cdda/data/json/monstergroups/` — `GROUP_ZOMBIE`, `GROUP_ZOMBIE_UPGRADE` の既存構造確認

### ファイル構成
- modinfo.json
- data/monsters.json
- data/monstergroups.json
- data/death_drops.json

### 実装順序
1. modinfo.json
2. data/monsters.json（基本種 → 進化種の順）
3. data/death_drops.json
4. data/monstergroups.json

### モンスター仕様

| フィールド | mon_zombie_scrap | mon_zombie_scrap_hulk | 根拠 |
|---|---|---|---|
| id | `mon_zombie_scrap` | `mon_zombie_scrap_hulk` | |
| copy-from | `mon_zombie_base` | `mon_zombie_scrap` | 基本ゾンビ → 進化段階 |
| name | "scrap zombie" | "scrap hulk" | |
| hp | 110 | 380 | 標準(80)の約1.4倍 → ハルク級 |
| speed | 55 | 75 | 低速度（金属融合による鈍足） |
| melee_skill | 5 | 6 | 中程度～高めの近接精度 |
| melee_dice | 3d4 + 8 bash | 4d8 + 14 bash | スクラップによる高ダメージ |
| armor | bash 8, cut 10, stab 6, electric 2 | bash 14, cut 16, stab 10, bullet 12, electric 4 | 金属融合による高防御 |
| special_attacks | grab, bite_humanoid, scratch_humanoid, smash | grab, bite_humanoid, scratch_humanoid, smash | 標準ゾンビ攻撃＋粉砕 |
| upgrades | half_life 168 → `mon_zombie_scrap_hulk` | false（最終段階） | 168ターン（約7日）で進化 |
| death_drops | `mon_zombie_scrap_death_drops` | `mon_zombie_scrap_hulk_death_drops` | |
| extend.flags | `["SMELLS"]` | — | 臭気フラグ追加 |
| delete.flags | `["STUMBLES"]` | — | よろめき削除（金属骨格） |

### モンスターグループ仕様

**GROUP_ZOMBIE（汎用ゾンビ出現テーブル）:**
| モンスター | weight | cost_multiplier |
|---|---|---|
| `mon_zombie_scrap` | 10 | 5（通常出現） |
| `mon_zombie_scrap` | 5 | 15（低確率高コスト出現） |

**GROUP_ZOMBIE_UPGRADE（進化テーブル）:**
| モンスター | weight |
|---|---|
| `mon_zombie_scrap` | 30 |

### 死亡ドロップ仕様

**mon_zombie_scrap_death_drops:**
| アイテム | 数量 | 確率 |
|---|---|---|
| `default_zombie_items` | — | 100%（グループ参照） |
| `scrap` | 2–6 | 100% |
| `steel_chunk` | 1–3 | 60% |
| `sheet_metal_small` | 1–2 | 30% |

**mon_zombie_scrap_hulk_death_drops:**
| アイテム | 数量 | 確率 |
|---|---|---|
| `default_zombie_items` | — | 100%（グループ参照） |
| `scrap` | 6–12 | 100% |
| `steel_chunk` | 3–6 | 100% |
| `sheet_metal_small` | 2–4 | 50% |
| `steel_lump` | 1 | 20% |

### テスト手順
1. validate.shでJSON構文チェック（Level1）
2. link_mod_for_test.shでCDDAに配置
3. check_mods.shでmod読み込み確認（Level2）
4. CDDAを起動してLevel3確認:
   - デバッグメニューで `mon_zombie_scrap`, `mon_zombie_scrap_hulk` をスポーン
   - ステータス（HP、アーマー、ダメージ）が設計値通りか確認
   - 死亡時にドロップが発生することを確認
   - 自然スポーンすることを確認（長時間プレイまたはデバッグでモンスターグループ確認）

### 完了条件
- [ ] Level1: JSON構文OK
- [ ] Level2: 起動OK（エラーなし）
- [ ] Level3: 意図通り動作
  - [ ] `mon_zombie_scrap` がデバッグメニューでスポーン可能、戦闘可能
  - [ ] `mon_zombie_scrap_hulk` がデバッグメニューでスポーン可能、戦闘可能
  - [ ] 死亡時に対応するドロップテーブルが適用される
  - [ ] アーマー値（bash/cut/stab）が正しく適用されている
  - [ ] `GROUP_ZOMBIE` 経由で自然スポーンする
  - [ ] `mon_zombie_scrap` が進化して `mon_zombie_scrap_hulk` になる
