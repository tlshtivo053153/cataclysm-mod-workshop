# 検証ツール

このファイルは、CDDA mod開発で使う検証・チェックツールの詳細手順をまとめたものです。
簡易な概要は `CORE.md` を、初級者向け補足は `hints_basic.md` を参照してください。

---

## Level1: JSON構文チェック（validate.sh）

`scripts/validate.sh` は mod 内の全JSONファイルに対して構文チェックを行います。

### 特徴

| 項目 | 内容 |
|---|---|
| 入力 | ディレクトリパス（デフォルト: カレントディレクトリ） |
| 前提条件 | Python 3（`json.tool`） |
| 実行時間 | 1秒未満 |
| 検出範囲 | JSON構文エラーのみ（末尾カンマ、括弧の対応など） |

### 使い方

```bash
# modディレクトリ内で実行
bash scripts/validate.sh .

# または特定のmodディレクトリを指定
bash scripts/validate.sh mods/small/my_mod/
```

### CI用一括検証

```bash
# 全modを一括検証（mods/ 以下を再帰走査: modinfo.json列挙 + ID重複チェック + Level1 JSON構文）
python scripts/validate_mods.py

# 特定ディレクトリ配下のmodを検証
python scripts/validate_mods.py --base-dir /path/to/mods

# CIログ削減用 (F-1: per-file OKとヘッダ抑制、エラーと最終サマリは表示)
python scripts/validate_mods.py --quiet
```

### 頻度

**編集のたびに実行してください。** 軽量なので頻繁に回すことを推奨します。

---

## Level2自動: mod読み込みチェック（check_mods.sh）

`scripts/check_mods.sh` は CDDA本体の `--check-mods` 機能を使い、modがゲームエンジンに正しく読み込まれるかを検証します。

### 特徴

| 項目 | 内容 |
|---|---|
| 入力 | `modinfo.json` 内の `"id"` フィールドの値（mod_id） |
| 前提条件 | `external/cdda/cataclysm-tiles` バイナリ + modが `external/cdda/mods/` に配置済み |
| 実行時間 | 最大90秒（タイムアウト設定あり、`--timeout` で変更可能） |
| 検出範囲 | 依存解決・copy-from存在・必須フィールド・型不一致などCDDAエンジンレベルのエラー |

### 前提条件の確認

1. `external/cdda/cataclysm-tiles` が存在することを確認
2. modが `external/cdda/mods/` に配置されていることを確認（配置手順は後述）

### 完全な手順（5ステップ）

```bash
# Step 1: JSON構文チェック（Level1）
bash scripts/validate.sh mods/small/my_mod/

# Step 2: modをCDDAのmods/に配置（デフォルトsymlink。--link 明示も可）
bash scripts/place_mod_for_test.sh mods/small/my_mod/

# Step 3: mod_idを確認
cat mods/small/my_mod/modinfo.json | grep '"id"'
# 出力例: "id": "my_mod"

# Step 4: CDDA組み込みチェック（Level2）
bash scripts/check_mods.sh my_mod
# 隔離実行（推奨）: shared state汚染を防ぐ
bash scripts/check_mods.sh --isolated my_mod
# debug.log のERRORも検出する:
bash scripts/check_mods.sh --isolated --check-errors my_mod

# Step 5: エラー確認（debug.log）
cat external/cdda/config/debug.log
```

### check_mods.sh オプション

| オプション | 説明 |
|---|---|
| `--isolated` | 一時作業ディレクトリを使用し、共有状態（debug.log, flexcache）を汚染しない。並列実行が必要な場合に推奨 |
| `--check-errors` | CDDAの終了コードに加え、debug.log内のERROR行の有無も検証（ERRORがあればexit 4） |
| `--timeout N` | タイムアウト秒数を変更（デフォルト: 90秒） |

### mod_id の確認方法

`check_mods.sh` に渡すのは **ディレクトリ名ではなく、`modinfo.json` 内の `"id"` フィールドの値** です。

```bash
# modinfo.json から id を抽出
grep '"id"' mods/small/my_mod/modinfo.json
```

**注意**: `place_mod_for_test.sh` が作成するリンク名はソースディレクトリのベース名です。ディレクトリ名と `modinfo.json` の `id` が一致しない場合があります。その場合は、`id` の値を `check_mods.sh` に渡してください。

例:
- ソースディレクトリ: `mods/small/MyCoolMod/` → リンク名: `MyCoolMod`
- modinfo.json の id: `"id": "my_cool_mod"` → 実行: `bash scripts/check_mods.sh my_cool_mod`

### 検出できるエラー

- `copy-from target not found` — 親IDが存在しない（スペルミスや依存mod未読み込み）
- `missing required field` / `missing mandatory member` — 必須フィールドの欠落
- `unknown type` — typeフィールドのスペルミス
- 依存modの解決失敗

### 検出できないエラー

- JSON構文エラー（`validate.sh` で事前にチェック）
- ゲーム内での実際の動作不具合（Level3で確認）
- バランス問題

### debug.log の読み方

`check_mods.sh` は実行前に `external/cdda/config/debug.log` をクリアします（`--isolated` 使用時は一時ディレクトリに独立したdebug.logを作成）。
つまり、実行後の `debug.log` の内容は**すべてそのセッションのエラー**です。

```bash
# 最後のセッションのERROR行だけ確認
cat external/cdda/config/debug.log | grep ERROR
```

- `-----------------------------------------` でセッションが区切られます（最新セッションのみ読めばよい）
- `Stale game data detected` 警告は無視してよい

### 注意点

