#!/usr/bin/env python

import json
import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial.distance import jaccard
from scipy.spatial.distance import hamming
from scipy.cluster.hierarchy import fclusterdata
from geopy.geocoders import Nominatim
from mpl_toolkits.basemap import Basemap

geolocator = Nominatim()
ratings_file_name = 'MTP.txt'
places_file_name = 'Mapping.json'
num_user_IDs = 35869
num_place_IDs = 913

R = np.zeros((num_user_IDs, num_place_IDs))

print('Loading Data...')
with open(ratings_file_name, 'r') as f:
    for line in f:
        line = line.split(', ')
        user = int(line[0]) - 1
        places = [int(x) - 1 for x in line[1:]]
        R[user,:][places] = 1.0

with open(places_file_name, 'r') as f:
    place_names = json.load(f)

# Remove all-zero rows (invactive users) and columns (unused place IDs)
exists = ~(R==0).all(0)
R = R[~(R==0).all(1),:]
R = R[:,~(R==0).all(0)]

place_indices = {}
index = 0
for i in range(exists.shape[0]):
    if exists[i]:
        place_indices[index] = i
        index = index+1

# target user
# Target_ID = 31385
Target_ID = 14579
Target_Row = R[Target_ID,:]

P = np.diag(np.sum(R, axis=1))
Q = np.diag(np.sum(R, axis=0))

print('Computing Similarity Matrices...')
P_inv = np.sqrt(P)
P_inv[np.diag_indices(P.shape[0])] = 1/P_inv[np.diag_indices(P.shape[0])]
Q_inv = np.sqrt(Q)
Q_inv[np.diag_indices(Q.shape[0])] = 1/Q_inv[np.diag_indices(Q.shape[0])]

SU = P_inv.dot(R).dot(R.T).dot(P_inv)
SI = Q_inv.dot(R.T).dot(R).dot(Q_inv)

print('Computing Recommendation Matrices...')
GU = SU.dot(R)
GI = R.dot(SI)

Target_U = np.argsort(-GU[Target_ID,:])
Target_I = np.argsort(-GI[Target_ID,:])

num_rank = 10
num_pos = 100
coords = []

print('\nUser-based Ranking:')
for i in range(num_rank):
    name = place_names[str(place_indices[Target_U[i]]+1)]
    print(name, ': ', GU[Target_ID,Target_U[i]])
 
print('\nPlace-based Ranking:')
for i in range(num_pos):
    name = place_names[str(place_indices[Target_I[i]]+1)]
    try:
        coords.append(geolocator.geocode(name)[-1])
    except:
        pass
    if i < num_rank:
        print(name, ': ', GI[Target_ID,Target_I[i]])

orig_set = (np.where(R[Target_ID,:]==1)[0])
orig_coords = []
for i in orig_set:
    try:
        orig_coords.append(geolocator.geocode(place_names[str(place_indices[i]+1)])[-1])
    except:
        pass

true_pos_U = []
for i in range(num_pos):
    count = 0
    for j in range(i):
        if Target_U[j] in orig_set:
            count += 1
    true_pos_U.append(count/len(orig_set))

true_pos_I = []
for i in range(num_pos):
    count = 0
    for j in range(i):
        if Target_I[j] in orig_set:
            count += 1
    true_pos_I.append(count/len(orig_set))

num_places = Q.shape[0]
random_pos = [i/num_places for i in range(num_pos)]

f1 = plt.figure(1)
U_plot = plt.plot(list(range(1,num_pos+1)), true_pos_U, 'b', linewidth=4.0, label='User-based CF', )
I_plot = plt.plot(list(range(1,num_pos+1)), true_pos_I, 'r', linewidth=4.0, label='Place-based CF')
rand_plot = plt.plot(list(range(1,num_pos+1)), random_pos, 'k', linewidth=4.0, label='At Random')
plt.legend(loc='upper left')
plt.title('True Positive Rate for Recommendations')
plt.ylabel('True Positive Rate')
plt.xlabel('Number of Recommendations')

clusters = fclusterdata(R.T, 40, criterion='distance')
unique_clusters, counts = np.unique(clusters, return_counts=True)

for i,clust in enumerate(unique_clusters):
    if counts[i] >=2 and counts[i] <= 30:
        print('\nCluster:', clust)
        for place in np.where(clusters == clust)[0]:
            print(place_names[str(place_indices[place]+1)])

f2 = plt.figure(2)
plt.title('Travel Map (Prior Destinations in Red, Recommendations in Blue)')
world_map = Basemap(projection='gall', resolution = 'l', area_thresh = 100000.0, lat_0=0, lon_0=0)
world_map.drawcoastlines()
world_map.drawcountries()

lats = [x[0] for x in coords]
longs = [x[1] for x in coords]
lats += [x[0] for x in orig_coords]
longs += [x[1] for x in orig_coords]

x,y = world_map(longs, lats)
c_vals = [0]*len(coords) + [1]*len(orig_coords)
s_vals =[30]*len(coords) + [15]*len(orig_coords)
world_map.scatter(x, y, c=c_vals, s=s_vals, cmap=plt.cm.bwr)

plt.show()
