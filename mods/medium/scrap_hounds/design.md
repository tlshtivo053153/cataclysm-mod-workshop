## Mod設計書: Scrap Hounds（廃材犬）

### 仕様書から継承
- **目的**: 廃材を漁る野良犬の群れを追加する。既存の `scrap_zombie` はゾンビ系だが、本modは生きた野生犬として「狩る／狩られる」体験を作る。野良犬encounterに装甲・群れ・リーダーを持つ危険な個体を低確率で混ぜる。
- **スコープ**:
  - 含むもの: MONSTER 3種＋死亡ドロップ 1件＋`GROUP_STRAY_DOGS` へのsame-ID merge。解体は親 `dog_with_skull_fur` を維持。
  - 含まないもの: 新mapgen、NPC、シナリオ、職業、新モンスターシステム、既存モンスターの改変、独自の進化系統（`upgrades` なし）、`GROUP_DOGS` への注入。
- **成功基準**: 3種がデバッグスポーンでき、hound/maulerは群れ、alphaは単独で出現。解体で肉・皮・骨、死亡ドロップでスクラップ。Level1/2通過、Level3で出現・戦闘・解体・ドロップ・セーブ/ロード確認。

### ターゲットバージョン
- CDDA: 0.I RC（確認checkout: `f044a1c7c4f6184c129ce6dacff99ea573df326a`。計画書の `46730b6` と異なるため本設計のgrep結果を正とする）

### 依存関係
- 依存mod: dda（必須）

### 使用予定ID一覧
| 種別 | ID | copy-from | 説明 |
|---|---|---|---|
| MONSTER | `mon_sh_scrap_hound` | `mon_coyote` | 群れ型。基本個体 |
| MONSTER | `mon_sh_scrap_mauler` | `mon_sh_scrap_hound` | 装甲型。houndの上位 |
| MONSTER | `mon_sh_scrap_alpha` | `mon_sh_scrap_mauler` | 希少なリーダー。maulerの上位 |
| item_group | `sh_hound_death_drops` | —（新規、`subtype: "collection"`） | 死亡ドロップ。`scrap` / `steel_chunk` |
| monstergroup | `GROUP_STRAY_DOGS` | same-ID merge（新規IDではない） | 野良犬グループに低weightで注入 |

命名規約: 全新規IDは `sh_` 接頭辞（モンスターは `mon_sh_*`）。`#` 不使用、英小文字・数字・アンダースコアのみ。

### 親を `mon_coyote` にする理由
- 野生犬で `petfood` を持たず、ペット化・`DOGFOOD` / `CANPLAY` / `PET_MOUNTABLE` の継承を避けられる。`mon_dog` は使わない。

### `mon_coyote` 継承の決定表
| フィールド | 決定 |
|---|---|
| `name` / `description` / `hp` / `speed` / `melee_*` / `armor` / `volume` / `weight` | 上書き |
| `aggression` / `morale` / `aggro_character` / `anger_triggers` | 群れとして敵対する値に上書き（親は `aggression` 未定義・`morale` 20のため必須） |
| `default_faction` | `coyote` を維持（野生犬扱い。`dog` にしない） |
| `species` | `MAMMAL` 固定 |
| `categories` | `WILDLIFE` 固定 |
| `flags` | `"extend": { "flags": [ "NO_BREED" ] }` で追加。`flags` の全置換はしない |
| `reproduction` / `baby_flags` | `NO_BREED` で繁殖を抑止。専用pupは作らない |
| `zombify_into` / `burn_into` | 両方 `""` にして無効化する（親は `mon_zombie_dog` / `mon_dog_scorched` のため必須） |
| `harvest` | 親の `dog_with_skull_fur` を維持 |
| `death_drops` | `sh_hound_death_drops` に上書き（親は未定義のため必須） |
| `special_attacks` | 3種とも親継承（変更なし）。置換時は全再宣言が必要（親: `EAT_FOOD` / `EAT_CARRION`＋`bite_grab` / `scratch_grab_required`） |

### ステータス目標
| ID | hp | speed | melee | armor (bash/cut) | aggro† | pack_size | weight‡ | cost_multiplier |
|---|---|---|---|---|---|---|---|---|
| `mon_sh_scrap_hound` | 40 | 155 | 2d3+2 cut, skill 6 | 2/1 | 10 | 2–4 | 3 | 0 |
| `mon_sh_scrap_mauler` | 70 | 120 | 3d4+4 cut, skill 6 | 6/4 | 20 | 1–2 | 1 | 5 |
| `mon_sh_scrap_alpha` | 90 | 130 | 3d4+6 cut, skill 7 | 8/6 | 30 | 1 | 1 | 10 |

比較対象（実測値）:
| モンスター | hp | speed | melee | skill | armor |
|---|---|---|---|---|---|
| `mon_coyote`（親） | 34 | 155 | 2d3+2 cut | 6 | なし |
| `mon_dog` | 30 | 150 | 2d3+3 cut | 6 | なし |
| `mon_zombie_dog` | 36 | 105 | 1d6+2 cut | 4 | electric 1のみ |

