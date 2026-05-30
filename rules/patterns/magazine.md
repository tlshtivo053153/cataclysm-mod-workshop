# MAGAZINE 実装パターン

CDDAに新規マガジン（弾倉）を追加するためのパターンファイル。

## 概要

MAGAZINE は `"type": "ITEM"` + `"subtypes": ["MAGAZINE"]` で定義する。銃（GUN）の `magazines` フィールドで指定された口径・容量のマガジンが自動的に関連付けられる。

## ファイル構成

| ファイル | type | 内容 |
|---|---|---|
| `modinfo.json` | `MOD_INFO` | mod登録情報 |
| `data/items.json` | `ITEM` (MAGAZINE) | マガジンアイテム定義 |
| `data/recipes.json` | `recipe` | クラフトレシピ（オプション） |

## 参照ファイル（external/cdda/）

| ファイル | 目的 |
|---|---|
| `data/json/items/magazine/` | 全口径のマガジン定義。copy-from先・バランス比較の参照 |
| `data/json/recipes/weapon/magazines.json` | 既存マガジンレシピ。tools/qualities/componentsの参照 |
| `data/json/flags.json` | MAG_COMPACT, MAG_BULKY, MAG_DESTROY 等のフラグ定義 |

## 基本パターン

### copy-from を使う場合（既存マガジンをベースに派生）

```json
[
  {
    "id": "mymod_stanag45",
    "copy-from": "stanag30",
    "type": "ITEM",
    "subtypes": [ "MAGAZINE" ],
    "name": { "str": "improvised 45-round STANAG extended magazine" },
    "description": "A field-expedient extended magazine. Holds 45 rounds.",
    "looks_like": "stanag30",
    "weight": "330 g",
    "volume": "500 ml",
    "longest_side": "350 mm",
    "material": [ "plastic", "steel" ],
    "reload_time": 130,
    "mag_jam_mult": 2,
    "flags": [ "MAG_BULKY" ],
    "pocket_data": [
      {
        "pocket_type": "MAGAZINE",
        "rigid": true,
        "ammo_restriction": { "223": 45, "300blk": 30 }
      }
    ],
    "price": "12 USD",
    "price_postapoc": "1 USD 50 cent"
  }
]
```

## copy-from の継承動作（重要）

MAGAZINE で `copy-from` を使用する場合、以下の配列フィールドは**指定した場合に完全上書き**される（バニラの値とはマージされず、上書きした値だけが有効になる）。省略したフィールドは親の値が継承される。

| フィールド | 動作 | 注意点 |
|---|---|---|
| `flags` | 指定時は完全上書き | 親が `["MAG_COMPACT"]` でも、子で `["MAG_BULKY"]` を指定すれば上書きされる。省略すれば親の flags が継承される |
| `pocket_data` | 指定時は完全上書き | 親の `allowed_speedloaders` は引き継がれない。必要なら明示的に再定義する |
| `ammo_type` | 指定時は完全上書き | 親と同じ口径で良いなら `ammo_type` ごと省略する（継承される） |
| `material` | 指定時は完全上書き | 素材を追加する場合は親の素材も含めて全素材を列挙する。素材変更不要なら省略する |

**即席マガジンでは `allowed_speedloaders` を継承しないのが適切**（改造品でスピードローダー対応は想定しない）。バニラの `augmag_30rd`（stanag30 から copy-from）も `pocket_data` を上書きして `allowed_speedloaders` を継承していない。

## 主要フィールド

### name
- MAGAZINE は `{"str": "名称"}` 形式（`str_sp` ではない）
- バニラの全408マガジンが `str` 形式を使用。`str_sp` は0件

### ammo_type と ammo_restriction
- `ammo_type`: 使用可能な口径の配列。例: `["223", "300blk"]`
- `pocket_data[].ammo_restriction`: 口径ごとの装填数。**口径によって容量が異なる場合がある**

```json
// 同じマガジンでも口径により容量が変わる例
"ammo_type": [ "223", "300blk" ],
"pocket_data": [ {
  "pocket_type": "MAGAZINE",
  "rigid": true,
  "ammo_restriction": { "223": 45, "300blk": 30 }
} ]
```

口径により実口径が異なるため、物理的制約から容量差を設けるのが自然（例: 300blk は 223 より直径が大きく同じマガジン長では装填数が減る）。バニラでは全STANAGマガジンが 223/300blk 同一容量だが、即席マガジンでは口径差による制限を加える設計も有効。

### reload_time
- 整数値。装填にかかる時間の相対値
- 目安:
  - 標準マガジン: 100
  - 拡張マガジン: 130〜150
  - ドラムマガジン: 200

### mag_jam_mult
- マガジン由来のジャム確率倍率。整数値
- ドラムマガジンは `2`、標準マガジンは未設定（デフォルト 1）
- 即席マガジンには `2` を設定し信頼性低下を表現する

### flags
主なマガジンフラグ:

| フラグ | 意味 |
|---|---|
| `MAG_COMPACT` | コンパクト。ポーチ・ポケット収納可。標準マガジンに付与 |
| `MAG_BULKY` | かさばる。専用ポーチが必要。ドラムマガジン・拡張マガジンに付与 |
| `MAG_DESTROY` | 装填時にマガジン破壊（使い捨て） |

- `MAG_COMPACT` と `MAG_BULKY` は排他。どちらか一方のみ設定する
- `MAG_BULKY` は `flag_restriction` 互換性のため、対応するポーチ/チェストリグ側でも参照される

## バランス設計

### 新規マガジン追加前のギャップ分析

追加する口径・容量帯にギャップがあることを確認する：

1. 対象口径の全マガジンを `external/cdda/data/json/items/magazine/` から収集
2. 容量順にソートし、飛んでいる容量帯を特定
3. そのギャップを埋める価値があるか評価（既存マガジンとの差別化、製作可否）

### バランス比較表の作成

同口径の既存マガジンとの比較表を作り、トレードオフを明確にする：

| マガジン | 容量 | 重量 | 体積 | 装填時間 | 信頼性 | フラグ | 入手性 |
|---|---|---|---|---|---|---|---|
| (標準) | 30rd | 141g | 283ml | 100 | — | MAG_COMPACT | loot |
| **(新規)** | **45rd** | **330g** | **500ml** | **130** | **jam=2** | **MAG_BULKY** | **craft** |
| (ドラム) | 50rd | 725g | 663ml | 200 | jam=2 | MAG_BULKY | loot only |

### 設計指針
- **中間グレードを狙う**: 標準マガジンより大容量だが、ドラムマガジンより軽量・安価
- **トレードオフを明確に**: 容量増加の代償として重量・装填時間・信頼性のいずれかを悪化させる
- **レシピの有無で差別化**: ドラムマガジンが loot 専用なら、自作可能な中間グレードに価値がある
- **素材コストは製作難易度に見合うように**: 標準マガジン2本分 + 溶接消耗品など

## レシピ設計

### 基本パターン（改造レシピ）

既存マガジンを素材に新規マガジンを作るレシピ：

```json
[
  {
    "result": "mymod_stanag45",
    "type": "recipe",
    "activity_level": "MODERATE_EXERCISE",
    "category": "CC_WEAPON",
    "subcategory": "CSC_WEAPON_MAGAZINES",
    "skill_used": "fabrication",
    "difficulty": 3,
    "skills_required": [ "gun", 2 ],
    "time": "45 m",
    "autolearn": true,
    "using": [ [ "welding_standard", 5 ] ],
    "tools": [ [ [ "small_repairkit", 10 ], [ "large_repairkit", 5 ] ] ],
    "qualities": [
      { "id": "SAW_M", "level": 1 },
      { "id": "HAMMER", "level": 1 },
      { "id": "SCREW_FINE", "level": 1 }
    ],
    "components": [
      [ [ "stanag30", 2 ] ],
      [ [ "duct_tape", 40 ] ],
      [ [ "spring", 1 ] ]
    ]
  }
]
```

### 必須フィールド（0.I RC）
- `activity_level`: 必須。マガジン加工は `"MODERATE_EXERCISE"`
- `category`: `"CC_WEAPON"`
- `subcategory`: `"CSC_WEAPON_MAGAZINES"`

### skills_required の書式
- フラット配列 `["gun", 2]` を使用する
- ❌ 入れ子配列 `[["gun", 2]]` は誤り

### tools / qualities の選定
- マガジン改造に必要な工具を `external/cdda/data/json/recipes/weapon/magazines.json` の既存レシピから参照する
- 溶接を伴う場合は `"using": [["welding_standard", N]]` を使用
- `repairkit`（small/large）は銃器整備の標準ツール。マガジン加工でも使用

## 実装チェックリスト

- [ ] `name` が `{"str": "..."}` 形式か（`str_sp` ではない）
- [ ] `copy-from` 使用時、`type: "ITEM"` と `subtypes: ["MAGAZINE"]` を明示しているか
- [ ] flags 配列が意図通りに上書きされているか（MAG_COMPACT → MAG_BULKY など）
- [ ] `pocket_data` で口径別の `ammo_restriction` が適切か（口径により容量差がある場合）
- [ ] `reload_time` が既存マガジンのバランス範囲内か
- [ ] 即席マガジンには `mag_jam_mult: 2` を設定しているか
- [ ] `looks_like` に適切なバニラマガジンIDを指定しているか（タイルセットフォールバック用）
- [ ] レシピの `activity_level` が `"MODERATE_EXERCISE"` になっているか
- [ ] レシピの `skills_required` がフラット配列 `["gun", N]` 形式か
- [ ] レシピの tools/qualities/components が既存類似レシピと整合しているか
- [ ] 追加する口径・容量帯が既存マガジンと重複していないか
