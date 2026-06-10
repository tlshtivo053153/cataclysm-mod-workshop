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

# 使用文字とその意味を表示（パレット + meaning アノテーション）
python3 mapgen_compiler.py -i <input.yml> --explain
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
| `--explain` | コンパイル後のグリッド上に出現する文字とその意味（パレット定義 + `meaning` アノテーション）を一覧表示する |

## DSL 構文

### 最小構成

最初の部屋は anchor として `(0, 0)` に自動配置される。座標指定は不要。

```yaml
entries:
  - om_terrain: "my_building"
    rooms:
      - id: "main"
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
| `rooms` | いいえ | 部屋定義のリスト（または dict） |
| `doors` | いいえ | ドア定義のリスト |
| `features` | いいえ | 部屋相対フィーチャー（または絶対座標フィーチャー） |
| `global` | いいえ | 絶対座標タイル |
| `canvas` | いいえ | エントリレベル: レイアウト用の `cols`/`rows` 指定（後述） |
| `layout` | いいえ | グリッド状の部屋配置マトリクス（後述） |
| `auto_doors` | いいえ | 隣接/包含する部屋間に自動ドア生成（デフォルト: `true`） |
| `default_door_char` | いいえ | 自動生成ドアの文字（デフォルト: `"+"`） |
| `no_door` | いいえ | 自動ドアを抑制する部屋ペアのリスト |

### 部屋 (rooms)

部屋の最小サイズは 2x2 以上を推奨。w=1 または h=1 の部屋は壁の描画が破綻し、
内部領域が存在しないためフィーチャー配置やドア接続が正しく動作しない。

**絶対座標 `x`/`y` は廃止されました。** 使用するとコンパイルエラーになります。
代わりに相対配置キー（`right_of` / `left_of` / `above` / `below` / `inside`）または
レイアウトグリッド（`layout` + `canvas.cols` / `canvas.rows`）を使用してください。

最初の部屋（anchor 部屋）には配置キーを指定する必要はなく、自動的に `(0, 0)` に配置されます。
2番目以降の部屋には必ずいずれかの相対配置キーを指定する必要があります。

**部屋の基本構文（リスト形式）:**

```yaml
rooms:
  - id: "living"
    w: 8        # 幅（壁含む、推奨 ≥ 2）
    h: 10       # 高さ（壁含む、推奨 ≥ 2）
    wall: "#"   # 壁文字
    floor: "."  # 床文字
```

**部屋の基本構文（dict 形式）— ルームIDをキーにしたマッピングでも記述可能:**

```yaml
rooms:
  living:
    w: 8
    h: 10
    wall: "#"
    floor: "."
```

#### 内寸指定 (inner_w / inner_h)

`w`/`h` の代わりに `inner_w`/`inner_h` で内寸を指定できる。
壁は自動で追加され `w = inner_w + 2`, `h = inner_h + 2` となる。

`inner_w` と `w` は同時指定不可。`inner_h` と `h` も同時指定不可。

```yaml
rooms:
  - id: "room"
    inner_w: 6  # 内寸幅6 → 実際の幅 w = 8 になる
    inner_h: 4  # 内寸高4 → 実際の高さ h = 6 になる
    wall: "#"
    floor: "."
