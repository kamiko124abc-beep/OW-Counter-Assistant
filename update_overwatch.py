#!/usr/bin/env python3
"""Official patch -> review JSON -> explicit approval. Python standard library only."""
import argparse
import ast
import copy
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import urllib.request
import urllib.parse
import uuid

ROOT = Path(__file__).resolve().parent
URL = 'https://overwatch.blizzard.com/en-us/news/patch-notes/live/'
TABLES = {'all_matchups_extra.py': ['ALL_EXTRA_MATCHUPS'],
          'matchups.py': ['MATCHUPS'],
          'dmon_matchups.py': ['D_MON_DANGER', 'D_MON_SELF_DANGER']}
ENGLISH = ['D.Mon','D.Va','Doomfist','Domina','Hazard','Junker Queen','Mauga','Orisa','Ramattra','Reinhardt','Roadhog','Sigma','Winston','Wrecking Ball','Zarya','Anran','Ashe','Bastion','Cassidy','Echo','Emre','Freja','Genji','Hanzo','Junkrat','Mei','Pharah','Reaper','Shion','Sojourn','Soldier: 76','Sombra','Symmetra','Torbjörn','Tracer','Vendetta','Venture','Widowmaker','Ana','Baptiste','Brigitte','Illari','Jetpack Cat','Juno','Kiriko','Lifeweaver','Lúcio','Mercy','Mizuki','Moira','Wuyang','Zenyatta']


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temp.replace(path)


class Node:
    def __init__(self, tag='', attrs=()):
        self.tag, self.attrs, self.children = tag, dict(attrs), []

    def find(self, cls):
        result = [self] if cls in self.attrs.get('class', '').split() else []
        for child in self.children:
            if isinstance(child, Node):
                result.extend(child.find(cls))
        return result

    def text(self):
        return ' '.join(' '.join(c.text() if isinstance(c, Node) else c for c in self.children).split())


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node()
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        node = Node(tag, attrs)
        self.stack[-1].children.append(node)
        if tag not in {'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}:
            self.stack.append(node)

    def handle_endtag(self, tag):
        for i in range(len(self.stack)-1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                break

    def handle_data(self, text):
        self.stack[-1].children.append(text)


def parse_patch(html):
    from heroes import TANK_HEROES, DPS_HEROES, SUPPORT_HEROES
    aliases = dict(zip([x.casefold() for x in ENGLISH], TANK_HEROES+DPS_HEROES+SUPPORT_HEROES))
    page = Page()
    page.feed(html)
    patches = []
    for block in page.root.find('PatchNotes-patch'):
        titles = block.find('PatchNotes-patchTitle')
        if not titles or 'Retail Patch Notes' not in titles[0].text():
            continue
        title = titles[0].text()
        match = re.search(r'([A-Z][a-z]+ \d{1,2}, \d{4})', title)
        if not match:
            raise ValueError('公式パッチの日付形式が変わりました。解析を停止します。')
        date = datetime.strptime(match[1], '%B %d, %Y').date().isoformat()
        heroes = []
        def flatten(node):
            yield node
            for child in node.children:
                if isinstance(child, Node):
                    yield from flatten(child)
        mode = 'live'
        for node in flatten(block):
            if node.tag == 'h4' and node.text() == 'Stadium Updates':
                mode = 'stadium'
            if node.tag == 'h4' and node.text() == 'Bug Fixes':
                mode = 'bugfix'
            if mode == 'bugfix' and node.tag == 'strong' and node.text().casefold() in aliases:
                name = node.text()
                heroes.append({'english': name, 'hero': aliases[name.casefold()], 'mode': mode, 'notes': 'Bug fix: see full patch notes.'})
            if 'PatchNotesHeroUpdate' not in node.attrs.get('class', '').split():
                continue
            names = node.find('PatchNotesHeroUpdate-name')
            if not names:
                raise ValueError('ヒーロー見出しを解析できません。')
            name = names[0].text()
            heroes.append({'english': name, 'hero': aliases.get(name.casefold()), 'mode': mode, 'notes': node.text()})
        patches.append({'date': date, 'title': title, 'heroes': heroes, 'notes': block.text()})
    if not patches:
        raise ValueError('公式パッチを検出できません。HTML形式・接続を確認してください。')
    return max(patches, key=lambda p: p['date'])


def entries(root=ROOT):
    """Locate only literal numeric leaves; byte spans preserve every comment/string."""
    result = {}
    for filename, names in TABLES.items():
        raw = (root / filename).read_bytes()
        lines = raw.splitlines(keepends=True)
        offsets = [0]
        for line in lines:
            offsets.append(offsets[-1] + len(line))
        tree = ast.parse(raw)
        def walk(node, path, table):
            if isinstance(node, ast.Dict):
                for key, value in zip(node.keys, node.values):
                    walk(value, path + [ast.literal_eval(key)], table)
            elif isinstance(node, ast.Constant) and type(node.value) is int:
                if table == 'MATCHUPS' and path[-1] != 'danger':
                    return
                if table == 'D_MON_DANGER':
                    hero, enemy = path[0], 'D.Mon'
                elif table == 'D_MON_SELF_DANGER':
                    hero, enemy = 'D.Mon', path[0]
                else:
                    hero, enemy = path[:2]
                key = json.dumps([filename, table, path], ensure_ascii=False)
                result[key] = {'file': filename, 'table': table, 'path': path, 'hero': hero, 'enemy': enemy,
                               'current': node.value, 'start': offsets[node.lineno-1]+node.col_offset,
                               'end': offsets[node.end_lineno-1]+node.end_col_offset}
        for node in tree.body:
            if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id in names for t in node.targets):
                walk(node.value, [], node.targets[0].id)
    return result


def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args], text=True).strip()


