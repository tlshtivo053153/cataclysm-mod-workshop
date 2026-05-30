# GUN 実装パターン

CDDAに新規銃器（GUN）を追加するためのパターンファイル。

## 概要

GUN は `"type": "ITEM"` + `"subtypes": ["GUN"]` で定義する。新規銃器は既存のベースクラスから `copy-from` で派生させるのが標準パターン。

## ファイル構成

| ファイル | type | 内容 |
|---|---|---|
| `modinfo.json` | `MOD_INFO` | mod登録情報 |
| `data/items.json` | `ITEM` (GUN) | 銃器アイテム定義 |
| `data/recipes.json` | `recipe` | クラフトレシピ（オプション） |

## 参照ファイル（external/cdda/）

| ファイル | 目的 |
|---|---|
| `data/json/items/classes/gun.json` | ベースクラス定義。copy-from先の継承フィールド確認 |
| `data/json/items/gun/` | 同口径の既存銃バランス比較・copy-from先の実装パターン参照 |
| `data/json/items/ammo/` | 使用する弾薬IDの存在確認 |
| `data/json/recipes/weapon/ranged.json` | 既存銃器レシピ。tools/qualities/componentsの参照 |

## ベースクラス（重要）

CDDA 0.I のベースガンクラスには以下の種類がある:

| クラスID | skill | 動作方式 | 利用例 |
|---|---|---|---|
| `gun_base_handgun_manual` | pistol | 手動式拳銃 | pipe pistol, cap & ball revolver |
| `gun_base_handgun_semi` | pistol | 半自動拳銃 | Glock, M1911 |
| `gun_base_rifle_manual` | rifle | 手動式ライフル | pipe rifle, bolt-action |
| `gun_base_22_semi_rifle` | rifle | 半自動ライフル | Ruger 10/22 |
| `smg_base` | smg | 短機関銃 | UZI, MP5 |

### ベースクラスの継承モデル（最重要）

**`gun_base_handgun_manual` は独立定義であり、`pistol_base` や `gun_base` を継承していない。**

```json
// gun.json:310-328 — gun_base_handgun_manual の完全定義
{
  "abstract": "gun_base_handgun_manual",
  "type": "ITEM",
  "subtypes": [ "GUN" ],
  "color": "light_gray",
  "symbol": "⨽",
  "weapon_category": [ "AUTOMATIC_PISTOLS" ],
  "melee_damage": { "bash": 7 },
  "to_hit": { "grip": "solid", "length": "hand", "surface": "line", "balance": "neutral" },
  "flags": [ "ALLOWS_BODY_BLOCK", "RELOAD_ONE", "NO_TURRET", "EASY_CLEAN", "RELOAD_EJECT" ],
  "blackpowder_tolerance": 56,
  "name": { "str": "base gun", "//~": "NO_I18N" },
  "skill": "pistol",
  "sight_dispersion": 60,
  "durability": 8,
  "handling": 10,
  "reload": 200,
  "reload_noise_volume": 10,
  "faults": [ { "fault": "fault_gun_blackpowder" }, { "fault": "fault_gun_dirt" } ]
}
```

### 継承されるフィールド vs 明示が必要なフィールド

`gun_base_handgun_manual` は完全な銃器定義ではなく、最小限の基本設定のみを含む。以下のフィールドは**ベースクラスに存在しないため、必ず明示設定が必要**:

| フィールド | 設定要否 | 説明 |
|---|---|---|
| `ammo` | **必須（明示）** | 使用弾薬の配列。ベースクラスに未定義 |
| `pocket_data` | **必須（明示）** | マガジンポケット定義。ベースクラスに未定義 |
| `ranged_damage` | **必須（明示）** | 弾丸ダメージ。ベースクラスに未定義 |
| `loudness` | **必須（明示）** | 発射音量。ベースクラスに未定義 |
| `clip_size` | **必須（明示）** | 装填数。ベースクラスに未定義 |
| `valid_mod_locations` | **必須（明示）** | アタッチメントスロット。ベースクラスに未定義 |
| `barrel_volume` | **推奨（明示）** | 銃身内容積（blackpowder用）。ベースクラスに未定義 |

以下はベースクラスから継承されるため、**通常は明示不要**:

| フィールド | 継承値（`gun_base_handgun_manual`） |
|---|---|
| `skill` | `"pistol"` |
| `sight_dispersion` | `60` |
| `handling` | `10` |
| `reload` | `200`（pipe 武器ではベースクラスの値にかかわらず `200` に統一する場合が多い） |
| `reload_noise_volume` | `10` |
| `weapon_category` | `["AUTOMATIC_PISTOLS"]` |
| `melee_damage` | `{"bash": 7}` |
| `to_hit` | `{"grip": "solid", "length": "hand", "surface": "line", "balance": "neutral"}` |
| `faults` | `[ { "fault": "fault_gun_blackpowder" }, { "fault": "fault_gun_dirt" } ]`（オブジェクト配列形式） |
| `color` | `"light_gray"` |
| `symbol` | `"⨽"` |
| `durability` | `8` |
| `blackpowder_tolerance` | `56` |
| `flags` | `ALLOWS_BODY_BLOCK`, `RELOAD_ONE`, `NO_TURRET`, `EASY_CLEAN`, `RELOAD_EJECT` |

