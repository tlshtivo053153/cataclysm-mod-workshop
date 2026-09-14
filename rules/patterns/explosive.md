# カウントダウン爆発アイテム実装パターン

CDDAに新規のカウントダウン式爆発物・ノイズメーカー（TOOL）を追加するためのパターンファイル。

## 概要

投擲式爆発物は以下の2状態 TOOL パターンで実装する：

- **未活性状態** (`_popper`): `use_action: { type: "transform" }` で活性化。プレイヤーがインベントリから起動
- **活性化状態** (`_act`): `countdown_action` で指定秒数後に爆発。`tick_action` で動作中演出

バニラの代表例：
| パターン | アイテム | countdown_action | ノイズ発生方法 |
|---|---|---|---|
| 爆発型 | `grenade` / `grenade_act` | `"type": "explosion"` | 爆風に比例した暗黙的ノイズ |
| 音響型 | `firecracker` / `firecracker_act` | `"type": "sound"` | sound_volume で明示指定 |

## ファイル構成

| ファイル | type | 内容 |
|---|---|---|
| `modinfo.json` | `MOD_INFO` | mod登録情報。`category: "items"` 推奨 |
| `data/items.json` | `ITEM` (TOOL) | 未活性 + 活性化 の2アイテム定義 |
| `data/recipes.json` | `recipe` | クラフトレシピ（任意） |

## 参照ファイル（external/cdda/）

| ファイル | 目的 |
|---|---|
| `data/json/items/tool/explosives.json` | `grenade`/`grenade_act`（爆発型）、`firecracker`/`firecracker_act`（音響型）の全フィールド確認 |
| `data/json/items/ammo.json` | `duct_tape` 等、AMMOアイテムのID・チャージ数確認 |
| `data/json/items/containers/containers.json` | 容器アイテムID確認（`bottle_plastic` 等） |
| `data/json/items/chemicals_and_resources.json` | `chem_carbide` 等、材料AMMOアイテムのID・ammo_type確認 |
| `data/json/recipes/weapon/explosive.json` | 爆発物レシピの `activity_level`・カテゴリ・コンポーネント形式確認 |

## 未活性アイテムの基本構造

```json
{
  "id": "carbide_popper",
  "type": "ITEM",
  "subtypes": [ "TOOL" ],
  "category": "weapons",
  "name": { "str": "calcium carbide popper" },
  "description": "A small plastic container separated by a seal.  ...",
  "weight": "50 g",
  "volume": "50 ml",
  "price": "5 cent",
  "price_postapoc": "25 cent",
  "material": [ "plastic" ],
  "symbol": "*",
  "color": "light_gray",
  "use_action": {
    "type": "transform",
    "need_wielding": true,
    "target": "carbide_popper_act",
    "msg": "You break the seal, mixing the calcium carbide with water.  The pressure builds rapidly…",
    "target_timer": "5 seconds",
    "menu_text": "Break seal"
  },
  "flags": [ "BOMB" ]
}
```

### transform use_action フィールド

| フィールド | 必須 | 説明 |
|---|---|---|
| `type` | 必須 | `"transform"` |
| `target` | 必須 | 変換先の活性化アイテムID（`_act` 側） |
| `need_wielding` | 必須 | `true` にすることでインベントリからの誤操作を防止（`grenade` と同様） |
| `msg` | 必須 | 活性化時のメッセージ |
| `target_timer` | 必須 | 変換先アイテムの初期カウントダウン時間。**活性化側の `countdown_interval` と同じ値を設定すること** |
| `menu_text` | 必須 | アクションメニューでの表示名 |

### 未活性側のフラグ

- **`BOMB`**: `transform` パターンを使用する場合、未活性側に必須。バニラ `grenade` をはじめ全 transform 型爆発物が付与
- `NO_DROP` は付けない（投擲可能にするため）

## 活性化アイテムの基本構造（爆発型）

