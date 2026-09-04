from heroes import TANK_HEROES, DPS_HEROES, SUPPORT_HEROES
from matchups import MATCHUPS
from dmon_matchups import get_dmon_matchup, D_MON_SELF_DANGER
from counter_matrix import COUNTER_MATRIX, COUNTER_SOURCE


def recommend_heroes(enemies, role, limit=3):
    # ロールに合わせて候補ヒーローを決める
    if role == "タンク":
        candidates = TANK_HEROES

    elif role == "DPS":
        candidates = DPS_HEROES

    elif role == "サポート":
        candidates = SUPPORT_HEROES

    else:
        raise ValueError(f"不明なロールです: {role}")

    recommendations = []

    # 候補ヒーローを1人ずつ調べる
    for hero in candidates:

        hero_matchups = COUNTER_MATRIX.get(hero, {})

        total_danger = 0
        penalty = 0
        strong_counter_count = 0
        max_danger = 0
        details = []

        # 敵5人から受ける危険度を合計
        for enemy in enemies:
            if enemy == "選択してください":
                continue

            if hero == enemy:
                danger = 5

            elif hero == "D.Mon":
                danger = D_MON_SELF_DANGER.get(enemy, 5)

            elif enemy == "D.Mon":
                dmon_data = get_dmon_matchup(hero)
                danger = dmon_data["danger"]

            else:
                danger = hero_matchups.get(enemy, 5)

            total_danger += danger
            max_danger = max(max_danger, danger)
                        
            if danger >= 7:
                strong_counter_count += 1

            if danger >= 10:
                penalty += 8
            elif danger == 9:
                penalty += 6
            elif danger == 8:
                penalty += 4
            elif danger == 7:
                penalty += 2
            if hero == enemy:
                source = "mirror"

            elif hero == "D.Mon":
                if enemy in D_MON_SELF_DANGER:
                    source = "dmon_self"
                else:
                    source = "default"

            elif enemy == "D.Mon":
                source = "dmon"

            else:
                source = COUNTER_SOURCE.get(
                    hero,
                    {}
                ).get(
                    enemy,
                    "default"
                )
            

            details.append({
                "enemy": enemy,
                "danger": danger,
                "source": source
            })
        if max_danger >= 10:
            max_penalty = 6
        elif max_danger == 9:
            max_penalty = 4
        elif max_danger == 8:
            max_penalty = 2
        elif max_danger == 7:
            max_penalty = 1
        else:
            max_penalty = 0

        recommendations.append({
            "hero": hero,
            "danger": total_danger,
            "score": total_danger + penalty + max_penalty,
            "penalty": penalty,
            "max_penalty": max_penalty,
            "strong_counter_count": strong_counter_count,
            "max_danger": max_danger,
            "details": details
        })

    # 危険度が低い順に並べる
    recommendations.sort(
        key=lambda x: (
            x["score"],
            x["strong_counter_count"],
            x["max_danger"],
            x["danger"]
        )
    )

    # limit=Noneなら全候補を返す
    if limit is None:
        return recommendations

    # 指定された人数を返す
    return recommendations[:limit]