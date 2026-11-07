## Mod仕様書: Scrap Hounds（廃材犬）

### 背景・動機
- 廃材を漁る野良犬の群れを追加する。既存の `scrap_zombie` はゾンビ系だが、本modは生きた野生犬として「狩る／狩られる」体験を作る。
- 野良犬encounter（`GROUP_STRAY_DOGS`）に、装甲・群れ・リーダーを持つ危険な個体を低確率で混ぜる。

### 追加/変更内容（What）
- 含むもの:
  - MONSTER 3種: `mon_sh_scrap_hound`（群れ型）、`mon_sh_scrap_mauler`（装甲型）、`mon_sh_scrap_alpha`（希少なリーダー）
  - 死亡ドロップ 1件 `sh_hound_death_drops`: `scrap` / `steel_chunk` を低確率で追加
  - monstergroup 同一IDマージ 1件: `GROUP_STRAY_DOGS` に低weightで追加
  - 解体は親 `dog_with_skull_fur` をそのまま使う（新規harvestは作らない）
- 含まないもの:
  - 新mapgen、NPC、シナリオ、職業、新モンスターシステム
  - 既存モンスターの改変、独自の進化系統（`upgrades` なし）
  - `GROUP_DOGS`（ゾンビ犬用）への注入
  - junkyard出現が必要なら別modのmapgen案件とする

### ゲームプレイへの影響（Why）
- 野良犬encounterに装甲・群れ・リーダーを持つ危険な個体が低確率で混ざる。
- 倒すと死亡ドロップでスクラップが得られ、狩猟とクラフトの循環につながる。
- 既存システムの拡張のみ。新ゲームシステムは追加しない。

### 成功基準
- 3種がデバッグスポーンでき、hound/maulerは群れ、alphaは単独で出現する。
- 解体で肉・皮・骨、死亡ドロップでスクラップが得られる。
- Level1（JSON構文）・Level2（ERRORなし）を通過する。
- Level3で出現・戦闘・解体・ドロップ・セーブ/ロードを確認する。

### スコープ判断
- 中規模mod。新規ゲーム内ID 4（MONSTER 3＋死亡ドロップ 1）に加え same-ID merge 1件（`GROUP_STRAY_DOGS`、新規IDに数えない）のため、新規 `item_group` 定義を含み「copy-fromのみ」を満たさず、Step 1・2は省略しない。
