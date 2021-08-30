import networkx as nx
import csv

G = nx.DiGraph()

# read in edges, remove first row manually
with open("trustdeduplicated.csv") as csvDataFile:
    csvReader = csv.reader(csvDataFile, delimiter=';')

    for row in csvReader:
        G.add_edge(row[0], row[1], value=row[2])

# pick an own identity to start with 
ownidentity = '0'

# we get shortest paths only from own identity
paths = nx.shortest_path(G, source = ownidentity)

# get ranks from paths, we can get lengths only above if we don't care about path
ranks = {}
for target in paths:
    ranks[(ownidentity,target)] = len(paths[target]) - 1

# set rank to -1 (our equivalent of infinity) if value < 0
for e in G.edges:
    source = e[0]
    target = e[1]
    if float(G.get_edge_data(source, target)['value']) < 0:
        ranks[(source, target)] = -1
        
# convert ranks to capacities
capacities = {}
rank_to_capacity = [100, 40, 16, 6, 2, 1]
for pair in ranks:
    rank = ranks[pair]
    if rank < 0:
        capacity = 0
    elif rank > 5:
        capacity = 1
    else:
        capacity = rank_to_capacity[rank - 1]
    capacities[pair] = capacity

def calculate_score(target):
    # calculate score - average of trust values for target weighted by capacity
    trusters = G.predecessors(target)
    score = 0
    for t in trusters:
        truster_pair = (ownidentity, t)
        value = 0
        # we only care about trust values from trusters that we have a path to 
        # so check that we have a capacity from ownidentity to truster 
        if G.get_edge_data(str(t), target) and truster_pair in capacities:
            value = float(G.get_edge_data(str(t), target)['value'])
            score += value * capacities[truster_pair] / 100.0 
    return score

# rank should take away influence from trusters



# examine a single record - using global vars G, paths, ranks, capacities
def inspect(source, target):
    print("Source: " + source)
    print("Target: " + target)
    if G.get_edge_data(source, target):
        print("Trust value: " + G.get_edge_data(source, target)['value'])
    else:
        print("Trust value: not directly valued")
    print("Path: " + str(paths[target]))
    print("Rank: " + str(ranks[(source, target)]))
    print("Capacity: " + str(capacities[(source, target)]))


inspect(ownidentity, '4077')
inspect(ownidentity, '10592')

for target in paths:
    # inspect(ownidentity, target)
    score = calculate_score(target)
    print("{};{};{}".format(ownidentity,target,score)) 

