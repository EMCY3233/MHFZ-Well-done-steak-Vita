import unittest
from layer_union import summarize


def row(layer, path='data/a', size=2, digest='a'):
    return dict(RemotePath=f'/ux0:/{layer}/PCSG00350/{path}', Bytes=str(size), SHA256=digest * 64)


class LayerUnionTests(unittest.TestCase):
    def test_precedence_and_collision_classification(self):
        result = summarize([row('app'), row('patch'), row('rePatch', size=3, digest='b')])
        self.assertEqual((result['union_files'], result['union_bytes']), (1, 3))
        self.assertEqual(result['transitions'][1]['identical'], 1)
        self.assertEqual(result['transitions'][2]['different'], 1)
        self.assertEqual(result['winning_layers'], {'rePatch': 1})

    def test_duplicates_rejected(self):
        with self.assertRaises(ValueError):
            summarize([row('app'), row('app')])

    def test_untrusted_inventory_fields_rejected(self):
        for value in [row('app', '../a'), row('app', 'a//b'), row('app', size=-1), row('app', digest='z'), row('other')]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                summarize([value])


if __name__ == '__main__':
    unittest.main()