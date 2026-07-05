# enchantment / effect_type 実装パターン

CDDA 0.I RC で enchantment と effect_type を定義する際のパターンと値セマンティクス。

## effect_type の基本構成

```json
{
  "type": "effect_type",
  "id": "mymod_tier_1",
  "name": [ "Effect Display Name" ],
  "desc": [ "Description shown in character sheet." ],
  "rating": "good",
  "max_intensity": 1,
  "enchantments": [
    {
      "condition": "ALWAYS",
      "values": [
        { "value": "MELEE_DAMAGE", "add": 2 },
        { "value": "MELEE_TO_HIT", "add": 2 }
      ]
    }
  ]
}
```

### 必須フィールド
- `type`: 常に `"effect_type"`
- `id`: 一意の識別子
- `name`: 表示名（文字列の配列）
- `enchantments`: 効果の配列

### 任意フィールド
- `desc`: 説明文（文字列オブジェクトの配列）
- `rating`: `"good"` / `"bad"` / `"neutral"` / `"mixed"`
- `max_intensity`: 最大強度（デフォルト 1）
- `max_duration`: 最大持続時間
- `show_in_info`: `true` でキャラクターシートに表示

## math式による動的enchantment値

`add` / `multiply` の値に静的数値ではなく `{ "math": [...] }` で数式を指定することで、
単一の `effect_type` で可変効果を実現できる。

```json
{
  "type": "effect_type",
  "id": "mymod_buff",
  "name": [ "Dynamic Buff" ],
  "enchantments": [{
    "condition": "ALWAYS",
    "values": [
      { "value": "MELEE_DAMAGE", "add": { "math": [ "u_melee_damage" ] } },
      { "value": "ATTACK_SPEED", "add": { "math": [ "u_attack_speed * -10" ] } },
      { "value": "WEAPON_DISPERSION", "multiply": { "math": [ "u_dispersion * -0.05" ] } }
    ]
  }]
}
```

### 設計上の利点

- **Tier 集約**: 従来 Tier ごとに別々の `effect_type` が必要だったが、変数で動的に値を変更できるため 1 つに集約可能（24→3 の削減実績あり）
- **EOC 側で変数を設定** → enchantment 側で math 式が評価時に変数を読み取り → 動的効果発動
- 変数が未定義または `0` の場合、効果もゼロになる（安全）

### 制約

- math 式の評価はキャラクターコンテキスト（`u_`）で行われる。**アイテム変数（`n_`）は enchantment の math 式から直接アクセス不可。** → 後述の「変数スコープの制約」参照
- math 式内の変数は enchantment 評価時に遅延評価される。EOC で変数を設定したフレームと実際の反映タイミングにズレがある可能性があるため、RECURRING EOC による定期的な再評価を併用すること

## enchantment value のセマンティクス早見表

### 攻撃系

| value 名 | `add` | `multiply` | 備考 |
|----------|-------|-----------|------|
| `MELEE_DAMAGE` | ダメージ加算 | 倍率（0.15 = +15%） | 近接ダメージ |
| `MELEE_TO_HIT` | 命中加算 | 倍率 | 近接命中 |
| `RANGED_DAMAGE` | ダメージ加算 | 倍率 | 遠隔ダメージ |

### 射撃系

| value 名 | `add` | `multiply` | 備考 |
|----------|-------|-----------|------|
| `WEAPON_DISPERSION` | **実例なし** | 倍率（負値で精度向上） | `-0.25` = 拡散 25% 減 |
| `RANGE` | 射程加算 | 倍率 | |

### 速度系

| value 名 | `add` | `multiply` | 備考 |
|----------|-------|-----------|------|
| `ATTACK_SPEED` | move cost 加減算 | 倍率 | **負値で攻撃高速化** |
| `SPEED` | 移動速度加算 | 倍率 | |
| `MOVE_COST` | move cost 加減算 | 倍率 | **負値で移動高速化** |

### その他

| value 名 | `add` | `multiply` | 備考 |
|----------|-------|-----------|------|
| `STRENGTH` | 能力値加算 | 倍率 | |
| `DEXTERITY` | 能力値加算 | 倍率 | |
| `PERCEPTION` | 能力値加算 | 倍率 | |
| `CARRY_WEIGHT` | 重量加算 | 倍率 | |
| `LUMINATION` | 光度加算 | 倍率 | |
| `HEARING_MULT` | — | 倍率 | `-0.75` = 聴覚 75% 減 |
| `THIRST` | — | 倍率 | 喉の渇き量 |
| `PAIN` | — | 倍率 | `-0.99` = 痛み 99% 減 |

## 重要なセマンティクス

### `ATTACK_SPEED` は move cost（注意）
- **負値で攻撃が速くなる**（move cost を減らすため）
- `"add": -10` = 攻撃の move cost を 10 減らす（約 10% 高速化）
- `"multiply": -0.1` = 攻撃の move cost を 10% 減らす
- `"multiply": 1.5` = 攻撃が 50% 遅くなる

### `WEAPON_DISPERSION` は `multiply` のみ
- CDDA 0.I RC の実例では `multiply` のみ使用されている（`add` の使用例は未確認）
- `"multiply": -0.05` = 拡散 5% 減（tier ごとに累積）
- `"multiply": -1` = 拡散 100% 減（完全な精度）
- `add` を使う場合は実機で動作確認すること

## enchantment の condition（条件付き発動）

```json
"enchantments": [
  {
    "condition": "ALWAYS",
    "values": [ ... ]
  },
  {
    "condition": { "u_has_wielded_with_skill": "pistol" },
    "values": [ ... ]
  },
  {
    "condition": { "u_has_effect": "cig" },
    "values": [ ... ]
  }
]
```

