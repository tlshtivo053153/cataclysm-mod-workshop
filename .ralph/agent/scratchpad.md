# Scratchpad — 技術的負債リメディエーション

## 2026-09-14 P0-1 着手前メモ
- 目的: tech_debt_remediation_plan.md v2 の P0 から順次実施。今回は ONE task = P0-1 のみ。
- P0-1 根拠: `.github/workflows/ci.yml:5,7` が `branches: [master]` のため main で CI 未発火。実リモートは origin/main のみ（`git status` で main ahead 17 確認、HEAD 0065c74 と計画書の基準一致）。
- 変更: push / pull_request 両方の `branches: [master]` → `[main]`。2箇所のみ。独立・リスクなし。
- DoD: `grep -n "branches: \[main\]"` が2箇所。CI green は main 向け PR で確認（本イテレーションではローカルで YAML 構文確認のみ）。
- 計画: task spec:p0-1 を start → 編集 → grep 検証 → commit → close。P0-2〜P0-6/P1/P2 は次イテレーション以降。
- Confidence: 100（機械的2行変更）。決定ジャーナル不要。

## 2026-09-14 P0-1 完了メモ
- 変更: ci.yml:5,7 を [master]→[main]。commit 279afd3。
- 検証: grep で2箇所 [main] 確認、python yaml.safe_load OK、ruff/black green。
- 残: CI green 自体は main 向け PR で確認（初回 push は17+1コミット分が走る点に注意）。
- 次: P0-3（P0-2 の前提）が ready。P0-4/P0-6 は独立で並行可。