```json
{
  "id": "carbide_popper_act",
  "type": "ITEM",
  "subtypes": [ "TOOL" ],
  "category": "weapons",
  "name": { "str": "active calcium carbide popper", "str_pl": "active calcium carbide poppers" },
  "description": "Acetylene gas is building up inside this container, and it's about to burst.  You should throw it immediately!",
  "weight": "50 g",
  "volume": "50 ml",
  "price": "0 cent",
  "price_postapoc": "0 cent",
  "material": [ "plastic" ],
  "symbol": "*",
  "color": "light_gray",
  "use_action": { "type": "message", "message": "The seal is already broken on this calcium carbide popper.  Throw it, quickly!", "name": "Break seal" },
  "tick_action": [ { "type": "sound", "sound_message": "A hissing fizz comes from the carbide popper.", "sound_volume": 0, "sound_id": "misc", "sound_variant": "lit_fuse" } ],
  "countdown_action": { "type": "explosion", "explosion": { "power": 3, "shrapnel": 0 } },
  "countdown_interval": "5 seconds",
  "flags": [ "TRADER_AVOID", "NPC_THROW_NOW" ]
}
```

### 活性化アイテムの主要フィールド

| フィールド | 必須 | 説明 |
|---|---|---|
| `name` | 必須 | `{ "str": "...", "str_pl": "..." }` 形式。活性化状態では `str_pl` を推奨（`firecracker_act` 等で使用。`grenade_act` は例外で `str_pl` 無し） |
| `price` / `price_postapoc` | 必須 / 推奨 | 活性化状態はトレード不可のため `"0 cent"`（`grenade_act` 準拠。`c4armed` は `price_postapoc` 無しだが、両方設定するのが安全） |
| `use_action` | **強く推奨** | ダミーの message 型 use_action を設定し、再活性化を防止する（`grenade_act` のパターン） |
| `tick_action` | 推奨 | カウントダウン中の毎tick演出。**単一でも配列 `[{...}]` で記述すること** |
| `countdown_action` | 必須 | カウントダウン満了時のアクション |
| `countdown_interval` | 必須 | カウントダウン時間。**未活性側の `target_timer` と同じ値を設定すること** |

### tick_action の注意点

- **単一の sound でも必ず配列で記述**: `[ { "type": "sound", ... } ]`（バニラ `firecracker_act` 参照）
- 裸のオブジェクト `{ "type": "sound", ... }` はゲーム起動エラーになる

### countdown_action の選択

| タイプ | 用途 | ノイズ | アイテム消費 |
|---|---|---|---|
| `"type": "explosion"` | 爆発・破裂 | 爆風パワーに比例して**自動生成**（`sound_volume` 不要） | **確実に消費される** |
| `"type": "sound"` | 純粋ノイズ | `sound_volume` で明示指定 | 消費挙動は未定義 |

- **ノイズ目的でも `"explosion"` を推奨**: アイテムが確実に消費され、暗黙ノイズも発生する
- `explosion` の `power` は小さめ（3〜10）にして、ダメージよりノイズを主目的にする

### shrapnel の指定

- `"shrapnel": 0`（整数）: 破片なしの最小限爆風。バニラに使用例は無いが、0.I RC で有効な可能性がある
- エラーが出る場合、オブジェクト形式 `"shrapnel": { "casing_mass": 0, "fragment_mass": 0 }` に変更する
- バニラ `grenade_act` はオブジェクト形式を使用（`"casing_mass": 217, "fragment_mass": 0.02`）

### 活性化側のフラグ

| フラグ | 必須 | 説明 |
|---|---|---|
| `TRADER_AVOID` | 必須 | NPCトレーダーが扱わないようにする。`firecracker_act`/`grenade_act` 共通 |
| `NPC_THROW_NOW` | 推奨 | NPCが所持した場合即座に投擲する（`c4armed` で使用）。`grenade_act` には未付与だが、ノイズメーカー用途ではNPCの行動誘導に有効 |
| `BOMB` | 任意 | `grenade_act` は残留。音響型では不要 |

## レシピ定義

```json
{
  "result": "carbide_popper",
  "type": "recipe",
  "activity_level": "LIGHT_EXERCISE",
  "category": "CC_WEAPON",
  "subcategory": "CSC_WEAPON_EXPLOSIVE",
  "skill_used": "fabrication",
  "difficulty": 1,
  "time": "2 m",
  "autolearn": true,
  "qualities": [ { "id": "CUT", "level": 1 } ],
  "components": [
    [ [ "chem_carbide", 20 ] ],
    [ [ "water", 1 ], [ "water_clean", 1 ] ],
    [ [ "bottle_plastic", 1 ] ],
    [ [ "duct_tape", 10 ] ]
  ]
}
```

