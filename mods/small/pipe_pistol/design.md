## Mod設計書: pipe_pistol

### 目的
pipe rifleの拳銃版として、9mm単発式パイプピストルを追加する。

### スコープ
- **含む:**
  - 銃器1種: `ppis_9mm_pipe_pistol`（9mmパイプピストル, copy-from `gun_base_handgun_manual`）
  - レシピ1種: `ppis_9mm_pipe_pistol` のクラフトレシピ
- **含まない:**
  - 複数口径バリエーション
  - マガジン改造
  - モンスター・シナリオ追加

### ターゲットバージョン
- CDDA: 0.I RC

### 依存関係
- 依存mod: dda（必須）

### 使用予定ID一覧
| 種別 | ID | 説明 |
|---|---|---|
| GUN | `ppis_9mm_pipe_pistol` | 9mm単発式パイプピストル |

### 参照ファイル（external/cdda/） — 要確認
- [ ] `external/cdda/data/json/items/ranged/` — pipe rifle のベースステータス確認、glock_19 等のベンチマーク
- [ ] `external/cdda/data/json/items/gun/` — `gun_base_handgun_manual` の実在確認

### ファイル構成
- modinfo.json
- data/items.json
- data/recipes.json

### 実装順序
1. modinfo.json
2. data/items.json
3. data/recipes.json

### アイテム仕様

| フィールド | 値 | 根拠 |
|---|---|---|
| id | `ppis_9mm_pipe_pistol` | プレフィックス `ppis_` |
| copy-from | `gun_base_handgun_manual` | 手動式拳銃ベース |
| name | "9mm pipe pistol" | |
| description | "A home-made pistol.  It is a pipe with a crude grip and hammer mechanism, designed to strike the single 9mm round it holds." | |
| looks_like | `glock_19` | 外見参照 |
| weight | "1200 g" | pipe rifleより軽量 |
| volume | "900 ml" | |
| barrel_length | "203 mm" | 拳銃サイズの銃身長 |
| ammo | `["9mm"]` | |
| clip_size | 1 | 単発式 |
| ranged_damage | -1 (bullet) | バレル短縮による減衰 |
| dispersion | 650 | pipe rifleより低精度 |
| durability | 6 | 即席武器の低耐久 |
| loudness | 35 | |
| reload | 200 | 手動装填の遅さ |
| valid_mod_locations | `[["sights mount", 1]]` | 最低限のサイトのみ |
| flags | `RELOAD_EJECT`, `EASY_CLEAN` | |
| material | `["steel", "wood"]` | パイプ＋木製グリップ |

### レシピ仕様

| フィールド | 値 | 根拠 |
|---|---|---|
| result | `ppis_9mm_pipe_pistol` | |
| category | `CC_WEAPON` | |
| subcategory | `CSC_WEAPON_RANGED` | |
| skill_used | `fabrication` | |
| skills_required | `[["gun", 1]]` | |
| difficulty | 2 | 簡易銃器工作 |
| time | "30 m" | |
| reversible | true | 分解可能 |
| autolearn | true | |
| proficiencies | `prof_gunsmithing_basic`, `prof_gunsmithing_improv` | |
| qualities | SAW_M_FINE ×1, SCREW_FINE ×1 | |
| components | pipe ×1, 2x4 ×1, scrap ×1 | 最小限の部品構成 |

### テスト手順
1. validate.shでJSON構文チェック（Level1）
2. link_mod_for_test.shでCDDAに配置
3. check_mods.shでmod読み込み確認（Level2）
4. CDDAを起動してLevel3確認:
   - デバッグメニューで `ppis_9mm_pipe_pistol` をスポーン
   - 9mm弾薬を装填して射撃可能か確認
   - クラフトメニューにレシピが表示されることを確認

### 完了条件
- [ ] Level1: JSON構文OK
- [ ] Level2: 起動OK（エラーなし）
- [ ] Level3: 意図通り動作
  - [ ] `ppis_9mm_pipe_pistol` がデバッグメニューでスポーン可能
  - [ ] 9mm弾薬を1発装填し射撃できる
  - [ ] クラフトメニューにレシピが表示される
  - [ ] ステータスが設計値通り（単発、dispersion 650、durability 6）
