from counter_matrix import COUNTER_MATRIX
from matchups import MATCHUPS
from dmon_matchups import get_dmon_matchup


def get_danger_level(danger):

    if danger >= 9:
        return "🔴 かなり危険"

    elif danger >= 6:
        return "🟠 注意"

    elif danger >= 3:
        return "🟡 少し注意"

    else:
        return "🟢 大きな相性不利なし"


def analyze_matchup(my_hero, enemies):

    results = []

    # 新しい相性データ
    hero_matrix = COUNTER_MATRIX.get(my_hero, {})

    # 旧データに説明文があれば再利用
    old_matchups = MATCHUPS.get(my_hero, {})

    for enemy in enemies:

        if enemy == "選択してください":
            continue

        # ミラー
        if enemy == my_hero:
            danger = 5

        # D.Mon専用データ
        elif enemy == "D.Mon" and my_hero != "D.Mon":
            dmon_data = get_dmon_matchup(my_hero)
            danger = dmon_data["danger"]

        # 通常の相性データ
        else:
            danger = hero_matrix.get(enemy, 5)

        # 説明文が旧データにあれば使用
        old_data = old_matchups.get(enemy)

        if old_data:
            reason = old_data.get(
                "reason",
                "相性データをもとに危険度を判定しています。"
            )
            advice = old_data.get(
                "advice",
                "相手の得意な距離や動きに注意して戦いましょう。"
            )

        else:
            reason = (
                f"{my_hero}との相性データから"
                f"危険度{danger}/10と判定しています。"
            )
            advice = (
                "相手の得意な距離やアビリティに注意し、"
                "無理な正面戦闘を避けましょう。"
            )

        level = get_danger_level(danger)

        results.append({
            "hero": enemy,
            "danger": danger,
            "level": level,
            "reason": reason,
            "advice": advice
        })

    results.sort(
        key=lambda x: x["danger"],
        reverse=True
    )

    return results