```

`inner_w = 0` は有効（w = 2 になる）が、内部領域が存在しないためフィーチャーやドアを配置できません。
実用上は `inner_w` / `inner_h` ともに 1 以上を指定してください。負の値はエラー。

#### 相対配置

部屋同士の位置関係を宣言的に記述する。参照先の部屋は自身より先に定義されている必要がある（DAG）。

| キー | 説明 |
|---|---|
| `right_of` | 指定した部屋の右側に配置 |
| `left_of` | 指定した部屋の左側に配置 |
| `above` | 指定した部屋の上側に配置 |
| `below` | 指定した部屋の下側に配置 |
| `inside` | 指定した部屋の内側に配置（包含関係） |
| `align` | 隣接軸方向の配置揃え（デフォルト値は配置方向により異なる） |
| `gap` | 部屋間の間隔。0 以上（デフォルト: `0`） |

`align` の指定可能な値:

- `right_of` / `left_of` の場合（上下方向の揃え）: `top`, `bottom`, `center`, `middle`
  - デフォルト: `top`
- `above` / `below` の場合（左右方向の揃え）: `left`, `right`, `center`, `middle`
  - デフォルト: `left`
- `inside` の場合: `top`, `bottom`, `left`, `right`, `center`, `middle` のほか、
  `top-left` (`north-west`), `top-right` (`north-east`),
  `bottom-left` (`south-west`), `bottom-right` (`south-east`) などの複合指定が可能
  - デフォルト: `north`

```yaml
rooms:
  - id: "hall"
    inner_w: 4
    inner_h: 4
    wall: "#"
    floor: "."
  - id: "kitchen"
    right_of: "hall"    # hall の右隣に配置
    align: center       # 上下中央揃え
    w: 8
    h: 8
    wall: "#"
    floor: ","
  - id: "closet"
    inside: "kitchen"   # kitchen の内側に配置
    align: south-east   # 南東（右下）隅に配置
    w: 4
    h: 4
    wall: "="
    floor: "o"
```

`gap` で部屋間の間隔を空けることができる:

```yaml
rooms:
  - id: "left"
    w: 6
    h: 6
    wall: "#"
    floor: "."
  - id: "right"
    right_of: "left"
    gap: 2     # 2マス離して配置
    w: 6
    h: 6
    wall: "#"
    floor: "."
```

複数の配置キー（例: `right_of` と `left_of` の両方）を同時指定するとエラー。

`right_of`/`left_of`/`above`/`below`/`inside` は `x`/`y` 絶対座標や旧 `place` dict と併用不可。

### トップレベル canvas（サイズ変更）

デフォルトのキャンバスサイズは 24x24。
トップレベルに `canvas` キーを指定することで、カスタムサイズのキャンバスが使用できる。

```yaml
canvas:
  w: 32
  h: 32
entries:
  - om_terrain: "my_large_building"
    rooms: ...
```

制約:
- `w` と `h` は 2 以上
- 正方形である必要がある（`w == h`）

**これはエントリ内の `canvas`（`cols`/`rows` でレイアウトグリッドを定義するもの）とは別物です。** レイアウト用 `canvas` は次節で説明します。

### レイアウト (layout) — グリッド配置

エントリ内に `canvas`（`cols`/`rows`）と `layout` マトリクスを指定することで、
部屋をグリッド状に配置できる。セルを結合して大きな部屋を作ることも可能。

```yaml
entries:
  - om_terrain: "test_house"
    fill_ter: "t_floor"
    canvas:
      cols: [8, 8]      # 各列の幅
      rows: [6, 6]      # 各行の高さ
    layout:
      - [hall, kitchen]        # 1行目: hall, kitchen
      - [closet, bathroom]     # 2行目: closet, bathroom
    rooms:
      - id: hall
        inner_w: 6
        inner_h: 4
        wall: "#"
        floor: "."
      - id: kitchen
        inner_w: 6
        inner_h: 4
        wall: "#"
        floor: "="
      - id: closet
        inner_w: 6
        inner_h: 4
        wall: "#"
        floor: ","
      - id: bathroom
        inner_w: 6
        inner_h: 4
        wall: "#"
        floor: "o"
```

この例では、キャンバスを 2x2 のグリッドセルに分割し、各セルに部屋を割り当てている。
`hall` のサイズは `cols[0]` x `rows[0]`（8x6）、`kitchen` は 8x6、`closet` と `bathroom` は同様に 8x6 となる。

**セル結合**: 同じ room ID を複数セルに記述すると、セルが結合される:

```yaml
canvas:
  cols: [8, 8, 8]
  rows: [6, 6]
