import streamlit as st
from heroes import TANK_HEROES, DPS_HEROES, SUPPORT_HEROES
from analyzer import analyze_matchup
from recommender import recommend_heroes
from switch_advice import get_switch_advice, get_switch_reason


st.set_page_config(
    page_title="OW Counter Assistant",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# -----------------------------
# DESIGN
# -----------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=Noto+Sans+JP:wght@400;500;600;700;800;900&display=swap');

:root {
    --bg: #050814;
    --panel: rgba(12, 19, 38, .84);
    --panel2: rgba(17, 28, 54, .78);
    --line: rgba(122, 159, 255, .20);
    --text: #f7f9ff;
    --muted: #93a4c7;
    --cyan: #2ddcff;
    --blue: #4f7cff;
    --purple: #a855f7;
    --pink: #ff3ea5;
    --orange: #ff9b42;
    --gold: #ffc83d;
    --green: #39e991;
    --red: #ff4d6d;
}

html, body, [class*="css"] {
    font-family: "Inter", "Noto Sans JP", sans-serif;
}

.stApp {
    color: var(--text);
    background:
        radial-gradient(circle at 10% 0%, rgba(79,124,255,.18), transparent 28rem),
        radial-gradient(circle at 90% 10%, rgba(168,85,247,.17), transparent 30rem),
        radial-gradient(circle at 60% 90%, rgba(255,62,165,.08), transparent 28rem),
        linear-gradient(145deg, #050814 0%, #07101f 52%, #040711 100%);
}

[data-testid="stHeader"] {
    background: rgba(5,8,20,.55);
    backdrop-filter: blur(14px);
}

[data-testid="stToolbar"] {
    right: 1rem;
}

.block-container {
    max-width: 1380px;
    padding-top: 2rem;
    padding-bottom: 4rem;
}

.hero-banner {
    position: relative;
    overflow: hidden;
    border: 1px solid rgba(119,155,255,.25);
    border-radius: 28px;
    padding: 36px 38px;
    margin-bottom: 24px;
    background:
        linear-gradient(115deg, rgba(11,20,43,.98) 0%, rgba(13,21,44,.94) 47%, rgba(41,18,76,.80) 100%);
    box-shadow:
        0 22px 70px rgba(0,0,0,.36),
        inset 0 1px 0 rgba(255,255,255,.05);
}
.hero-banner::before {
    content: "";
    position: absolute;
    width: 390px;
    height: 390px;
    right: -80px;
    top: -180px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(45,220,255,.30), transparent 67%);
    filter: blur(4px);
}
.hero-banner::after {
    content: "";
    position: absolute;
    width: 350px;
    height: 350px;
    right: 150px;
    bottom: -250px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(255,62,165,.28), transparent 68%);
}
.eyebrow {
    color: #8faaff;
    font-size: .78rem;
    letter-spacing: .22em;
    font-weight: 800;
    margin-bottom: 8px;
}
.hero-title {
    position: relative;
    z-index: 2;
    margin: 0;
    font-size: clamp(2.05rem, 4vw, 4.3rem);
    line-height: .98;
    font-weight: 900;
    letter-spacing: -.055em;
    text-shadow: 0 0 30px rgba(79,124,255,.18);
}
.hero-title span {
    background: linear-gradient(90deg, #ffffff, #72e8ff 40%, #a990ff 70%, #ff75c5);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.hero-sub {
    position: relative;
    z-index: 2;
    color: #aab8d6;
    max-width: 700px;
    font-size: 1rem;
    margin-top: 13px;
    margin-bottom: 0;
}
.badges {
    position: relative;
    z-index: 2;
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    margin-top: 22px;
}
.badge {
    border: 1px solid rgba(113,153,255,.24);
    background: rgba(255,255,255,.035);
    border-radius: 999px;
    padding: 8px 12px;
    color: #c8d4ee;
    font-size: .80rem;
    font-weight: 700;
}

.section-kicker {
    color: #8396bd;
    font-size: .72rem;
    letter-spacing: .16em;
    font-weight: 800;
    margin-bottom: 3px;
}
.section-title {
    font-weight: 900;
    font-size: 1.35rem;
    margin: 0 0 12px 0;
}

div[data-testid="stVerticalBlockBorderWrapper"] {
    border: 1px solid var(--line) !important;
    background: linear-gradient(145deg, rgba(14,23,46,.88), rgba(8,15,31,.90));
    border-radius: 22px !important;
    box-shadow: 0 14px 45px rgba(0,0,0,.22);
}

div[data-baseweb="select"] > div {
    min-height: 49px;
    border-radius: 13px !important;
    border-color: rgba(125,157,229,.22) !important;
    background: rgba(6,12,27,.80) !important;
}
div[data-baseweb="select"] > div:hover {
    border-color: rgba(45,220,255,.55) !important;
}

div[role="radiogroup"] {
    gap: .65rem;
}
div[role="radiogroup"] label {
    background: rgba(8,15,31,.75);
    border: 1px solid rgba(125,157,229,.21);
    padding: 12px 18px;
    border-radius: 13px;
    transition: .18s ease;
}
div[role="radiogroup"] label:hover {
    transform: translateY(-1px);
    border-color: rgba(45,220,255,.50);
    box-shadow: 0 0 24px rgba(45,220,255,.08);
}

.stButton > button {
    width: 100%;
    min-height: 58px;
    border: 0 !important;
    border-radius: 16px !important;
    color: white !important;
    font-weight: 900 !important;
    font-size: 1.05rem !important;
    background: linear-gradient(100deg, #ff8a3d 0%, #ff3f91 47%, #7b4dff 100%) !important;
    box-shadow:
        0 0 0 1px rgba(255,255,255,.12) inset,
        0 12px 34px rgba(255,62,165,.23),
        0 0 30px rgba(123,77,255,.17);
    transition: .18s ease !important;
}
.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow:
        0 0 0 1px rgba(255,255,255,.22) inset,
        0 16px 42px rgba(255,62,165,.31),
        0 0 42px rgba(123,77,255,.25);
}

.result-header {
    margin: 30px 0 15px 0;
    padding: 18px 22px;
    border-radius: 18px;
    border: 1px solid rgba(141,119,255,.26);
    background: linear-gradient(90deg, rgba(80,58,196,.20), rgba(28,216,255,.06));
}
.result-header h2 {
    margin: 0;
    font-size: 1.45rem;
    font-weight: 900;
}
.result-header p {
    color: #94a6cc;
    margin: 4px 0 0 0;
    font-size: .86rem;
}

.pick-card {
    position: relative;
    overflow: hidden;
    min-height: 318px;
    border-radius: 22px;
    padding: 22px;
    background: linear-gradient(145deg, rgba(15,25,50,.98), rgba(8,14,30,.98));
    border: 1px solid rgba(108,145,226,.24);
    box-shadow: 0 16px 45px rgba(0,0,0,.28);
}
.pick-card.rank1 {
    border-color: rgba(255,200,61,.68);
    box-shadow: 0 0 34px rgba(255,200,61,.12), 0 16px 45px rgba(0,0,0,.28);
}
.pick-card.rank2 {
    border-color: rgba(45,220,255,.54);
    box-shadow: 0 0 30px rgba(45,220,255,.09), 0 16px 45px rgba(0,0,0,.28);
}
.pick-card.rank3 {
    border-color: rgba(255,126,93,.50);
    box-shadow: 0 0 30px rgba(255,126,93,.08), 0 16px 45px rgba(0,0,0,.28);
}
.rank-bubble {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 38px;
    height: 38px;
    border-radius: 12px;
    font-weight: 900;
    font-size: 1.1rem;
    background: rgba(255,255,255,.07);
    border: 1px solid rgba(255,255,255,.10);
}
.rank1 .rank-bubble { color: #ffd75e; background: rgba(255,200,61,.13); }
.rank2 .rank-bubble { color: #72ebff; background: rgba(45,220,255,.11); }
.rank3 .rank-bubble { color: #ff956e; background: rgba(255,126,93,.10); }
.pick-name {
    margin: 15px 0 4px 0;
    font-size: 1.55rem;
    font-weight: 900;
}
.pick-label {
    color: #8799bd;
    font-size: .73rem;
    letter-spacing: .12em;
    font-weight: 800;
}
.score-pill {
    display: inline-block;
    margin: 12px 0 14px 0;
    padding: 7px 11px;
    border-radius: 999px;
    background: rgba(101,126,255,.12);
    border: 1px solid rgba(101,126,255,.22);
    color: #ced8ff;
    font-size: .79rem;
    font-weight: 800;
}
.compat {
    font-size: .86rem;
    line-height: 1.85;
    color: #c7d2ea;
}
.compat .easy { color: #57eda3; }
.compat .neutral { color: #ffd464; }
.compat .danger { color: #ff7089; }

.metric-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 9px;
    margin-top: 14px;
}
.mini-metric {
    padding: 10px;
    border-radius: 12px;
    border: 1px solid rgba(112,144,211,.14);
    background: rgba(255,255,255,.028);
}
.mini-metric b {
    display: block;
    font-size: 1rem;
    color: #fff;
}
.mini-metric span {
    display: block;
    margin-top: 2px;
    font-size: .66rem;
    color: #7588ad;
}

.threat-row {
    display: flex;
    align-items: center;
    gap: 11px;
    margin: 8px 0;
}
.threat-name {
    width: 120px;
    font-weight: 800;
    color: #dbe5fa;
}
.threat-track {
    flex: 1;
    height: 9px;
    border-radius: 999px;
    background: rgba(255,255,255,.055);
    overflow: hidden;
}
.threat-fill {
    height: 100%;
    border-radius: 999px;
    background: linear-gradient(90deg, #ffbd38, #ff4d78);
    box-shadow: 0 0 16px rgba(255,77,120,.25);
}
.threat-value {
    width: 44px;
    text-align: right;
    font-size: .78rem;
    color: #92a4c9;
    font-weight: 700;
}

[data-testid="stAlert"] {
    border-radius: 15px;
    border: 1px solid rgba(255,255,255,.08);
}
[data-testid="stExpander"] {
    border-radius: 16px !important;
    border-color: rgba(120,151,219,.18) !important;
    background: rgba(8,15,31,.45);
}
[data-testid="stDataFrame"] {
    border: 1px solid rgba(123,153,219,.18);
    border-radius: 16px;
    overflow: hidden;
}

.footer {
    margin-top: 36px;
    padding-top: 18px;
    border-top: 1px solid rgba(129,158,221,.14);
    color: #6f82a8;
    font-size: .75rem;
    display: flex;
    justify-content: space-between;
    gap: 12px;
    flex-wrap: wrap;
}

@media (max-width: 800px) {
    .block-container { padding: 1rem .9rem 2.5rem .9rem; }
    .hero-banner { padding: 25px 22px; border-radius: 21px; }
    .metric-grid { grid-template-columns: 1fr; }
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero-banner">
    <div class="eyebrow">COUNTER ANALYSIS / PICK SUPPORT</div>
    <h1 class="hero-title">OW COUNTER <span>ASSISTANT</span></h1>
    <p class="hero-sub">
        敵の構成を入力するだけ。危険度と相性から、
        今の試合で使いやすいヒーローをすばやく分析します。
    </p>
    <div class="badges">
        <span class="badge">⚡ クイック分析</span>
        <span class="badge">🎯 ロール別おすすめ</span>
        <span class="badge">📊 相性を見える化</span>
    </div>
</div>
""", unsafe_allow_html=True)

# -----------------------------
# INPUT
# -----------------------------
left, right = st.columns([0.42, 0.58], gap="large")

with left:
    with st.container(border=True):
        st.markdown('<div class="section-kicker">STEP 01</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-title">自分のロールを選択</div>', unsafe_allow_html=True)

        my_role = st.radio(
            "自分のロール",
            ["タンク", "DPS", "サポート"],
            horizontal=True,
            label_visibility="collapsed",
        )

        if my_role == "タンク":
            my_heroes = TANK_HEROES
        elif my_role == "DPS":
            my_heroes = DPS_HEROES
        else:
            my_heroes = SUPPORT_HEROES

        st.markdown('<div class="section-kicker" style="margin-top:18px">STEP 02</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-title">自分のヒーロー</div>', unsafe_allow_html=True)
        my_hero = st.selectbox(
            "自分のヒーロー",
            my_heroes,
            label_visibility="collapsed",
        )

with right:
    with st.container(border=True):
        st.markdown('<div class="section-kicker">STEP 03</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-title">敵チームを入力</div>', unsafe_allow_html=True)

        row1 = st.columns(2)
        with row1[0]:
            enemy_tank = st.selectbox(
                "敵タンク",
                TANK_HEROES,
                index=None,
                placeholder="選択してください",
            )
        with row1[1]:
            enemy_dps_1 = st.selectbox(
                "敵DPS 1",
                DPS_HEROES,
                index=None,
                placeholder="選択してください",
            )

        row2 = st.columns(3)
        with row2[0]:
            enemy_dps_2 = st.selectbox(
                "敵DPS 2",
                DPS_HEROES,
                index=None,
                placeholder="選択してください",
            )
        with row2[1]:
            enemy_support_1 = st.selectbox(
                "敵サポート 1",
                SUPPORT_HEROES,
                index=None,
                placeholder="選択してください",
            )
        with row2[2]:
            enemy_support_2 = st.selectbox(
                "敵サポート 2",
                SUPPORT_HEROES,
                index=None,
                placeholder="選択してください",
            )

analyze_clicked = st.button("🔎　敵チームを分析する　→", use_container_width=True)

# -----------------------------
# RESULT
# -----------------------------
if analyze_clicked:
    enemies = [
        enemy_tank,
        enemy_dps_1,
        enemy_dps_2,
        enemy_support_1,
        enemy_support_2,
    ]

    # 未選択の項目を除外
    enemies = [
        enemy
        for enemy in enemies
        if enemy is not None
    ]

    # 敵が1人も選択されていない場合は分析しない
    if not enemies:
        st.warning("⚠️ 敵ヒーローを1人以上選択してください。")
        st.stop()

    results = analyze_matchup(my_hero, enemies)
    recommendations = recommend_heroes(enemies, my_role)
    all_recommendations = recommend_heroes(enemies, my_role, limit=None)

    current_recommendation = next(
        (
            recommendation
            for recommendation in all_recommendations
            if recommendation["hero"] == my_hero
        ),
        None,
    )

    best_recommendation = all_recommendations[0]

    st.markdown("""
    <div class="result-header">
        <h2>✦ 分析結果</h2>
        <p>ANALYSIS RESULT — 敵編成に対するおすすめと危険度</p>
    </div>
    """, unsafe_allow_html=True)

    # Pick change advice
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
            for i, recommendation in enumerate(all_recommendations, start=1)
            if recommendation["hero"] == my_hero
        )

        score_difference = current_score - best_score
        switch_advice = get_switch_advice(score_difference)

        with st.container(border=True):
            st.markdown("### 🔄 ピック変更アドバイス")
            c1, c2, c3 = st.columns(3)
            c1.metric("現在のヒーロー", my_hero)
            c2.metric("現在順位", f"{current_rank}位")
            c3.metric("最上位候補", best_hero)

            if switch_advice == "continue":
                st.success(
                    f"✅ 継続推奨：スコア差は{score_difference}です。"
                    " 今のヒーローをそのまま使っても問題なさそうです。"
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
                    f" {best_hero}の方が今回の敵編成には低リスクです。"
                )

            if switch_advice != "continue":
                reason_parts = []
                if best_easy_enemies:
                    reason_parts.append(
                        '<span class="easy">● 比較的戦いやすい：'
                        + "・".join(best_easy_enemies) + "</span>"
                    )
                if best_neutral_enemies:
                    reason_parts.append(
                        '<span class="neutral">● 五分〜やや注意：'
                        + "・".join(best_neutral_enemies) + "</span>"
                    )
                if best_dangerous_enemies:
                    reason_parts.append(
                        '<span class="danger">● 注意が必要：'
                        + "・".join(best_dangerous_enemies) + "</span>"
                    )

                st.markdown(
                    '<div class="compat"><b>💡 '
                    + best_hero
                    + "を候補にする理由</b><br>"
                    + "<br>".join(reason_parts)
                    + "</div>",
                    unsafe_allow_html=True,
                )

    st.markdown("## 👑 おすすめヒーロー TOP 3")
    st.caption("今回の敵編成に対して、推薦スコアが低い順に表示しています。")

    top_cols = st.columns(3, gap="medium")

    for i, (col, recommendation) in enumerate(
        zip(top_cols, recommendations),
        start=1,
    ):
        hero = recommendation["hero"]
        danger = recommendation["danger"]
        penalty = recommendation["penalty"]
        max_penalty = recommendation["max_penalty"]
        score = recommendation["score"]
        strong_counter_count = recommendation["strong_counter_count"]
        details = recommendation["details"]

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

        compatibility = []
        if easy_enemies:
            compatibility.append(
                '<span class="easy">● 戦いやすい：'
                + "・".join(easy_enemies) + "</span>"
            )
        if neutral_enemies:
            compatibility.append(
                '<span class="neutral">● 注意：'
                + "・".join(neutral_enemies) + "</span>"
            )
        if dangerous_enemies:
            compatibility.append(
                '<span class="danger">● 危険：'
                + "・".join(dangerous_enemies) + "</span>"
            )

        medal = "BEST PICK" if i == 1 else "RECOMMENDED"

        role_badges = {
            "タンク": "🛡️ TANK",
            "DPS": "🎯 DPS",
            "サポート": "✚ SUPPORT",
        }
        role_badge = role_badges.get(my_role, my_role)

        with col:
            st.markdown(
                f"""
                <div class="pick-card rank{i}">
                    <div class="rank-bubble">{i}</div>
                    <div style="
                        display:inline-block;
                        margin-left:8px;
                        padding:5px 10px;
                        border-radius:999px;
                        background:rgba(90,150,255,.12);
                        border:1px solid rgba(90,180,255,.30);
                        font-size:.72rem;
                        font-weight:800;
                        letter-spacing:.06em;
                    ">{role_badge}</div>
                    <div class="pick-name">{hero}</div>
                    <div class="pick-label">{medal}</div>
                    <div class="score-pill">推薦スコア {score}</div>
                    <div class="compat">
                        {"<br>".join(compatibility)}
                    </div>
                    <div class="metric-grid">
                        <div class="mini-metric">
                            <b>{danger}</b><span>合計危険度</span>
                        </div>
                        <div class="mini-metric">
                            <b>{strong_counter_count}</b><span>強カウンター</span>
                        </div>
                        <div class="mini-metric">
                            <b>+{penalty + max_penalty}</b><span>ペナルティ</span>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if strong_counter_count == 0:
                st.success("✅ 強いカウンターなし")
            elif strong_counter_count == 1:
                st.warning("⚠️ 強いカウンターが1人")
            else:
                st.error(f"🚨 強いカウンターが{strong_counter_count}人")

            with st.expander(f"{hero} の相性内訳"):
                for detail in details:
                    enemy = detail["enemy"]
                    enemy_danger = detail["danger"]
                    source = detail["source"]

                    if source == "registered":
                        source_text = "登録済み"
                    elif source == "reverse":
                        source_text = "自動補完"
                    elif source in ("dmon", "dmon_self"):
                        source_text = "D.Mon専用"
                    elif source == "mirror":
                        source_text = "ミラー"
                    else:
                        source_text = "標準値"

                    st.write(
                        f"**{enemy}**　危険度 {enemy_danger}/10 "
                        f"（{source_text}）"
                    )

    with st.expander("📊 全候補ランキングを見る"):
        ranking_data = []
        for i, recommendation in enumerate(all_recommendations, start=1):
            ranking_data.append(
                {
                    "順位": i,
                    "ヒーロー": recommendation["hero"],
                    "推薦スコア": recommendation["score"],
                    "合計危険度": recommendation["danger"],
                    "強カウンター": recommendation["strong_counter_count"],
                    "最大危険度": recommendation["max_danger"],
                }
            )

        st.dataframe(
            ranking_data,
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("## ⚠️ 敵チームの脅威度")
    st.caption("現在選択しているヒーローに対して、危険な相手を上から確認できます。")

    threat_left, threat_right = st.columns([0.58, 0.42], gap="large")

    with threat_left:
        with st.container(border=True):
            for result in results:
                hero = result["hero"]
                danger = result["danger"]
                width = max(5, min(100, danger * 10))
                st.markdown(
                    f"""
                    <div class="threat-row">
                        <div class="threat-name">{hero}</div>
                        <div class="threat-track">
                            <div class="threat-fill" style="width:{width}%"></div>
                        </div>
                        <div class="threat-value">{danger}/10</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    with threat_right:
        with st.container(border=True):
            st.markdown("### 🧠 対策ポイント")
            if results:
                for idx, result in enumerate(results[:3], start=1):
                    st.markdown(
                        f"**{idx}. {result['hero']} — {result['level']}**"
                    )
                    st.write(result["reason"])
                    st.caption(result["advice"])
            else:
                st.write("敵を選択すると対策ポイントが表示されます。")

    with st.expander("🔍 危険な敵の詳細を見る"):
        for result in results:
            hero = result["hero"]
            danger = result["danger"]
            level = result["level"]
            reason = result["reason"]
            advice = result["advice"]

            st.markdown(f"### {level}　{hero}")
            st.write(f"**危険度：{danger}/10**")
            st.write("**なぜ注意？**")
            st.write(reason)
            st.write("**初心者向け対策**")
            st.write(advice)
            st.divider()

st.markdown("""
<div class="footer">
    <span><b>OW COUNTER ASSISTANT</b> — FAN-MADE GAME TOOL</span>
    <span>非公式ファンメイドツールです。Blizzard Entertainmentとは提携・承認関係はありません。</span>
</div>
""", unsafe_allow_html=True)
