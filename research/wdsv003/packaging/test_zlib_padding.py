import unittest
import zlib
from zlib_padding import inspect_segment


class PaddingTests(unittest.TestCase):
    def test_all_padding_lengths(self):
        seen = set()
        for length in range(1, 100):
            payload = bytes(range(length))
            stream = zlib.compress(payload)
            padding = (-len(stream)) % 4
            seen.add(padding)
            self.assertTrue(inspect_segment(stream + b'\0'*padding, length)['matches_pinned_padding_policy'])
        self.assertEqual(seen, {0, 1, 2, 3})

    def test_extra_and_nonzero_tail_rejected_as_policy(self):
        stream = zlib.compress(b'abc')
        for tail in [b'\0'*21, b'X', b'\0'*((-len(stream)) % 4 + 4)]:
            self.assertFalse(inspect_segment(stream + tail, 3)['matches_pinned_padding_policy'])

    def test_wrong_alignment_rejected_as_policy(self):
        stream = zlib.compress(b'abc')
        self.assertFalse(inspect_segment(stream, 3)['matches_pinned_padding_policy'])

    def test_bad_stream_and_size(self):
        stream = zlib.compress(b'abc')
        for raw, size in [(stream[:-1], 3), (stream, 2), (stream, 4), (b'garbage', 3), (stream, -1)]:
            with self.assertRaises((ValueError, zlib.error)):
                inspect_segment(raw, size)