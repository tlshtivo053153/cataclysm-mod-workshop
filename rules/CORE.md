# CDDA Mod開発 コアルール

## 開発の進め方（9ステップ）

### 小規模modの定義（Step 1・2省略条件）

以下**すべて**を満たす場合、Step 1（仕様書作成）とStep 2（仕様書レビュー）を省略可能：
- 新規に定義するゲーム内ID（item_id, recipe_id 等）が5個以下（modinfo.json は除く）
- 既存タイプの `copy-from` のみ（新規 `type` 定義なし）
- 既存システムの拡張のみ（新規ゲームシステム・マップジェネレータ・NPC行動ロジック等を追加しない）
- 既存の同カテゴリアイテムから明確に派生したもの（例：「iron_rod をベースにした新素材の棍棒」）

### Step 1: 仕様書作成（小規模modは省略可）
- `templates/spec_template.md` を使用
- このmodが何を追加/変更し、ゲームプレイにどう影響するかを記述
- JSON構文を含めない
- **省略条件**: 小規模modの定義（前述）を満たす場合

### Step 2: 仕様書レビュー
- 以下のプロンプトをAIエージェントに実行：
  ```
  以下のmod仕様書を批判的にレビューしてください。
  - この仕様は既存のCDDAゲームシステムと矛盾していないか
  - スコープが適切か（過大でないか、過小でないか）
  - プレイヤー体験として面白いか、実用的か
  - 改善案や削減すべき範囲があれば指摘してください
  ```
- レビュー結果を反映して仕様書をブラッシュアップ
- **省略条件**: Step 1を省略した場合

### Step 3: 計画書作成
- `templates/design_template.md` を使用
- Step 1の仕様書を基に、実装の詳細を記述
- 使用するtype、copy-from先、ID命名、依存関係を決定
- **使用予定ID一覧**と**参照ファイル一覧**を明記

### Step 4: CDDA参照との整合性確認
- `external/cdda/data/json/` で計画書に記載した以下を実在確認：
  - copy-from先のID
  - 使用予定のフラグ名
  - 使用予定のマテリアルID
  - レシピの `activity_level` の設定値
  - `name` フィールドの形式（str_sp / str / 単純文字列）の適切性
- **新規レシピの場合**: `external/cdda/data/json/recipes/` から同カテゴリ・類似素材の既存レシピを1〜2個見つけ、`tools`・`qualities`・`components` の構成が既存レシピと整合しているか比較する
- design_template.md の「参照ファイル（実在確認済み）」欄にチェックをつける

### Step 5: 計画書レビュー
- 以下のプロンプトをAIエージェントに実行：
  ```
  以下のmod計画書を技術的観点から批判的にレビューしてください。
  - ID命名規則に違反がないか（prefix統一、使用可能文字）
  - copy-from先が適切か、不要なフィールドの上書きがないか
  - 依存関係に漏れがないか
  - 実装後の修正コストが高い設計がないか
  - 計画書とexternal/cdda/data/json/の実際のデータに矛盾がないか
  ```
- レビュー結果を反映して計画書をブラッシュアップ

