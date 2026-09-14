# トラップ実装パターン

CDDAに新規トラップを追加するためのパターンファイル。

## 概要

トラップを追加する場合、以下の2〜3要素を定義する：

- **trap 定義** (`"type": "trap"`): マップ上に設置されたトラップの挙動（action, visibility, drops等）
- **ITEM/TOOL 定義** (`"type": "ITEM"`, `"subtypes": [ "TOOL" ]`): プレイヤーが所持・設置するアイテム（`place_trap` use_action で trap 定義を参照）
- **recipe 定義** (任意): 製作レシピ

## ファイル構成

小規模トラップmod（2 trap＋2 item＋1 recipe）の最小構成：

| ファイル | type | 内容 |
|---|---|---|
| `modinfo.json` | `MOD_INFO` | mod登録情報。`category: "items"` 推奨 |
| `data/traps.json` | `trap` | トラップ定義 ×N |
| `data/items.json` | `ITEM` (TOOL) | トラップアイテム ×N（`place_trap` use_action） |
| `data/recipes.json` | `recipe` | 製作レシピ（任意） |

## 参照ファイル（external/cdda/）

| ファイル | 目的 |
|---|---|
| `data/json/traps.json` | 全trap定義。`tr_bubblewrap`, `tr_light_snare`, `tr_beartrap`, `tr_nailboard` 等の構造確認 |
| `data/json/items/tool/traps.json` | トラップアイテム定義（`light_snare_kit`, `board_trap`, `beartrap` 等）。`place_trap` use_action パターン確認 |
| `data/json/items/tool/deployable.json` | `place_trap` use_action の別パターン（`cot` 等） |
| `data/json/recipes/recipe_traps.json` | トラップレシピ構造（`caltrops`, `caltrops_glass` 等） |
| `data/json/items/containers/containers.json` | 缶アイテムID（`can_drink`, `can_food`, `can_medium`） |
| `data/json/items/generic/string.json` | 紐アイテムID（`string_36`, `string_6`） |
| `data/json/materials.json` | マテリアルID（`cotton`, `steel`, `wood` 等） |

## trap 定義の基本構造

```json
{
  "type": "trap",
  "id": "tr_imp_trap_noise",
  "name": "noise maker",
  "color": "light_gray",
  "symbol": "^",
  "visibility": 2,
  "avoidance": 8,
  "difficulty": 0,
  "action": "bubble",
  "drops": [ "imp_trap_noise_alarm" ],
  "vehicle_data": { "sound_volume": 90, "sound": "CLANK!  CLANK!  CLANK!" }
}
```

### 主要フィールド

| フィールド | 必須 | 説明 |
|---|---|---|
| `type` | 必須 | `"trap"` |
| `id` | 必須 | 一意のID（`tr_` プレフィックス推奨） |
| `name` | 必須 | 単純文字列。`str_sp` 不可 |
| `color` | 必須 | マップ表示色（`light_gray`, `dark_gray`, `brown` 等） |
| `symbol` | 必須 | マップ表示記号（通常 `"^"`） |
| `visibility` | 必須 | 見えやすさ（0=不可視, 高いほど見えやすい） |
| `avoidance` | 必須 | クリーチャーの回避率（0=必ず回避, 高いほど回避しない） |
| `difficulty` | 必須 | 解除難易度（0=自動成功） |
| `action` | 必須 | トラップ発動時のC++アクション（後述の制限あり） |
| `drops` | 任意 | 解除・破壊時のドロップアイテムID配列。**一部actionでは無視される** |
| `vehicle_data` | 任意 | 車両が踏んだ時の挙動（`sound_volume`, `sound`, `damage` 等） |

## ITEM 定義（place_trap use_action）

```json
{
  "id": "imp_trap_noise_alarm",
  "type": "ITEM",
  "subtypes": [ "TOOL" ],
  "copy-from": "light_snare_kit",
  "name": { "str": "noise alarm" },
  "description": "...",
  "weight": "1200 g",
  "volume": "1500 ml",
  "material": [ "steel", "cotton" ],
  "use_action": {
    "type": "place_trap",
    "needs_solid_neighbor": true,
    "trap": "tr_imp_trap_noise",
    "moves": 150,
    "practice": 2,
    "done_message": "You string up the noise alarm."
  },
  "flags": [ "SINGLE_USE" ]
}
```

### place_trap use_action フィールド