def clean_check():
    if git('status', '--porcelain'):
        raise ValueError('未コミットの変更があります。先に保存・コミットしてから再実行してください。')


@contextmanager
def lock():
    path = ROOT / '.update.lock'
    try:
        path.mkdir()
    except FileExistsError:
        raise ValueError('別の更新が実行中です。終了済みの場合だけ .update.lock を削除してください。')
    try:
        yield
    finally:
        path.rmdir()


def backup():
    target = ROOT / '.update_backups' / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')+'-'+uuid.uuid4().hex[:8])
    target.mkdir(parents=True)
    for name in git('ls-files', '-z').split('\0'):
        if name and (ROOT/name).is_file():
            dest = target/name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT/name, dest)
    write_json(target/'backup_info.json', {'created_at': now(), 'head': git('rev-parse','HEAD')})
    print('バックアップ:', target)
    return target


def checks():
    for path in ROOT.rglob('*.py'):
        if any(p in {'.git','.venv','venv','.update_backups','__pycache__'} for p in path.parts):
            continue
        compile(path.read_bytes(), str(path), 'exec')
    subprocess.run([sys.executable, '-B', str(ROOT/'run_tests.py')], cwd=ROOT, check=True)
    subprocess.run([sys.executable, '-B', '-m', 'unittest', 'test_update_overwatch'], cwd=ROOT, check=True)
    for path in sorted(ROOT.glob('*random*test*.py')):
        subprocess.run([sys.executable, '-B', str(path)], cwd=ROOT, check=True)
    return {'syntax': 'passed', 'run_tests': 'passed', 'updater_tests': 'passed', 'checked_at': now()}


def commit(paths, message):
    git('add', '--', *paths)
    try:
        git('commit', '-m', message)
    except Exception:
        git('reset', '--', *paths)
        raise
    print('コミット:', git('rev-parse','--short','HEAD'), '（pushはしていません）')


def prepare():
    clean_check()
    backup()
    req = urllib.request.Request(URL, headers={'User-Agent': 'OW-Counter-Assistant/1.0'})
    with urllib.request.urlopen(req, timeout=45) as response:
        if urllib.parse.urlparse(response.url).hostname != 'overwatch.blizzard.com':
            raise ValueError('公式以外へのリダイレクトを拒否しました。')
        raw = response.read(5_000_001)
    if len(raw) > 5_000_000:
        raise ValueError('ページサイズが想定を超えています。')
    patch = parse_patch(raw.decode('utf-8'))
    patch.update({'url': URL, 'fetched_at': now(), 'html_sha256': digest(raw)})
    patch_id = patch['date'] + '-' + digest(patch['notes'].encode())[:12]
    directory = ROOT/'updates'/patch_id
    if directory.exists():
        print('取得済みです。既存のレビューを維持します:', directory)
        return
    changed = {h['hero'] for h in patch['heroes'] if h['hero'] and h['mode'] == 'live'}
    candidates = []
    for key, entry in entries().items():
        if entry['hero'] == entry['enemy'] or not changed.intersection([entry['hero'],entry['enemy']]):
            continue
        item = {k:v for k,v in entry.items() if k not in {'start','end'}}
        item.update({'id': key, 'proposed': entry['current'], 'approved': False,
                     'suggested_range': [max(0,entry['current']-1),min(10,entry['current']+1)],
                     'reason': '公式に相性値はないため据え置きを初期提案。対象ヒーローの変更・距離・5v5/6v6条件を確認し、必要なら±1から手動評価。'})
        candidates.append(item)
    review = {'schema': 1, 'patch_id': patch_id, 'status': 'pending',
              'source_hashes': {f:digest((ROOT/f).read_bytes()) for f in TABLES},
              'candidates': candidates}
    report = checks()
    directory.mkdir(parents=True)
    (directory/'source.html').write_bytes(raw)
    write_json(directory/'patch.json',patch)
    write_json(directory/'proposal.json',review)
    write_json(directory/'tests.json',report)
    names = list(dict.fromkeys(h['hero'] or h['english']+'（未登録）' for h in patch['heroes']))
    (directory/'REVIEW.md').write_text('# '+patch['title']+'\n\n公式: '+URL+'\n\n取得日時: '+patch['fetched_at']+'\n\n変更ヒーロー: '+ '、'.join(names)+'\n\n相性候補: '+str(len(candidates))+'件。初期提案値は現在値。proposal.json の proposed を修正し、採用する行だけ approved を true にしてください。相性値は公式値ではありません。原文・モード条件は patch.json を参照。\n',encoding='utf-8')
    write_json(ROOT/'updates/latest.json', {'patch_id':patch_id})
    commit(['updates'], 'Prepare Overwatch patch review '+patch_id)
    print('対象パッチ:', patch['title'])
    print('変更ヒーロー:', '、'.join(names))
    print('提案:', directory/'proposal.json', len(candidates),'件')


