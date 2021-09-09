import wotlib as wl

# This script is an attempt to reimplement the Freenet Web of Trust scoring algorithm
# with the improvement mentioned in 
# https://github.com/xor-freenet/plugin-WebOfTrust/blob/master/developer-documentation/core-developers-manual/OadSFfF-version1.2-non-print-edition.pdf

# Initial full calculation ---------------------------------------------

wl.elapsed("start")

#trusts, G = wl.load_data("trustdeduplicated.csv", quirk=True)
trusts, G = wl.load_data("test01.csv")

# pick an own identity to start with 
ownidentity = '0'

# Ranks ---------------------------------------------------------------- 

paths, ranks = wl.calc_paths_and_ranks(G, trusts, ownidentity)

# Capacities -----------------------------------------------------------

capacities = wl.derive_capacities(ranks)

wl.elapsed("converted ranks to capacities")

# Scores ---------------------------------------------------------------

# inspect(ownidentity, '10592')

scores = {ownidentity: wl.calculate_scores_for_all(G, paths, capacities, ownidentity)}

wl.elapsed("calculated scores")

# manual testing - not updating global state of G, paths, ranks, capacities, scores
print("case 1 change from -10 to -100")
wl.update_trust(G, trusts, paths, ranks, capacities, scores, "0", "13348", "1408", -100)

print("case 2 change from 100.0 to 50.0")
wl.update_trust(G, trusts, paths, ranks, capacities, scores, "0", "6", "10695", 50.0)

print("case 3 change from -10.0 to 50.0")
wl.update_trust(G, trusts, paths, ranks, capacities, scores, "0", "24" , "6214", 50)

print("case 4 change from 100.0 to -50")
wl.update_trust(G, trusts, paths, ranks, capacities, scores, "0", "8", "8191", 100.0)
