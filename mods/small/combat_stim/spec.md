## Mod仕様書: combat_stim

### 背景・動機
- `rules/patterns/enchantment.md` は wm_weapon_mastery で `effect_type` へのインライン enchantment を実証済みだが、**単体 `type: "enchantment"` を定義して他オブジェクトから ID 参照するパターン**は未実証である
- 単体 enchantment は base の `mech_recon_vision`（effect_type → ID 参照）や Aftershock の `ench_cold_armor`（防具）で使われており、mod 開発で再利用頻度が高い
- 本modはクラフト可能な戦闘興奮剤を追加しつつ、この未実証パターンを最小構成で検証する

### 追加/変更内容（What）
- 含むもの:
  - 単体 enchantment 定義 `cst_ench_stim`（MELEE_DAMAGE / ATTACK_SPEED / PAIN の補正）
  - effect_type `cst_effect_stim`（`"enchantments": [ "cst_ench_stim" ]` で ID 参照）
  - 医薬品アイテム `cst_combat_stim`（copy-from: `adrenaline_injector`）
  - クラフトレシピ1件
- 含まないもの:
  - モンスター・マップ・NPC の追加
  - 既存アイテム・既存効果の改変
  - 離脱（クラッシュ）効果などの複雑な遅延処理

### ゲームプレイへの影響（Why）
- プレイヤーは興奮剤をクラフトし、数分間だけ近接戦闘を強化できる
- 既存システムとの関係: effect_type / enchantment / consume_drug は既存の仕組みのみを使用する

### 成功基準
- デバッグメニューで `cst_combat_stim` をスポーンでき、使用すると `cst_effect_stim` が付与される
- 効果中のみ近接ダメージ・攻撃速度・痛み耐性が変化する（キャラクターシートで確認）
- `rules/patterns/enchantment.md` に「単体 enchantment + ID 参照」の実証例として追記できる知見が得られる

### スコープ判断
- 新規 type 定義（`enchantment`）を含むため小規模mod省略条件を満たさず、本仕様書と設計書を作成する