- **タイムアウト**: 90秒で強制終了します。大規模modや多数の依存がある場合は時間がかかることがあります。環境が遅い場合は `--timeout N` で延長してください
- **パフォーマンス**: `validate.sh` と比べて重い処理です。マイルストーン毎（機能完成時、PR前など）に実行してください
- **mod配置の更新**: ソースを修正したら、symlinkなら自動反映、コピーなら再度 `place_mod_for_test.sh` を実行してください
- **同時実行**: 共有状態を使用する場合（`--isolated` なし）は並列実行不可。`--isolated` を使用すれば並列実行が可能です。

---

## mod配置（place_mod_for_test.sh）

modは `mods/<size>/<mod_name>/` に開発し、CDDAの `--check-mods` で検証するために `external/cdda/mods/` に配置する必要があります。

### 使い方

```bash
# symlinkで配置（デフォルト。--link 明示も可。ソース修正が即時反映）
bash scripts/place_mod_for_test.sh mods/small/my_mod/

# コピーで配置
bash scripts/place_mod_for_test.sh --copy mods/small/my_mod/

# 変更予定のみ表示（何も変更しない）
bash scripts/place_mod_for_test.sh --dry-run mods/small/my_mod/
```

既存のリンク/ディレクトリ/ファイルがあれば確認の上で削除してから配置し直します（対話時はプロンプト、非対話時は exit 2 で `--force` を要求）。
既に同じソースへのリンクなら `Already placed` で何もせず成功します。

### 運用ルール

- mod のソース編集は repo の `mods/` 側で行ってください。`external/cdda/mods` の symlink 越しに変換スクリプトを実行すると repo の `mods/` を直接書き換えます。
- 変換は repo の `mods/<mod>` を入力に実行してください（`external/cdda/mods` 経由で実行しない）。
- 変換前に `git status --porcelain -- mods/<mod>` が空であることを確認してください。
- 上書き配置は不可逆です（`--force` は確認なしに DEST を削除）。既存配置がある場合は先に `--dry-run` で計画を確認してください。

### 非推奨の旧ラッパー

`link_mod_for_test.sh` と `copy_mod_for_test.sh` は `place_mod_for_test.sh` に統合されました。旧ラッパーは下位互換性のために残されていますが、新規の利用は推奨しません。2026-12-31に削除予定です（ラッパー側の表記も同一）。

---

## 検証フローまとめ

```
編集中 ──→ validate.sh（Level1: JSON構文）──→ 修正 ──→ 編集中
              ↑                                        |
              └────────────────────────────────────────┘
                （頻繁に実行、1秒未満）

機能完成時 ──→ place_mod_for_test.sh ──→ check_mods.sh（Level2: 読み込み）
                                               ↓
                                         debug.log確認
                                               ↓
                                         エラーあれば修正
                                               ↓
                                         エラーなし ──→ CDDA起動（Level3: 動作確認）
```

---

## Exitコード・エラー出力規約 (E-6正本)

エラー・usage出力は stderr (`>&2`) に統一する。正常系の進捗 (`OK:`、`All files passed`、`Already placed` 等) および対話プロンプト (`WARNING: ...`/`Aborted.`) は stdoutのままとする。

| ツール | 0 | 1 | 2 | 3 | 4 |
|---|---|---|---|---|---|
| `validate.sh` | 全JSON正常 | 構文エラー/JSONなし | — | — | — |
| `place_mod_for_test.sh` | 配置成功 (冪等・`Aborted.`含む) | usage/処理エラー (検証失敗・コピー失敗等) | 非対話で要`--force`のみ | — | — |
| `check_mods.sh` | 通過 | usage/前提条件不備 | CDDA check失敗 | タイムアウト | `--check-errors`時のdebug.log ERROR |
| Python CLI群 (E-1) | 成功 | 処理エラー | usage (argparse・mapgen欠損等) | — | — |

`.bak` 除外は `scripts/common.py:_is_backup_path` に一本化する (base相対で `.bak` 成分または末尾 `~`/`~数字` (`data.json~`、`data.json~1`、`mydir~`) を含むパスのみ除外し、baseの先祖が `.bak` でも除外しない。旧 `.bak` ディレクトリと新 `~` 命名の両方を除外する)。`validate.sh` の `find -type d \( -name .bak -o -name '*~' \) -prune` はそのshell等価実装、`validate_mods.py:find_mod_dirs/_iter_json_objects` は同関数を直接呼ぶ。

## 移行メモ (2026-09-14 破壊的変更)

- デフォルトsymlink化 (`place_mod_for_test.sh`): デフォルトがコピー→symlinkに反転。symlink越しの変換は repo 直書きになるため運用ルール (上記) を確認すること。
- mod配置の厳格化: ソースに `modinfo.json` がない場合は配置を拒否 (exit 1)。modディレクトリ自体 (modinfo.json を含む層) を指定すること。
- exit/stderr契約 (E-1/E-6): Python CLIは `main() -> int + sys.exit` に統一 (import利用は戻り値判定に移行)。`validate.sh` のNG系・`place` の非対話要`--force` (exit 2) は stdoutパーサを壊すため `2>&1` 合流や `exit==1` 判定を見直すこと。`summarize_debug_log.py --top` 負数は usage として exit 2、`--top 0` は human出力のみ `No errors shown (top=0; N group(s) hidden)` を返し (jsonは `[]`)、空結果は human `No errors found.` (jsonは `[]`)。
- 旧ラッパー廃止予告 (E-5): `link_mod_for_test.sh` / `copy_mod_for_test.sh` は `place_mod_for_test.sh` (デフォルトsymlink、`--copy` でコピー) に置換。2026-12-31に削除予定（上記「非推奨の旧ラッパー」節と同一）。
- Linux/CI専用化 (F-1): `place_mod_for_test.sh` はGNU coreutils必須。macOSでは `grealpath` 等の代替かLinux環境を用意すること。
