"""تست‌های خروجی ابسیدین — ساختار، D-22، داده‌های جدید، اسپلیت جلسات."""
import os, sys, json, time, tempfile, unittest, zipfile
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from hypno.config import Config
from hypno.adapters.store import Store
from hypno.run import App


def _make_app(tmp):
    """ساخت یک App واقعی با دیتابیس تمیز و بدون مغز."""
    cfg = Config(root=tmp, host='127.0.0.1', port=9999,
                 state_dir=tmp, research_dir=tmp,
                 bot_token='', owners=('u',),
                 api_key='', base_url='', model='', dev_user='u')
    return App(cfg)


class StructureTests(unittest.TestCase):
    """بررسی ساختار پوشه‌ها و عدم وجود RAG-Chunks."""

    def test_sources_folder_exists_not_rag_chunks(self):
        with tempfile.TemporaryDirectory() as d:
            app = _make_app(d)
            app.obsidian_export({})
            vault = os.path.join(d, 'obsidian-vault', 'Hypno-Fugu-Vault')
            # Sources/ باید وجود داشته باشد
            self.assertTrue(os.path.isdir(os.path.join(vault, 'Sources')))
            # RAG-Chunks/ نباید وجود داشته باشد
            self.assertFalse(os.path.isdir(os.path.join(vault, 'RAG-Chunks')))

    def test_daily_and_edge_folders_exist(self):
        with tempfile.TemporaryDirectory() as d:
            app = _make_app(d)
            app.obsidian_export({})
            vault = os.path.join(d, 'obsidian-vault', 'Hypno-Fugu-Vault')
            self.assertTrue(os.path.isdir(os.path.join(vault, 'Daily')))
            self.assertTrue(os.path.isdir(os.path.join(vault, 'Edge')))

    def test_obsidian_core_plugins(self):
        with tempfile.TemporaryDirectory() as d:
            app = _make_app(d)
            app.obsidian_export({})
            cp = os.path.join(d, 'obsidian-vault', 'Hypno-Fugu-Vault',
                              '.obsidian', 'core-plugins.json')
            self.assertTrue(os.path.isfile(cp))
            plugins = json.load(open(cp))
            self.assertIn('daily-notes', plugins)
            self.assertIn('graph', plugins)
            self.assertIn('tag-pane', plugins)

    def test_obsidian_daily_notes_config(self):
        with tempfile.TemporaryDirectory() as d:
            app = _make_app(d)
            app.obsidian_export({})
            dn = os.path.join(d, 'obsidian-vault', 'Hypno-Fugu-Vault',
                               '.obsidian', 'daily-notes.json')
            self.assertTrue(os.path.isfile(dn))
            cfg = json.load(open(dn))
            self.assertEqual(cfg['folder'], 'Daily')
            self.assertEqual(cfg['format'], 'YYYY-MM-DD')

    def test_zip_created_and_valid(self):
        with tempfile.TemporaryDirectory() as d:
            app = _make_app(d)
            result = app.obsidian_export({})
            self.assertEqual(result['ok'], 1)
            zp = result['zip_path']
            self.assertTrue(os.path.isfile(zp))
            with zipfile.ZipFile(zp, 'r') as z:
                names = z.namelist()
                # ریشه باید Hypno-Fugu-Vault/ باشد
                self.assertTrue(any(n.startswith('Hypno-Fugu-Vault/') for n in names))
                self.assertTrue(any('.obsidian' in n for n in names))