### レシピ設計指針

| 要素 | 指針 | 根拠 |
|---|---|---|
| `category` / `subcategory` | `CC_WEAPON` / `CSC_WEAPON_EXPLOSIVE` | バニラ `firecracker` レシピ準拠 |
| `activity_level` | 火薬不使用なら `LIGHT_EXERCISE`、それ以外は `BRISK_EXERCISE` | バニラ同カテゴリレシピ参照 |
| `difficulty` | 1〜2（最低難易度） | 単純な容器＋化学反応は高度な技能不要 |
| `autolearn` | `true` | 簡易な仕組みは書物不要 |
| `qualities` | `CUT` level 1（テープ切断） | 簡易爆発物は level 1 で可。バニラ `firecracker` は level 2 だが、より単純な容器破裂型なら level 1 に下げて差別化 |
| `components` | 既存爆発物レシピのパターンに従う | `duct_tape` は常に10チャージ（全11既存レシピで統一） |

### AMMO アイテムを components で使う場合

- `duct_tape`（`ammo_type: "tape"`, `count: 1`）: `[ "duct_tape", 10 ]` で10チャージ消費
- `chem_carbide`（`ammo_type: "components"`, `count: 100`）: `[ "chem_carbide", 20 ]` で20チャージ消費
- `ammo_type` の指定は不要。IDとチャージ数のみで参照できる

## 実装チェックリスト

- [ ] 未活性・活性化の両方で `type: "ITEM"` + `subtypes: [ "TOOL" ]` を明示しているか
- [ ] `name` が TOOL 形式 `{ "str": "..." }` か（`str_sp` ではない）
- [ ] 活性化側の `name` に `str_pl` が設定されているか（推奨。`grenade_act` は例外）
- [ ] 未活性側の `use_action` に `need_wielding: true` が設定されているか
- [ ] `target_timer`（未活性側）と `countdown_interval`（活性化側）が同じ値か
- [ ] 活性化側にダミーの `use_action: { "type": "message" }` を設定し再活性化を防止しているか
- [ ] `tick_action` が配列 `[{...}]` で記述されているか（単一soundでも配列必須）
- [ ] `countdown_action` が適切なタイプ（`explosion` / `sound`）か
- [ ] `shrapnel` の形式が正しいか（整数 `0` またはオブジェクトで指定）
- [ ] 未活性側に `BOMB` フラグ、活性化側に `TRADER_AVOID` フラグが付いているか
- [ ] 活性化側の `price` が `"0 cent"` か（`price_postapoc` も `"0 cent"` を推奨）
- [ ] recipe の `activity_level` が設定されているか（0.I RC 必須）
- [ ] recipe の `components` で使用する全アイテムIDがバニラに存在するか
- [ ] `duct_tape` を使用する場合、消費量が既存レシピと整合しているか（標準10）
- [ ] `chem_carbide` 等 `ammo_type: "components"` のAMMOアイテムが `[ "id", N ]` で正しくチャージ数指定されているか
- [ ] description の英文がテキストスタイルチェッカーに準拠しているか（文区切りにダブルスペース）

## 検証手順

1. `bash scripts/validate.sh <mod_dir>` — JSON構文チェック（Level1）
2. `bash scripts/place_mod_for_test.sh <mod_dir>` — CDDAに配置
3. `bash scripts/check_mods.sh <mod_id>` — ゲーム読み込みチェック（Level2）
4. CDDA起動 → デバッグメニューで以下確認（Level3）:
   - アイテムスポーン・クラフト可否
   - 活性化（use_actionトリガー）→ カウントダウン開始
   - `tick_action` の音声・メッセージが毎tick発生するか
   - カウントダウン満了時の爆発/ノイズ発生
   - 爆発後アイテムが正しく消費されるか
   - ゾンビがノイズ発生地点に向かうか

### Level2 検証時の注意

- `shrapnel: 0`（整数）が原因でエラーが出た場合、オブジェクト形式に変更して再テスト
- `Stale game data detected` エラーが出た場合: `external/cdda/config/flexcache` を削除して再実行

## 実装例

- `mods/small/carbide_popper/` — 爆発型ノイズメーカー。`chem_carbide` + `bottle_plastic` + `water`。最小限の power:3 爆風で注意誘引
