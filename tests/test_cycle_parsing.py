"""Contract tests for the model-response parser.

The model is asked for strict JSON but frequently wraps it in prose or
fences, returns a bare array instead of an object, or includes a malformed
row. Each of these must degrade gracefully — a quiet candidate set, never
a crash.
"""

import unittest

from ofn.adapters.cycle_parsing import parse_candidates, json_dumps_safe


OBJECT_SHAPE = '{"candidates":[{"key":"foot-care-am","title":"Foot care AM","style_id":"educational","framing":"beauty","confidence":0.8}]}'
BARE_ARRAY = '[{"key":"a","title":"A","style_id":"educational","framing":"beauty","confidence":0.7}]'
FENCED = '```json\n{"candidates":[{"key":"b","title":"B","style_id":"x","framing":"beauty","confidence":0.6}]}\n```'
PROSE_WRAPPED = 'Here are the ideas:\n{"candidates":[{"key":"c","title":"C","style_id":"x","framing":"beauty","confidence":0.5}]}\nHope this helps!'
ONE_BAD_ROW = '{"candidates":[{"key":"good","title":"Good","style_id":"x","framing":"beauty","confidence":0.8},{"key":"","title":"no key"},{"title":"no key either"}]}'
EMPTY = ''
GARBAGE = 'I cannot help with that.'


class TestParseObjectShape(unittest.TestCase):
    def test_object_shape_parsed(self):
        cs = parse_candidates(OBJECT_SHAPE, now_epoch_s=1700000000)
        self.assertEqual(len(cs), 1)
        self.assertEqual(cs[0].key, "foot-care-am")
        self.assertEqual(cs[0].confidence, 0.8)


class TestParseBareArray(unittest.TestCase):
    def test_bare_array_fallback(self):
        cs = parse_candidates(BARE_ARRAY, now_epoch_s=1700000000)
        self.assertEqual(len(cs), 1)
        self.assertEqual(cs[0].key, "a")


class TestParseFenced(unittest.TestCase):
    def test_markdown_fences_stripped(self):
        cs = parse_candidates(FENCED, now_epoch_s=1700000000)
        self.assertEqual(len(cs), 1)
        self.assertEqual(cs[0].key, "b")


class TestParseProseWrapped(unittest.TestCase):
    def test_prose_around_json_tolerated(self):
        cs = parse_candidates(PROSE_WRAPPED, now_epoch_s=1700000000)
        self.assertEqual(len(cs), 1)
        self.assertEqual(cs[0].key, "c")


class TestParseBadRowSkipped(unittest.TestCase):
    def test_one_bad_row_does_not_void_the_rest(self):
        cs = parse_candidates(ONE_BAD_ROW, now_epoch_s=1700000000)
        self.assertEqual(len(cs), 1)
        self.assertEqual(cs[0].key, "good")


class TestParseEmpty(unittest.TestCase):
    def test_empty_returns_nothing(self):
        self.assertEqual(parse_candidates(""), ())
        self.assertEqual(parse_candidates("   "), ())

    def test_garbage_returns_nothing(self):
        self.assertEqual(parse_candidates(GARBAGE), ())


class TestCandidateGetsEvidence(unittest.TestCase):
    """A candidate with no observations still gets one synthetic observation
    so the scout's screen (which requires evidence) can judge it. This is
    honest: the source is 'model_proposal', not a measured trend."""

    def test_model_sourced_observation_attached(self):
        cs = parse_candidates(
            '{"candidates":[{"key":"x","title":"X","style_id":"e",'
            '"framing":"beauty","confidence":0.9}]}',
            now_epoch_s=1700000000)
        self.assertEqual(len(cs), 1)
        self.assertEqual(len(cs[0].observations), 1)
        self.assertEqual(cs[0].observations[0].source_id, "model_proposal")


class TestJsonDumpsSafe(unittest.TestCase):
    def test_never_raises(self):
        class Weird:
            pass
        # Should not raise even on a non-serialisable object.
        out = json_dumps_safe({"x": Weird()})
        self.assertIn("x", out)


if __name__ == "__main__":
    unittest.main()
