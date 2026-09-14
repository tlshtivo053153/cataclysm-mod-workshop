# MONSTER 実装パターン

CDDAに新規モンスター（特にゾンビ系進化系統）を追加するためのパターンファイル。

## 概要

ゾンビ系モンスターを追加する場合、以下の要素を定義する：

- **MONSTER**: `copy-from: mon_zombie_base`（または既存ゾンビ）で継承、必要なフィールドのみ上書き
- **item_group (death_drops)**: `subtype: "collection"` で死亡ドロップを定義
- **monstergroup**: same-ID merge でバニラの出現テーブルに注入

## ファイル構成

小規模モンスターmod（2種＋ドロップ＋出現設定）の最小構成：

| ファイル | type | 内容 |
|---|---|---|
| `modinfo.json` | `MOD_INFO` | mod登録情報。`category: "creatures"` 推奨 |
| `data/monsters.json` | `MONSTER` | モンスター定義（copy-fromで継承） |
| `data/death_drops.json` | `item_group` | 死亡ドロップ定義（subtype: collection） |
| `data/monstergroups.json` | `monstergroup` | same-ID mergeで出現テーブルに注入 |

## 参照ファイル（external/cdda/）

| ファイル | 目的 |
|---|---|
| `data/json/monsters/zed-classic.json` | `mon_zombie_base` のabstract定義（全デフォルトフィールド確認） + `mon_zombie_tough` — 中盤装甲ゾンビの実装パターン |
| `data/json/monsters/zed_misc.json` | `mon_zombie_hulk` — 後半大型ゾンビ（smash / species / delete flags） |
| `data/json/monsterdrops/zombie.json` | `mon_zombie_hulk_death_drops` の構造確認 |
| `data/json/monstergroups/zombies.json` | `GROUP_ZOMBIE` 構造（monsters 配列のエントリ形式） |
| `data/json/monstergroups/zombie_upgrades.json` | `GROUP_ZOMBIE_UPGRADE` 構造 |
| `data/json/items/resources/metal.json` | ドロップ用バニラアイテムID一覧 |

## copy-from 継承パターン

### abstract base からの継承

```json
{
  "id": "mon_zombie_scrap",
  "type": "MONSTER",
  "name": { "str": "scrap zombie" },
  "description": "...",
  "copy-from": "mon_zombie_base",
  "hp": 110,
  "speed": 55,
  ...
}
```

- `copy-from` に abstract な base（`mon_zombie_base` 等）を指定
- 子側で `type: "MONSTER"` を明示する（abstract は継承されない）
- `name`、`description` を必ず設定する（base の値はそのまま使わない）

### 既存モンスターからの継承

```json
{
  "id": "mon_zombie_scrap_hulk",
  "type": "MONSTER",
  "name": { "str": "scrap hulk" },
  "description": "...",
  "copy-from": "mon_zombie_scrap",
  "species": [ "ZOMBIE" ],
  ...
}
```

- 進化形は前段階のモンスターを `copy-from` するとフィールド記述量を削減できる

## MONSTER フィールド実装ルール

### name フィールド

```json
"name": { "str": "scrap zombie" }
```

- `{"str": "..."}` 形式（バニラで支配的な形式）
- 一部モンスター（動的名前生成）では `{"str_sp": "..."}` も使用されるが、新規モンスターは `str` でよい

### special_attacks — 完全上書きに注意

**`copy-from` 時に `special_attacks` を設定すると、親の配列は完全に破棄される。** 継承したい攻撃も明示的に再宣言が必要。

base のデフォルト:
```json
"special_attacks": [
  [ "PARROT", 400 ],
  [ "PARROT_AT_DANGER", 0 ],
  { "id": "grab", "cooldown": 2 },
  { "id": "bite_humanoid", "cooldown": 5 },
  { "id": "scratch_humanoid" }
]
```

子で上書きする場合（PARROTを削除しsmashを追加する例）:
```json
"special_attacks": [
  { "id": "grab", "cooldown": 7 },
  { "id": "bite_humanoid", "cooldown": 5 },
  { "id": "scratch_humanoid" },
  { "id": "smash", "throw_strength": 48 }
]
```

参考実装: `mon_zombie_tough` は PARROT を削除し grab/bite/scratch のみを再宣言している。

### smash 特殊攻撃

```json
{ "id": "smash", "throw_strength": 48 }
```