layout:
  - [hall, hall, storage]      # hall は列0-1 を結合（幅16）
  - [kitchen, living, storage]  # storage は列2 を結合（高さ12）
rooms:
  - id: hall
    inner_w: 14
    inner_h: 4
    wall: "#"
    floor: "."
  - id: storage
    inner_w: 6
    inner_h: 10
    wall: "#"
    floor: "="
  - id: kitchen    # 1セル占有（8x6）
    inner_w: 6
    inner_h: 4
    wall: "#"
    floor: ","
  - id: living     # 1セル占有（8x6）
    inner_w: 6
    inner_h: 4
    wall: "#"
    floor: "o"
```

**レイアウト使用時の注意:**

- `canvas.cols` / `canvas.rows` の各要素は正の整数でなければならない
- `cols` の合計幅、`rows` の合計高さはキャンバスサイズ（デフォルト 24）を超えてはならない
- `layout` マトリクスの各行の要素数は `cols` の要素数と一致する必要がある
- `layout` の行数は `rows` の要素数と一致する必要がある
- `layout` に出現する room ID はすべて `rooms` に定義されている必要がある
- `rooms` に定義した部屋はすべて `layout` マトリクス内に最低 1 セル割り当てられている必要がある
- レイアウト使用時は部屋の `w`/`h` を省略可能（セルから自動計算される）
- `w`/`h` を手動指定した場合、レイアウトから計算されたサイズと一致しなければエラー
- レイアウト使用時は相対配置キー（`right_of` 等）は不要であり、指定しても配置解決には使われない（ただし依存先部屋の存在チェックや循環参照チェックは引き続き行われる）
- `canvas`（`cols`/`rows`）と `layout` は必ずペアで使用する。片方だけだとエラー

### ドア (doors)

隣接する部屋間、または包含関係にある部屋間にドアを配置。

```yaml
doors:
  # 隣接する部屋間（ドア位置は自動計算）
  - from: "left"
    to: "right"
    char: "="
    offset: 2           # 重複区間内のオフセット（省略可: 中央）

  # position 指定（left / center / right）
  - from: "a"
    to: "b"
    char: "+"
    position: center    # 重複区間の中央に配置（offset と排他）

  # 包含関係（outer が inner を包含）
  - from: "outer"
    to: "inner"
    char: "="
    side: "south"       # north/south/east/west（デフォルト south）
    offset: 1           # 省略可
```

#### position vs offset

`position` と `offset` は相互排他（同時指定不可）。

| position | コンセプト | オフセット値 |
|---|---|---|
| `left` | 左端 | `0` |
| `center` | 中央 | `overlap_length // 2` |
| `right` | 右端 | `overlap_length - 1` |

例: 重複区間の長さが 5 のとき、`offset=2` は 3 番目（0-indexed で 2）の位置に配置される。

`side` は包含関係（外側の部屋 container と内側の部屋 inner）のドアにのみ有効。隣接する部屋間で `side` を指定するとエラー。

#### 自動ドア (auto_doors)

`auto_doors: true`（デフォルト）の場合、明示的な `doors` 定義がなくても、
コンパイラが隣接および包含する部屋間に自動的にドアを配置する。

```yaml
entries:
  - om_terrain: "test"
    fill_ter: "t_floor"
    auto_doors: true           # 明示指定（デフォルト true なので省略可）
    default_door_char: "="     # 自動ドアの文字（デフォルト "+"）
    rooms:
      - id: "left"
        w: 6
        h: 6
        wall: "#"
        floor: "."
      - id: "right"
        right_of: "left"
        w: 6
        h: 6
        wall: "#"
        floor: "."
```

自動ドアの生成順序:
1. 隣接部屋間（東西南北すべての辺をチェック）
2. 包含部屋間（south → north → east → west の順で最初に見つかった辺に配置）

