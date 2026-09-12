# Phase 2 Question List (130 cases)

Auto-generated from `eval/test_cases_multi_area.py`. See `questions.json` for details.

Questions are in Japanese, matching what was actually tested (the RAG systems answer Japanese-language questions about Tokyo POIs).

| ID | Level | Area | Query Type | Question | Expected Keywords |
|---|---|---|---|---|---|
| MA-SBY-L1-01 | L1 Basic retrieval | shibuya | single_area | 渋谷駅の場所を教えてください | 渋谷, 駅, 35., 139. |
| MA-SBY-L1-02 | L1 Basic retrieval | shibuya | single_area | 渋谷駅周辺のコンビニを教えてください | コンビニ, ローソン, ファミリーマート, セブン |
| MA-SBY-L1-03 | L1 Basic retrieval | shibuya | single_area | 渋谷駅周辺のスターバックスはありますか？ | スターバックス, 渋谷 |
| MA-SBY-L1-04 | L1 Basic retrieval | shibuya | single_area | 渋谷駅近くのカフェはありますか？ | カフェ, 渋谷 |
| MA-SBY-L2-01 | L2 Spatial reasoning | shibuya | single_area | 渋谷駅に最も近いコンビニはどれですか？距離も推定してください | コンビニ, 近い, 距離, m |
| MA-SBY-L2-02 | L2 Spatial reasoning | shibuya | single_area | 渋谷駅周辺のカフェとバー、どちらが多いですか？ | カフェ, バー, 多い, 数 |
| MA-SBY-L2-03 | L2 Spatial reasoning | shibuya | single_area | 渋谷駅の東側と西側、どちらにカフェが多いですか？ | カフェ, 東, 西, 多い |
| MA-SBY-L2-04 | L2 Spatial reasoning | shibuya | single_area | 渋谷ヒカリエから最も近いカフェはどこですか？ | カフェ, ヒカリエ, 近い |
| MA-SBY-L3-01 | L3 Constraint satisfaction | shibuya | single_area | 渋谷駅周辺で24時間営業のコンビニはありますか？ | コンビニ, 24時間, 営業 |
| MA-SBY-L3-02 | L3 Constraint satisfaction | shibuya | single_area | 渋谷駅から500m以内で、電話番号がわかるカフェを教えてください | カフェ, 500m, 電話 |
| MA-SBY-L3-03 | L3 Constraint satisfaction | shibuya | single_area | 渋谷駅周辺のドトールを全て教えてください | ドトール, 渋谷 |
| MA-SBY-L3-04 | L3 Constraint satisfaction | shibuya | single_area | 渋谷109の近くでランチができるレストランは？ | 109, レストラン, ランチ |
| MA-SBY-L4-01 | L4 Decision support | shibuya | single_area | 渋谷駅から近い順にカフェを3つ教えてください | カフェ, 近い, 順, 3 |
| MA-SBY-L4-02 | L4 Decision support | shibuya | single_area | 渋谷駅周辺でカフェとコンビニが両方近い場所は？ | カフェ, コンビニ, 近い |
| MA-SBY-L4-03 | L4 Decision support | shibuya | single_area | ハチ公像の周辺300mにある飲食店を教えてください | ハチ公, 300m, 飲食店 |
| MA-SBY-L4-04 | L4 Decision support | shibuya | single_area | 渋谷駅500m圏と1km圏でカフェの件数はどう変わりますか？ | カフェ, 500m, 1km, 件数 |
| MA-SBY-L5-01 | L5 Advanced reasoning | shibuya | single_area | 渋谷駅から最も近いカフェと、そこから300m以内の他カフェ数は？ | カフェ, 近い, 300m, 数 |
| MA-SBY-L5-02 | L5 Advanced reasoning | shibuya | single_area | 渋谷駅周辺でコンビニの競合状況を分析してください | コンビニ, 競合, セブン, ファミリーマート, ローソン |
| MA-SBY-L5-03 | L5 Advanced reasoning | shibuya | single_area | 渋谷駅周辺でカフェの近くにある書店を教えてください | カフェ, 書店, 近く |
| MA-SBY-L5-04 | L5 Advanced reasoning | shibuya | single_area | 渋谷駅周辺のカフェの平均距離と最寄り・最遠の距離差は？ | カフェ, 平均, 距離, 最寄り, 最遠 |
| MA-SJK-L1-01 | L1 Basic retrieval | shinjuku | single_area | 新宿駅の場所を教えてください | 新宿, 駅, 35., 139. |
| MA-SJK-L1-02 | L1 Basic retrieval | shinjuku | single_area | 新宿駅周辺のコンビニを教えてください | コンビニ, ファミリーマート, セブン |
| MA-SJK-L1-03 | L1 Basic retrieval | shinjuku | single_area | 新宿駅周辺のスターバックスはありますか？ | スターバックス, 新宿 |
| MA-SJK-L1-04 | L1 Basic retrieval | shinjuku | single_area | 新宿駅近くのカフェはありますか？ | カフェ, 新宿 |
| MA-SJK-L2-01 | L2 Spatial reasoning | shinjuku | single_area | 新宿駅に最も近いコンビニはどれですか？ | コンビニ, 近い, 距離 |
| MA-SJK-L2-02 | L2 Spatial reasoning | shinjuku | single_area | 新宿駅から500m以内にカフェは何件ありますか？ | カフェ, 500m, 件 |
| MA-SJK-L2-03 | L2 Spatial reasoning | shinjuku | single_area | 新宿駅の東側と西側、どちらに飲食店が多いですか？ | 飲食店, 東, 西, 多い |
| MA-SJK-L2-04 | L2 Spatial reasoning | shinjuku | single_area | 新宿御苑から最も近いカフェはどこですか？ | カフェ, 新宿御苑, 近い |
| MA-SJK-L3-01 | L3 Constraint satisfaction | shinjuku | single_area | 新宿駅周辺で24時間営業のコンビニは？ | コンビニ, 24時間, 営業 |
| MA-SJK-L3-02 | L3 Constraint satisfaction | shinjuku | single_area | 新宿駅から300m以内でWi-Fiが使えるカフェは？ | カフェ, 300m, Wi-Fi |
| MA-SJK-L3-03 | L3 Constraint satisfaction | shinjuku | single_area | 新宿駅周辺のドトールを全て教えてください | ドトール, 新宿 |
| MA-SJK-L3-04 | L3 Constraint satisfaction | shinjuku | single_area | 東京都庁の近くでランチができるレストランは？ | 都庁, レストラン, ランチ |
| MA-SJK-L4-01 | L4 Decision support | shinjuku | single_area | 新宿駅から近い順にカフェを3つ教えてください | カフェ, 近い, 順, 3 |
| MA-SJK-L4-02 | L4 Decision support | shinjuku | single_area | 新宿駅周辺でカフェとコンビニが両方近い場所は？ | カフェ, コンビニ, 近い |
| MA-SJK-L4-03 | L4 Decision support | shinjuku | single_area | 歌舞伎町の周辺300mにある飲食店を教えてください | 歌舞伎町, 300m, 飲食店 |
| MA-SJK-L4-04 | L4 Decision support | shinjuku | single_area | 新宿駅500m圏と1km圏でカフェの件数はどう変わりますか？ | カフェ, 500m, 1km, 件数 |
| MA-SJK-L5-01 | L5 Advanced reasoning | shinjuku | single_area | 新宿駅から最も近いカフェと、そこから300m以内の他カフェ数は？ | カフェ, 近い, 300m, 数 |
| MA-SJK-L5-02 | L5 Advanced reasoning | shinjuku | single_area | 新宿駅周辺でコンビニの競合状況を分析してください | コンビニ, 競合, セブン, ファミリーマート |
| MA-SJK-L5-03 | L5 Advanced reasoning | shinjuku | single_area | 新宿駅周辺でカフェの近くにある書店を教えてください | カフェ, 書店, 近く, 紀伊國屋 |
| MA-SJK-L5-04 | L5 Advanced reasoning | shinjuku | single_area | 新宿駅周辺のカフェの平均距離と最寄り・最遠の距離差は？ | カフェ, 平均, 距離, 最寄り, 最遠 |
| MA-IKB-L1-01 | L1 Basic retrieval | ikebukuro | single_area | 池袋駅の場所を教えてください | 池袋, 駅, 35., 139. |
| MA-IKB-L1-02 | L1 Basic retrieval | ikebukuro | single_area | 池袋駅周辺のコンビニを教えてください | コンビニ, ファミリーマート, セブン |
| MA-IKB-L1-03 | L1 Basic retrieval | ikebukuro | single_area | 池袋駅周辺のスターバックスはありますか？ | スターバックス, 池袋 |
| MA-IKB-L1-04 | L1 Basic retrieval | ikebukuro | single_area | 池袋駅近くのカフェはありますか？ | カフェ, 池袋 |
| MA-IKB-L2-01 | L2 Spatial reasoning | ikebukuro | single_area | 池袋駅に最も近いコンビニはどれですか？ | コンビニ, 近い, 距離 |
| MA-IKB-L2-02 | L2 Spatial reasoning | ikebukuro | single_area | 池袋駅から500m以内にカフェは何件ありますか？ | カフェ, 500m, 件 |
| MA-IKB-L2-03 | L2 Spatial reasoning | ikebukuro | single_area | 池袋駅の東側と西側、どちらに飲食店が多いですか？ | 飲食店, 東, 西, 多い |
| MA-IKB-L2-04 | L2 Spatial reasoning | ikebukuro | single_area | サンシャインシティから最も近いカフェはどこですか？ | カフェ, サンシャイン, 近い |
| MA-IKB-L3-01 | L3 Constraint satisfaction | ikebukuro | single_area | 池袋駅周辺で24時間営業のコンビニは？ | コンビニ, 24時間, 営業 |
| MA-IKB-L3-02 | L3 Constraint satisfaction | ikebukuro | single_area | 池袋駅から300m以内でWi-Fiが使えるカフェは？ | カフェ, 300m, Wi-Fi |
| MA-IKB-L3-03 | L3 Constraint satisfaction | ikebukuro | single_area | 池袋駅周辺のマツモトキヨシを全て教えてください | マツモトキヨシ, 池袋 |
| MA-IKB-L3-04 | L3 Constraint satisfaction | ikebukuro | single_area | 池袋西口公園の近くでランチができるレストランは？ | 西口公園, レストラン, ランチ |
| MA-IKB-L4-01 | L4 Decision support | ikebukuro | single_area | 池袋駅から近い順にカフェを3つ教えてください | カフェ, 近い, 順, 3 |
| MA-IKB-L4-02 | L4 Decision support | ikebukuro | single_area | 池袋駅周辺でカフェとコンビニが両方近い場所は？ | カフェ, コンビニ, 近い |
| MA-IKB-L4-03 | L4 Decision support | ikebukuro | single_area | 東武百貨店池袋店の周辺300mにある飲食店を教えてください | 東武百貨店, 300m, 飲食店 |
| MA-IKB-L4-04 | L4 Decision support | ikebukuro | single_area | 池袋駅500m圏と1km圏でカフェの件数はどう変わりますか？ | カフェ, 500m, 1km, 件数 |
| MA-IKB-L5-01 | L5 Advanced reasoning | ikebukuro | single_area | 池袋駅から最も近いカフェと、そこから300m以内の他カフェ数は？ | カフェ, 近い, 300m, 数 |
| MA-IKB-L5-02 | L5 Advanced reasoning | ikebukuro | single_area | 池袋駅周辺でコンビニの競合状況を分析してください | コンビニ, 競合, セブン, ファミリーマート |
| MA-IKB-L5-03 | L5 Advanced reasoning | ikebukuro | single_area | 池袋駅周辺でカフェの近くにある書店を教えてください | カフェ, 書店, 近く, ジュンク堂 |
| MA-IKB-L5-04 | L5 Advanced reasoning | ikebukuro | single_area | 池袋駅周辺のカフェの平均距離と最寄り・最遠の距離差は？ | カフェ, 平均, 距離, 最寄り, 最遠 |
| MA-TKY-L1-01 | L1 Basic retrieval | tokyo | single_area | 東京駅の場所を教えてください | 東京駅, 35., 139. |
| MA-TKY-L1-02 | L1 Basic retrieval | tokyo | single_area | 東京駅周辺のコンビニを教えてください | コンビニ, ファミリーマート, セブン |
| MA-TKY-L1-03 | L1 Basic retrieval | tokyo | single_area | 東京駅周辺のスターバックスはありますか？ | スターバックス, 東京駅 |
| MA-TKY-L1-04 | L1 Basic retrieval | tokyo | single_area | 東京駅近くのカフェはありますか？ | カフェ, 東京駅 |
| MA-TKY-L2-01 | L2 Spatial reasoning | tokyo | single_area | 東京駅に最も近いコンビニはどれですか？ | コンビニ, 近い, 距離 |
| MA-TKY-L2-02 | L2 Spatial reasoning | tokyo | single_area | 東京駅から500m以内にカフェは何件ありますか？ | カフェ, 500m, 件 |
| MA-TKY-L2-03 | L2 Spatial reasoning | tokyo | single_area | 東京駅の東側と西側、どちらに飲食店が多いですか？ | 飲食店, 東, 西, 多い |
| MA-TKY-L2-04 | L2 Spatial reasoning | tokyo | single_area | KITTEから最も近いカフェはどこですか？ | カフェ, KITTE, 近い |
| MA-TKY-L3-01 | L3 Constraint satisfaction | tokyo | single_area | 東京駅周辺で24時間営業のコンビニは？ | コンビニ, 24時間, 営業 |
| MA-TKY-L3-02 | L3 Constraint satisfaction | tokyo | single_area | 東京駅から300m以内でWi-Fiが使えるカフェは？ | カフェ, 300m, Wi-Fi |
| MA-TKY-L3-03 | L3 Constraint satisfaction | tokyo | single_area | 東京駅周辺のタリーズコーヒーを全て教えてください | タリーズ, 東京駅 |
| MA-TKY-L3-04 | L3 Constraint satisfaction | tokyo | single_area | 東京国際フォーラムの近くでランチができるレストランは？ | 国際フォーラム, レストラン, ランチ |
| MA-TKY-L4-01 | L4 Decision support | tokyo | single_area | 東京駅から近い順にカフェを3つ教えてください | カフェ, 近い, 順, 3 |
| MA-TKY-L4-02 | L4 Decision support | tokyo | single_area | 東京駅周辺でカフェとコンビニが両方近い場所は？ | カフェ, コンビニ, 近い |
| MA-TKY-L4-03 | L4 Decision support | tokyo | single_area | 丸ビルの周辺300mにある飲食店を教えてください | 丸ビル, 300m, 飲食店 |
| MA-TKY-L4-04 | L4 Decision support | tokyo | single_area | 東京駅500m圏と1km圏でカフェの件数はどう変わりますか？ | カフェ, 500m, 1km, 件数 |
| MA-TKY-L5-01 | L5 Advanced reasoning | tokyo | single_area | 東京駅から最も近いカフェと、そこから300m以内の他カフェ数は？ | カフェ, 近い, 300m, 数 |
| MA-TKY-L5-02 | L5 Advanced reasoning | tokyo | single_area | 東京駅周辺でコンビニの競合状況を分析してください | コンビニ, 競合, セブン, ファミリーマート |
| MA-TKY-L5-03 | L5 Advanced reasoning | tokyo | single_area | 東京駅周辺でカフェの近くにある書店を教えてください | カフェ, 書店, 近く, 丸善 |
| MA-TKY-L5-04 | L5 Advanced reasoning | tokyo | single_area | 東京駅周辺のカフェの平均距離と最寄り・最遠の距離差は？ | カフェ, 平均, 距離, 最寄り, 最遠 |
| MA-CROSS-01 | L3 Constraint satisfaction | shibuya,shinjuku | cross_area | 渋谷駅と新宿駅の周辺、カフェが多いのはどちらですか？ | カフェ, 渋谷, 新宿, 多い |
| MA-CROSS-02 | L3 Constraint satisfaction | ikebukuro,shibuya | cross_area | 池袋と渋谷で、コンビニの密度が高いのはどちらですか？ | コンビニ, 池袋, 渋谷, 密度 |
| MA-CROSS-03 | L3 Constraint satisfaction | tokyo,shinjuku | cross_area | 東京駅と新宿駅の周辺で、飲食店の種類が豊富なのはどちらですか？ | 飲食店, 東京駅, 新宿, 種類 |
| MA-CROSS-04 | L3 Constraint satisfaction | shibuya,shinjuku,ikebukuro,tokyo | cross_area | 4エリアの中で最もカフェが多い駅はどこですか？ | カフェ, 多い, 駅 |
| MA-CROSS-05 | L3 Constraint satisfaction | shibuya,ikebukuro | cross_area | 渋谷と池袋、24時間営業の店舗が多いのはどちらですか？ | 24時間, 渋谷, 池袋, 多い |
| MA-CROSS-06 | L3 Constraint satisfaction | shibuya,shinjuku,ikebukuro,tokyo | cross_area | スターバックスが最も多いエリアはどこですか？ | スターバックス, 多い, エリア |
| MA-CROSS-07 | L3 Constraint satisfaction | shibuya,shinjuku,ikebukuro,tokyo | cross_area | 各エリアで最もPOI密度が高いカテゴリは同じですか？ | カテゴリ, 密度, エリア |
| MA-CROSS-08 | L3 Constraint satisfaction | shibuya,shinjuku,ikebukuro,tokyo | cross_area | 4エリアの中で駅から最も近いカフェがあるのはどこですか？ | カフェ, 近い, 駅 |
| MA-CROSS-09 | L4 Decision support | shibuya,shinjuku | cross_area | 渋谷駅周辺にあるスターバックスは、新宿駅周辺と比べて何店舗差がありますか？ | スターバックス, 渋谷, 新宿, 店舗 |
| MA-CROSS-10 | L4 Decision support | tokyo,shibuya | cross_area | 東京駅の最寄りカフェと渋谷駅の最寄りカフェ、駅からの距離が近いのはどちらですか？ | カフェ, 東京駅, 渋谷, 距離 |
| MA-CROSS-11 | L4 Decision support | shinjuku,ikebukuro | cross_area | 新宿と池袋でマクドナルドの店舗数を比較してください | マクドナルド, 新宿, 池袋, 店舗 |
| MA-CROSS-12 | L4 Decision support | shibuya,tokyo | cross_area | 渋谷駅500m圏のコンビニ数と東京駅500m圏のコンビニ数、どちらが多い？ | コンビニ, 渋谷, 東京駅, 500m |
| MA-CROSS-13 | L4 Decision support | shibuya,shinjuku,ikebukuro,tokyo | cross_area | 各エリアの最寄りコンビニの距離を比較してください | コンビニ, 最寄り, 距離, 比較 |
| MA-CROSS-14 | L2 Spatial reasoning | shibuya,shinjuku,ikebukuro,tokyo | cross_area | 4エリア全体でコンビニは合計何件ありますか？ | コンビニ, 合計, 件 |
| MA-CROSS-15 | L2 Spatial reasoning | shibuya,shinjuku,ikebukuro,tokyo | cross_area | 全エリアで最も多いPOIカテゴリは何ですか？ | カテゴリ, 多い |
| MA-CROSS-16 | L2 Spatial reasoning | shibuya,shinjuku,ikebukuro,tokyo | cross_area | 4エリアの総POI数を教えてください | POI, 総数 |
| MA-CROSS-17 | L2 Spatial reasoning | shibuya,shinjuku,ikebukuro,tokyo | cross_area | 全エリアのカフェを合計すると何件ですか？ | カフェ, 合計, 件 |
| MA-CROSS-18 | L4 Decision support | shibuya,shinjuku,ikebukuro,tokyo | cross_area | ラーメン店が3件以上ある駅はどこですか？ | ラーメン, 3件, 駅 |
| MA-CROSS-19 | L4 Decision support | shibuya,shinjuku,ikebukuro,tokyo | cross_area | 駅から200m以内にカフェが最も多いエリアはどこですか？ | カフェ, 200m, 多い, エリア |
| MA-CROSS-20 | L4 Decision support | shibuya,shinjuku,ikebukuro,tokyo | cross_area | 24時間営業のコンビニが10件以上あるエリアはどこですか？ | 24時間, コンビニ, 10件, エリア |
| MA-LM-01 | L2 Spatial reasoning | shibuya | single_area | 渋谷109から最も近いカフェはどこですか？ | 109, カフェ, 近い |
| MA-LM-02 | L2 Spatial reasoning | ikebukuro | single_area | サンシャインシティから500m以内にコンビニは何件ありますか？ | サンシャイン, コンビニ, 500m, 件 |
| MA-LM-03 | L2 Spatial reasoning | tokyo | single_area | 東京国際フォーラムの最寄りのレストランを教えてください | 国際フォーラム, レストラン, 最寄り |
| MA-LM-04 | L2 Spatial reasoning | shinjuku | single_area | 新宿アルタから一番近い銀行はどこですか？ | アルタ, 銀行, 近い |
| MA-LM-05 | L2 Spatial reasoning | tokyo | single_area | KITTEから300m以内のカフェを教えてください | KITTE, カフェ, 300m |
| MA-LM-06 | L3 Constraint satisfaction | shibuya | single_area | 渋谷ヒカリエの近くで24時間営業のコンビニはありますか？ | ヒカリエ, 24時間, コンビニ |
| MA-LM-07 | L3 Constraint satisfaction | tokyo | single_area | 皇居前広場の近くで食事できるレストランは？ | 皇居, レストラン, 食事 |
| MA-LM-08 | L3 Constraint satisfaction | ikebukuro | single_area | 池袋西口公園の周辺でWi-Fiが使えるカフェは？ | 西口公園, Wi-Fi, カフェ |
| MA-LM-09 | L3 Constraint satisfaction | tokyo | single_area | 丸ビルの近くでスターバックスはありますか？ | 丸ビル, スターバックス |
| MA-LM-10 | L3 Constraint satisfaction | shinjuku | single_area | 歌舞伎町の近くで深夜営業しているバーは？ | 歌舞伎町, 深夜, バー |
| MA-LM-11 | L4 Decision support | shinjuku | single_area | 東京都庁から最も近いカフェと、その駅からの距離は？ | 都庁, カフェ, 駅, 距離 |
| MA-LM-12 | L4 Decision support | ikebukuro | single_area | サンシャインシティの近くにあるカフェとコンビニの数は？ | サンシャイン, カフェ, コンビニ, 数 |
| MA-LM-13 | L4 Decision support | shibuya | single_area | 渋谷スクランブルスクエアの周辺で飲食店のカテゴリ別件数は？ | スクランブルスクエア, 飲食店, カテゴリ, 件数 |
| MA-LM-14 | L4 Decision support | shinjuku | single_area | 新宿御苑から最寄りのカフェまでの距離と方角は？ | 新宿御苑, カフェ, 距離, 方角 |
| MA-LM-15 | L4 Decision support | shibuya | single_area | ハチ公像から見て東側にあるカフェを教えてください | ハチ公, 東, カフェ |
| MA-DET-01 | L1 Basic retrieval | ikebukuro | single_area | 池袋駅周辺のホテルを教えてください | 池袋, ホテル |
| MA-DET-02 | L1 Basic retrieval | tokyo | single_area | 東京駅近くの銀行はありますか？ | 東京駅, 銀行 |
| MA-DET-03 | L1 Basic retrieval | shibuya | single_area | 渋谷109の近くのカフェを教えてください | 109, カフェ |
| MA-DET-04 | L1 Basic retrieval | shinjuku | single_area | 新宿駅西口付近のコンビニはどこですか？ | 新宿, 西口, コンビニ |
| MA-DET-05 | L1 Basic retrieval | ikebukuro | single_area | 池袋駅から最も近い薬局は？ | 池袋, 薬局, 近い |
| MA-DET-06 | L2 Spatial reasoning | ikebukuro | single_area | サンシャインシティの近くのレストランは？ | サンシャイン, レストラン |
| MA-DET-07 | L2 Spatial reasoning | shinjuku | single_area | 歌舞伎町の近くで食事できる場所は？ | 歌舞伎町, 食事 |
| MA-DET-08 | L2 Spatial reasoning | tokyo | single_area | 丸の内で朝食が取れるカフェは？ | 丸の内, 朝食, カフェ |
| MA-DET-09 | L2 Spatial reasoning | shibuya | single_area | ハチ公像の周りにコンビニはある？ | ハチ公, コンビニ |
| MA-DET-10 | L2 Spatial reasoning | shinjuku | single_area | 都庁前でランチができる場所は？ | 都庁, ランチ |
| MA-DET-11 | L1 Basic retrieval | - | single_area | おすすめのカフェを教えてください | カフェ |
| MA-DET-12 | L1 Basic retrieval | - | single_area | 24時間営業のコンビニはどこにありますか？ | 24時間, コンビニ |
| MA-DET-13 | L1 Basic retrieval | - | single_area | 美味しいラーメン屋を探しています | ラーメン |
| MA-DET-14 | L1 Basic retrieval | - | single_area | Wi-Fiが使える場所を教えてください | Wi-Fi |
| MA-DET-15 | L1 Basic retrieval | - | single_area | 近くに薬局はありますか？ | 薬局 |
