import streamlit as st
from heroes import TANK_HEROES, DPS_HEROES, SUPPORT_HEROES
from analyzer import analyze_matchup
from recommender import recommend_heroes
from switch_advice import get_switch_advice, get_switch_reason


st.title("🎮 OW Counter Assistant")

# 自分のロールを選ぶ
my_role = st.selectbox(
    "自分のロール",
    ["タンク", "DPS", "サポート"]
)

# 選んだロールのヒーローを表示する
if my_role == "タンク":
    my_heroes = TANK_HEROES

elif my_role == "DPS":
    my_heroes = DPS_HEROES

else:
    my_heroes = SUPPORT_HEROES


# 自分のヒーローを選ぶ
my_hero = st.selectbox(
    "自分のヒーロー",
    my_heroes
)


# 敵チーム
st.subheader("敵チーム")

enemy_tank = st.selectbox(
    "敵タンク",
    ["選択してください"] + TANK_HEROES
)

enemy_dps_1 = st.selectbox(
    "敵DPS 1",
    ["選択してください"] + DPS_HEROES
)

enemy_dps_2 = st.selectbox(
    "敵DPS 2",
    ["選択してください"] + DPS_HEROES
)

enemy_support_1 = st.selectbox(
    "敵サポート 1",
    ["選択してください"] + SUPPORT_HEROES
)

enemy_support_2 = st.selectbox(
    "敵サポート 2",
    ["選択してください"] + SUPPORT_HEROES
)


