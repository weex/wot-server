import csv
import networkx as nx

from collections import deque
from time import time

debug = False

start = time()
def elapsed(message):
    if debug:
        print(str(time() - start), ",", message)

def load_data(filename, delimiter=','):
    trusts = {}       # raw data
    G = nx.DiGraph()  # graph of valid ranks (non-negative value)

    elapsed("initialized DiGraph")

    # read in edges, remove first row manually
    with open(filename) as csvDataFile:
        csvReader = csv.reader(csvDataFile, delimiter=delimiter)

        for row in csvReader:
            pair = (row[0], row[1])
            value = float(row[2])
            trusts[pair] = value
        
            # negative trust links should not be in paths
            if value >= 0:
                G.add_edge(row[0], row[1], value=value)

    return trusts, G

def calc_paths_and_ranks(G, trusts, source):
    # we get shortest paths only from one identity
    paths = nx.shortest_path(G, source = source)
    
    # get ranks from paths
    ranks = {}
    for target in paths:
        ranks[(source, target)] = len(paths[target]) - 1
    
    # set rank to -1 (our equivalent of infinity) for all edges with value < 0
    for pair in trusts:
        if trusts[pair] < 0:
            ranks[pair] = -1
    
    return paths, ranks

def get_capacity(rank):
    rank_to_capacity = [100, 40, 16, 6, 2, 1]
    if rank < 0:
        return 0
    elif rank > 5:
        return 1
    else:
        return rank_to_capacity[rank]

# convert ranks to capacities
def derive_capacities(ranks):
    capacities = {}
    for pair in ranks:
        rank = ranks[pair]
        capacities[pair] = get_capacity(rank)
    return capacities

def calculate_score(G, capacities, source, target):
    if source == target:
        return 100.0

    # calculate score - average of trust values for target weighted by capacity
    score = 0

    trusters = G.predecessors(target)
    for t in trusters:
        truster_pair = (source, t)
        # we only care about trust values from trusters that we have a path to 
        # so check that we have a capacity from ownidentity to truster 
        if G.get_edge_data(str(t), target) and truster_pair in capacities:
            value = G.get_edge_data(str(t), target)['value']
            score += value * capacities[truster_pair] / 100.0 
    
    return score

def calculate_score_for_all(G, paths, capacities, source): 
    scores = {}
    for target in paths:
        scores[target] = calculate_score(G, capacities, source, target)
    return scores

def score_all_from_file(filename, source):
    trusts, G = load_data(filename)
    paths, ranks = calc_paths_and_ranks(G, trusts, source)
    capacities = derive_capacities(ranks)
    return calculate_score_for_all(G, paths, capacities, source)

# update_trust
# process one trust value change and update all affected scores 
def update_trust(G, trusts, paths, ranks, capacities, scores, ownidentity, source, target, trust):
    pair = (source, target)
    affected_ranks = [target]

    # get current trust
    old_trust = None
    if pair in trusts:
        print("edge ({}, {}) found".format(source, target))
        old_trust = trusts[pair]
    else:
        print("({}, {}) new trust link!".format(source, target))

    # compare, there are four cases
    # 1. old was neg or non-existent, new is neg => no change
    if (old_trust < 0 or old_trust is None) and trust < 0:
        print("neg/no to neg\n")
        pass

    # 2. old was pos, new is pos => rank and capacity not affected, just update value and score
    elif old_trust >= 0 and trust >= 0:
        trusts[pair] = trust 
        G[source][target]['value'] = trust

        # we'll calculate later at least the scores from paths that include target
        #recalc_descendants(target)

    # 3. old was neg or non-existent, new is pos => add edge, calc affected ranks, affected capacities, and affected scores
    elif (old_trust < 0 or old_trust is None) and trust >= 0:
        # update trust
        trusts[pair] = trust
        G.add_edge(source, target, value=trust)
        new_paths = nx.shortest_path(G, source = source)
       
        print("len old paths {} len new paths {}".format(len(paths), len(new_paths)))

        # calc affected ranks, i.e. ranks for paths that included target or target's successors
        q = deque()
        q.append(target)
        while q:
            this_target = q.popleft()
            old_rank = ranks[(ownidentity, this_target)]
            ranks[(ownidentity, this_target)] = len(paths[this_target]) - 1
            if old_rank != ranks[(ownidentity, this_target)]:
                print("traversal to {}, rank changed from {} to {}".format(this_target, old_rank, ranks[(ownidentity, this_target)]))
                affected_ranks.append(this_target)
            else:
                print("traversal to {}, rank unchanged".format(this_target))
            
            # add any successors of the current node if target is in shortest path from ownidentity
            for t in G.successors(this_target):
                if target in paths[t]:
                    q.append(t)
        print("affected ranks: {}".format(affected_ranks))

        # change affected capacities
        for t in affected_ranks:
            pair = (ownidentity, t)
            old_capacity = capacities[pair]
            capacities[pair] = get_capacity(ranks[pair])
            print("                capacity changed from {} to {}".format(old_capacity, capacities[pair]))

        # update scores
        for t in affected_ranks:
            old_score = scores[ownidentity][t]
            new_score = calculate_score(G, capacities, source, t)
            print("                score changed from {} to {}".format(old_score, new_score))
            scores[ownidentity][t] = new_score
            #inspect(ownidentity, t)

    # 4. old was pos, new is neg => recalc all?
    elapsed(target)

# examine a single record
def inspect(G, paths, ranks, capacities, source, target):
    print("Source: " + source)
    print("Target: " + target)
    if G.get_edge_data(source, target):
        print("Trust value: " + str(G.get_edge_data(source, target)['value']))
    else:
        print("Trust value: not directly valued")
    print("Path: " + str(paths[target]))
    print("Rank: " + str(ranks[(source, target)]))
    print("Capacity: " + str(capacities[(source, target)]))