> **注意**: 手動式ベースクラス（`gun_base_handgun_manual`, `gun_base_rifle_manual`）の faults は `fault_gun_blackpowder` + `fault_gun_dirt` のみ。半自動系の faults（`fault_gun_chamber_spent`, `fault_stovepipe` 等）は含まれない。

## 基本パターン: 即席単発火器

pipe rifle (`rifle_22`) を雛形とする、手動式ベースクラスからの派生パターン:

```json
[
  {
    "id": "mymod_pipe_pistol",
    "copy-from": "gun_base_handgun_manual",
    "type": "ITEM",
    "subtypes": [ "GUN" ],
    "name": { "str": "pipe pistol" },
    "description": "A home-made pistol.  It is a pipe with a crude grip and hammer mechanism, designed to strike the single round it holds.",
    "looks_like": "glock_19",
    "ascii_picture": "sm_pipe_gun",
    "weight": "1200 g",
    "volume": "900 ml",
    "longest_side": "35 cm",
    "barrel_length": "203 mm",
    "price": "75 USD",
    "price_postapoc": "5 USD",
    "material": [ "steel", "wood" ],

    "ammo": [ "9mm" ],
    "ranged_damage": { "damage_type": "bullet", "amount": -1 },
    "dispersion": 650,
    "durability": 6,
    "blackpowder_tolerance": 60,
    "loudness": 35,
    "clip_size": 1,
    "reload": 200,
    "barrel_volume": "120 ml",
    "valid_mod_locations": [ [ "sights mount", 1 ] ],
    "flags": [ "RELOAD_EJECT", "EASY_CLEAN" ],
    "pocket_data": [
      {
        "pocket_type": "MAGAZINE",
        "rigid": true,
        "ammo_restriction": { "9mm": 1 }
      }
    ]
  }
]
```

## flags の再宣言パターン

pipe 武器では、継承元のフラグの一部のみを明示的に再宣言する:

```json
// ベースクラスは ALLOWS_BODY_BLOCK, RELOAD_ONE, NO_TURRET, EASY_CLEAN, RELOAD_EJECT を持つ
// 下位定義では RELOAD_EJECT と EASY_CLEAN のみを再宣言
"flags": [ "RELOAD_EJECT", "EASY_CLEAN" ]
```

CDDAの `copy-from` では、配列フィールド（`flags` 含む）は**指定時に完全上書き**される。ただし `clip_size: 1` の単発式銃はゲーム側で `RELOAD_ONE` を自動推論するため、pipe 武器は `RELOAD_EJECT` + `EASY_CLEAN` の2フラグのみの再宣言で十分（バニラ `rifle_22` の実績あり）。他のフラグを維持したい場合は、必要なフラグをすべて明示的に列挙すること。

## 主要フィールド

### name
- GUN は `{"str": "名称"}` 形式（`str_sp` ではない）
- バニラ全GUNが `str` 形式を使用

### type / subtypes
- 0.I では `copy-from` 使用時も `"type": "ITEM"` + `"subtypes": ["GUN"]` を**必ず明示する**
- 省略すると CDDA 起動時エラーになる

### ammo と pocket_data
- ベースクラスを `copy-from` する場合、両方とも必須（ベースクラスに未定義のため）
- 単発式の場合は `clip_size: 1` と `pocket_data` 内の `ammo_restriction` を一致させる

### dispersion
- 命中精度の悪さ（高いほど悪い）
- 目安（バニラ実値に基づく）:
  - 競技用/精密ライフル: 30〜100
  - 軍用ライフル: 100〜300
  - 即席ライフル: 550（`rifle_22` pipe rifle の実値）
  - 即席拳銃: 650〜900（`ashot` 900、pipe pistol 650）
- 同口径のバニラ銃を参照して設定する

### durability
- pipe 武器共通で `6`（バニラ pipe rifle, pipe SMG と一致）
- 市販銃は `7`〜`9`

### blackpowder_tolerance
- 黒色火薬許容量。pipe 武器は `60`（バニラ pipe rifle と一致）
- ベースクラスの値（`56`）から上書きするのが pipe 武器のパターン

### loudness
- 発射音量。同口径のバニラ銃を参照
- pipe rifle (22): 25 → pipe pistol (9mm): 35（口径差を反映）

