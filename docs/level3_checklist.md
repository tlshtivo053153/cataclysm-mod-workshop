# Level3 検証チェックリスト (機械可読)

> 由来: `mods/small/{combat_stim,bone_armor,hedge_magic}/design.md` の「テスト手順」「完了条件」節からの転記 (2026-09-14)。
> 運用: Level1/Level2 は CI・手動で済み (`[x]`)、Level3 はゲーム内手動確認のため未実行 (`[ ]`)。
> 未実行項目の追跡: `issue.md #9` (新規3modのLevel3検証が未実行) と紐付け。本ファイルの `[ ]` がゼロになったら #9 を解決済みに更新する。
> 自動化は本タスク (C-3) の非目標。実行時は1行ずつ `[ ]` → `[x]` + 日付・確認者・結果を記録する。
> 形式: 1チェック項目=1行 `- [ ] ID: 手順`。ID は `<mod>-L<level>-<連番>` で機械可読 (`grep -c "^- \[ \]"` で未実行件数を取得可)。

## combat_stim (`combat_stim`)

設計書: `mods/small/combat_stim/design.md`。成功基準: `cst_combat_stim` 使用で `cst_effect_stim` が付与され、enchantment の補正が反映される。

- [x] combat_stim-L1-01: `bash scripts/validate.sh mods/small/combat_stim/` (Level1 JSON構文)
- [x] combat_stim-L2-01: `bash scripts/place_mod_for_test.sh --link mods/small/combat_stim/` (配置)
- [x] combat_stim-L2-02: `bash scripts/check_mods.sh --check-errors combat_stim` (Level2、ERROR なし)
- [ ] combat_stim-L3-01: CDDA 起動 → デバッグメニューで `cst_combat_stim` をスポーンする (→ `issue.md #9`)
- [ ] combat_stim-L3-02: `cst_combat_stim` を使用し `cst_effect_stim` が付与されることを確認する (→ `issue.md #9`)
- [ ] combat_stim-L3-03: キャラクターシートで enchantment 補正 (MELEE_DAMAGE +2 / ATTACK_SPEED -10 / PAIN ×-0.5) の反映を確認する (→ `issue.md #9`)

## bone_armor (`bone_armor`)

設計書: `mods/small/bone_armor/design.md`。成功基準: スポーン・装備・クラフトが正常動作し、Level2 を通過する。

- [x] bone_armor-L1-01: `bash scripts/validate.sh mods/small/bone_armor/` (Level1 JSON構文)
- [x] bone_armor-L2-01: `bash scripts/place_mod_for_test.sh --link mods/small/bone_armor/` (配置)
- [x] bone_armor-L2-02: `bash scripts/check_mods.sh --check-errors bone_armor` (Level2、ERROR なし)
- [ ] bone_armor-L3-01: CDDA 起動 → デバッグメニューで `bna_bone_cuirass` / `bna_bone_helmet` / `bna_bone_armguards` の3点をスポーンする (→ `issue.md #9`)
- [ ] bone_armor-L3-02: 3点を装備し、防護値・部位カバー (`bna_bone_cuirass` は torso のみ) を確認する (→ `issue.md #9`)
- [ ] bone_armor-L3-03: クラフトメニューで3レシピの表示・作成可否を確認する (→ `issue.md #9`)

## hedge_magic (`hedge_magic`)

設計書: `mods/small/hedge_magic/design.md`。成功基準: 呪文書から呪文を習得・詠唱でき、Level2 を通過する。

- [x] hedge_magic-L1-01: `bash scripts/validate.sh mods/small/hedge_magic/` (Level1 JSON構文)
- [x] hedge_magic-L2-01: `bash scripts/place_mod_for_test.sh --link mods/small/hedge_magic/` (配置)
- [x] hedge_magic-L2-02: `bash scripts/check_mods.sh --check-errors hedge_magic` (Level2、ERROR なし)
- [ ] hedge_magic-L3-01: CDDA 起動 → デバッグメニューで `hmg_grimoire` を入手する (→ `issue.md #9`)
- [ ] hedge_magic-L3-02: `hmg_grimoire` を使用し `hmg_thorn_dart` / `hmg_second_wind` を習得する (→ `issue.md #9`)
- [ ] hedge_magic-L3-03: 習得した2呪文を詠唱し、効果 (stab ダメージ / `adrenaline` 付与) を確認する (→ `issue.md #9`)

## 実行ログ

| 日付 | 項目ID | 結果 | 備考 |
|---|---|---|---|
| (未実行) | | | Level3 はすべて未実行。実行時に追記する |
