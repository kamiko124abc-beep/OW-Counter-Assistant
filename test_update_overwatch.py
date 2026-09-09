import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
import update_overwatch as u


def block(date, name='D.Va'):
    return '<div class="PatchNotes-patch"><h3 class="PatchNotes-patchTitle">Overwatch Retail Patch Notes – '+date+'</h3><div class="PatchNotesHeroUpdate"><h5 class="PatchNotesHeroUpdate-name">'+name+'</h5><div>Health increased (5v5).</div></div></div>'


class Tests(unittest.TestCase):
    def test_latest_and_alias(self):
        p = u.parse_patch(block('September 1, 2026')+block('September 8, 2026','wrecking Ball'))
        self.assertEqual(p['date'],'2026-09-08')
        self.assertEqual(p['heroes'][0]['hero'],'レッキング・ボール')

    def test_modes_and_bugfixes(self):
        html = block('September 8, 2026')
        extra = '<h4>Stadium Updates</h4><div class="PatchNotesHeroUpdate"><h5 class="PatchNotesHeroUpdate-name">Ana</h5></div><h4>Bug Fixes</h4><strong>Mercy</strong>'
        html = html[:-6] + extra + '</div>'
        heroes = u.parse_patch(html)['heroes']
        self.assertEqual([h['mode'] for h in heroes], ['live','stadium','bugfix'])
        self.assertEqual(heroes[-1]['hero'], 'マーシー')

    def test_unknown_and_invalid(self):
        self.assertIsNone(u.parse_patch(block('September 8, 2026','New Hero'))['heroes'][0]['hero'])
        with self.assertRaises(ValueError):
            u.parse_patch('<html>Maintenance</html>')

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        for f in u.TABLES:
            shutil.copy2(u.ROOT/f,self.root/f)
        self.items = u.entries(self.root)
        self.review = {'schema':1,'status':'pending','source_hashes':{f:u.digest((self.root/f).read_bytes()) for f in u.TABLES},'candidates':[]}
        for key,e in self.items.items():
            item = {k:v for k,v in e.items() if k not in {'start','end'}}
            item.update(id=key, proposed=e['current'], approved=False)
            self.review['candidates'].append(item)

    def tearDown(self):
        self.temp.cleanup()

    def select(self):
        item = self.review['candidates'][0]
        item.update(proposed=(item['current']+1)%11, approved=True)
        return item

    def test_apply_preserves_other_entries_and_strings(self):
        chosen = self.select()
        selected = u.validate(self.review,self.root)
        before = {f:(self.root/f).read_bytes() for f in u.TABLES}
        u.apply_values(selected,self.root)
        after = u.entries(self.root)
        for key,e in after.items():
            self.assertEqual(e['current'],chosen['proposed'] if key == chosen['id'] else self.items[key]['current'])
        entry,value = selected[0]
        expected = before[entry['file']][:entry['start']]+str(value).encode()+before[entry['file']][entry['end']:]
        self.assertEqual((self.root/entry['file']).read_bytes(),expected)

    def test_recommended_only_and_no_mutation(self):
        item = self.review['candidates'][0]
        item.update(recommended=True, proposed=(item['current']+1)%11)
        other = self.review['candidates'][1]
        other.update(approved=True, proposed=(other['current']+1)%11)
        selected_review = u.recommended_review(self.review)
        selected = u.validate(selected_review, self.root)
        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[0][0]['path'], item['path'])
        self.assertFalse(item['approved'])
        self.assertFalse(selected_review['candidates'][1]['approved'])

    def test_recommended_missing_or_invalid(self):
        with self.assertRaises(ValueError): u.recommended_review(self.review)
        self.review['candidates'][0]['recommended'] = 'true'
        with self.assertRaises(ValueError): u.recommended_review(self.review)

    def test_unapproved_rejected(self):
        with self.assertRaises(ValueError): u.validate(self.review,self.root)

    def test_invalid_values_and_duplicate(self):
        item = self.select()
        for value in [-1,11,True,1.5,'6']:
            item['proposed'] = value
            with self.assertRaises(ValueError): u.validate(self.review,self.root)
        item['proposed'] = 1
        self.review['candidates'].append(copy.deepcopy(item))
        with self.assertRaises(ValueError): u.validate(self.review,self.root)

    def test_stale_rejected(self):
        self.select()
        with (self.root/'matchups.py').open('a') as f: f.write('\n')
        with self.assertRaises(ValueError): u.validate(self.review,self.root)

    def test_failed_checks_restore(self):
        self.select()
        patch_id='2026-09-08-0123456789ab'
        self.review['patch_id']=patch_id
        folder=self.root/'updates'/patch_id
        u.write_json(self.root/'updates/latest.json',{'patch_id':patch_id})
        u.write_json(folder/'proposal.json',self.review)
        before={f:(self.root/f).read_bytes() for f in u.TABLES}
        with patch.object(u,'ROOT',self.root), patch.object(u,'git',return_value=''), patch.object(u,'backup',return_value=self.root), patch.object(u,'checks',side_effect=RuntimeError('failure')), patch.object(u,'validate',return_value=u.validate(self.review,self.root)), patch.object(u,'apply_values',side_effect=lambda s: apply_real(s,self.root)):
            with self.assertRaises(RuntimeError): u.approve()
        for f,data in before.items(): self.assertEqual((self.root/f).read_bytes(),data)
        self.assertEqual(json.loads((folder/'proposal.json').read_text())['status'],'pending')


apply_real=u.apply_values
if __name__ == '__main__': unittest.main()
