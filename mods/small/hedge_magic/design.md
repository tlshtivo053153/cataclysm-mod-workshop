## Mod設計書: hedge_magic

### 仕様書から継承
- **目的**: STAMINA ベースの自己完結型 magic_type + SPELL + 呪文書（BOOK / learn_spell）の実装
- **スコープ**: magic_type 1件、SPELL 2件、BOOK 1件、レシピ1件のみ
- **成功基準**: 呪文書から呪文を習得・詠唱でき、Level2 を通過する

### ターゲットバージョン
- CDDA: 0.I RC

### 依存関係
- 依存mod: dda（必須）

### 使用予定ID一覧
| 種別 | ID | 説明 |
|---|---|---|
| magic_type | `hmg_hedge_magic` | STAMINA を消費する民間魔術体系 |
| SPELL | `hmg_thorn_dart` | 棘の飛礫（stab ダメージ・単体攻撃） |
| SPELL | `hmg_second_wind` | 活力の護符（自身に `adrenaline` 効果） |
| ITEM (BOOK) | `hmg_grimoire` | 呪文書（copy-from: `book_nonf_hard_tpl`, learn_spell） |
| recipe | `hmg_grimoire` | 製本レシピ |

### 参照ファイル（実在確認済み）
- [x] `external/cdda/data/mods/MindOverMatter/powers/classless.json` — `mom_psionics`（STAMINA magic_type の実例, 3行目）
- [x] `external/cdda/data/mods/Magiclysm/Spells/classless.json` — `magic_type` + SPELL の基本構成、`energy_source: "STAMINA"` の上書き例（megablast, 115行目付近）
- [x] `external/cdda/data/mods/Magiclysm/Spells/magus.json` — `magic_missile`（最小攻撃呪文, 31行目）
- [x] `external/cdda/data/json/artifact/legacy_artifact_active.json` — `AEA_ADRENALINE`（`effect_str: "adrenaline"` の実例）
- [x] `external/cdda/data/json/effects.json` — `adrenaline` 効果（3529行目）
- [x] `external/cdda/data/json/flags.json` — 呪文フラグ `VERBAL` / `SOMATIC` / `NO_LEGS`（1145行目〜）
- [x] `external/cdda/data/json/damage_types.json` — `stab` ダメージタイプ
- [x] `external/cdda/data/json/items/book/abstract.json` — `book_nonf_hard_tpl`（69行目, BOOK abstract）
- [x] `external/cdda/data/mods/Magiclysm/items/spell_scrolls.json` — `learn_spell` の書式（23行目）
- [x] `external/cdda/data/json/item_actions.json` — `learn_spell`（189行目）
- [x] `external/cdda/data/json/recipes/recipe_others.json` — 製本レシピの書式（book_binder, 1313行目）

### ファイル構成
```
mods/small/hedge_magic/
├── spec.md
├── design.md
├── modinfo.json
└── data/
    ├── magic_type.json
    ├── spells.json
    ├── items.json
    └── recipes.json
```

### 設計詳細

| SPELL | effect | damage_type | range | 習得 | energy |
|---|---|---|---|---|---|
| hmg_thorn_dart | attack | stab | 3〜12 | 呪文書 | STAMINA 1250 |
| hmg_second_wind | attack + effect_str: adrenaline | — | self | 呪文書 | STAMINA 1500 |

- `spell_class: "NONE"`（クラスレス）。Magiclysm の呪文書と同じく `learn_spell` で習得可能
- `magic_type` に `max_book_level` を設定しない（書物学習を許可するため。MindOverMatter は 0 で禁止している）
- 呪文の `name` は `{ "str": ... }` + 自動複数形（冗長な `str_pl` は 0.I でエラーになるため付けない）

### 実装順序
1. modinfo.json
2. data/magic_type.json
3. data/spells.json
4. data/items.json
5. data/recipes.json

### テスト手順
1. `bash scripts/validate.sh mods/small/hedge_magic/`（Level1）
2. `bash scripts/place_mod_for_test.sh --link mods/small/hedge_magic/`
3. `bash scripts/check_mods.sh --check-errors hedge_magic`（Level2）
4. CDDA 起動 → デバッグメニューで `hmg_grimoire` を入手 → 使用して呪文習得 → 詠唱確認（Level3）

### 完了条件
- [x] Level1: JSON構文OK
- [x] Level2: 起動OK（ERROR なし）
- [ ] Level3: 意図通り動作（習得・詠唱・効果付与）— **未実行（手動確認待ち）**
