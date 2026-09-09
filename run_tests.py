"""Deterministic regression tests for the existing application logic."""
import random
from analyzer import analyze_matchup
from recommender import recommend_heroes
from heroes import TANK_HEROES, DPS_HEROES, SUPPORT_HEROES
from update_overwatch import entries


def main():
    roles = {'タンク': TANK_HEROES, 'DPS': DPS_HEROES, 'サポート': SUPPORT_HEROES}
    heroes = sum(roles.values(), [])
    for item in entries().values():
        assert 0 <= item['current'] <= 10, item
    for hero in heroes:
        assert analyze_matchup(hero, []) == []
        assert analyze_matchup(hero, ['選択してください']) == []
        assert analyze_matchup(hero, [hero])[0]['danger'] == 5
        result = analyze_matchup(hero, heroes)
        assert len(result) == len(heroes)
        assert all(0 <= row['danger'] <= 10 for row in result)
    rng = random.Random(20260910)
    for i in range(1000):
        enemies = rng.sample(heroes, i % 6)
        for role, candidates in roles.items():
            rows = recommend_heroes(enemies, role, limit=None)
            assert len(rows) == len(candidates)
            assert {row['hero'] for row in rows} == set(candidates)
            keys = [(r['score'],r['strong_counter_count'],r['max_danger'],r['danger']) for r in rows]
            assert keys == sorted(keys)
            for row in rows:
                assert row['danger'] == sum(d['danger'] for d in row['details'])
                assert len(row['details']) == len(enemies)
                assert all(0 <= d['danger'] <= 10 for d in row['details'])
                if not enemies:
                    assert row['score'] == row['danger'] == row['max_danger'] == 0
            assert recommend_heroes(enemies, role) == rows[:3]
    print('PASS: 全52ヒーロー・敵0人・ミラー・ランダム1,000編成×3ロール')


if __name__ == '__main__':
    main()
