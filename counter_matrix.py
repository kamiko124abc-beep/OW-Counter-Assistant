from all_matchups_extra import ALL_EXTRA_MATCHUPS


# おすすめ計算で使う相性データ
COUNTER_MATRIX = ALL_EXTRA_MATCHUPS


# すべて現在は明示データとして扱う
COUNTER_SOURCE = {
    hero: {
        enemy: "registered"
        for enemy in enemies
    }
    for hero, enemies in COUNTER_MATRIX.items()
}