def validate(review, root=ROOT):
    if review.get('schema') != 1 or review.get('status') != 'pending':
        raise ValueError('未承認の提案ではありません。')
    if review.get('source_hashes') != {f:digest((root/f).read_bytes()) for f in TABLES}:
        raise ValueError('提案作成後に相性データが変わりました。古い提案の適用を拒否します。')
    current = entries(root)
    selected, seen = [], set()
    for item in review['candidates']:
        key = item['id']
        if key in seen or key not in current:
            raise ValueError('候補IDが不正または重複しています。')
        seen.add(key)
        original = current[key]
        if any(item.get(k) != original[k] for k in ('file','table','path','hero','enemy','current')):
            raise ValueError('候補の識別情報が変更されています。')
        if type(item['approved']) is not bool or type(item['proposed']) is not int or not 0 <= item['proposed'] <= 10:
            raise ValueError('approved は true/false、proposed は0〜10の整数にしてください。')
        if item['approved'] and item['proposed'] != item['current']:
            selected.append((original,item['proposed']))
    if not selected:
        raise ValueError('採用する変更がありません。proposed を修正し approved を true にしてください。')
    return selected


def apply_values(selected, root=ROOT):
    for filename in TABLES:
        edits = [(entry,value) for entry,value in selected if entry['file'] == filename]
        if edits:
            path = root/filename
            data = path.read_bytes()
            for entry,value in sorted(edits, key=lambda pair:pair[0]['start'], reverse=True):
                data = data[:entry['start']] + str(value).encode() + data[entry['end']:]
            path.write_bytes(data)


def recommended_review(review):
    """The explicit CLI command grants approval; preparation never does."""
    result = copy.deepcopy(review)
    count = 0
    for item in result['candidates']:
        recommended = item.get('recommended', False)
        if type(recommended) is not bool:
            raise ValueError('recommended は true/false にしてください。')
        item['approved'] = recommended
        count += recommended and item['proposed'] != item['current']
    if not count:
        raise ValueError('具体的な推奨変更はまだありません。レビューの作成が必要です。')
    result['approval_method'] = 'explicit --approve-recommended command'
    return result


def approve(recommended=False):
    latest = json.loads((ROOT/'updates/latest.json').read_text())['patch_id']
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}-[0-9a-f]{12}', latest):
        raise ValueError('パッチIDが不正です。')
    relative = 'updates/'+latest+'/proposal.json'
    path = ROOT/relative
    if git('diff','--cached','--name-only'):
        raise ValueError('ステージ済み変更があります。先にコミットしてください。')
    dirty = set(git('diff','--name-only').splitlines()) | set(git('ls-files','--others','--exclude-standard').splitlines())
    if dirty - {relative}:
        raise ValueError('提案以外に未コミット変更があります。先にコミットしてください。')
    review = json.loads(path.read_text())
    if review.get('patch_id') != latest:
        raise ValueError('パッチIDが一致しません。')
    if recommended:
        review = recommended_review(review)
    selected = validate(review)
    saved = backup()
    originals = {f:(ROOT/f).read_bytes() for f in TABLES}
    proposal_before = path.read_bytes()
    report_path = path.parent/'applied_tests.json'
    try:
        apply_values(selected)
        report = checks()
        review.update({'status':'applied','applied_at':now(),'backup':str(saved)})
        write_json(path,review)
        write_json(report_path,report)
        commit([*TABLES, relative, str(report_path.relative_to(ROOT))], 'Apply reviewed Overwatch patch '+latest)
    except BaseException:
        for filename,data in originals.items():
            (ROOT/filename).write_bytes(data)
        path.write_bytes(proposal_before)
        report_path.unlink(missing_ok=True)
        raise
    print(len(selected),'件の承認値を反映しました。')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument('--approve', action='store_true', help='編集済み提案の approved=true の変更を反映')
    actions.add_argument('--approve-recommended', action='store_true', help='レビューの推奨変更を一括承認して反映')
    actions.add_argument('--check', action='store_true', help='検証のみ')
    args = parser.parse_args()
    try:
        with lock():
            if args.check:
                print(checks())
            elif args.approve_recommended:
                approve(recommended=True)
            elif args.approve:
                approve()
            else:
                prepare()
    except Exception as exc:
        print('更新を停止しました:', exc, file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
