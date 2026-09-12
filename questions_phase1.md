# Phase 1 Question List (90 cases: 55 Structured + 35 GraphRAG)

Auto-generated from `eval/test_cases_v2.py` and `eval/test_cases_graphrag.py`. See `questions_phase1.json` for details.

Questions are in Japanese, matching what was actually tested (the RAG systems answer Japanese-language questions about Shibuya POIs).

See `docs/phase1_vs_phase2_test_design.md` for how these Phase 1 questions compare to Phase 2's, particularly at L4/L5.

| ID | Source | Level | Category | Question | Expected Keywords |
|---|---|---|---|---|---|
| L1-01 | structured | L1 Basic retrieval | basic_retrieval | 渋谷駅の場所を教えてください | 渋谷, 駅, 35., 139. |
| L1-02 | structured | L1 Basic retrieval | basic_retrieval | 東宝シネマの座標は？ | 東宝, シネマ, 座標, 緯度, 経度 |
| L1-03 | structured | L1 Basic retrieval | basic_retrieval | 渋谷東武ホテルはどこにありますか？ | 東武, ホテル, 渋谷 |
| L1-04 | structured | L1 Basic retrieval | basic_retrieval | 渋谷神南郵便局の場所を教えて | 神南, 郵便局, 渋谷 |
| L1-05 | structured | L1 Basic retrieval | basic_retrieval | 三菱UFJ銀行渋谷支店の位置情報 | 三菱, UFJ, 銀行, 渋谷 |
| L1-06 | structured | L1 Basic retrieval | basic_retrieval | 渋谷駅周辺のコンビニを教えてください | コンビニ, ローソン, ファミリーマート, セブン |
| L1-07 | structured | L1 Basic retrieval | basic_retrieval | 渋谷にあるカフェを3つ教えて | カフェ, コーヒー |
| L1-08 | structured | L1 Basic retrieval | basic_retrieval | 渋谷の映画館を教えてください | 映画館, シネマ, cinema |
| L1-09 | structured | L1 Basic retrieval | basic_retrieval | 渋谷周辺の薬局はどこですか？ | 薬局, ドラッグ |
| L1-10 | structured | L1 Basic retrieval | basic_retrieval | 渋谷にあるホテルを教えて | ホテル, 宿泊 |
| L2-01 | structured | L2 Spatial reasoning | spatial_reasoning | 渋谷駅に最も近いコンビニはどれですか？距離も推定してください | コンビニ, 近い, 距離, m, メートル |
| L2-02 | structured | L2 Spatial reasoning | spatial_reasoning | 東宝シネマから徒歩圏内（500m以内）にあるカフェを教えてください | カフェ, 徒歩, 500m, 圏内 |
| L2-03 | structured | L2 Spatial reasoning | spatial_reasoning | 渋谷駅と原宿駅の中間地点に近いカフェはありますか？ | カフェ, 中間, 地点 |
| L2-04 | structured | L2 Spatial reasoning | spatial_reasoning | 渋谷神南郵便局の周辺200m以内にある飲食店を教えてください | 郵便局, 200m, 飲食店, 周辺 |
| L2-05 | structured | L2 Spatial reasoning | spatial_reasoning | 渋谷駅から最も遠い映画館はどれですか？ | 映画館, 遠い, シネマ |
| L2-06 | structured | L2 Spatial reasoning | spatial_reasoning | 渋谷駅周辺で最も飲食店が集中しているのはどのあたりですか？ | 飲食店, 集中, エリア, 多い |
| L2-07 | structured | L2 Spatial reasoning | spatial_reasoning | 渋谷駅周辺のカフェとバー、どちらが多いですか？ | カフェ, バー, 多い, 数 |
| L2-08 | structured | L2 Spatial reasoning | spatial_reasoning | 渋谷駅周辺は「商業エリア」と「住宅エリア」のどちらの特性が強いですか？POI構成から推定してください | 商業, 住宅, 特性, POI |
| L2-09 | structured | L2 Spatial reasoning | spatial_reasoning | 渋谷駅周辺で医療施設（病院、クリニック、薬局）の分布を教えてください | 病院, クリニック, 薬局, 医療, 分布 |
| L2-10 | structured | L2 Spatial reasoning | spatial_reasoning | 渋谷駅周辺の宿泊施設の密度は高いですか？低いですか？理由も教えてください | ホテル, 宿泊, 密度, 高い, 低い |
| L2-11 | structured | L2 Spatial reasoning | spatial_reasoning | 渋谷駅の東側と西側、どちらにカフェが多いですか？ | カフェ, 東, 西, 多い |
| L2-12 | structured | L2 Spatial reasoning | spatial_reasoning | 渋谷駅周辺の映画館と劇場、どちらが多いですか？それぞれの数も教えてください | 映画館, 劇場, 数, 多い |
| L2-13 | structured | L2 Spatial reasoning | spatial_reasoning | 渋谷駅周辺のコンビニとスーパー、生活利便性の観点からどちらが充実していますか？ | コンビニ, スーパー, 生活, 利便性, 充実 |
| L2-14 | structured | L2 Spatial reasoning | spatial_reasoning | 渋谷駅周辺の銀行と郵便局、金融サービスへのアクセスはどちらが良いですか？ | 銀行, 郵便局, 金融, アクセス |
| L2-15 | structured | L2 Spatial reasoning | spatial_reasoning | 渋谷駅周辺で最も多いPOIカテゴリは何ですか？上位3つを教えてください | カテゴリ, 多い, 上位, ランキング |
| L3-01 | structured | L3 Constraint satisfaction | constraint_satisfaction | 渋谷駅から徒歩5分以内（約400m）にあるカフェを教えてください | カフェ, 徒歩, 5分, 400m |
| L3-02 | structured | L3 Constraint satisfaction | constraint_satisfaction | 電話番号がわかっている渋谷の映画館を教えてください | 映画館, 電話, 番号 |
| L3-03 | structured | L3 Constraint satisfaction | constraint_satisfaction | ウェブサイトを持っている渋谷のレストランを教えてください | レストラン, ウェブサイト, サイト |
| L3-04 | structured | L3 Constraint satisfaction | constraint_satisfaction | 「渋谷」という名前が含まれるホテルを教えてください | 渋谷, ホテル, 名前 |
| L3-05 | structured | L3 Constraint satisfaction | constraint_satisfaction | 渋谷駅周辺で24時間営業のコンビニはありますか？ | コンビニ, 24時間, 営業 |
| L3-06 | structured | L3 Constraint satisfaction | constraint_satisfaction | 渋谷駅から500m以内で、電話番号とウェブサイトの両方がわかるカフェを教えてください | カフェ, 500m, 電話, ウェブサイト |
| L3-07 | structured | L3 Constraint satisfaction | constraint_satisfaction | 渋谷駅周辺で、駅から近く（300m以内）、かつ映画館の近く（200m以内）にあるカフェはありますか？ | カフェ, 駅, 300m, 映画館, 200m |
| L3-08 | structured | L3 Constraint satisfaction | constraint_satisfaction | 渋谷駅周辺で、薬局が近く（200m以内）にあるクリニックを教えてください | 薬局, クリニック, 200m, 近く |
| L3-09 | structured | L3 Constraint satisfaction | constraint_satisfaction | 渋谷駅周辺で、コンビニが3軒以上集まっているエリアはどこですか？ | コンビニ, 3軒, 集まっている, エリア |
| L3-10 | structured | L3 Constraint satisfaction | constraint_satisfaction | 渋谷駅から500m以内で、カフェではなくバーを探しています。候補を教えてください | バー, 500m, カフェ, ではなく |
| L4-01 | structured | L4 Decision support | decision_support | 渋谷駅周辺で保育園を開設する場合、最適な場所はどこですか？公園の近さと交番の有無を考慮してください | 保育園, 公園, 交番, 最適, 場所 |
| L4-02 | structured | L4 Decision support | decision_support | 渋谷駅周辺で高齢者向けデイサービスを開設するなら、どのエリアが適していますか？医療施設へのアクセスを重視してください | 高齢者, デイサービス, 医療, アクセス, 適している |
| L4-03 | structured | L4 Decision support | decision_support | 渋谷駅周辺で学習塾を開設する場合、駅からのアクセスとコンビニの近さを考慮して、候補地を提案してください | 学習塾, 駅, アクセス, コンビニ, 候補 |
| L4-04 | structured | L4 Decision support | decision_support | 渋谷駅周辺で待ち合わせスポットとして最適な場所はどこですか？わかりやすさと周辺の飲食店を考慮してください | 待ち合わせ, 最適, わかりやすい, 飲食店 |
| L4-05 | structured | L4 Decision support | decision_support | 渋谷駅周辺で観光客向けの案内所を設置するなら、どこが効果的ですか？観光スポットと駅からのアクセスを考慮してください | 観光, 案内所, 効果的, スポット, アクセス |
| L4-06 | structured | L4 Decision support | decision_support | 渋谷駅周辺で新規カフェの出店を検討しています。競合（既存カフェ）の数と、集客が見込めるPOI（駅、商業施設）を考慮して、出店の向き不向きを判断してください | カフェ, 出店, 競合, 集客, 判断 |
| L4-07 | structured | L4 Decision support | decision_support | 渋谷駅周辺で新規コンビニの出店余地はありますか？既存コンビニの分布と密度から判断してください | コンビニ, 出店, 余地, 分布, 密度 |
| L4-08 | structured | L4 Decision support | decision_support | 渋谷駅周辺で新規ベーカリー（パン屋）を出店する場合、既存の競合と周辺のカフェ（協業可能性）を考慮して、出店戦略を提案してください | パン屋, ベーカリー, 出店, 競合, カフェ, 戦略 |
| L4-09 | structured | L4 Decision support | decision_support | 渋谷駅周辺で深夜営業のバーを出店する場合、既存バーとの競合、駅からのアクセスを考慮して、適切なエリアを提案してください | バー, 深夜, 出店, 競合, アクセス, エリア |
| L4-10 | structured | L4 Decision support | decision_support | 渋谷駅周辺で薬局を出店する場合、既存薬局との競合と、医療施設（病院、クリニック）との近接性を考慮して、出店の可否を判断してください | 薬局, 出店, 競合, 病院, クリニック, 可否 |
| L5-01 | structured | L5 Advanced reasoning | advanced_reasoning | 「渋谷駅周辺はカフェが多い」という結論は、検索半径を500mから300mに変えても成立しますか？両方の範囲でのカフェ数を比較して判断してください | カフェ, 500m, 300m, 比較, 成立 |
| L5-02 | structured | L5 Advanced reasoning | advanced_reasoning | 「渋谷駅周辺は飲食店が充実している」という評価は、カフェを除外した場合でも成立しますか？ | 飲食店, 充実, カフェ, 除外, 成立 |
| L5-03 | structured | L5 Advanced reasoning | advanced_reasoning | 渋谷駅周辺のコンビニ密度について、「十分に多い」と言える最小半径はどのくらいですか？ | コンビニ, 密度, 十分, 最小, 半径 |
| L5-04 | structured | L5 Advanced reasoning | advanced_reasoning | 高齢者向け住宅の候補地として、渋谷駅周辺と恵比寿駅周辺を比較してください。評価軸は：医療施設の数、薬局の数、公共施設（郵便局、交番）の有無としてください | 高齢者, 渋谷, 恵比寿, 比較, 医療, 薬局, 公共 |
| L5-05 | structured | L5 Advanced reasoning | advanced_reasoning | 子育て世帯向けの居住地として、渋谷駅周辺を評価してください。公園、保育施設、医療施設、スーパーの観点から総合的に判断してください | 子育て, 居住, 公園, 保育, 医療, スーパー, 総合 |
| L5-06 | structured | L5 Advanced reasoning | advanced_reasoning | ビジネスパーソン向けの立地として、渋谷駅周辺を評価してください。カフェ（作業場所）、コンビニ（利便性）、金融機関（銀行、ATM）の観点から判断してください | ビジネス, カフェ, コンビニ, 金融, 銀行, 評価 |
| L5-07 | structured | L5 Advanced reasoning | advanced_reasoning | 観光客向けのエリアとして、渋谷駅周辺を評価してください。観光スポット、飲食店、宿泊施設の観点から、強みと弱みを分析してください | 観光, 飲食店, 宿泊, 強み, 弱み, 分析 |
| L5-08 | structured | L5 Advanced reasoning | advanced_reasoning | 渋谷駅周辺で「雰囲気の良い」カフェを探しています。データから判断できる範囲で推薦し、判断の限界も説明してください | 雰囲気, カフェ, 推薦, 判断, 限界 |
| L5-09 | structured | L5 Advanced reasoning | advanced_reasoning | 渋谷駅周辺で「静かな」レストランを探しています。データから推測できることと、できないことを区別して回答してください | 静か, レストラン, 推測, できる, できない |
| L5-10 | structured | L5 Advanced reasoning | advanced_reasoning | 渋谷駅周辺のPOIデータに基づいて、このエリアの「治安」について推測できることはありますか？交番の有無などから判断し、データの限界も述べてください | 治安, 交番, 推測, データ, 限界 |
| GR-01 | graphrag | - | relation | 渋谷駅の東側にあるカフェで、同じエリアにコンビニもある場所はどこですか？ | カフェ, コンビニ, 東 |
| GR-02 | graphrag | - | relation | 銀行とカフェが両方あるエリアを教えてください | 銀行, カフェ, エリア |
| GR-03 | graphrag | - | relation | ホテルの近くにあるレストランを教えてください | ホテル, レストラン, 近く |
| GR-04 | graphrag | - | relation | 駅周辺で、薬局とコンビニが同じ場所にあるところはありますか？ | 薬局, コンビニ, 駅 |
| GR-05 | graphrag | - | relation | 映画館の近くにあるカフェはどこですか？ | 映画館, カフェ |
| GR-06 | graphrag | - | multi_hop | カフェを起点に、そこから50m以内にある書店を教えてください | カフェ, 書店, 50m |
| GR-07 | graphrag | - | multi_hop | 渋谷駅から100m以内のコンビニと、そこから近いカフェを教えてください | コンビニ, カフェ, 100m |
| GR-08 | graphrag | - | multi_hop | ホテルから徒歩で行ける範囲にあるレストランとカフェを教えてください | ホテル, レストラン, カフェ |
| GR-09 | graphrag | - | aggregation | 飲食店が最も多いエリアはどこですか？ | 飲食店, エリア, 多い |
| GR-10 | graphrag | - | aggregation | 北側と南側でPOIの数が多いのはどちらですか？ | 北, 南, 数, 多い |
| GR-11 | graphrag | - | aggregation | 渋谷で最も多いカテゴリのPOIは何ですか？上位3つを教えてください | カテゴリ, 多い, 上位 |
| GR-12 | graphrag | - | comparison | 東側と西側で、飲食店のカテゴリ多様性が高いのはどちらですか？ | 東, 西, 飲食店, 多様性 |
| GR-13 | graphrag | - | comparison | 駅の近く（200m以内）と遠く（500m以上）で、どちらにホテルが多いですか？ | 駅, 近く, 遠く, ホテル |
| GR-14 | graphrag | - | proximity | 渋谷駅に最も近いホテルはどこですか？ | 駅, 近い, ホテル |
| GR-15 | graphrag | - | proximity | 渋谷駅から300m以内にある映画館を距離順に教えてください | 映画館, 300m, 距離 |
| GR-16 | graphrag | - | brand | 渋谷にあるスターバックスは何店舗ありますか？ | スターバックス, 店舗, 数 |
| GR-17 | graphrag | - | brand | ファミリーマートとローソン、どちらが店舗数が多いですか？ | ファミリーマート, ローソン, 多い |
| GR-18 | graphrag | - | brand | 渋谷駅の東側にあるドトールコーヒーを教えてください | ドトール, 東 |
| GR-19 | graphrag | - | brand | マクドナルドの近くにあるスターバックスはありますか？ | マクドナルド, スターバックス, 近く |
| GR-20 | graphrag | - | brand | 渋谷で最も店舗数が多いコンビニチェーンはどこですか？ | コンビニ, 多い, チェーン |
| GR-21 | graphrag | - | complementary | ホテルに泊まる場合、近くで食事できるレストランを教えてください | ホテル, レストラン, 近く |
| GR-22 | graphrag | - | complementary | 映画を見た後に行けるカフェを探しています | 映画, カフェ |
| GR-23 | graphrag | - | complementary | 渋谷駅を出てすぐのところで軽食を取れる場所はありますか？ | 駅, 軽食, 近く |
| GR-24 | graphrag | - | complementary | 本屋で本を買った後にコーヒーを飲めるカフェは近くにありますか？ | 本屋, 書店, カフェ, コーヒー |
| GR-25 | graphrag | - | complementary | 観光名所の近くで食事ができる場所を教えてください | 観光, 名所, 食事 |
| GR-26 | graphrag | - | competitor | このカフェが混んでいる場合、近くに代わりのカフェはありますか？ | カフェ, 代わり, 近く |
| GR-27 | graphrag | - | competitor | 渋谷駅周辺でラーメン屋が密集しているエリアはどこですか？ | ラーメン, 密集, エリア |
| GR-28 | graphrag | - | competitor | この居酒屋の他に、同じエリアで別の選択肢を教えてください | 居酒屋, 選択肢, エリア |
| GR-29 | graphrag | - | cuisine | 渋谷でイタリアン料理を食べられるお店を教えてください | イタリアン, 料理, 店 |
| GR-30 | graphrag | - | cuisine | 和食と洋食、どちらの店が渋谷には多いですか？ | 和食, 洋食, 多い |
| GR-31 | graphrag | - | cuisine | ラーメン屋が集まっているエリアを教えてください | ラーメン, 集まっている, エリア |
| GR-32 | graphrag | - | cuisine | 寿司屋の近くにある別の和食店を教えてください | 寿司, 和食, 近く |
| GR-33 | graphrag | - | hours | 渋谷で24時間営業のお店を教えてください | 24時間, 営業 |
| GR-34 | graphrag | - | hours | 深夜でも食事ができるレストランはありますか？ | 深夜, 食事, レストラン |
| GR-35 | graphrag | - | hours | 早朝から営業しているカフェを教えてください | 早朝, 営業, カフェ |
