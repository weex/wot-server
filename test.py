import unittest

from weboftrust import (load_data, calc_paths_and_ranks, get_capacity,
                       derive_capacities, calculate_score, calculate_score_for_all,
                       update_scores_from_one_trust)

class TestWebOfTrust(unittest.TestCase):
    def test_paths_and_ranks(self):
        """
        Test generating paths and ranks for simplest web 
        """
        trusts, G = load_data("testdata/test01.csv")
        source = "0" 
        paths, ranks = calc_paths_and_ranks(G, trusts, source)

        self.assertEqual(paths, {'0': ['0'], '1': ['0', '1'], '2': ['0', '1', '2']})
        self.assertEqual(ranks, {('0', '0'): 0, ('0', '1'): 1, ('0', '2'): 2, ('1', '3'): -1})
        self.assertFalse('3' in G)

    def test_get_capacity(self):
        """
        Test converting rank to capacity 
        """
        self.assertEqual(get_capacity(-1), 0)
        self.assertEqual(get_capacity(0), 100)
        self.assertEqual(get_capacity(1), 40)
        self.assertEqual(get_capacity(4), 2)
        self.assertEqual(get_capacity(23), 1)
        self.assertEqual(get_capacity(255), 1)

    def test_derive_capacities(self):
        """
        Test converting ranks dict to capacities 
        """
        trusts, G = load_data("testdata/test01.csv")
        source = "0" 
        paths, ranks = calc_paths_and_ranks(G, trusts, source)

        self.assertEqual(derive_capacities(ranks),
                         {('0', '0'): 100, ('0', '1'): 40, ('0', '2'): 16, ('1', '3'): 0})

    def test_calculate_score(self):
        """
        Test calculating score for arbitrary node
        """
        trusts, G = load_data("testdata/test01.csv")
        source = "0" 
        paths, ranks = calc_paths_and_ranks(G, trusts, source)
        capacities = derive_capacities(ranks)

        self.assertEqual(calculate_score(G, capacities, source, source), 100.0)
        self.assertEqual(calculate_score(G, capacities, source, '1'), 100.0)
        self.assertEqual(calculate_score(G, capacities, source, '2'), 40.0)

    def test_calculate_scores_for_all(self):
        """
        Test calculating score for all nodes
        """
        trusts, G = load_data("testdata/test01.csv")
        source = "0" 
        paths, ranks = calc_paths_and_ranks(G, trusts, source)
        capacities = derive_capacities(ranks)

        self.assertEqual(calculate_score_for_all(G, paths, capacities, source),
                         {'0': 100.0, '1': 100.0, '2': 40.0})

    def test_update_trust1(self):
        """
        Test four cases of updating a single trust value 
        """
        trusts, G = load_data("testdata/test01.csv")
        ownidentity = "0" 
        paths, ranks = calc_paths_and_ranks(G, trusts, ownidentity)
        capacities = derive_capacities(ranks)
        scores = calculate_score_for_all(G, paths, capacities, ownidentity)

        # negative trust changes to another negative trust
        new_scores = update_scores_from_one_trust(G, trusts, paths, ranks, capacities, scores, ownidentity, '1', '3', -100.0) 
        self.assertEqual(scores, {'0': 100.0, '1': 100.0, '2': 40.0})

        # positive trust changes to another positive trust 
        new_scores = update_scores_from_one_trust(G, trusts, paths, ranks, capacities, scores, ownidentity, '1', '2', 50.0) 
        self.assertEqual(new_scores, {'0': 100.0, '1': 100.0, '2': 20.0})

        # negative trust changes to positive trust
        new_scores  = update_scores_from_one_trust(G, trusts, paths, ranks, capacities, scores, ownidentity, '1', '3', 100.0) 
        self.assertEqual(new_scores, {'0': 100.0, '1': 100.0, '2': 40.0, '3': 40.0})

        # positive trust changes to negative trust
        new_scores  = update_scores_from_one_trust(G, trusts, paths, ranks, capacities, scores, ownidentity, '0', '1', -100.0) 
        self.assertEqual(new_scores, {'0': 100.0, '1': -100.0, '2': 0.0, '3': 0.0})
        

if __name__ == '__main__':
    unittest.main()
