## Mod仕様書: hedge_magic

### 背景・動機
- `SPELL` は base に 245 件、`magic_type` は mod 専用の型として存在するが、本プロジェクトでは未実装。MOD_INFO カテゴリ `magical` も未使用
- 既存の魔法mod（Magiclysm 等）はマナ基盤を前提とするため大規模になりやすい
- 本modは **STAMINA をエネルギー源とする自己完結型の魔法** を最小構成で追加し、magic_type / SPELL / 呪文書（BOOK）の実装ノウハウを蓄積する

### 追加/変更内容（What）
- 含むもの:
  - `magic_type` 1件（`hmg_hedge_magic`, energy_source: STAMINA）
  - `SPELL` 2件: 攻撃呪文 `hmg_thorn_dart` と自己強化呪文 `hmg_second_wind`
  - 呪文書アイテム `hmg_grimoire`（BOOK subtype, `use_action: learn_spell`）とそのレシピ
- 含まないもの:
  - マナ基盤・呪文クラス・職業・モンスターの追加
  - 独自スキル（base の魔法スキルは使わず、`spell_class: "NONE"` のクラスレス呪文とする）

### ゲームプレイへの影響（Why）
- プレイヤーは呪文書をクラフトして2つの呪文を習得し、スタミナを消費して行使できる
- 魔力（マナ）システムに依存しないため、既存modなしでも動作する

### 成功基準
- 呪文書を読む（使用する）と2呪文を習得できる
- 呪文一覧から詠唱でき、`hmg_thorn_dart` は対象にダメージ、`hmg_second_wind` は自身に `adrenaline` 効果を付与する
- Level2 を通過し、`magical` カテゴリのmodとして認識される

### スコープ判断
- 新規 type（`magic_type`）を含み、新規IDも7件（magic_type 1 + SPELL 2 + ITEM 1 + recipe 1 + 内部参照）のため、仕様書・設計書を作成する