| フィールド | 必須 | 説明 |
|---|---|---|
| `type` | 必須 | `"place_trap"` |
| `trap` | 必須 | 設置する trap 定義のID |
| `moves` | 必須 | 設置所要移動コスト |
| `practice` | 任意 | 設置で得られる traps スキル練習値 |
| `done_message` | 任意 | 設置完了メッセージ |
| `needs_solid_neighbor` | 任意 | `true` で両端に壁が必要（通路設置型） |

### name 形式

- TOOL subtype → `{"str": "..."}` を使用（`str_sp` 不可）

## copy-from 継承時の注意

`light_snare_kit` 等の既存トラップアイテムから `copy-from` する場合：

| フィールド | copy-from元 | 上書き値 | 備考 |
|---|---|---|---|
| `name` | 平文（旧形式） | `{"str": "..."}` | 0.I形式で上書き必須 |
| `material` | 文字列単体 | 配列（`["steel", "cotton"]`） | 配列で上書き可 |
| `use_action` | オブジェクト全体 | オブジェクト全体 | `trap` 参照先を変更するため全面上書き |
| `category` | `"traps"` | （継承） | 上書き不要 |
| `flags` | `["SINGLE_USE"]` | `["SINGLE_USE"]` | 同一値でも再宣言推奨 |

## C++ trap action のハードコード制限（重要）

一部の `action` は C++ 実装でドロップアイテムやメッセージをハードコードしており、
JSON の `drops` フィールドや `vehicle_data` では上書きできない。

### 制限のある action 一覧

| action | ドロップアイテム | メッセージ | 備考 |
|---|---|---|---|
| `snare_light` | **常に `light_snare_kit`** | 固定 | `drops` フィールド完全無視。トリガー時はC++が `light_snare_kit` を直 spawn |
| `bubble` | **ドロップなし**（トラップ消滅） | 固定（`"You step on some bubble wrap!"`） | 踏んだ時のメッセージ・サウンドとも変更不可。`vehicle_data.sound` と `vehicle_data.sound_volume` は車両用に有効 |
| `beartrap` | **常に `beartrap`** | 固定 | `drops` フィールド無視（トリガー時）。解除時は別 |
| `crossbow` | `crossbow`, `string_36`（常時）+ `bolt_steel`（90%確率） | 固定 | `drops` フィールド無視 |
| `shotgun` | **常に `shotgun` + `string_36`** | 固定 | `drops` フィールド無視 |

### drops フィールドが有効なケース

- プレイヤーがトラップを**手動解除**（disarm）する場合、`on_disarmed` メソッドが `drops` を参照する
- 一部の action（`board`, `caltrops`）は確率で `on_disarmed` を呼び、その際に `drops` を使用
- **トリガー時（踏んだ時）は action のC++コードが直接 spawn を行い、`drops` は参照されない**

### 制限への対策

1. **可能な限り `drops` を正しく設定する**（手動解除時のため）
2. **action を変更できない場合**、ドロップしたバニラアイテムから自作アイテムに変換する簡易レシピを追加する
3. **新規 action が必要な場合**、EOC（`action: "eocs"`）でカスタム挙動をJSON定義する（複雑）

## レシピ定義

```json
{
  "type": "recipe",
  "activity_level": "LIGHT_EXERCISE",
  "result": "imp_trap_noise_alarm",
  "category": "CC_OTHER",
  "subcategory": "CSC_OTHER_TRAPS",
  "skill_used": "fabrication",
  "difficulty": 1,
  "time": "20 m",
  "autolearn": true,
  "components": [
    [ [ "can_drink", 3 ], [ "can_food", 3 ], [ "can_medium", 3 ] ],
    [ [ "string_36", 1 ], [ "string_6", 1 ] ]
  ]
}
```

### 必須フィールド（0.I RC）
- `activity_level` が必須。省略するとゲーム起動時エラー
- 軽作業 → `"LIGHT_EXERCISE"`、金属加工 → `"BRISK_EXERCISE"`

## 検証手順

1. `bash scripts/validate.sh <mod_dir>` — JSON構文チェック
2. `bash scripts/place_mod_for_test.sh <mod_dir>` — CDDAに配置
3. `bash scripts/check_mods.sh <mod_id>` — ゲーム読み込みチェック
4. CDDA起動 → デバッグメニューでアイテムスポーン → 設置 → 発動確認

### Level2 検証時の注意
- テキストスタイルチェッカー（0.I新機能）が英文の `.` `!` `?` 後2スペースを要求
- `Stale game data detected` エラーが出た場合: `external/cdda/config/flexcache` を削除して再実行

## 実装例

- `mods/small/improvised_traps/` — 騒音警報（`action: "bubble"`）+ 廃材スネア（`action: "snare_light"`）。C++制限の実例あり
