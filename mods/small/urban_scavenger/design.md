# Urban Scavenger（都市廃墟漁り）

## コンセプト

廃墟と化した都市で這うように生き延びるサバイバー。略奪者や犯罪者（Burglar）ではなく、元は一般市民。施錠された扉をこじ開け、暗い建物を漁り、ゾンビの群れをすり抜けることに長ける。戦闘より回避と探索を重視。

## 既存職業との差別化

| 職業 | skills | 特徴 | Urban Scavengerとの違い |
|---|---|---|---|
| Burglar | traps 6, dodge 2 | プロの侵入犯。safecracking, stethoscope, boltcutter所持 | 犯罪者ではなく一般人のサバイバー。より広範なサバイバル技能 |
| Vagabond | melee 2, fab 2, tailor 2, cooking 2 | 放浪者。duffelbag+backpack、空のジャグ | 都市特化ではない。施錠突破・暗所探索の装備がない |
| Backpacker | survival 3 | 裕福な旅行者。hiking backpack、ガイドブック | 野外志向。都市スカベンジの道具なし |
| Homeless | スキルなし | 最低限の装備（bindle, ragpouch） | まったくの無技能。単なる貧困者 |

## スペック

| 項目 | 値 |
|---|---|
| id | urban_scavenger |
| points | 2 |
| npc_background | BG_survival_story_EVACUEE |
| skills | traps 4, survival 3, dodge 2, fabrication 1, melee 1 |
| proficiencies | prof_lockpicking |

## 装備

| ID | 用途 |
|---|---|
| pants_cargo | 下半身 |
| boots | 足 |
| hoodie | 上半身（防寒） |
| socks | 足 |
| mask_dust | 防塵マスク |
| daypack | バッグ |
| crowbar | 施錠突破・近接武器 |
| crude_picklock | 簡易ピック |
| wearable_light | ヘッドランプ |
| water_clean (canteen) | 飲料水 |
| lighter (charges: 100) | 着火具 |
| pockknife | ナイフ |
| starter_wallet_full | 財布 |
| tshirt (variant: generic_tshirt) | 下着 |
| boxer_shorts (male) | 男性下着 |
| bra + panties (female) | 女性下着 |

## 参照アイテム（実在確認済み）

| ID | ファイル | 状態 |
|---|---|---|
| pants_cargo | items/armor/pants.json | ✅ |
| boots | items/armor/boots.json | ✅ |
| hoodie | items/armor/torso.json | ✅ |
| socks | items/armor/feet.json | ✅ |
| mask_dust | items/armor/masks.json | ✅ |
| daypack | items/armor/storage.json | ✅ |
| crowbar | items/tool/entry_tools.json | ✅ |
| crude_picklock | items/tool/entry_tools.json | ✅ |
| wearable_light | items/tool_armor.json | ✅ |
| water_clean | items/comestibles/water.json | ✅ |
| canteen | items/containers/ | ✅ |
| lighter | items/tool/lighting.json | ✅ |
| pockknife | items/tool/knives.json | ✅ |
| starter_wallet_full | itemgroups/ | ✅ |
| tshirt (variant: generic_tshirt) | items/armor/torso_clothes.json | ✅ |
| boxer_shorts | items/armor/underwear.json | ✅ |
| bra | items/armor/underwear.json | ✅ |
| panties | items/armor/underwear.json | ✅ |
| BG_survival_story_EVACUEE | professions.json | ✅ |
| prof_lockpicking | proficiencies/traps.json | ✅ |

## 設計判断の根拠

- **traps 4**: Burglar(traps 6)より低く、Scoundrel(traps 3)より高い。素人よりは熟練しているがプロの犯罪者ではない。crude_picklock (LOCKPICK 3) を十分に扱える値
- **survival 3**: BackpackerやWinter Scavengerと同レベル。都市での物資探索・応急処置に必要十分
- **dodge 2**: 「戦わずに逃げる」立ち回りを表現。Burglarと同値
- **fabrication 1, melee 1**: 補助技能。crowbarを最低限扱える。Vagabondの半分
- **prof_lockpicking**: 必須。crude_picklockを効果的に使うため
- **crowbar**: PRY 3。施錠ドア・マンホール開放。都市探索の要。近接武器としても使用可
- **crude_picklock**: 軽量(23g)。Burglarのpicklocks(544g)より劣るが、アラーム抑制効果あり
- **daypack**: 軽量防水バッグ。travelpackと迷ったが、daypackの方が軽く低encumbrance
- **mask_dust**: 廃墟の埃・粉塵からの保護。bandanaより防御高く重量許容範囲
- **wearable_light**: ヘッドランプ。ハンズフリーで暗所探索可能
- **canteen + water_clean**: Winter Scavengerと同パターン

## 新規定義ID

- `urban_scavenger`（職業のみ、計1個）
