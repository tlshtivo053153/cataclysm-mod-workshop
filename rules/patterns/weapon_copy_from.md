# 武器 copy-from 設計パターン

CDDA 0.I で武器アイテムを追加する際の推奨パターン。

## 基本パターン: 既存武器をベースに派生

```json
[
  {
    "id": "base_custom_weapon",
    "type": "ITEM",
    "subtypes": ["GUN", "TOOL"],
    "name": { "str_sp": "カスタム兵器" },
    "description": "これは基底定義。copy-from で継承しないで直接使わないこと。",
    "weight": "2500 g",
    "volume": "1500 ml",
    "price": "500 USD",
    "price_postapoc": "50 USD",
    "material": ["steel", "plastic"],
    "symbol": "(",
    "color": "light_gray",
    "to_hit": -1,
    "flags": ["STAB", "DURABLE_MELEE"]
  },
  {
    "id": "custom_weapon_v2",
    "type": "ITEM",
    "subtypes": ["GUN", "TOOL"],
    "copy-from": "base_custom_weapon",
    "name": { "str_sp": "カスタム兵器改" },
    "description": "改良版。差分のみ記述する。",
    "relative": {
      "weight": "200 g"
    },
    "proportional": {
      "price": 1.2
    }
  }
]
```

## 設計指針

1. **基底IDは直接出現させない**
   - `base_` プレフィックスを付け、ゲーム内では出現させない
   - または `abstract` 型として定義する（0.I 対応）

2. **差分のみ記述する**
   - `copy-from` を使う際は変更点だけを書く
   - `relative` / `proportional` を活用して数値調整

3. **必須フィールドは上書き可能にしておく**
   - `name`, `description` は必ず定義（copy-from 継承時も明示推奨）
   - `weight`, `volume` は文字列形式（0.I 必須）

4. **ITEM 型統合に対応**
   - 0.I では `type: "GUN"` ではなく `type: "ITEM"` + `subtypes: ["GUN"]`
   - 複数 subtypes を持つ場合は `subtypes: ["GUN", "TOOL"]`