- `smash` はバニラの定義済み攻撃ID。新規定義不要
- `throw_strength` パラメータで吹き飛ばし強度を指定。有効範囲: 30〜108
- 中盤モンスター: 48、後半大型: 96（hulk相当）
- cooldown を指定しない場合、毎ターン発動可能。hulk は未指定で毎ターン smash 可能。中盤以下では cooldown を設定して頻度を抑える選択肢もある（任意、バランス次第）

### melee_damage 形式

```json
"melee_skill": 5,
"melee_dice": 3,
"melee_dice_sides": 4,
"melee_damage": [ { "damage_type": "bash", "amount": 8 } ]
```

- `melee_skill`: 近接命中精度スキル（base デフォルト: 4）。tough: 6, hulk: 5
- `melee_dice` / `melee_dice_sides`: 基本ダメージダイス（3d4 = 3〜12）
- `melee_damage`: 追加固定ダメージ（`bash` / `cut` / `stab`）
- base (`mon_zombie_base`) は `2d3 + 0cut`。継承時は必要な値のみ上書き

### armor 形式

```json
"armor": { "bash": 8, "cut": 10, "stab": 6, "bullet": 12, "electric": 4 }
```

- 有効なキー: `bash`, `cut`, `stab`, `bullet`, `electric`, `acid`, `heat`, `cold`, `biological`
- 必要な装甲タイプのみ指定。base は `{"electric": 1}` のみ
- tough 参考値: `{"bash": 2, "cut": 1, "bullet": 1, "electric": 2}`
- hulk 参考値: `{"bash": 8, "cut": 12, "bullet": 10, "electric": 5}`

### upgrades 進化形式

単体進化（特定モンスターに進化）:
```json
"upgrades": { "half_life": 168, "into": "mon_zombie_scrap_hulk" }
```

グループ進化（グループからランダム）:
```json
"upgrades": { "half_life": 120, "into_group": "GROUP_ZOMBIE_UPGRADE" }
```

進化なし（最終形態）:
```json
"upgrades": false
```

- **`into`** は特定モンスターIDを指定。1対1進化に使用（例: hunter → predator）
- **`into_group`** は monsterグループIDを指定。グループ内からランダム選択
- `half_life` の単位はゲーム内日数（168 = 約7日で半分が進化）

### species 上書き（進化形向け）

```json
"species": [ "ZOMBIE" ]
```

- base は `["ZOMBIE", "HUMAN"]`。完全に変異した進化形では `HUMAN` を削除して `["ZOMBIE"]` のみに
- hulk, hunter, predator 等の上位変異体がこのパターン

### flags の extend / delete

追加:
```json
"extend": { "flags": [ "SMELLS" ] }
```

削除:
```json
"delete": { "flags": [ "STUMBLES" ] }
```

- `extend` / `delete` は `copy-from` 時に使用可能
- 親の flags を全て再宣言する必要はない
- `extend` には複数フィールドの同時拡張が可能（flags, weakpoint_sets, families 等）
- 削除の実例: hulk は `STUMBLES` を削除。重量級モンスターでは同様に削除を検討

### volume / weight（単位付き文字列必須）

```json
"volume": "200 L",
"weight": "400 kg"
```

- 0.H以降、単位付き文字列が必須（数値のみは不可）
- 通常ゾンビ: `"62500 ml"` / `"81500 g"`
- hulk: `"875 L"` / `"1000 kg"`
- 大型モンスターでは `L` / `kg` 単位を使用

### color

```json
"color": "dark_gray"
```

- base デフォルト: `"light_green"`
- 色名は `external/cdda/data/json/` の既存モンスターを参照
- 金属系: `dark_gray` / `light_gray`、赤系: `light_red`、紫系: `white_magenta`

### death_drops

```json
"death_drops": "mon_zombie_scrap_death_drops"
```

- item_group ID を文字列で参照
- base デフォルト: `"default_zombie_death_drops"`
- 死亡ドロップの item_group は `subtype: "collection"` で別ファイルに定義

## death_drops 実装パターン

### 基本構造

```json
{
  "type": "item_group",
  "subtype": "collection",
  "id": "mon_zombie_scrap_death_drops",
  "entries": [
    { "group": "default_zombie_items" },
    { "item": "scrap", "count": [ 2, 6 ] },
    { "item": "steel_chunk", "count": [ 1, 3 ], "prob": 60 }
  ]
}
```