以下の場合、自動ドアは生成されない:
- 同じ部屋ペアに明示的な `doors` 定義がすでにある
- `no_door` リストで抑制されている
- 重複区間（overlap）が 2 未満でドアを配置できない
- `gap` が 1 以上あり部屋が隣接していない

#### 自動ドア抑制 (no_door)

特定の部屋ペア間の自動ドアを抑制する:

```yaml
no_door:
  - [main, closet]    # main と closet 間には自動ドアを生成しない
  - [main, bathroom]
```

### フィーチャー (features)

部屋内の相対座標、またはキャンバス絶対座標にタイルを配置。

#### 部屋相対フィーチャー

```yaml
features:
  - room: "living"
    tiles:
      - char: "H"       # 文字
        x: 1            # room 左上からの相対X
        y: 1            # room 左上からの相対Y
        meaning: "heater"  # 意味アノテーション（省略可）
      - char: ">"
        x: 6
        y: 7
```

#### 絶対座標フィーチャー（room キー省略）

`room` キーを省略すると、キャンバス上の絶対座標として扱われる。
グリッド範囲内（0 〜 canvas_size-1）である必要がある。

```yaml
features:
  - tiles:                    # room なし → 絶対座標
      - char: "^"
        x: 0
        y: 0
        meaning: "roof access"
```

#### meaning フィールド

`meaning` フィールドは `--explain` 出力およびパレット照合に使用される任意の文字列アノテーション。

- `--explain` フラグ使用時に、文字とその意味の一覧が表示される
- パレットに同じ文字の意味が定義されている場合、`meaning` の値がパレット定義と一致するか検証される
- パレット定義と矛盾する場合、`meaning_conflict` 警告が出力される
- どのパレットにも定義がない場合、`meaning_not_in_palette` 警告が出力される

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
本バリデーションは、両方のエントリに該当する階段文字が存在する場合のみ実行される。
片方にしか存在しない階段（例: 上階に `>` があるが下階に `<` がない）は許容される。

**階段位置バリデーションについて**: 複数階層を定義する場合、エントリは正しいz-order（屋上 → 地上 → 地下）で記述することを推奨。階段バリデーションはエントリの記述順を z-order と見なすが、チェックは隣接エントリ間でのみ行われる。

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

DSL で予約済みのキー以外（`om_terrain`, `fill_ter`, `palette`, `rooms`, `doors`, `features`,
`global`, `canvas`, `layout`, `auto_doors`, `default_door_char`, `no_door` 以外）は
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
| 部屋範囲外 | room がキャンバス外（オーバーフロー方向と対策ヒントが表示される） |
| ドア不可 | from/to の部屋が隣接も包含もしていない |
| フィーチャー範囲外 | feature 座標が room 内にない、またはキャンバス外 |
| 部屋ID重複 | rooms 内で id が重複 |
| 部屋サイズ不正 | w < 1 または h < 1（`inner_w` が負もエラー） |
| 部屋の部分重複 | 2部屋が包含でも隣接でもなく重なっている |
| ドア位置不正 | 計算されたドア位置が wall_char でない |
| ドア重複不足 | 隣接辺/内壁の重複長が 2 未満 |
| 階段位置不一致 | 階層間で階段文字の座標が一致しない |
| 絶対座標 x/y 使用 | `x`/`y` は廃止。相対配置キーまたはレイアウトを使用すること |
| 旧 place dict 使用 | `place` は廃止。相対配置キーを使用すること |
| 配置キー不足 | 最初の部屋以外に相対配置キーがない（またはレイアウト未使用） |
| 循環参照 | 部屋の相対配置が循環依存している |
| 参照先不在 | right_of 等で指定した部屋が存在しない |
| 内寸/外寸の衝突 | w と inner_w（または h と inner_h）の同時指定 |
| 複数配置キー | right_of / left_of / above / below / inside の複数指定 |
| 配置キー + x/y 混在 | 新配置キーと x/y 絶対座標の併用 |
| gap 負値 | gap が 0 未満 |
| position + offset 同時指定 | ドアに position と offset の両方を指定 |
| position 値不正 | position が left/center/right 以外 |
| side が隣接ドアに指定 | side は包含ドアのみ有効 |
| layout 系エラー | cols/rows が空、各行のセル数不一致、不明 room ID 参照、layout 未割当 room、w/h の layout 計算値との不一致、キャンバス超過 |
| canvas 関連エラー | w/h が 2 未満、正方形でない、w/h 欠落、`cols`/`rows` と `layout` の不一致 |

