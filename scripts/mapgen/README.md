# Mapgen DSL コンパイラ

## 概要

CDDA の mapgen JSON を YAML DSL で記述し、コンパイルするツール。
矩形の部屋配置・ドア接続・フィーチャー配置を宣言的に記述できる。

## CLI 使用方法

```bash
cd scripts

# 単一ファイルコンパイル
python3 mapgen_compiler.py -i <input.yml> -o <output.json>

# バリデーションのみ（JSON出力なし）
python3 mapgen_compiler.py -i <input.yml> --check-only

# mod ディレクトリ内の全 DSL をバッチコンパイル
# data/mapgen_dsl/*.yml → data/mapgen/*.json に出力
python3 mapgen_compiler.py --mod-dir ../mods/small/<mod_name>/

# 外部パレット指定（単一ファイル）
python3 mapgen_compiler.py -i <input.yml> --palette-dir ../mods/<mod_name>/data/palettes/

# 外部パレット指定（複数ディレクトリ）
python3 mapgen_compiler.py -i <input.yml> --palette-dir path1/ path2/

# バックアップなしで上書き
python3 mapgen_compiler.py -i <input.yml> -o <output.json> --no-backup
```

オプション:
| オプション | 説明 |
|---|---|
| `-i, --input` | 入力 YAML ファイル |
| `-o, --output` | 出力 JSON ファイル（省略時は `.yml` → `.json`） |
| `--check-only` | コンパイル検証のみ、ファイル出力しない |
| `--mod-dir` | mod ディレクトリ指定（バッチコンパイル） |
| `--dsl-dir` | バッチ時の DSL ソースディレクトリ（デフォルト: `data/mapgen_dsl`） |
| `--palette-dir` | 追加パレットディレクトリ（複数指定可）。`--mod-dir` 使用時は自動で `{mod_dir}/data/palettes/` も検索 |
| `--backup / --no-backup` | バックアップ作成の有無（デフォルト: 有効） |

## DSL 構文

### 最小構成

```yaml
entries:
  - om_terrain: "my_building"
    rooms:
      - id: "main"
        x: 5
        y: 5
        w: 8
        h: 8
        wall: "#"
        floor: "."
```

### 基本要素

| キー | 必須 | 説明 |
|---|---|---|
| `om_terrain` | はい | OMT 地形ID（`_north` などのサフィックスは付けない） |
| `fill_ter` | いいえ | 外周の地形（デフォルト: `t_floor`） |
| `palette` | いいえ | 使用パレット名のリスト（YAML DSL キーは単数形 `palette`。CDDA JSON 出力では `palettes`（複数形）になる。これは CDDA ゲーム側の JSON フィールド名に合わせた意図的な設計） |
| `rooms` | いいえ | 部屋定義のリスト |
| `doors` | いいえ | ドア定義のリスト |
| `features` | いいえ | 部屋相対フィーチャー |
| `global` | いいえ | 絶対座標タイル |

### 部屋 (rooms)

部屋の最小サイズは 2x2 以上を推奨。w=1 または h=1 の部屋は壁の描画が破綻し、
内部領域が存在しないためフィーチャー配置やドア接続が正しく動作しない。

```yaml
rooms:
  - id: "room_id"
    x: 3        # 左上X座標 (0-23)
    y: 4        # 左上Y座標 (0-23)
    w: 8        # 幅（壁含む、推奨 ≥ 2）
    h: 10       # 高さ（壁含む、推奨 ≥ 2）
    wall: "#"   # 壁文字
    floor: "."  # 床文字
```

### ドア (doors)

隣接する部屋間、または包含関係にある部屋間にドアを配置。

```yaml
doors:
  # 隣接する部屋間（ドア位置は自動計算）
  - from: "left"
    to: "right"
    char: "="
    offset: 2         # 省略可: 重複区間内のオフセット

  # 包含関係（outer が inner を包含）
  - from: "outer"
    to: "inner"
    char: "="
    side: "south"     # 省略可（デフォルト south）: north/south/east/west
    offset: 1         # 省略可
```

### フィーチャー (features)

部屋内の相対座標にタイルを配置。

```yaml
features:
  - room: "living"
    tiles:
      - char: "H"    # 文字
        x: 1         # room 左上からの相対X
        y: 1         # room 左上からの相対Y
      - char: ">"
        x: 6
        y: 7
```

### グローバルタイル (global)

グリッド絶対座標にタイルを配置。範囲指定可能。

```yaml
global:
  - char: ","
    x: 0          # 単一座標
    y: 0
  - char: ","
    x: [0, 23]    # 範囲 [start, end]
    y: [0, 23]
```

### 複数階層

`entries` に複数のエントリを記述することで地上/屋上/地下を一括定義できる。
階段文字（`<`, `>`, `*`, `^`）の位置がエントリ間で一致しない場合コンパイルエラー。

**重要**: 複数階層を定義する場合、エントリは上から下の順序（屋上 → 地上 → 地下）で記述すること。階段バリデーションはエントリの記述順を z-order と見なして隣接エントリ間の整合性をチェックする。

```yaml
entries:
  - om_terrain: "my_building_roof"
    # ... 屋上（最上階）
  - om_terrain: "my_building"
    # ... 地上階
  - om_terrain: "my_building_under"
    # ... 地下（最下階）
```

### パススルーフィールド

`om_terrain`, `fill_ter`, `palette`, `rooms`, `doors`, `features`, `global` 以外の未知キーは
そのまま JSON の `object` に透過出力される。`rows` は DSL が生成するため、パススルーに `rows` を指定すると上書きされてしまう点に注意。

コンパイラが生成するキー（`fill_ter`, `rows`, `palettes`）とパススルーキーが衝突した場合、
コンパイルエラーではなく**警告**が出力される（CDDA がパススルー値での上書きを受理するため）。
ただし、`rows` キーはグリッドデータ自体を上書きするため、意図しない動作の原因になる。

```yaml
entries:
  - om_terrain: "my_building"
    place_loot: [...]    # パススルー: JSON にそのまま出力
    comment: "any key"   # パススルー
```

## コンパイル時検証

### エラー（コンパイル停止）

| 検証項目 | 条件 |
|---|---|
| 部屋範囲外 | room が 24x24 をはみ出す |
| ドア不可 | from/to の部屋が隣接も包含もしていない |
| フィーチャー範囲外 | feature 座標が room 内にない、またはグリッド外 |
| 部屋ID重複 | rooms 内で id が重複 |
| 部屋サイズ不正 | w < 1 または h < 1 |
| 部屋の部分重複 | 2部屋が包含でも隣接でもなく重なっている |
| ドア位置不正 | 計算されたドア位置が wall_char でない |
| ドア重複不足 | 隣接辺の重複長が2未満 |
| 階段位置不一致 | 階層間で階段文字の座標が一致しない |

### 警告（継続）

| 警告 | 内容 |
|---|---|
| `undefined_palette_char` | 使用文字がパレットに定義されていない |
| `unreachable_cells` | BFSで到達不能な通過可能タイルを検出 |
| `invisible_door` | ドア文字が壁文字と同一 |
| `passthrough_collision` | パススルーキーがコンパイラ生成キーと衝突 |
| `no_entry_point` | 入口点なし（階段も周辺通過可能セルもなし）— 密封マップは合法だが注意 |