- `type: "item_group"` + `subtype: "collection"` が必須
- `default_zombie_items` を `group` 参照でネストし、通常ゾンビの衣服ドロップを維持
- `prob` がないアイテムは100%ドロップ
- `prob` は 1〜100 の整数（パーセント指定）
- `count` は `[min, max]` の配列
- `steel_lump` のように単品ドロップの場合は `count` を省略可能（デフォルト1個）

### 参照確認必須のアイテムID

ドロップアイテムIDは必ず `external/cdda/data/json/items/` で実在確認する。

金属系:
| ID | 位置 |
|---|---|
| `scrap` | `resources/metal.json:24` |
| `steel_chunk` | `resources/metal.json:269` |
| `sheet_metal_small` | `resources/metal.json:247` |
| `steel_lump` | `resources/metal.json:290` |

## monstergroup same-ID merge

**CDDAは同一IDのmonstergroupを自動マージする。** この仕組みを利用し、バニラの出現テーブルに新モンスターを注入できる。

### 書式

```json
{
  "type": "monstergroup",
  "id": "GROUP_ZOMBIE",
  "monsters": [
    { "monster": "mon_zombie_scrap", "weight": 10, "cost_multiplier": 5 },
    { "monster": "mon_zombie_scrap", "weight": 5, "cost_multiplier": 15 }
  ]
}
```

### 必須ルール

- **`id` をバニラと同一にする**（例: `GROUP_ZOMBIE`, `GROUP_ZOMBIE_UPGRADE`）
- **`monsters` 配列のみ記述する。** `default`, `is_animal`, `auto_total` 等のグループレベルフィールドは書かない（バニラ定義から継承される）
- **`copy-from` は使用しない。** same-ID merge では同じ `id` を定義するだけで自動マージされる

### 用途

| monstergroup ID | 用途 | 備考 |
|---|---|---|
| `GROUP_ZOMBIE` | 市街地自然出現 | `cost_multiplier` で出現タイミングを制御（5=中盤, 15=後半） |
| `GROUP_ZOMBIE_UPGRADE` | 通常ゾンビの進化先プール | `cost_multiplier` 不要（weight のみ） |

### 注意点

- `cost_multiplier` の値が高いほど出現が遅れる（日数経過後に出現し始める）
- 最終進化形（hulk相当）は直接 spawn させず、前段階からの進化（`upgrades.into`）のみで出現させる設計が推奨される

### 実在確認

same-ID merge を設計する前に、注入先の monstergroup がバニラに存在することを確認する:
```bash
grep -r '"id": "GROUP_ZOMBIE"' external/cdda/data/json/monstergroups/
```
モンスターIDも同様に存在確認:
```bash
grep -r '"id": "mon_zombie_scrap"' external/cdda/data/json/
```

## 実装手順（依存関係順）

1. `modinfo.json` — 最初に作成
2. `data/death_drops.json` — monsters.json から参照されるため先に作成
3. `data/monsters.json` — death_drops を参照
4. `data/monstergroups.json` — monster ID を参照

## バランス設計の指針

### 中盤モンスター比較対象

既存の同格モンスターと比較してトレードオフを設計する:

| モンスター | HP | Speed | Armor(bash/cut) | 特徴 |
|---|---|---|---|---|
| `mon_zombie_tough` | 100 | 85 | 2/1 | cutダメージ、中速 |
| scrap zombie (例) | 110 | 55 | 8/10 | bashダメージ、低速・高装甲 |

### 後半モンスター比較対象

| モンスター | HP | Speed | Armor(bash/cut) | 特徴 |
|---|---|---|---|---|
| `mon_zombie_hulk` | 480 | 130 | 8/12 | 高速・高HP |
| scrap hulk (例) | 380 | 75 | 14/16 | 低速・超高装甲 |

## テスト手順

1. **Level1**: `bash scripts/validate.sh <mod_dir>` — JSON構文チェック
2. **Level2**: `bash scripts/place_mod_for_test.sh <mod_dir>` + `bash scripts/check_mods.sh <mod_id>` — CDDAロードチェック
3. **Level3**: ゲーム内デバッグメニューで以下を確認
   - Spawn Monster → 全モンスターがスポーン可能か
   - 戦闘で装甲・ダメージが期待通りか
   - 解体（Butcher）で死亡ドロップが正しいか
   - Test Monster Group → GROUP_ZOMBIE から自然出現するか
