import unittest

from aims.ui.main_ui_components.map_component import parse_sequences_string_to_sequence_ids


class MapTestCase(unittest.TestCase):
    def test_parse_sequences(self):
        sequences = parse_sequences_string_to_sequence_ids("sequences: -1")
        print (sequences)
        self.assertEqual(sequences, [-1])
        sequences = parse_sequences_string_to_sequence_ids("sequences: 1, 2, 3, 23")
        print (sequences)
        self.assertEqual(sequences, [1,2,3, 23])  # add assertion here
        sequences = parse_sequences_string_to_sequence_ids("sequences: , 1, 2, 3")
        print (sequences)
        self.assertEqual(sequences, [1,2,3])  # add assertion here


if __name__ == '__main__':
    unittest.main()