class D22Tests(unittest.TestCase):
    """بررسی D-22: بدون جارگون و بدون لو دادن مسیر سرور."""

    def test_dashboard_no_server_paths(self):
        with tempfile.TemporaryDirectory() as d:
            app = _make_app(d)
            app.obsidian_export({})
            dash = os.path.join(d, 'obsidian-vault', 'Hypno-Fugu-Vault',
                                '00-Dashboard.md')
            content = open(dash, encoding='utf-8').read()
            # مسیر سرور نباید باشد
            self.assertNotIn(d, content)
            self.assertNotIn('.sqlite', content)
            self.assertNotIn('DB:', content)

    def test_no_rag_jargon_in_folder_names(self):
        with tempfile.TemporaryDirectory() as d:
            app = _make_app(d)
            app.obsidian_export({})
            vault = os.path.join(d, 'obsidian-vault', 'Hypno-Fugu-Vault')
            for root, dirs, files in os.walk(vault):
                for dir_name in dirs:
                    self.assertNotIn('RAG', dir_name,
                                     f'جارگون RAG در نام پوشه: {dir_name}')

    def test_source_type_in_frontmatter_is_source_not_rag(self):
        with tempfile.TemporaryDirectory() as d:
            app = _make_app(d)
            # یک منبع اضافه کن تا فایل ساخته شود
            app.store.add_research(
                'تست بدون جارگون',
                'self-hypnosis safety consent exit routine grounding focus '
                'relaxation attention technique induction deepening',
                'local://test', 'user', 'hypnosis_core safety')
            app.obsidian_export({})
            vault = os.path.join(d, 'obsidian-vault', 'Hypno-Fugu-Vault')
            for fname in os.listdir(os.path.join(vault, 'Sources')):
                if fname.endswith('.md') and fname != 'MOC-Sources.md':
                    content = open(os.path.join(vault, 'Sources', fname),
                                   encoding='utf-8').read()
                    self.assertIn('type: source', content)
                    self.assertNotIn('type: rag_chunk', content)

    def test_brain_name_no_jargon(self):
        with tempfile.TemporaryDirectory() as d:
            app = _make_app(d)
            app.obsidian_export({})
            dash = open(os.path.join(d, 'obsidian-vault', 'Hypno-Fugu-Vault',
                                     '00-Dashboard.md'), encoding='utf-8').read()
            # مغز بدون API key باید فارسی باشد
            self.assertIn('قوانین + منبع', dash)
            self.assertNotIn('fallback', dash)


class DataExportTests(unittest.TestCase):
    """بررسی داده‌های جدید: یادداشت روزانه، امتیازات لبه."""

    def test_daily_notes_export(self):
        with tempfile.TemporaryDirectory() as d:
            app = _make_app(d)
            app.store.add_daily_note('u', 'امروز خوب بود')
            app.obsidian_export({})
            vault = os.path.join(d, 'obsidian-vault', 'Hypno-Fugu-Vault')
            daily_files = os.listdir(os.path.join(vault, 'Daily'))
            self.assertGreater(len(daily_files), 0)

    def test_edge_scores_export(self):
        with tempfile.TemporaryDirectory() as d:
            app = _make_app(d)
            app.store.log_edge_daily('u', 7, 8, 5, 'سبز')
            app.obsidian_export({})
            edge_moc = open(os.path.join(d, 'obsidian-vault', 'Hypno-Fugu-Vault',
                                        'Edge', 'MOC-Edge.md'),
                            encoding='utf-8').read()
            self.assertIn('نمرات لبه', edge_moc)
            self.assertIn('7', edge_moc)
            self.assertIn('سبز', edge_moc)

    def test_lab_results_export(self):
        with tempfile.TemporaryDirectory() as d:
            app = _make_app(d)
            app.store.add_lab_result('u', 'quiz',
                                      {'guess': 'سبز', 'answer': 'سبز',
                                       'correct': True})
            app.store.add_lab_result('u', 'decision',
                                      {'dominant': 'خود', 'body_share': 0.3,
                                       'self_share': 0.5, 'super_share': 0.2})
            app.obsidian_export({})
            edge_moc = open(os.path.join(d, 'obsidian-vault', 'Hypno-Fugu-Vault',
                                        'Edge', 'MOC-Edge.md'),
                            encoding='utf-8').read()
            self.assertIn('کوییز', edge_moc)
            self.assertIn('تصمیم', edge_moc)
            self.assertIn('✅', edge_moc)

    def test_empty_state_not_dead_end(self):
        """D-19: حتی بدون داده هم نقشه‌ها ساخته شوند."""
        with tempfile.TemporaryDirectory() as d:
            app = _make_app(d)
            app.obsidian_export({})
            vault = os.path.join(d, 'obsidian-vault', 'Hypno-Fugu-Vault')
            # همه MOCها باید وجود داشته باشند
            for path in ('Memory/MOC-Memory.md', 'Sessions/MOC-Sessions.md',
                         'Sources/MOC-Sources.md', 'Edge/MOC-Edge.md'):
                p = os.path.join(vault, path)
                self.assertTrue(os.path.isfile(p), f'{path} وجود ندارد')


