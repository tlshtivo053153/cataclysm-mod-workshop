## Mod設計書: carbide_popper

### 目的
炭化カルシウム（`chem_carbide`）と水、ペットボトルを組み合わせて作る、投擲式の破裂音ノイズメーカーを追加する。ゾンビを音で誘引するための低コストな撹乱ツールとして機能する。

### スコープ
- **含む:**
  - TOOLアイテム2種: `carbide_popper`（未活性） + `carbide_popper_act`（活性化済み）
  - レシピ1種: `carbide_popper` のクラフト
- **含まない:**
  - モンスター追加
  - シナリオ追加
  - マップ変更
  - 既存データの改変

### 成功基準
- アイテム `carbide_popper` をクラフトできる
- 活性化（Break seal）後、5秒間のカウントダウン中にtick音（hissing fizz）が発生する
- カウントダウン満了時に power:3 の破裂（explosion）が発生し、アイテムが消費される
- 破裂音によってゾンビが音源地点に誘引される

### ターゲットバージョン
- CDDA: 0.I RC

### 依存関係
- 依存mod: dda（必須）

### 使用予定ID一覧
| 種別 | ID | 説明 |
|---|---|---|
| ITEM/TOOL | `carbide_popper` | 未活性の炭化カルシウム破裂装置。`use_action: transform` で活性化 |
| ITEM/TOOL | `carbide_popper_act` | 活性化済み。`countdown_action: explosion` で5秒後に破裂 |
| recipe | `carbide_popper` | クラフトレシピ（`CC_WEAPON` / `CSC_WEAPON_EXPLOSIVE`） |

### 参照ファイル（実在確認済み）
- [ ] `external/cdda/data/json/items/chemicals_and_resources.json` — `chem_carbide`（ammo_type: "components", count: 100）の実在確認
- [ ] `external/cdda/data/json/items/containers/containers.json` — `bottle_plastic` の実在確認
- [ ] `external/cdda/data/json/items/ammo.json` — `duct_tape`（ammo_type: "tape", count: 1）の実在確認
- [ ] `external/cdda/data/json/items/comestibles/drink.json` — `water` / `water_clean` の実在確認
- [ ] `external/cdda/data/json/items/tool/explosives.json` — `grenade` / `grenade_act`（爆発型）、`firecracker` / `firecracker_act`（音響型）のパターン参照
- [ ] `external/cdda/data/json/recipes/weapon/explosive.json` — 爆発物レシピの `activity_level`・カテゴリ・コンポーネント形式確認
- [ ] `external/cdda/data/json/flags.json` — `BOMB`, `TRADER_AVOID`, `NPC_THROW_NOW` フラグ確認

### ファイル構成
- modinfo.json
- data/items.json
- data/recipes.json

### 実装順序
1. modinfo.json
2. data/items.json
3. data/recipes.json

### アイテム仕様

#### 未活性アイテム (`carbide_popper`)

| フィールド | 値 | 根拠 |
|---|---|---|
| type/subtypes | `ITEM` / `[ "TOOL" ]` | バニラ `grenade` と同一の型（TOOL は subtypes 配列で明示） |
| name | `{ "str": "calcium carbide popper" }` | TOOL は `str_sp` ではなく `{ "str": "..." }` を使用（CORE.md §298） |
| use_action | `transform` → target: `carbide_popper_act` | バニラ `grenade` と同一の transform パターン |
| target_timer | `"5 seconds"` | 活性化側の `countdown_interval` と一致 |
| need_wielding | `true` | インベントリからの誤操作防止（`grenade` と同様） |
| flags | `[ "BOMB" ]` | transform 型爆発物の未活性側に必須（バニラ全 grenade 系が付与） |

#### 活性化アイテム (`carbide_popper_act`)

| フィールド | 値 | 根拠 |
|---|---|---|
| name | `{ "str": "...", "str_pl": "..." }` | 活性化状態では複数形（str_pl）を推奨（`firecracker_act` 準拠） |
| price / price_postapoc | `"0 cent"` | 活性化状態はトレード不可（`grenade_act` 準拠） |
| use_action | `message` 型（ダミー） | 再活性化の防止（`grenade_act` のパターン） |
| tick_action | 配列 `[{ "type": "sound", ... }]` | 単一soundでも配列必須。カウントダウン中の hissing fizz 音 |
| countdown_action | `{ "type": "explosion", ... }` | ノイズ目的でも `explosion` を推奨（アイテム確実消費＋暗黙ノイズ発生） |
| countdown_interval | `"5 seconds"` | 未活性側の `target_timer` と一致 |
| explosion.power | `3` | ダメージよりノイズを主目的とする最小限の爆風 |
| explosion.shrapnel | `0`（整数） | 破片なし。0.I RC では整数 `0` が有効。エラー発生時は `{ "casing_mass": 0, "fragment_mass": 0 }` に変更 |
| flags | `[ "TRADER_AVOID", "NPC_THROW_NOW" ]` | NPCトレーダー非取扱＋NPC即時投擲誘導 |

#### レシピ (`carbide_popper`)

| フィールド | 値 | 根拠 |
|---|---|---|
| category | `CC_WEAPON` | バニラ `firecracker` レシピ準拠 |
| subcategory | `CSC_WEAPON_EXPLOSIVE` | 同 |
| activity_level | `LIGHT_EXERCISE` | 火薬不使用のため（0.I RC 必須項目） |
| difficulty | `1` | 単純な容器＋化学反応は高度な技能不要 |
| autolearn | `true` | 簡易な仕組みのため書物不要 |
| qualities | `CUT` level 1 | テープ切断用。バニラ `firecracker`（level 2）より単純なため level 1 に差別化 |
| components | `chem_carbide`(20), `water`/`water_clean`(1), `bottle_plastic`(1), `duct_tape`(10) | `duct_tape` は全バニラ爆発物レシピで 10 チャージ統一 |

### テスト手順
1. `bash scripts/validate.sh mods/small/carbide_popper` でJSON構文チェック（Level1）
2. `bash scripts/link_mod_for_test.sh mods/small/carbide_popper` でCDDAに配置
3. `bash scripts/check_mods.sh carbide_popper` でmod読み込み確認（Level2）
4. CDDA起動 → デバッグメニューで以下Level3確認:
   - `carbide_popper` のアイテムスポーン・クラフト可否
   - 活性化（Break seal）→ 5秒カウントダウン開始
   - tick_action の hissing fizz 音が毎tick発生するか
   - カウントダウン満了時の爆炸発生とアイテム消費
   - ゾンビが破裂音発生地点に向かうか
5. Level2 で `shrapnel: 0`（整数）が原因のエラーが出た場合、`{ "casing_mass": 0, "fragment_mass": 0 }` に変更して再テスト
6. `Stale game data detected` エラーが出た場合: `external/cdda/config/flexcache` を削除して再実行

### 完了条件
- [ ] Level1: JSON構文OK
- [ ] Level2: 起動OK（エラーなし）
- [ ] Level3: 意図通り動作
  - [ ] `carbide_popper` をクラフトできる
  - [ ] 活性化後、5秒間のカウントダウン中にtick音が発生する
  - [ ] カウントダウン満了時に破裂（explosion）が発生し、アイテムが消費される
  - [ ] 破裂音にゾンビが誘引される
