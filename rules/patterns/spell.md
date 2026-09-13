# 魔法（magic_type / SPELL）実装パターン

CDDA 0.I RC で呪文を追加する際のパターン。マナ基盤なしで自己完結させる場合は
`energy_source: "STAMINA"` の `magic_type` を使う。
実装例: `mods/small/hedge_magic/`

## 概要

呪文追加は以下の要素で構成する：

- **magic_type 定義** (`"type": "magic_type"`): エネルギー源・詠唱不能条件を定義
- **SPELL 定義** (`"type": "SPELL"`): 呪文本体（効果・威力・射程・コスト）
- **学習手段**: 呪文書アイテム（`BOOK` + `use_action: learn_spell`）、職業の `spells`、変異の `spells` など

> `magic_type` は mod 専用の型。base には定義がなく、Magiclysm / MindOverMatter / Xedra_Evolved 等の
> mod がそれぞれ独自の magic_type を定義している。自作modでも同様に自前で定義すれば mod 依存なしで動作する。

## ファイル構成

| ファイル | type | 内容 |
|---|---|---|
| `modinfo.json` | `MOD_INFO` | `category: "magical"` |
| `data/magic_type.json` | `magic_type` | 魔法体系（エネルギー源） |
| `data/spells.json` | `SPELL` | 呪文定義 ×N |
| `data/items.json` | `ITEM` (BOOK) | 呪文書（任意） |
| `data/recipes.json` | `recipe` | 呪文書のレシピ（任意） |

## 参照ファイル（external/cdda/）

| ファイル | 目的 |
|---|---|
| `data/mods/MindOverMatter/powers/classless.json` | STAMINA magic_type（`mom_psionics`）の最小例 |
| `data/mods/Magiclysm/Spells/classless.json` | magic_type + SPELL の基本構成 |
| `data/mods/Magiclysm/Spells/magus.json` | 最小攻撃呪文（`magic_missile`） |
| `data/mods/Magiclysm/items/spell_scrolls.json` | `learn_spell` 呪文書の書式 |
| `data/json/artifact/legacy_artifact_active.json` | `effect_str` で既存 effect を付与する例（`AEA_ADRENALINE`） |
| `data/json/bionic_spells.json` | magic_type なしで動く呪文の例 |
| `data/json/flags.json` | 呪文フラグ（`VERBAL`, `SOMATIC`, `NO_LEGS`, `NO_HANDS`, `NO_PROJECTILE` 等） |
| `data/json/damage_types.json` | ダメージタイプID（`bash`/`cut`/`stab`/`electric` 等） |

## magic_type の基本構造

```json
{
  "id": "hmg_hedge_magic",
  "type": "magic_type",
  "energy_source": "STAMINA",
  "cannot_cast_flags": "NO_SPELLCASTING",
  "cannot_cast_message": "You can't focus enough to work your charm!"
}
```

| フィールド | 説明 |
|---|---|
| `energy_source` | `"MANA"` / `"STAMINA"` / `"HP"` / `"BIONIC"` / `"NONE"` |
| `cannot_cast_flags` | 詠唱を禁止するフラグ（`NO_SPELLCASTING` 等） |
| `cannot_cast_message` | 詠唱不能時のメッセージ |
| `max_book_level` | `0` で書物学習を禁止（MindOverMatter は 0、Magiclysm は未設定）。**呪文書で習得させる場合は設定しない** |

### エネルギー源の選び方

- **MANA**: Magiclysm 系。マナ残量・回復の仕組み（変異・装備等）を別途用意する必要がある
- **STAMINA**: マナ基盤不要で自己完結。MindOverMatter / aftershock psionics で実績あり。小規模modに推奨
- MAGIC.md は `doc/` に存在しない（0.I 時点）。フィールドは mod の実例を参照する

## SPELL の基本構造

```json
{
  "id": "hmg_thorn_dart",
  "type": "SPELL",
  "name": { "str": "Thorn Dart" },
  "description": "Hurls a conjured thorn at a nearby enemy.",
  "valid_targets": [ "hostile" ],
  "flags": [ "VERBAL", "SOMATIC", "NO_LEGS" ],
  "effect": "attack",
  "shape": "blast",
  "damage_type": "stab",
  "min_damage": { "math": [ "(u_spell_level('hmg_thorn_dart') * 1.5) + 4" ] },
  "max_damage": { "math": [ "(u_spell_level('hmg_thorn_dart') * 2.5) + 8" ] },
  "min_range": 3,
  "max_range": 12,
  "range_increment": 0.5,
  "base_energy_cost": 1250,
  "final_energy_cost": 750,
  "difficulty": 1,
  "max_level": 10,
  "base_casting_time": 100,
  "spell_class": "NONE",
  "magic_type": "hmg_hedge_magic",
  "energy_source": "STAMINA"
}
```