## 2026-09-14 P0-3 着手前メモ
- 目的: P0-3 のみ実施（ONE task）。P0-2 の前提で validate.sh / test_shell_integration.py 共有のため先行。
- 根拠: common.py:100-101 が <parent>/.bak を作成し、:168 rglob が .bak 配下も列挙 → 2回実行で .bak/.bak と .bak/*.1 が増殖（計画書 §P0-3 実測）。
- 変更: (1) _is_backup_path(base,p) 追加 — p.relative_to(base).parts に .bak 含む場合のみ除外（絶対パス全体判定だと祖先 .bak で全スキップする）。(2) process_directory:168 をフィルタ付きに。(3) backup位置は互換維持。(4) backup_file に世代コメント（無印=最古、.1,.2=新しい）+ output_dir!=input_dir で backup しない仕様を doc 化。(5) validate.sh に .bak 除外（find prune）。(6) validate_mods.py find_mod_dirs に .bak 除外（relative parts 判定）。
- DoD: 2回実行で (root/".bak"/".bak") 不存在、processor が .bak パスを受信しない、変換後 validate_mods.py が Duplicate を出さない。注意: .bak 内ファイル数不変は P1-8 の no-op 前提で P0-3 スコープ外。
- 計画: start 済 → common.py 編集 → validate.sh/mods 編集 → test_common.py 拡張 → pytest/ruff/black/mypy → commit → close。
- Confidence: 90（機械的除外+既定テスト拡張）。決定ジャーナル不要。

## 2026-09-14 P0-3 完了メモ
- 変更: common.py に _is_backup_path 追加 + rglob フィルタ、backup_file/process_directory に世代・in-place 仕様を doc 化。validate.sh は find prune、validate_mods.py find_mod_dirs は relative parts 除外。commit c473873。
- 検証: pytest 309 passed（+14）、ruff/black/mypy green、bash -n OK。adversarial: 祖先.bak配下の base は処理される（1件）、.bak のみ配置では No JSON files で exit 1。変更ファイルの C90 green。
- 残: .bak 内ファイル数不変は P1-8 の no-op 前提で対象外。次は P0-2（P0-3後直列）または独立な P0-4/P0-6。
- Backpressure: tests pass, lint pass, typecheck pass, audit pass, coverage pass, complexity 2, duplication pass, performance pass (2.94s), specs pass。

## 2026-09-14 P0-2 着手前メモ
- 目的: P0-2 のみ実施（ONE task）。P0-3 完了後の直列タスクで validate.sh / test_shell_integration.py を共有するため今実施。P0-4/P0-6 は独立で次回以降。
- 根拠: place_mod_for_test.sh:13 LINK_MODE=false がデフォルトコピー、:32-39 パス検証が rm より後、:61-80 -- なし・非原子的 cp、--dry-run なし。計画書§P0-2 仕様に従う。
- 変更: (1) LINK_MODE=true デフォルト、--copy/--dry-run 追加、--link 明示、併用 exit1。(2) MOD_NAME basename -- 検証、両辺 realpath -m、DEST 配下判定（セパレータ込み case）、SRC==DEST 拒否、相互包含拒否、macOS 非対応コメント。(3) copy 原子化（tmp.$$ + cp -a -- + 件数/modinfo 確認 + mv、trap 掃除）。(4) symlink は ln -s -- SRC_REAL。(5) rm/cp に --。(6) --dry-run は mkdir 前に表示 exit0。(7) 冪等 already placed exit0。(8) 同時修正: copy ラッパー --copy 委譲、validate.sh find -H、verification.md/AGENTS.md/check_mods ヒント更新、運用ルール明記。(9) TestPlaceModForTest 新設 + symlink 起点回帰。
- DoD: フラグなし→symlink、--copy→実体、異常系 exit1、dry-run 無変更、冪等 exit0、cp 失敗で旧 DEST 温存、find -H 回帰、bash -n OK、pytest/ruff/black/mypy green。
- Confidence: 85（shell 仕様追従、既定テスト拡張）。決定ジャーナル不要。

## 2026-09-14 P0-2 完了メモ
- 変更: place_mod を symlink デフォルト化 + --copy/--dry-run + パス検証（basename --、両辺 realpath -m、セパレータ込み case、相互包含拒否）+ copy 原子化（tmp.$$ + 件数/modinfo 検証 + mv、trap）+ 冪等 already placed。DEST_REAL は lexical 結合（既存 symlink の realpath 解決で prefix 判定が誤爆するバグをテストで検出・修正）。同時修正: copy ラッパー --copy 委譲、validate.sh find -H、verification.md/AGENTS.md/check_mods ヒント + 運用ルール。
- 検証: pytest 325 passed（test_shell 31 件含む）、ruff/black/mypy green、bash -n OK。adversarial: dry-run 無変更（snapshot 一致）、冪等 exit0、cp 失敗で旧 DEST 温存・tmp 残存なし、sibling mods_evil が誤ブロックされない、symlink 起点 validate 回帰。
- 残: 次は P0-4（P1）または P0-6（P2）。P0-5 は P0-2 完了で unblock。
- Backpressure: tests pass, lint pass, typecheck pass, audit pass, coverage pass, complexity n/a (shell), duplication pass, performance pass, specs pass。

## 2026-09-14 P0-4 着手前メモ
- 目的: P0-4 のみ実施（ONE task, P1）。P0-6/P0-5は次回。
- 根拠: convert_price.py:55-59 regexがJSON文脈無視で破壊、:68-69 非原子直書き、:38-73 共通処理の独自再実装。
- 変更: (1) NO_CONVERT_CONTEXTS配下は不変+警告。(2) int(bool除外)のみ変換、float・負は警告+不変。(3) 変更なし→Noneでskip。(4) format_price型注釈。(5) run_standard_pipeline統一。(6) copy_unchanged追加・伝搬。(7) 単一→既存dir対応。(8) 相互包含拒否。(9) missing inputをfailed=1に修正。
- Confidence: 85。決定ジャーナル不要。

## 2026-09-14 P0-4 完了メモ
- 変更: convert_priceをregex→再帰JSON変換（NO_CONVERT_CONTEXTS 6種は不変+警告、bool除外・float/負は警告+不変、変更なし→Noneでskip）。commonにcopy_unchanged/missing→failed/相互包含拒否/単一→既存dirを追加。test_common期待値更新、test_convert_priceをTestJsonConversionに改名し回帰拡充。
- 検証: pytest 350 passed（+25）、ruff/black/mypy green。adversarial: float 1.5不変・文字列内pattern不変・proportional不変+兄弟変換を確認。
- 残: 次はP0-6（P2）またはP0-5（P0-2完了でunblock済み）。
- Backpressure: tests pass, lint pass, typecheck pass, audit pass, coverage pass, complexity n/a, duplication pass, performance pass (3.81s), specs pass。

## 2026-09-14 P0-6 着手前メモ
- 目的: P0-6 のみ実施（ONE task, P2）。P0-5は次回。
- 根拠: remove_invalid_fields.py:39-48 がキー名一致のみで無条件 del。pipe_pistol items.json:18 の有効 "ammo": ["9mm"] を削除する破壊を実測再現済み（計画書§P0-6）。
- 監査（実測）: 28項目を `"field"\s*:` キー位置で external/cdda/data/json 全体に照合。magazine 172 / ammo 693 / sound_volume 17 / baby_egg 152 / charges_per_use 223 件の key-hit（itemgroups・vehicle loot・monster reproduction・trap vehicle_data・item 直接フィールド）。残り23項目は key-hit 0 → remove_always。bashing/cutting は値位置のみ（skill/verb）でキーとしては0件のため remove_always に残す。src/ は本環境に不存在（game install のみ）のため data/json + doc/JSON で代替監査。
- 変更: (1) invalid_fields.json を {"remove_always": [23件], "remove_by_type": {}} に。5フィールドは両方から除外（残す方向・安全側）。(2) InvalidFieldsConfig dataclass + 厳格スキーマ検証（legacy list 拒否・重複/空文字/overlap は ValueError→exit 1）。(3) 削除は remove_always 無条件 + by_type は dict の type 文字列一致時のみ。不一致・欠落・非文字列は警告+保持。(4) 既存テストは新シグネチャに更新（同一コミット、P0例外規定）。
- DoD: pipe_pistol の ammo 保持（実ファイル回帰）、5フィールド保持、真の無効削除継続、type欠落で不削除、不正フォーマットで exit 1、pytest/ruff/black green（mypy は ignore_errors 対象）。
- Confidence: 75（空 remove_by_type・legacy拒否は判断含む）→ DEC-001/DEC-002 を decisions.md に記録。
- 計画: scratchpad/decisions 記録 → json+py+test 編集 → pytest/ruff/black → adversarial（pipe_pistol 実ファイル + 不正config CLI exit1）→ commit → close。

## 2026-09-14 P0-6 完了メモ
- 変更: invalid_fields.json を {remove_always: 23件, remove_by_type: {}} に（magazine/ammo/sound_volume/baby_egg/charges_per_use を除外）。remove_invalid_fields.py に InvalidFieldsConfig + 厳格スキーマ検証（legacy list 拒否・重複/空文字/overlap/未知キーは ValueError→exit 1）+ 型ゲート削除（不一致・欠落・非文字列 type は警告+保持）。test は 7→37 件に拡充（実config回帰・pipe_pistol実ファイル・CLI exit1 含む）。commit 3d17526。
- 検証: pytest 380 passed（+30）、ruff/black/mypy green。adversarial: 実ファイルで ammo 保持+armor_bullet 削除を CLI で確認、legacy list は exit 1 パス。
- 残: 次は P0-5（README事実修正）。P0 全完了後は green 確認 → P1。
- Backpressure: tests pass, lint pass, typecheck pass, audit pass, coverage pass, complexity n/a, duplication pass, performance pass (4.11s), specs pass。
