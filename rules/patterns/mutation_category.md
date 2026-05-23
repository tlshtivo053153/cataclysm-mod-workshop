# 変異カテゴリ実装パターン

CDDAに新規の変異カテゴリ（プレイヤーが突然変異誘発剤で変異できる系統）を追加するための包括的なパターンファイル。

## 概要

変異カテゴリmodは以下の要素を組み合わせて一つの変異系統を定義する：
- **Vitamin**: 体内プライマー濃度を管理（変異のトリガー）
- **Mutation Category**: カテゴリ情報（名前、閾値変異ID、関連vitamin）
- **Mutagen Items**: プライマーを注入する変異誘発剤アイテム
- **Mutagen Effects**: 変異誘発中の身体的影響（空腹、痛み、ステータス変動）
- **Mutations**: 変異ツリー本体（ルート→中位→閾値後）
- **Extended Mutations**: 既存変異へのカテゴリ追加

## ファイル構成

変異カテゴリmodは以下の7ファイルで構成する：

| ファイル | type | 内容 |
|---|---|---|
| `modinfo.json` | `MOD_INFO` | mod登録情報。`category: "mutation"` 推奨 |
| `data/mutation_category.json` | `mutation_category` | カテゴリ定義（vitamin/threshold_mut連携） |
| `data/vitamin.json` | `vitamin` | counter型, disease_excessでmutagen_effect強度制御 |
| `data/mutagen_items.json` | `ITEM` (`copy-from: mutagen_flavor`) | 経口/注射用変異誘発剤 |
| `data/mutagen_effects.json` | `effect_type` | 変異誘発中の効果（max_intensity: 3） |
| `data/mutations.json` | `mutation` | 変異ツリー全定義 |
| `data/extended_mutations.json` | `mutation` (`copy-from` + `extend`) | 既存変異にカテゴリ追加 |

---

## 各ファイルの実装テンプレート

### 1. modinfo.json

```json
[
  {
    "type": "MOD_INFO",
    "id": "my_mutations",
    "name": "MY Mutations",
    "authors": [ "Your Name" ],
    "description": "Adds a MY mutation category with custom mutations.",
    "category": "mutation",
    "dependencies": [ "dda" ],
    "version": "1.0"
  }
]
```

### 2. mutation_category.json

```json
[
  {
    "type": "mutation_category",
    "id": "SUID",
    "name": "Suid",
    "threshold_mut": "THRESH_SUID",
    "mutagen_message": "You feel an overwhelming stubbornness and a desire to root through the earth.",
    "memorial_message": "Let the boar's will consume you.",
    "vitamin": "mutagen_suid",
    "base_removal_chance": 33,
    "base_removal_cost_mul": 2.5
  }
]
```

**フィールド解説:**

| フィールド | 必須 | 説明 |
|---|---|---|
| `id` | ○ | カテゴリID。変異の `category` フィールドと一致させる |
| `name` | ○ | 表示名（例: `"Suid"`, `"Turtle"`, `"Formicid"`） |
| `threshold_mut` | ○ | 閾値変異ID（`valid: false, purifiable: false, threshold: true`） |
| `mutagen_message` | △ | 変異誘発剤使用時のメッセージ |
| `memorial_message` | △ | 閾値越え時のメモリアルメッセージ |
| `vitamin` | ○ | 対応するvitamin ID |
| `base_removal_chance` | ○ | 変異除去（パリファイア）の基本成功率（%）。低いほど除去困難 |
| `base_removal_cost_mul` | ○ | 変異除去コスト倍率。バニラ基準は1.0 |

### 3. vitamin.json

```json
[
  {
    "id": "mutagen_suid",
    "type": "vitamin",
    "vit_type": "counter",
    "name": { "str": "Suid Primer" },
    "excess": "mutagen_suid",
    "min": 0,
    "max": 2500,
    "rate": "1 h",
    "disease_excess": [ [ 100, 500 ], [ 501, 2199 ], [ 2200, 2500 ] ]
  }
]
```

**フィールド解説:**