- `"ALWAYS"` — 常時発動
- 条件オブジェクト — 条件を満たすときのみ発動（EOC condition と同じ構文）

## effect_type + EOC の組み合わせパターン

```
character_kills_monster → u_run_inv_eocs → XP加算
                                          ↓
                          u_add_effect("mymod_tier_N") → effect_type → enchantments → ステータス反映
```

1. `effect_type` で enchantment を定義（静的な効果）
2. EOC で `u_add_effect` / `u_lose_effect` を使って動的に effect を付与・解除
3. RECURRING EOC で定期的に effect を再評価・更新

### 更新パターン
```json
// 1. 全 tier effect を除去
{ "u_lose_effect": [ "mymod_tier_1", "mymod_tier_2", "mymod_tier_3", "mymod_tier_4" ] },
// 2. 現在の状態に応じて該当 tier を付与
{ "u_add_effect": "mymod_tier_2", "duration": "1 hour" }
```

- `duration` は次の recheck より長く設定する（recheck 間隔が 30 秒なら 1 時間で十分）
- effect を付け替えるときは、まず古い effect を `u_lose_effect` で全て除去してから新しい effect を付与する

## 変数スコープの制約: n_ → u_ ブリッジパターン

### 問題

enchantment の math 式はキャラクターコンテキスト（`u_`）で評価される。
アイテムに保存された変数（`n_`）は enchantment から**直接アクセスできない**。

```
EOC (wm_enhance_*_nested) → n_wm_buff_* を更新（アイテム変数）
                                     ↓
                               enchantment の math 式からは n_ にアクセス不可
```

### 解決策: EOC で n_ → u_ ブリッジ

`u_run_inv_eocs` の per-item コンテキスト内で、アイテム変数 `n_` をキャラクター変数 `u_` にコピーしてから effect を付与する。

```
per-item EOC → n_wm_buff_* を読み取り → math: u_wm_* = n_wm_buff_* → u_add_effect
                                                    ↓
                                    effect_type の enchantment math が u_wm_* を参照
```

### 実装例

`wm_apply_buffs`（`u_run_inv_eocs` の per-item EOC）:

```json
{
  "type": "effect_on_condition",
  "id": "wm_apply_buffs",
  "effect": [{
    "if": { "npc_has_flag": "WM_SUPPORTED" },
    "then": [
      { "math": [ "u_wm_melee_damage = n_wm_buff_melee_damage" ] },
      { "math": [ "u_wm_melee_tohit = n_wm_buff_melee_tohit" ] },
      { "math": [ "u_wm_attack_speed = n_wm_buff_attack_speed" ] },
      { "u_add_effect": "wm_buff_supported", "duration": "1 hour" }
    ]
  }]
}
```

## 変数残留防止のゼロクリアパターン

### 問題

武器種別ごとに異なる effect を付与する場合、持ち替え時に前の武器種別の `u_` 変数が残留する。
例えば近接武器 → 遠隔武器に持ち替えたとき、`u_wm_melee_damage` が残ったままだと
遠隔武器使用時にも近接ダメージボーナスが適用されてしまう。

### 解決策: 各分岐で未使用変数を明示的に 0 クリア

```json
// 近接武器ブロック
"then": [
  { "math": [ "u_wm_melee_damage = n_wm_buff_melee_damage" ] },
  { "math": [ "u_wm_melee_tohit = n_wm_buff_melee_tohit" ] },
  { "math": [ "u_wm_attack_speed = n_wm_buff_attack_speed" ] },
  { "math": [ "u_wm_ranged_damage = 0" ] },
  { "math": [ "u_wm_dispersion = 0" ] },
  { "u_add_effect": "wm_buff_melee", "duration": "1 hour" }
]

// 遠隔武器ブロック
"then": [
  { "math": [ "u_wm_melee_damage = 0" ] },
  { "math": [ "u_wm_melee_tohit = 0" ] },
  { "math": [ "u_wm_attack_speed = 0" ] },
  { "math": [ "u_wm_ranged_damage = n_wm_buff_ranged_damage" ] },
  { "math": [ "u_wm_dispersion = n_wm_buff_dispersion" ] },
  { "u_add_effect": "wm_buff_ranged", "duration": "1 hour" }
]
```

### 原則

- **全ブロックが全 u_ 変数を網羅する** — 各 if/then ブロック内で、その武器種別に関係ない変数も明示的に 0 を代入
- **抜けがあると残留バグの原因**になる（発見が難しく、プレイヤーには不可解な挙動に見える）

## 使用できない旧 enchantment value

0.I で削除された値（`common_errors.md` も参照）:
- `ARMOR_BALLISTIC`, `ARMOR_ACID`, `ARMOR_BASH`, `ARMOR_BIO`, `ARMOR_STAB`, `ARMOR_HEAT`, `ARMOR_ELEC`, `ARMOR_CUT`, `ARMOR_COLD`

## 参照先

- バニラ effect 定義: `external/cdda/data/json/effects.json`
- バニラ enchantment: `external/cdda/data/json/enchantments.json`
- 実装例:
  - `external/cdda/data/mods/BombasticPerks/perkdata/empath.json` — effect_type + enchantments
  - `external/cdda/data/mods/MindOverMatter/effects/effects_psionic.json` — 複雑な条件付き enchantment
  - `external/cdda/data/mods/Aftershock/items/item_enchants.json` — スタンドアロン enchantment 定義