### 警告（継続）

| 警告コード | 内容 |
|---|---|
| `undefined_palette_char` | 使用文字がパレットに定義されていない |
| `unreachable_cells` | BFSで到達不能な通過可能タイルを検出 |
| `invisible_door` | ドア文字が壁文字と同一 |
| `passthrough_collision` | パススルーキーがコンパイラ生成キーと衝突 |
| `no_entry_point` | 入口点なし（階段も周辺通過可能セルもなし）— 密封マップは合法だが注意 |
| `meaning_not_in_palette` | feature の `meaning` がどのパレットにも定義されていない |
| `meaning_conflict` | feature の `meaning` がパレット定義と矛盾している |

## 構文移行ガイド（旧 `x`/`y` 絶対座標からの移行）

旧バージョンでは部屋の位置を `x`/`y` 絶対座標で指定していましたが、
現在の DSL では相対配置またはレイアウトグリッドを使用します。

### 隣接する部屋の移行例

**旧:**
```yaml
rooms:
  - id: "a"
    x: 0
    y: 0
    w: 8
    h: 8
    wall: "#"
    floor: "."
  - id: "b"
    x: 8
    y: 0
    w: 8
    h: 8
    wall: "#"
    floor: "."
```

**新:**
```yaml
rooms:
  - id: "a"            # anchor — 座標指定不要
    w: 8
    h: 8
    wall: "#"
    floor: "."
  - id: "b"
    right_of: "a"      # a の右隣に配置
    w: 8
    h: 8
    wall: "#"
    floor: "."
```

### 上下配置の移行例

**旧:**
```yaml
rooms:
  - id: "top"
    x: 3
    y: 0
    w: 6
    h: 6
    wall: "#"
    floor: "."
  - id: "bottom"
    x: 3
    y: 6
    w: 6
    h: 6
    wall: "#"
    floor: "."
```

**新:**
```yaml
rooms:
  - id: "top"
    w: 6
    h: 6
    wall: "#"
    floor: "."
  - id: "bottom"
    below: "top"       # top の下に配置
    w: 6
    h: 6
    wall: "#"
    floor: "."
```

### グリッド配置への移行

複数の部屋をグリッド状に配置したい場合は、レイアウトグリッドが推奨:

**旧（絶対座標）:**
```yaml
rooms:
  - id: "a"
    x: 0
    y: 0
    w: 8
    h: 6
    wall: "#"
    floor: "."
  - id: "b"
    x: 8
    y: 0
    w: 8
    h: 6
    wall: "#"
    floor: "."
  - id: "c"
    x: 0
    y: 6
    w: 8
    h: 6
    wall: "#"
    floor: "."
  - id: "d"
    x: 8
    y: 6
    w: 8
    h: 6
    wall: "#"
    floor: "."
```

**新（レイアウト）:**
```yaml
entries:
  - om_terrain: "my_building"
    canvas:
      cols: [8, 8]
      rows: [6, 6]
    layout:
      - [a, b]
      - [c, d]
    rooms:
      - id: a
        inner_w: 6
        inner_h: 4
        wall: "#"
        floor: "."
      - id: b
        inner_w: 6
        inner_h: 4
        wall: "#"
        floor: "."
      - id: c
        inner_w: 6
        inner_h: 4
        wall: "#"
        floor: "."
      - id: d
        inner_w: 6
        inner_h: 4
        wall: "#"
        floor: "."
```