| フィールド | 説明 |
|---|---|
| `id` | 変異誘発剤の `use_action.vitamins`、`mutation_category.vitamin` と同一にする |
| `vit_type` | 常に `"counter"` |
| `name` | 内部診断用。`{ "str": "..." }` 形式が必須 |
| `excess` | idと同じ値を指定 |
| `max` | 最大プライマー量。通常 `2500` |
| `rate` | 減衰速度。通常 `"1 h"`（1時間あたり1減少） |
| `disease_excess` | 各蓄積量での強度 `[min, max]`。3段階で閾値2200以上がプライマーレベル |

**disease_excess の設計:**
- 第1段階 `[100, 500]`: 軽度変異
- 第2段階 `[501, 2199]`: 中度変異
- 第3段階 `[2200, 2500]`: プライマーレベル（閾値変異発現に十分な濃度）

### 4. mutagen_items.json

```json
[
  {
    "id": "mutagen_suid",
    "copy-from": "mutagen_flavor",
    "type": "ITEM",
    "subtypes": [ "COMESTIBLE" ],
    "name": { "str_sp": "suid mutagen" },
    "looks_like": "mutagen",
    "use_action": {
      "type": "consume_drug",
      "activation_message": "You drink the %s.",
      "vitamins": [ [ "mutagen_suid", 225 ], [ "mutagen", 125 ] ]
    }
  },
  {
    "id": "iv_mutagen_suid",
    "copy-from": "iv_mutagen_flavor",
    "type": "ITEM",
    "subtypes": [ "COMESTIBLE" ],
    "name": { "str_sp": "suid mutagenic primer" },
    "description": "A processed mutagenic primer the color of dried mud, with a faint animal musk.",
    "looks_like": "iv_mutagen",
    "color": "brown",
    "use_action": {
      "type": "consume_drug",
      "activation_message": "You inject the %s.",
      "tools_needed": { "syringe": -1 },
      "vitamins": [ [ "mutagen_suid", 450, 550 ] ]
    }
  }
]
```

**重要な注意点:**
- `copy-from: mutagen_flavor` / `iv_mutagen_flavor` は abstract アイテムのため、`type`/`subtypes` は継承されない。子定義で必ず `"type": "ITEM", "subtypes": ["COMESTIBLE"]` を明示すること。
- 経口変異誘発剤は `"vitamins": [ [ "mutagen_xxx", 225 ], [ "mutagen", 125 ] ]` で汎用 + 専用プライマーの両方を注入
- 注射用は `"vitamins": [ [ "mutagen_xxx", 450, 550 ] ]` で専用プライマーのみをランダム注入

### 5. mutagen_effects.json

```json
[
  {
    "type": "effect_type",
    "id": "mutagen_suid",
    "name": [ "Suid Mutation", "Suid Transformation", "Suid Metamorphosis" ],
    "desc": [
      "You consumed suid primer.",
      "The earth calls to you.  You feel an urge to root through every pile of dirt.",
      "Coarse bristles push through your skin, and your jaw aches as if your teeth are trying to escape."
    ],
    "max_intensity": 3,
    "resist_traits": [ "THRESH_SUID" ],
    "base_mods": {
      "hunger_min": [ 1 ],
      "hunger_max": [ 2 ],
      "hunger_tick": [ 500 ],
      "hurt_min": [ 1 ],
      "hurt_max": [ 2 ],
      "hurt_chance": [ -22 ],
      "hurt_tick": [ 150 ],
      "pain_min": [ 1 ],
      "pain_max": [ 2 ],
      "pain_chance": [ 100 ],
      "pain_tick": [ 75 ]
    },
    "scaling_mods": {
      "hunger_tick": [ -200 ],
      "str_mod": [ 1.5 ],
      "dex_mod": [ -1 ],
      "hurt_chance": [ 21, 0 ],
      "pain_chance": [ -30 ]
    },
    "rating": "bad",
    "blood_analysis_description": "Suid Primer Contamination"
  }
]
```

**フィールド解説:**

| フィールド | 説明 |
|---|---|
| `id` | 常に `"mutagen_xxx"`（vitamin.id と同一） |
| `name` | 3要素の配列（強度1, 2, 3に対応） |
| `desc` | 3要素の配列（強度1, 2, 3の説明文） |
| `max_intensity` | 常に `3` |
| `resist_traits` | `"THRESH_XXX"` を指定。閾値越え後に変異効果を無効化 |
| `base_mods` | 全強度共通の基本mod |
| `scaling_mods` | 強度が上がるごとに加算されるmod |
| `rating` | `"bad"`（副作用あり）、`"good"`、`"mixed"` のいずれか |

