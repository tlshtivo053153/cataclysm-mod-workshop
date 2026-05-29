## Mod設計書: Junk Bionics

### 仕様書から継承（小規模modのため仕様書省略・ここに直接記入）
- **目的**: 廃材・サルベージ部品から作られた粗悪な即席バイオニック3種を追加する。既存CBMがすべてハイテク品であるのに対し、低品質だが入手しやすい代替選択肢を提供する。
- **スコープ**:
  - 含む: 3種のbionic定義 + 3種のCBM item + bionics_commonアイテムグループへの出現追加
  - 含まない: クラフトレシピ、新規マップ出現地点、新規職業・シナリオ、モンスタードロップ
- **成功基準**: CDDA起動時にエラーなく読み込まれ、デバッグメニューで各CBMがスポーン可能であり、適切にバイオニックとして機能すること。

### ターゲットバージョン
- CDDA: 0.I RC

### 依存関係
- 依存mod: dda（必須）

### 使用予定ID一覧
| 種別 | ID | 説明 |
|---|---|---|
| bionic / ITEM(BIONIC_ITEM) | `bio_junk_power_storage` | 廃バッテリー製パワーストレージ（容量50kJ、標準の半分） |
| bionic / ITEM(BIONIC_ITEM) | `bio_junk_armor_torso` | 廃鉄板の皮下装甲（防御低め・encumbrance高め） |
| bionic / ITEM(BIONIC_ITEM) | `bio_junk_muscle` | スプリング製筋力補助（STR+1、標準の半分） |

計 4 ID（modinfo `junk_bionics` を含む）→ 小規模mod基準（5以下）を満たす。

### 参照ファイル（実在確認済み）
- [x] `external/cdda/data/json/bionics.json` — `bio_power_storage` (L1356), `bio_armor_torso` (L388), `bio_str_enhancer` (L1569)
- [x] `external/cdda/data/json/items/bionics.json` — `bionic_general_npc_usable` (CBM抽象ベース), `bio_power_storage` (L820), `bio_armor_torso` (L139), `bio_str_enhancer` (L1013)
- [x] `external/cdda/data/json/itemgroups/bionics.json` — `bionics_common` (L106, distribution型)
- [x] `external/cdda/data/json/items/generic.json` — `burnt_out_bionic` (looks_like用)
- [x] `external/cdda/data/json/body_parts.json` — 各部位の`bionic_slots`容量確認: torso=80, arm=30, leg=30（使用予定slot数が上限を超えないことを確認済み）

### ファイル構成
- `modinfo.json`
- `data/bionics.json` — `"type": "bionic"` ×3
- `data/items.json` — `"type": "ITEM"`, `"subtypes": [ "BIONIC_ITEM" ]` ×3（copy-from: `bionic_general_npc_usable`）
- `data/itemgroups.json` — `bionics_common` への extend（distribution型、subtype再宣言不要）

### 各bionic設計詳細

#### 1. bio_junk_power_storage
- **参照元**: `bio_power_storage`（容量100kJ, dupes_allowed）
- **差分**:
  - capacity: `"50 kJ"`（標準の半分）
  - name: `"Junk Power Storage"`
  - description: 廃品回収部品で組み立てた粗悪品であることを明記
  - CBM: weight 200g（標準70gの約3倍）、difficulty 2（低め）、price_postapoc `"1 USD"`
  - flags: `[ "BIONIC_NPC_USABLE" ]`

#### 2. bio_junk_armor_torso
- **参照元**: `bio_armor_torso`（protec bash=3 cut=3 bullet=3 stab=3, encumbrance=1, slots=10）
- **差分**:
  - protec: bash=2, cut=2, stab=2（bulletなし＝銃弾無効）
  - encumbrance: `[ [ "torso", 4 ] ]`（標準の4倍）
  - occupied_bodyparts: `[ [ "torso", 15 ] ]`（標準10→15）
  - BIONIC_SHOCKPROOFなし（金属製のため電撃に弱い）
  - canceled_mutations: VINES1/2/3 のみ（簡略化）
  - name: `"Scrap-Plated Torso"`
  - CBM: weight 4000g（標準3000gより重い）、difficulty 4、price_postapoc `"5 USD"`

#### 3. bio_junk_muscle
- **参照元**: `bio_str_enhancer`（STR+2, slots: torso=6 arm=4/4 leg=8/8）
- **差分**:
  - enchantments: STR+1（標準の半分）
  - occupied_bodyparts: torso=8 arm=6/6 leg=10/10（標準の1.25〜1.5倍）
  - パッシブ常時発動（BIONIC_TOGGLEDなし、act_costなし）
  - name: `"Pipe-Spring Musculature"`
  - CBM: weight 2500g（標準1500gより重い）、difficulty 5、price_postapoc `"5 USD"`

### item_group 追加
- `bionics_common`（distribution型）に各CBMを追加
- 出現重み: power_storage=10（共通品並み）、armor=5（ややレア）、muscle=5（ややレア）
- subtype再宣言不要（distribution型のため）

### looks_like
- 全CBMアイテムで `"burnt_out_bionic"` を使用（見た目が粗悪であることを表現）

### 実装順序
1. modinfo.json
2. data/bionics.json（bionic定義 ×3）
3. data/items.json（CBM item ×3）
4. data/itemgroups.json（bionics_common extend）

### テスト手順
1. `bash scripts/validate.sh mods/small/junk_bionics` でJSON構文チェック（Level1）
2. `bash scripts/link_mod_for_test.sh mods/small/junk_bionics` でCDDAに配置
3. CDDA起動でエラーなし確認（Level2）

### 完了条件
- [x] Level1: JSON構文OK
- [x] Level2: 起動OK（エラーなし）