### barrel_volume
- 銃身内容積。`barrel_length` に比例して計算
- 計算式: `barrel_volume = barrel_length × (360 / 610)`
- 例: pipe rifle (610mm → 360ml) を基準に pipe pistol (203mm → 203 × 360/610 ≈ 120ml)

## レシピ設計

### 即席火器レシピのパターン

pipe 武器のレシピは以下を雛形とする:

```json
[
  {
    "type": "recipe",
    "result": "mymod_pipe_pistol",
    "activity_level": "MODERATE_EXERCISE",
    "category": "CC_WEAPON",
    "subcategory": "CSC_WEAPON_RANGED",
    "skill_used": "fabrication",
    "skills_required": [ "gun", 1 ],
    "difficulty": 2,
    "time": "30 m",
    "reversible": true,
    "autolearn": true,
    "proficiencies": [
      { "proficiency": "prof_gunsmithing_basic" },
      { "proficiency": "prof_gunsmithing_improv" }
    ],
    "qualities": [
      { "id": "SAW_M_FINE", "level": 1 },
      { "id": "SCREW_FINE", "level": 1 }
    ],
    "components": [
      [ [ "pipe", 1 ] ],
      [ [ "2x4", 1 ] ],
      [ [ "scrap", 1 ] ]
    ]
  }
]
```

### レシピ設計指針

| 要素 | 指針 | 根拠 |
|---|---|---|
| `category` / `subcategory` | flat category を使用（`CC_WEAPON` / `CSC_WEAPON_RANGED`） | pipe 拳銃を nested pipe rifles グループに入れるのは不自然なため |
| `skill_used` | `"fabrication"` | pipe rifle レシピ準拠 |
| `skills_required` | `["gun", 1]`（フラット配列） | 単一スキルの場合はフラット配列 |
| `difficulty` | pipe pistol は `2`（pipe rifle は `3`） | ストックなし・構造簡易のため一段階低く設定 |
| `time` | `"30 m"` | pipe rifle と同一 |
| `proficiencies` | `prof_gunsmithing_basic` + `prof_gunsmithing_improv` | pipe rifle レシピ準拠 |
| `qualities` | `SAW_M_FINE: 1` + `SCREW_FINE: 1` | pipe rifle レシピ準拠 |
| `components` | pipe×1, 2x4×1, scrap×1 | pipe rifle からストック分（2x4, scrap）を削減 |

### skills_required の書式

CDDA 0.I では単一スキルと複数スキルで書式が異なる:

```json
// 単一スキル → フラット配列
"skills_required": [ "gun", 2 ]

// 複数スキル → 入れ子配列
"skills_required": [ [ "traps", 1 ], [ "gun", 1 ] ]
```

> 両方の書式がバニラで混在しており、いずれも有効。単一スキルか複数スキルかで使い分ける。

### proficiencies の書式

`proficiencies` は**必ずオブジェクト配列形式**で記述する（文字列配列ではない）:

```json
// ✅ 正しい
"proficiencies": [
  { "proficiency": "prof_gunsmithing_basic" },
  { "proficiency": "prof_gunsmithing_improv" }
]

// ❌ 誤り（CDDA 読み込みエラー）
"proficiencies": [ "prof_gunsmithing_basic", "prof_gunsmithing_improv" ]
```

## 実装チェックリスト

- [ ] 同口径のバニラ銃で `ranged_damage` のベースラインを確認したか
- [ ] `copy-from` 使用時も `type: "ITEM"` + `subtypes: ["GUN"]` を明示しているか
- [ ] `ammo` と `pocket_data` の両方を設定しているか（ベースクラスはどちらも持たない）
- [ ] `clip_size` と `pocket_data.ammo_restriction` の値が一致しているか
- [ ] `barrel_length` から `barrel_volume` を比例計算しているか
- [ ] `blackpowder_tolerance` を pipe 武器共通値 `60` に上書きしているか
- [ ] `durability` を pipe 武器共通値 `6` に設定しているか
- [ ] `flags` が意図通りか（配列フィールドは指定時に完全上書きされる）
- [ ] `name` が `{"str": "..."}` 形式か（`str_sp` ではない）
- [ ] description の英文がテキストスタイルチェッカーに準拠しているか（文区切りにダブルスペース）
- [ ] `looks_like` に実在するバニラ銃IDを指定しているか
- [ ] レシピの `category` / `subcategory` が flat（`CC_WEAPON` / `CSC_WEAPON_RANGED`）か nested（`CC_*` / `CSC_*_NESTED`）か、適切に選択しているか
- [ ] レシピの `proficiencies` がオブジェクト配列形式か（文字列配列ではない）
- [ ] レシピの `components` で使用する全アイテムIDがバニラに存在するか
- [ ] レシピの `activity_level` が設定されているか（0.I RC 必須）
