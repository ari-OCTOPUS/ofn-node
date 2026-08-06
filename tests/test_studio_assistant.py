import os, tempfile, unittest
from ofn.adapters.studio_assistant import StudioAssistantStore

class TestStudioAssistant(unittest.TestCase):
    def setUp(self):
        self.d=tempfile.TemporaryDirectory(); self.addCleanup(self.d.cleanup)
        self.s=StudioAssistantStore(os.path.join(self.d.name,'a.sqlite'))
        self.addCleanup(self.s.close)
    def test_seed_is_persistent_and_searchable(self):
        self.s.ingest_text('studio','seed','راهنما','قیمت گذاری شروع باید ساده باشد. امنیت و حریم خصوصی مهم است.',now_epoch_s=1)
        out=self.s.answer_local('studio','قیمت گذاری')
        self.assertEqual(out['mode'],'rag')
        self.assertTrue(out['sources'])
        self.assertIn('قیمت',out['answer'])
    def test_empty_question_returns_random_help(self):
        self.s.ingest_text('studio','seed','راهنما','نور نرم و نظم محتوا کمک می‌کند.',now_epoch_s=1)
        self.assertEqual(self.s.answer_local('studio','')['mode'],'rag')

    def test_chat_turns_are_persistent(self):
        self.s.record_chat('studio','سلام','جواب',[],now_epoch_s=2)
        h=self.s.chat_history('studio')
        self.assertEqual(h[0]['user'],'سلام')
        self.assertEqual(h[0]['assistant'],'جواب')

if __name__ == '__main__': unittest.main()

class TestRandomSuggestionShape(unittest.TestCase):
    def test_empty_question_shuffles_generic_tips_when_no_keyword_matches(self):
        d=tempfile.TemporaryDirectory(); self.addCleanup(d.cleanup)
        s=StudioAssistantStore(os.path.join(d.name,'a.sqlite')); self.addCleanup(s.close)
        s.ingest_text('studio','seed','راهنما','چیز عمومی بدون کلیدواژه',now_epoch_s=1)
        outs={s.answer_local('studio','')['answer'] for _ in range(12)}
        self.assertGreater(len(outs),1)


class TestWarmCopyAndNoTechnicalWords(unittest.TestCase):
    """The suggestion copy is simple, warm, non-technical, and never leaks a
    forbidden technical word (RAG, model, token, API, …) into what she reads."""

    FORBIDDEN = ('RAG', 'model', 'token', 'API', 'schema', 'payload',
                 'inference', 'database', 'backend', 'PPV', 'subscription')

    def setUp(self):
        d = tempfile.TemporaryDirectory(); self.addCleanup(d.cleanup)
        self.s = StudioAssistantStore(os.path.join(d.name, 'a.sqlite'))
        self.addCleanup(self.s.close)
        # A seed chunk carrying no keyword, so the generic warm pool is used.
        self.s.ingest_text('studio', 'seed', 'راهنما',
                           'چیز عمومی بدون کلیدواژه', now_epoch_s=1)

    def _answers(self):
        return {self.s.answer_local('studio', '')['answer'] for _ in range(20)}

    def test_the_warm_header_is_used(self):
        self.assertTrue(all(a.startswith('یه پیشنهاد کوچیک:') for a in self._answers()))

    def test_a_friendly_tip_is_present_in_the_pool(self):
        joined = '\n'.join(self._answers())
        # At least one of the warm, girl-friendly lines from the directive.
        self.assertTrue(
            'قشنگ انتخاب کن' in joined or 'کپشن کوتاه' in joined
            or 'آلبوم کوچیک' in joined or 'حس خوبی' in joined,
            "none of the warm suggestion lines are present in the pool")

    def test_no_forbidden_technical_word_leaks(self):
        for a in self._answers():
            for word in self.FORBIDDEN:
                self.assertNotIn(word, a,
                                 f"forbidden word '{word}' leaked into a suggestion")

    def test_price_tip_is_warm_and_non_technical(self):
        self.s.ingest_text('studio', 'seed', 'راهنما', 'قیمت گذاری ساده',
                           now_epoch_s=2)
        a = self.s.answer_local('studio', 'قیمت')['answer']
        self.assertIn('قیمت', a)
        for word in self.FORBIDDEN:
            self.assertNotIn(word, a)