# 分析ボタン
if st.button("🔍 分析する"):

    enemies = [
        enemy_tank,
        enemy_dps_1,
        enemy_dps_2,
        enemy_support_1,
        enemy_support_2
    ]

    results = analyze_matchup(my_hero, enemies)

    recommendations = recommend_heroes(enemies, my_role)

    all_recommendations = recommend_heroes(
        enemies,
        my_role,
        limit=None
    )

    current_recommendation = next(
        (
            recommendation
            for recommendation in all_recommendations
            if recommendation["hero"] == my_hero
        ),
        None
    )

    best_recommendation = all_recommendations[0]

    if current_recommendation is not None:
        current_score = current_recommendation["score"]
        best_score = best_recommendation["score"]
        best_hero = best_recommendation["hero"]
        best_details = best_recommendation["details"]

        switch_reason = get_switch_reason(best_details)

        best_easy_enemies = switch_reason["easy"]
        best_neutral_enemies = switch_reason["neutral"]
        best_dangerous_enemies = switch_reason["dangerous"]

        current_rank = next(
            i
            for i, recommendation in enumerate(
                all_recommendations,
                start=1
            )
            if recommendation["hero"] == my_hero
        )

        score_difference = current_score - best_score

        st.subheader("🔄 ピック変更アドバイス")

        st.write(
            f"現在：**{my_hero}** "
            f"｜順位：**{current_rank}位** "
            f"｜推薦スコア：**{current_score}**"
        )

        st.write(
            f"最上位候補：**{best_hero}** "
            f"｜順位：**1位** "
            f"｜推薦スコア：**{best_score}**"
        )

        switch_advice = get_switch_advice(score_difference)

        if switch_advice == "continue":
            st.success(
                f"✅ 継続推奨：スコア差は{score_difference}です。"
                "今のヒーローをそのまま使っても問題なさそうです。"
            )

        elif switch_advice == "consider":
            st.warning(
                f"🟡 変更検討：{best_hero}へ変更すると、"
                f"推薦スコアが{score_difference}改善します。"
            )

        else:
            st.error(
                f"🔄 変更推奨：{best_hero}へ変更すると、"
                f"推薦スコアが{score_difference}改善します。"
                f"{best_hero}の方が今回の敵編成には低リスクです。"
            )

        if switch_advice != "continue":
            st.write(f"**💡 {best_hero}を候補にする理由**")

            if best_easy_enemies:
                st.write(
                    "🟢 比較的戦いやすい："
                    + "・".join(best_easy_enemies)
                )

            if best_neutral_enemies:
                st.write(
                    "🟡 五分〜やや注意："
                    + "・".join(best_neutral_enemies)
                )

            if best_dangerous_enemies:
                st.write(
                    "🔴 注意が必要："
                    + "・".join(best_dangerous_enemies)
                )

    st.subheader("🏆 おすすめヒーロー TOP3")


    for i, recommendation in enumerate(recommendations, start=1):

        hero = recommendation["hero"]
        danger = recommendation["danger"]
        penalty = recommendation["penalty"]
        max_penalty = recommendation["max_penalty"]
        score = recommendation["score"]
        strong_counter_count = recommendation["strong_counter_count"]
        details = recommendation["details"]

        st.write(f"### {i}位　{hero}")
        st.write(f"敵チームへの合計危険度：{danger}")
        st.write(f"強カウンター：{strong_counter_count}人")
        st.write(f"強カウンターペナルティ：+{penalty}")
        st.write(f"最大危険度ペナルティ：+{max_penalty}")
        st.write(f"推薦スコア：{score}")

        if strong_counter_count == 0:
            st.success("✅ 強いカウンターがいないため、安定したおすすめです。")
        elif strong_counter_count == 1:
            st.warning("⚠️ 強いカウンターが1人います。相手の動きに注意。")
        else:
            st.error(
                f"🚨 強いカウンターが{strong_counter_count}人います。"
                "状況によっては別ヒーローも検討してください。"
            )
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

        st.write("**📋 相性まとめ**")

        if easy_enemies:
            st.write(
                "🟢 比較的戦いやすい："
                + "・".join(easy_enemies)
            )

        if neutral_enemies:
            st.write(
                "🟡 五分〜やや注意："
                + "・".join(neutral_enemies)
            )

        if dangerous_enemies:
            st.write(
                "🔴 注意："
                + "・".join(dangerous_enemies)
            )

        if i == 1:
            st.info(
                f"💡 順位の理由：推薦スコア{score}で、"
                f"今回の敵編成に対する{my_role}候補の中で"
                "最も低リスクと判定されています。"
            )
        elif i == 2:
            st.info(
                f"💡 順位の理由：推薦スコア{score}で、"
                "1位に次いで低リスクな候補です。"
            )
        else:
            st.info(
                f"💡 順位の理由：推薦スコア{score}で、"
                "今回の敵編成に対する有力な第3候補です。"
            )
        st.write("相性の内訳：")

        for detail in details:
            enemy = detail["enemy"]
            enemy_danger = detail["danger"]
            source = detail["source"]

            if source == "registered":
                source_text = "登録済み"
            elif source == "reverse":
                source_text = "自動補完"
            elif source == "dmon":
                source_text = "D.Mon専用"
            elif source == "dmon_self":
                source_text = "D.Mon専用"
            elif source == "mirror":
                source_text = "ミラー"
            else:
                source_text = "標準値"

            st.write(
                f"- {enemy}：{enemy_danger}/10 "
                f"（{source_text}）"
            )

    # 全候補ランキング
    with st.expander("📊 全候補ランキングを見る"):

        ranking_data = []

        for i, recommendation in enumerate(
            all_recommendations,
            start=1
        ):
            ranking_data.append({
                "順位": i,
                "ヒーロー": recommendation["hero"],
                "推薦スコア": recommendation["score"],
                "合計危険度": recommendation["danger"],
                "強カウンター": recommendation["strong_counter_count"],
                "最大危険度": recommendation["max_danger"],
            })

        st.dataframe(
            ranking_data,
            use_container_width=True,
            hide_index=True
        )

    st.subheader("⚠️ 危険な敵ランキング")

    for result in results:

        hero = result["hero"]
        danger = result["danger"]
        level = result["level"]
        reason = result["reason"]
        advice = result["advice"]

        st.write(f"## {level}　{hero}")
        st.write(f"**危険度：{danger}/10**")

        st.write("**なぜ注意？**")
        st.write(reason)

        st.write("**初心者向け対策**")
        st.write(advice)

        st.divider()