### 6. mutations.json

変異ツリーは以下の4階層で構成する：

1. **閾値ゲート** (`THRESH_XXX`) — `valid: false, purifiable: false, threshold: true`
2. **ルート変異**（起点） — `changes_to` で子変異を指定、`vitamin_cost` あり
3. **中位変異**（prereqs指定） — `prereqs` で親を指定、`changes_to` で子を指定
4. **閾値後変異** — `threshreq`, `purifiable: false` 必須

#### 閾値ゲート

```json
{
  "type": "mutation",
  "id": "THRESH_SUID",
  "name": { "str": "Swine" },
  "points": 1,
  "description": "You have crossed the threshold, embracing your inner boar.",
  "valid": false,
  "purifiable": false,
  "threshold": true,
  "threshold_substitutes": [ "THRESH_CHIMERA" ]
}
```

#### ルート変異（起点）

```json
{
  "type": "mutation",
  "id": "SUID_SNOUT",
  "name": { "str": "Snout" },
  "points": 0,
  "vitamin_cost": 160,
  "visibility": 9,
  "ugliness": 7,
  "mixed_effect": true,
  "description": "Your nose has flattened into a pig-like snout.",
  "types": [ "SCENT" ],
  "changes_to": [ "SUID_TUSKS", "SUID_HIDE" ],
  "category": [ "SUID" ],
  "social_modifiers": { "intimidate": -3 },
  "flags": [ "IMMUNE_SPOIL" ]
}
```

#### 中位変異（攻撃付き・防具制限ありの例）

```json
{
  "type": "mutation",
  "id": "SUID_TUSKS",
  "name": { "str": "Tusks" },
  "points": 2,
  "vitamin_cost": 200,
  "visibility": 8,
  "ugliness": 10,
  "description": "A pair of sharp tusks protrude from your lower jaw.",
  "prereqs": [ "SUID_SNOUT" ],
  "types": [ "TEETH" ],
  "changes_to": [ "SUID_GORE" ],
  "category": [ "SUID" ],
  "restricts_gear": [ "mouth" ],
  "destroys_gear": true,
  "attacks": {
    "attack_text_u": "You gore %s with your tusks!",
    "attack_text_npc": "%1$s gores %2$s with their tusks!",
    "body_part": "mouth",
    "blocker_mutations": [ "BEAK", "BEAK_HUM", "BEAK_PECK", "MUZZLE", "MUZZLE_LONG", "MUZZLE_RAT", "MUZZLE_BEAR", "SABER_TEETH" ],
    "chance": 20,
    "base_damage": { "damage_type": "stab", "amount": 22 }
  }
}
```

#### 中位変異（エンチャントのみの例）

```json
{
  "type": "mutation",
  "id": "FORM_ANTENNAE",
  "name": { "str": "Antennae" },
  "points": 1,
  "vitamin_cost": 160,
  "visibility": 6,
  "ugliness": 5,
  "description": "A pair of sensitive antennae sprout from your forehead.",
  "types": [ "EARS" ],
  "category": [ "FORMICID" ],
  "enchantments": [ { "condition": "ALWAYS", "values": [ { "value": "PERCEPTION", "add": 2 } ] } ]
}
```

#### 閾値後変異

```json
{
  "type": "mutation",
  "id": "SUID_GORE",
  "name": { "str": "Boar Charge" },
  "points": 4,
  "vitamin_cost": 300,
  "visibility": 10,
  "ugliness": 12,
  "description": "Your tusks have grown into lethal weapons.",
  "prereqs": [ "SUID_TUSKS" ],
  "types": [ "TEETH" ],
  "category": [ "SUID" ],
  "threshreq": [ "THRESH_SUID" ],
  "restricts_gear": [ "mouth" ],
  "destroys_gear": true,
  "attacks": {
    "attack_text_u": "You charge into %s with your tusks!",
    "attack_text_npc": "%1$s charges into %2$s with their tusks!",
    "body_part": "mouth",
    "blocker_mutations": [ "BEAK", "BEAK_HUM", "BEAK_PECK", "MUZZLE", "MUZZLE_LONG", "MUZZLE_RAT", "MUZZLE_BEAR", "SABER_TEETH" ],
    "chance": 25,
    "base_damage": { "damage_type": "stab", "amount": 35 }
  },
  "purifiable": false
}
```