class SessionsSplitTests(unittest.TestCase):
    """بررسی اسپلیت جلسات به تفکیک روز."""

    def test_multi_day_split(self):
        with tempfile.TemporaryDirectory() as d:
            app = _make_app(d)
            now = int(time.time())
            day1 = now - 86400
            day2 = now
            # log() از now() داخلی استفاده می‌کند، پس مستقیم insert می‌کنیم
            with app.store.conn() as db:
                db.execute("INSERT INTO messages(user_id,role,content,meta,created_at) VALUES(?,?,?,?,?)",
                          ('u', 'user', 'سلام روز اول', '{}', day1))
                db.execute("INSERT INTO messages(user_id,role,content,meta,created_at) VALUES(?,?,?,?,?)",
                          ('u', 'assistant', 'خوش آمدی', '{}', day1))
                db.execute("INSERT INTO messages(user_id,role,content,meta,created_at) VALUES(?,?,?,?,?)",
                          ('u', 'user', 'سلام روز دوم', '{}', day2))
            app.obsidian_export({})
            sess_dir = os.path.join(d, 'obsidian-vault', 'Hypno-Fugu-Vault',
                                    'Sessions')
            md_files = [f for f in os.listdir(sess_dir)
                        if f.endswith('.md') and f != 'MOC-Sessions.md']
            # باید حداقل ۲ فایل جداگانه باشد
            self.assertGreaterEqual(len(md_files), 2)

    def test_moc_sessions_links(self):
        with tempfile.TemporaryDirectory() as d:
            app = _make_app(d)
            app.store.log('u', 'user', 'تست', {})
            app.obsidian_export({})
            moc = open(os.path.join(d, 'obsidian-vault', 'Hypno-Fugu-Vault',
                                    'Sessions', 'MOC-Sessions.md'),
                       encoding='utf-8').read()
            self.assertIn('[[Sessions/', moc)


class MemoryTimestampTests(unittest.TestCase):
    """بررسی timestamp در حافظه."""

    def test_memory_has_timestamp(self):
        with tempfile.TemporaryDirectory() as d:
            app = _make_app(d)
            app.store.add_memory('u', 'preference', 'آرام‌سازی')
            app.obsidian_export({})
            moc = open(os.path.join(d, 'obsidian-vault', 'Hypno-Fugu-Vault',
                                    'Memory', 'MOC-Memory.md'),
                       encoding='utf-8').read()
            # باید فرمت YYYY-MM-DD HH:MM داشته باشد
            self.assertRegex(moc, r'\(\d{4}-\d{2}-\d{2} \d{2}:\d{2}\)')


class SourceMocTests(unittest.TestCase):
    """بررسی نقشهٔ منابع."""

    def test_source_moc_exists_and_links(self):
        with tempfile.TemporaryDirectory() as d:
            app = _make_app(d)
            app.store.add_research(
                'ایمنی هیپنوتیزم',
                'safety consent exit routine grounding focus relaxation '
                'attention technique induction deepening self-hypnosis',
                'local://safety', 'user', 'hypnosis_core safety')
            app.obsidian_export({})
            moc = open(os.path.join(d, 'obsidian-vault', 'Hypno-Fugu-Vault',
                                    'Sources', 'MOC-Sources.md'),
                       encoding='utf-8').read()
            self.assertIn('[[', moc)
            self.assertIn('ایمنی', moc)


if __name__ == '__main__':
    unittest.main()