数値は設計時に微調整してよいが、この比較表を必ず置く。†aggroは危険度の相対指標。実装時は `aggro_character: true`＋敵対的な `aggression` / `morale` / `anger_triggers` に展開する。‡`weight`・`pack_size`・`cost_multiplier` はmonstergroupエントリ側に記述する（MONSTER体重は `mon_coyote` 準拠の22 kg級を上書き）。`pack_size` のエントリ側記述は `wilderness.json` に前例あり。

### 死亡ドロップ
- `sh_hound_death_drops` は `subtype: "collection"` で、`{ "item": "scrap", "prob": 25, "count": [ 1, 2 ] }`、`{ "item": "steel_chunk", "prob": 10 }` を定義する。
- バニラの `mon_dog_death_drops` はペット用品を含むためネストしない。
- 1体あたりの期待スクラップ量: 約0.375個（0.25 × 平均1.5個。`steel_chunk` 0.1個は別枠）。

### `GROUP_STRAY_DOGS` の影響範囲
- 既存weight合計は100（`GROUP_PET_DOGS` 90＋変異種 7+1+1+1）。
- 追加は hound 3 / mauler 1 / alpha 1 = 5。マージ後105の約4.8%で、5%以下。
- `pack_size` は hound 2–4、mauler 1–2、alpha 1。alphaは単独。
- 使用箇所:

| ファイル | 用途 |
|---|---|
| `mapgen/animalshelter.json` | 動物保護施設の出現・配置 |
| `monstergroups/misc.json` | 雑多encounter（4箇所で参照） |
| `monstergroups/wilderness.json` | 荒野encounter（`pack_size: [1, 6]` の前例あり） |

### 参照ファイル（実在確認済み）
- [x] `external/cdda/data/json/monsters/mammal.json` — `mon_coyote`（hp 34 / speed 155 / melee 2d3+2 / skill 6、`harvest: dog_with_skull_fur`、`zombify_into: mon_zombie_dog`）。`mon_dog` / `mon_zombie_dog` 比較値も同ファイルで確認
- [x] `external/cdda/data/json/harvest.json` — `dog_with_skull_fur`
- [x] `external/cdda/data/json/monstergroups/mammal.json` — `GROUP_STRAY_DOGS`（合計100の内訳確認）
- [x] `external/cdda/data/json/monsters/monster_flags.json` — `NO_BREED`
- [x] `external/cdda/data/json/items/resources/metal.json` — `scrap` / `steel_chunk`
- [x] `external/cdda/data/json/mapgen/animalshelter.json`、`monstergroups/misc.json`、`monstergroups/wilderness.json` — `GROUP_STRAY_DOGS` の使用箇所。`pack_size` のエントリ側記述は `wilderness.json:152` で前例確認

### ファイル構成
```
mods/medium/scrap_hounds/
├── modinfo.json
├── spec.md
├── design.md
└── data/
    ├── monsters.json      # MONSTER 3種
    ├── death_drops.json   # item_group 1件
    └── monstergroups.json  # same-ID merge 1件
```

### 実装順序
1. modinfo.json
2. data/death_drops.json（monsters.json から参照されるため先）
3. data/monsters.json
4. data/monstergroups.json（monster ID を参照するため最後）
- 各編集後に Level1。逸脱はその都度 design.md に反映。

### テスト手順
1. `bash scripts/validate.sh mods/medium/scrap_hounds` でJSON構文チェック（Level1）
2. `bash scripts/place_mod_for_test.sh --dry-run mods/medium/scrap_hounds` で既存配置を確認→`--force` で配置
3. `bash scripts/check_mods.sh --isolated --check-errors scrap_hounds` でmod読み込み確認（Level2）
4. CDDAを起動してLevel3確認: デバッグスポーン／群れ出現／戦闘／解体ドロップ／死亡ドロップ／セーブロード

### 完了条件
- [ ] Level1: JSON構文OK（未実行、本設計は未実装）
- [ ] Level2: 起動OK（未実行、本設計は未実装）
- [ ] Level3: 出現・戦闘・解体・ドロップ確認（未実行、本設計は未実装）
- [ ] `design.md` が実装値と一致（実装時に更新）

### リスク
- `GROUP_STRAY_DOGS` の既存encounterへの影響（追加5/105≒4.8%。Level3で影響を確認）。
- `mon_coyote` の `zombify_into` / `burn_into` 無効化の確認（`""` 指定）。
- junkyardには出現しない（`GROUP_DOGS` はゾンビ犬専用のため不使用）。

### ID衝突確認記録
- 新規ID（`mon_sh_*` 3件、`sh_hound_death_drops`）は `external/cdda/data/json` と `mods/` に存在せず、衝突なし。
- `GROUP_STRAY_DOGS` はsame-ID merge対象（バニラIDと同一にするのが正規の書式）。別allowlistは作らない。
- JSON実装は行わない。`modinfo.json` / `data/*.json` は未作成。Level1/2/3未実行。