### 7. extended_mutations.json

既存の変異に自カテゴリを追加することで、変異ツリーがカテゴリの選択肢として表示されるようになる。

```json
[
  {
    "type": "mutation",
    "id": "TOUGH",
    "copy-from": "TOUGH",
    "extend": { "category": [ "SUID" ] }
  },
  {
    "type": "mutation",
    "id": "STR_UP",
    "copy-from": "STR_UP",
    "extend": { "category": [ "SUID" ] }
  },
  {
    "type": "mutation",
    "id": "THICKSKIN",
    "copy-from": "THICKSKIN",
    "extend": { "category": [ "SUID" ] }
  }
]
```

**ポイント:**
- `id` は拡張先と同じIDを指定
- `copy-from` も同じIDを指定
- `extend` でカテゴリ配列を追加（既存カテゴリは保持される）
- `changes_to`/`cancels` で参照される変異にも必ずカテゴリ追加が必要

---

## 設計ルール

### 変異ツリー構造
- **閾値ゲート** (`THRESH_*`): `valid: false, purifiable: false, threshold: true`
- **閾値後変異**: `threshreq` と `purifiable: false` が必須
- **変異分岐**: `changes_to` で子変異を指定、`prereqs` で親変異を指定
- **ルート変異**: 少なくとも3個以上の閾値前変異が必要（1個ではプライマーが機能しない）

### 競合管理
- 攻撃変異には `blocker_mutations` を指定し、他カテゴリの同名部位変異と競合させる
- 装備制限には `restricts_gear` + `destroys_gear: true`

### エンチャント vs mutation modifiers
- ステータス修正には mutation modifiers より modern enchantment system を推奨
- `PAIN_RESIST` のような専用valueが存在しない場合は `PAIN` + `multiply: -0.25` で代用
- `ARMOR_BALLISTIC`, `ARMOR_ACID` 等の旧防具フラグは enchantment では使えない

### Vitaminシステムとの連携
- プライマー量2200以上で `disease_excess` 強度3に達し、閾値越えが可能になる
- 経口変異誘発剤1本で225注入 → 約10本でプライマーレベル到達
- 注射用プライマーは450〜550のランダム注入 → 約5本でプライマーレベル到達

---

## 注意点・よくあるミス

### `copy-from: mutagen_flavor` の継承漏れ
- `mutagen_flavor` / `iv_mutagen_flavor` は abstract アイテムのため、`type` と `subtypes` は継承されない
- 子定義で必ず `"type": "ITEM", "subtypes": ["COMESTIBLE"]` を明示する

### 閾値前変異が少なすぎる問題
- 閾値前変異が1個だと、`changes_to` の分岐先がなくプライマーが機能しない
- 最低3個の閾値前変異を用意し、`changes_to` で適切に分岐させる

### `changes_to`/`cancels` 参照変異のカテゴリ不足
- `changes_to` や `cancels` で参照される既存変異にも必ずカテゴリを追加する
- 忘れると、その変異がカテゴリ画面に表示されず、ツリーが途切れる

### `threshreq` の付け忘れ
- 閾値後変異に `threshreq` がないと、閾値を越えていなくても取得できてしまう
- 閾値前変異として使いたい場合は意図的に `threshreq` を外す

### `EATPOISON` 依存連鎖
- `WEAKSTOMACH` → `EATPOISON`, `VOMITOUS` → `EATPOISON`, `NAUSEA` → `VOMITOUS` のような連鎖がある
- `extend` でカテゴリ追加する際は、依存先まで連鎖的にカテゴリ追加が必要

### `name` フィールド形式
- mutation の `name` は `{ "str": "変異名" }` 形式（`str_sp` ではない）
- `ITEM` 型の変異誘発剤は `{ "str_sp": "アイテム名" }` 形式

### mutation_type の有効値
- `types` に指定できる値は `external/cdda/data/json/mutations/mutation_type.json` に定義されたもののみ
- よくある間違い: `SMELL` → `SCENT`, `ATTACK` → `SECRETION`

### Vitamin disease_excess の閾値
- `[2200, 2500]` が強度3（プライマーレベル）。この範囲に達していないと閾値変異が発現しない
- `max: 2500` を超えるプライマーは無駄になるため、注入量の合計が2500に近づくよう設計する