### 主要フィールド

| フィールド | 必須 | 説明 |
|---|---|---|
| `effect` | 必須 | `"attack"` / `"spawn_item"` / `"summon"` / `"effect_on_condition"` / `"short_range_teleport"` / `"recover_energy"` 等 |
| `shape` | 必須 | `"blast"`（単体/範囲） / `"line"` / `"cone"` |
| `valid_targets` | 必須 | `"hostile"` / `"ally"` / `"self"` / `"ground"` / `"none"` |
| `damage_type` | 攻撃時 | `data/json/damage_types.json` のID（`bash`/`cut`/`stab`/`electric`/`heat`/`cold`/`acid` 等） |
| `min_damage` / `max_damage` / `damage_increment` | 威力 | `{ "math": [ "u_spell_level('spell_id') * N + M" ] }` でレベルスケール |
| `min_range` / `max_range` / `range_increment` | 射程 | タイル数 |
| `min_duration` / `max_duration` / `duration_increment` | 効果時間 | ターン数（100 = 1秒） |
| `base_energy_cost` / `final_energy_cost` | コスト | STAMINA の場合 1000 前後が目安（MindOverMatter 難易度1 ≒ 1250） |
| `base_casting_time` | 詠唱時間 | move cost（100 = 1秒） |
| `difficulty` / `max_level` | 成長 | 習得難易度と最大レベル |
| `spell_class` | 推奨 | クラスレスは `"NONE"` |
| `magic_type` | 任意 | 魔法体系。省略可（bionic_spells は省略） |
| `energy_source` | 任意 | magic_type と異なるエネルギー源を使う場合に上書き |
| `effect_str` | 効果次第 | `effect: "attack"` で既存 effect ID を付与する場合に指定（例: `"adrenaline"`） |

### 効果の実装パターン

1. **直接攻撃**: `effect: "attack"` + `damage_type` + 威力/射程
2. **既存 effect 付与**: `effect: "attack"` + `effect_str: "adrenaline"`（対象に base 効果を付与）
3. **EOC 呼び出し**: `effect: "effect_on_condition"` + `effect_str: "eoc_id"`（複雑な処理を EOC に委譲）
4. **アイテム生成**: `effect: "spawn_item"` + `effect_str: "item_id"`

## 学習手段（呪文書）

```json
{
  "type": "ITEM",
  "subtypes": [ "BOOK" ],
  "id": "hmg_grimoire",
  "copy-from": "book_nonf_hard_tpl",
  "name": { "str": "tattered grimoire" },
  "description": "...",
  "weight": "900 g",
  "volume": "1 L",
  "material": [ "paper", "leather" ],
  "use_action": { "type": "learn_spell", "spells": [ "hmg_thorn_dart", "hmg_second_wind" ] }
}
```

- `book_nonf_hard_tpl`（`data/json/items/book/abstract.json`）が BOOK の汎用 abstract
- `learn_spell` は base の item_action（`data/json/item_actions.json`）
- 呪文側が `spell_class: "NONE"` ならクラス条件なしで習得できる
- `MUST_HAVE_CLASS_TO_LEARN` フラグ付きの呪文はクラス保持者のみ習得可能（Magiclysm のクラス呪文など）

## name の複数形ルール

- SPELL は `{ "str": "Thorn Dart" }` 形式。`str_pl` は付けない（0.I では不要な `str_pl` がエラー）
- base の一部ファイルは単純文字列（`"name": "Magic Missile"`）も使うが、新規は `str` オブジェクト形式が安全

## よくある罠

- 呪文書で習得させるのに `magic_type.max_book_level: 0` が設定されていると習得できない
- `learn_spell` はアイテムの `use_action` なので、`subtypes: [ "BOOK" ]` を忘れると表示・使用がおかしくなる
- `flags` は base の `flags.json` に実在するフラグを使う（Magiclysm 独自フラグを mod 依存なしで使わない）
- `damage_type` を mod 独自定義せず base の `damage_types.json` のIDを使う

## チェックリスト

- [ ] `magic_type` を定義し、`energy_source` を決めた
- [ ] 呪文書で学ばせる場合、`max_book_level` を設定していない
- [ ] `spell_class: "NONE"`（クラスレス）にした
- [ ] `damage_type` / `material` / フラグが base に実在する
- [ ] `name` に不要な `str_pl` を付けていない
- [ ] modinfo の `category` を `"magical"` にした
- [ ] `bash scripts/validate.sh` → `check_mods.sh --check-errors` を通過した
- [ ] Level3 で「習得 → 詠唱 → 効果」を実機確認した