### Step 6: 実装
- 計画書に基づき、modinfo.json および data/*.json を作成
- 編集のたびに `bash scripts/validate.sh <mod_dir>` を実行（Level1）
- 実装中に計画書から逸脱する場合は、都度計画書を更新する

### Step 7: 読み込みエラー解消（Level2）
- `bash scripts/link_mod_for_test.sh <mod_dir>` でCDDAに配置
- `scripts/check_mods.sh <mod_id>` でmod読み込みチェック
- エラーが出ない状態にする
- 詳細は `rules/verification.md` 参照
- **前提条件**: `external/cdda/cataclysm-tiles` が存在し、modが `external/cdda/mods/` に配置済みであること

### Step 8: 動作確認（Level3）
- デバッグメニューで追加アイテムのスポーン、クラフト、効果を確認
- 仕様書または設計書に記載した「成功基準」を満たしているか検証
- バグ（意図しない動作）を発見したら記録し、Step 6に戻って修正

### Step 9: バランス調整
- 追加アイテム/仕様の性能を、**同カテゴリ・同入手難易度帯**の既存コンテンツと比較：
  - 武器: ダメージ vs 重量 vs 製作難易度（技能レベル・素材の希少性）
  - 防具: 防御値 vs 環境耐性 vs 重量 vs 機動性ペナルティ
  - クラフト: 技能レベル vs 素材コスト vs 完成品の性能 vs 既存レシピとの差別化
- **基準**: 「入手難易度と製作コストに見合った性能」であるか
  - 単純な±20%比較ではなく、**コスト・パフォーマンス・ユニーク性のトレードオフ**として評価
  - 例: 強力な性能を持つ場合は、素材を希少にするか技能レベルを上げるか、耐久性を下げるなどの代償を設ける
- 必要に応じて数値調整し、Step 7〜8を再実行して確認

## 命名規則
- IDは必ず `mod_prefix_` で始める（例: `mymod_iron_rod`）
- ただし、バニラの抽象アイテム（`mutagen_flavor`、`mutagen_sample` 等）を `copy-from` してバニラシステムを拡張する場合、バニラの命名慣習（`mutagen_formicid`、`insect_sample` 等）に従うことを優先する
- IDに使える文字: 英小文字・数字・アンダースコアのみ
- IDに `#` 文字は使用不可

## 単位（0.H以降）
- 重量: `"500 g"` 形式（旧modが数値のみの場合は変換が必要）
- 容量: `"1500 ml"` 形式（旧modが数値のみの場合は変換が必要）
- 価格: `"200 USD"` 形式

## modinfo.json
- `type`: 必ず `"MOD_INFO"`
- `id`: 必須。他modと重複しない一意のID
- `name`: 必須
- `dependencies`: `[ "dda" ]` を最低限記載する

## start_location
- `type`: 必ず `"start_location"`
- `id`: 必ず `sloc_` プレフィックス（例: `sloc_construction_site`）
- `name`: plain string（`str_sp` 禁止）
- `terrain`: 対象の om_terrain ID を文字列配列、または `{"om_terrain": "...", "om_terrain_match_type": "..."}` のオブジェクト配列で指定
  - 文字列: 完全一致
  - `"PREFIX"`: 前方一致（例: `"school_1"` → `school_1_0_0` にマッチ）
  - `"TYPE"`: 完全一致（文字列と同義）
  - `"CONTAINS"`: 部分一致（例: `"campsite"` → `campsite_cabin` にマッチ）
- **野外スタートには `"flags": [ "ALLOW_OUTSIDE" ]` が必須。** 屋根のない地形（field, forest, construction_site, rooftop 等）では必ず指定する。付け忘れるとCDDAが**エラーを出さずに**最寄りの屋内タイルへフォールバックし、想定外の場所にスポーンする

## scenario
- `type`: 必ず `"scenario"`
- `id`: 一意の文字列。バニラとの競合を避けるため `scenario_` プレフィックス推奨
- `name`: plain string（`str_sp` 禁止）
- `points`: 整数（0 = 基準、負 = ハード、正 = イージー）
- `description`: フレーバーテキスト
- `start_name`: 開始地点選択画面の表示名
- `allowed_locs`: `start_location` ID の文字列配列
- `professions`: （任意）許可する profession ID の文字列配列（allowlist）。指定しない場合は全職業が使用可能
- `flags`: 主なフラグ — `CITY_START`（都市内）、`LONE_START`（NPC仲間なし）、`SUR_START`（サバイバー施設）、`CHALLENGE`（チャレンジ）、`FIRE_START`（火災あり）

## copy-from の使い方
- 使用前に external/cdda/data/json/ で親IDの存在を確認する
- abstract アイテムを copy-from する場合、`abstract` フィールドは引き継がれない

### item_group の extend
- `copy-from` + `extend` で拡張する
- **distribution 型**（subtype 未指定含む）: subtype の再宣言は不要。`extend: { "items": [...] }` を使用
- **collection 型**: **`"subtype": "collection"` の明示的な再宣言が必須**。`extend` のキーは親のフィールド名に合わせる（通常 `"entries"`）
- subtype を再宣言しない場合、`already defined with type "collection"` エラーになる
- **例**: `science`（distribution 型）→ subtype 宣言不要で extend 可。`lab_mutagen_ingredients_fridge`（collection 型）→ `"subtype": "collection"` を追記すれば extend 可
- **参考**: Magiclysm `external/cdda/data/mods/Magiclysm/itemgroups/` — collection 型拡張時は必ず `"subtype": "collection"` を再宣言している

### harvest の extend
- `copy-from` + `extend: { "entries": [...] }` で拡張する
- バニラデータに多数の使用例あり（`external/cdda/data/json/harvest.json`）

### dissect システム（mutagen_group）
- 三層構造: MONSTER.dissect（string）→ harvest（`type: "mutagen_group"`）→ item_group（subtype: "collection"）→ アイテム
- `harvest_drop_type: mutagen_group` は `drop` フィールド値を item_group ID として解決する
- `dissect_only: true` により解剖（dissect）アクション限定で入手可能
- 新規変異サンプルの解剖入手を追加する際は、harvest 定義を extend するだけでモンスター個別の修正は不要

## バージョン差分（0.G → 0.H）
- volume/weight の単位が数値から文字列形式に変更
  - 旧: `"volume": 3` → 新: `"volume": "750 ml"`
  - 旧: `"weight": 500` → 新: `"weight": "500 g"`
- その他の差分は version_diff.md を参照

## monstergroup の same-ID merge

バニラの出現テーブル（`GROUP_ZOMBIE` 等）に新モンスターを注入するには、**同一IDのmonstergroupを定義する**。CDDAローダーが自動でマージする。

### 書式
```json
{
  "type": "monstergroup",
  "id": "GROUP_ZOMBIE",
  "monsters": [
    { "monster": "mon_my_zombie", "weight": 10, "cost_multiplier": 5 }
  ]
}
```

### 必須ルール
- **`id` をバニラと同一にする**（`GROUP_ZOMBIE`, `GROUP_ZOMBIE_UPGRADE` 等）
- **`monsters` 配列のみ記述する。** `default`, `is_animal`, `auto_total` 等のグループレベルフィールドは書かない（バニラ定義から継承される）
- **`copy-from` は使用しない。** 同一ID定義のみで自動マージされる
- `monster` フィールドには実在するモンスターIDを指定する
- `cost_multiplier` が高いほど出現タイミングが遅れる（日数経過後に出現）

### 実在確認
注入先の monstergroup がバニラに存在することを必ず確認する:
```bash
grep -r '"id": "GROUP_ZOMBIE"' external/cdda/data/json/monstergroups/
```

## snippet の same-ID merge

バニラのスニペットカテゴリ（`note`, `general_graffiti_snippets` 等）に新エントリを追加するには、**同一 `type` + `category` の定義を作成する**。CDDAローダーが自動でマージする。

### 書式
```json
[
  {
    "type": "snippet",
    "category": "note",
    "text": [
      { "id": "mymod_note_1", "text": "\"引用符付きテキスト\"" }
    ]
  },
  {
    "type": "snippet",
    "category": "general_graffiti_snippets",
    "text": [
      { "id": "mymod_graffiti_1", "text": "平文テキスト" }
    ]
  }
]
```

### 必須ルール
- **`type` と `category` をバニラと同一にする**
- **`copy-from` / `extend` は使用しない。** 同一カテゴリ名定義のみで自動マージされる
- **ID はモッド固有のプレフィックスを使用する**（バニラ・他modとの衝突防止）
- `name` フィールドは使用しない（`note` / `general_graffiti_snippets` では不使用。`note_child` のみ例外）

### カテゴリ別テキスト形式
| カテゴリ | テキスト形式 | 用途 |
|---|---|---|
| `note` | `"\"引用符付きテキスト\""` | 手書きの紙切れ表現（サバイバーノート） |
| `general_graffiti_snippets` | `"平文テキスト"` | 壁の落書き視覚表現（グラフィティ） |

- **テキスト形式を誤ると、バニラと表示が不統一になる。** JSON構文チェックでは検出不可のため、実装時に手動確認が必要
- 拡張先カテゴリのテキスト形式は、必ずバニラデータの全エントリを確認して従うこと。形式はカテゴリ単位で統一されている
- 上記以外のカテゴリ（`note_child`, `shelter_graffiti_snippets` 等）を拡張する場合も、必ずバニラデータのテキスト形式を確認すること

### 実在確認
拡張先の snippet カテゴリがバニラに存在することを必ず確認する:
```bash
grep -r '"category": "note"' external/cdda/data/json/snippets/
```

### 実証例
- Magiclysm: `note` カテゴリ拡張（`magiclysm_note_1`〜`_8`）
- DinoMod: `general_graffiti_snippets` カテゴリ拡張（`general_graffiti_dino_1`〜`_13`）

## 変異カテゴリの実装

変異カテゴリを新規追加する場合は `rules/patterns/mutation_category.md` を参照すること。

## 格闘スタイルの実装

格闘スタイル（martial_art）を新規追加する場合は `rules/patterns/martial_art.md` を参照すること。特に以下の点に注意：
- 武器限定テクニックの `attack_vectors` には `["vector_null"]` が必須
- `skill_requirements` のスキル名は常に `"melee"`（`"bashing"` 等の個別武器スキルではない）
- 指定した `weapon_category` に実際に属する武器を `external/cdda/data/json/items/melee/` で必ず確認する

## モンスターの実装

モンスター（MONSTER）を新規追加する場合は `rules/patterns/monster.md` を参照すること。特に以下の点に注意：
- `special_attacks` は `copy-from` 時に完全上書きされる。継承したい攻撃も明示的に再宣言が必要
- `smash` 攻撃の `throw_strength` 有効範囲は 30〜108
- `upgrades` の単体進化は `into`（グループ進化は `into_group`）
- flags 操作は `extend`（追加）/ `delete`（削除）を使用
- 死亡ドロップは `subtype: "collection"` の item_group で `default_zombie_items` をネストする

## バイオニック/CBMの実装

バイオニック（bionic）を新規追加する場合は `rules/patterns/bionic.md` を参照すること。特に以下の点に注意：
- bionic定義 (`"type": "bionic"`) とCBMアイテム (`"type": "ITEM"`, `"subtypes": [ "BIONIC_ITEM" ]`) を**同一ID**で二重定義する
- CBMアイテムは `bionic_general_npc_usable`（または `bionic_general`）から `copy-from` する
- `name` 形式: bionic/CBMいずれも `{ "str": "名称" }`、CBMアイテム名末尾は `" CBM"`
- `mutation_conflicts` に記載する変異IDは `external/cdda/data/json/mutations/mutations.json` で実在確認する
- `BIONIC_SHOCKPROOF` フラグの付与要否を検討する（金属製なら付けない）
- 故障リスクは `faults: [ { "fault": "fault_bionic_salvaged" } ]` を抽象ベースが継承するため、個別CBMでの記述は不要

## トラップの実装

トラップ（trap）/ トラップアイテム（ITEM/TOOL with place_trap）を新規追加する場合は `rules/patterns/trap.md` を参照すること。特に以下の点に注意：
- trap定義 (`"type": "trap"`) とアイテム定義 (`"type": "ITEM"`, `"subtypes": [ "TOOL" ]`) の**両方**が必要。アイテムの `use_action.place_trap.trap` で trap 定義を参照する
- 一部の C++ trap action（`snare_light`, `bubble`, `beartrap` 等）はドロップアイテムやメッセージをハードコードしており、JSONの `drops` フィールドは**トリガー時には無視される**
- `snare_light` アクションは常に `light_snare_kit` をドロップする。異なるアイテムをドロップさせるには別actionの使用または変換レシピの追加が必要
- trap 定義の `name` は単純文字列（`str_sp` 不可）
- ITEM/TOOL の `name` は `{"str": "..."}` 形式（`str_sp` 不可）
- `SINGLE_USE` フラグが必須（設置型トラップアイテム）
- `needs_solid_neighbor: true` で通路設置型（両端に壁が必要）にできる

## GUNMODの実装

GUNMOD（武器アタッチメント）を新規追加する場合は `rules/patterns/gunmod.md` を参照すること。特に以下の点に注意：
- `name` は `{"str": "..."}` 形式（TOOL相当。`str_sp` ではない）
- `location` は装着先の銃の `valid_mod_locations` と完全一致する必要がある
- `"underbarrel"` と `"underbarrel mount"` は別スロット。混同しないこと
- `mod_targets` はバニラ同種GUNMODと同等の広さを確保する（狭すぎると装着不可になる）
- `min_skills`（ITEM側）は装着難易度、recipe `skills_required` はクラフト難易度（別物）
- `integral_volume: "0 ml"` / `integral_weight: "0 g"` は追加アタッチメント用（既存パーツ置換ではない）

## カウントダウン爆発物の実装

投擲式爆発物・ノイズメーカー（未活性→活性化→カウントダウン→爆発の2状態TOOL）を新規追加する場合は `rules/patterns/explosive.md` を参照すること。特に以下の点に注意：
- `transform` use_action の `need_wielding: true` で誤操作防止
- `target_timer`（未活性側）と `countdown_interval`（活性化側）を同じ値に設定する
- `tick_action` は単一でも配列 `[{...}]` で記述
- 活性化側にダミー `use_action: { "type": "message" }` で再活性化を防止
- `countdown_action` の type に `"explosion"` を指定すると、爆風パワーに比例した暗黙ノイズを生成。純粋ノイズ目的でもアイテム消費の確実性から爆発型を推奨

## recipe の必須フィールド（0.I RC）
- `activity_level` が必須。省略するとゲーム起動時にエラー
- 値は `external/cdda/data/json/recipes/` の同カテゴリファイルを参照して選ぶ
- 大型爆発物（バレルボム級）は `"BRISK_EXERCISE"`。その他の爆発物・ノイズメーカーは `"LIGHT_EXERCISE"` が標準。必ず参照レシピを確認すること

## name フィールド形式（0.I RC）
- `ITEM`/`SPELL` → `{"str_sp": "名称"}` が必須（単純文字列は不可）
  - **ただし `TOOL` subtype のみ例外:** TOOL アイテムは `{"str": "名称"}` を使用（`str_sp` ではない）
  - **ただし `BIONIC_ITEM` subtype も例外:** CBMアイテムは `{"str": "名称"}` を使用（`str_sp` ではない）
  - **ただし `MAGAZINE` subtype も例外:** マガジンアイテムは `{"str": "名称"}` を使用（`str_sp` ではない）
  - **COMESTIBLE/FOOD/DRINK は `str_sp`:** 食品・飲料系も `ITEM` 型だが、`str_sp` が必須
- `MONSTER` → `{"str": "名称"}`（バニラで支配的な形式）。動的名前生成の一部モンスターでは `{"str_sp": "..."}` も使用される
- `overmap_terrain`/`mutation`/`profession`/`start_location`/`scenario` → 単純文字列が必須（`str_sp` は不可）

## よくあるエラー
- `unknown type` → typeフィールドのスペルミス
- `copy-from target not found` → 依存modの読み込み順か、IDのスペルミス
- `missing required field` / `missing mandatory member` → common_errors.md を参照
- JSON構文エラー → 末尾カンマ、括弧の対応を確認
- **`start_location` で想定外の場所にスポーンする** → `ALLOW_OUTSIDE` フラグの付け忘れ。屋根のない野外タイル（construction_site, field, forest, rooftop 等）では `"flags": [ "ALLOW_OUTSIDE" ]` が必須。エラーは出ず、最寄りの屋内タイルに沈黙フォールバックする
