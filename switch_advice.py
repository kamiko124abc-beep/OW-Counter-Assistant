def get_switch_advice(score_difference):
    if score_difference <= 2:
        return "continue"
    elif score_difference <= 5:
        return "consider"
    else:
        return "switch"

def get_switch_reason(details):
    easy_enemies = [
        detail["enemy"]
        for detail in details
        if detail["danger"] <= 4
    ]

    neutral_enemies = [
        detail["enemy"]
        for detail in details
        if 5 <= detail["danger"] <= 6
    ]

    dangerous_enemies = [
        detail["enemy"]
        for detail in details
        if detail["danger"] >= 7
    ]

    return {
        "easy": easy_enemies,
        "neutral": neutral_enemies,
        "dangerous": dangerous_enemies,
    }
