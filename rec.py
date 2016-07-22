#!/usr/bin/env python

import json
import numpy as np
import matplotlib.pyplot as plt
from scipy.cluster.hierarchy import fclusterdata
from mpl_toolkits.basemap import Basemap

ratings_file_name = 'MTP.txt'
names_file_name = 'Name_Mapping.json'
coords_file_name = 'Coord_Mapping.json'
num_user_IDs = 35869
num_place_IDs = 913

# R is ratings matrix of size n x p
# n = number of users, p = number of places
# R[i,j] = 1 if user i has been to place j, else 0
R = np.zeros((num_user_IDs, num_place_IDs))

print('Loading raw data...')
with open(ratings_file_name, 'r') as f:
    for line in f:
        line = line.split(', ')
        user = int(line[0]) - 1
        places = [int(x) - 1 for x in line[1:]]
        R[user,:][places] = 1.0

with open(names_file_name, 'r') as f:
    place_names = json.load(f)

with open(coords_file_name, 'r') as f:
    place_coords = json.load(f)

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

# Compute or preload
try:
    print('Loading recommendation matrices...')
    GU = np.load('GU_matrix.npy')
    GI = np.load('GI_matrix.npy')
except:
    print('Loading failed; computing link matrices...')
    # P is link matrix of size n x n
    P = np.diag(np.sum(R, axis=1))
    # Q is link matrix of size p x p
    Q = np.diag(np.sum(R, axis=0))

    P_inv = np.sqrt(P)
    P_inv[np.diag_indices(P.shape[0])] = 1/P_inv[np.diag_indices(P.shape[0])]
    Q_inv = np.sqrt(Q)
    Q_inv[np.diag_indices(Q.shape[0])] = 1/Q_inv[np.diag_indices(Q.shape[0])]

    print('Computing similarity matrices...')
    # SU is user-user similarity matrix of size n x n
    SU = P_inv.dot(R).dot(R.T).dot(P_inv)
    # SI is place-place similarity matrix of size p x p
    SI = Q_inv.dot(R.T).dot(R).dot(Q_inv)

    print('Computing recommendation matrices...')
    # GU is user-based recommendation matrix of size n x p
    GU = SU.dot(R)
    # GI is user-based recommendation matrix of size n x p
    GI = R.dot(SI)

    print('Saving...')
    np.save('GU_matrix', GU)
    np.save('GI_matrix', GI)

# Rarity is percent of users who have NOT visited a location
rarity = 1 - np.sum(R, axis=0)/R.shape[0]
penalty = 2.0

# Rows of recommendations matrices for target user
# Non-linear penalty applied for popular places using a power of rarity
GU_Target = GU[Target_ID,:] * np.power(rarity, penalty)
GI_Target = GI[Target_ID,:] * np.power(rarity, penalty)

# sorting of recommendation scores for target user
Target_U = np.argsort(-GU_Target)
Target_I = np.argsort(-GI_Target)

num_rank = 10 # number to display in ranking
num_pos = 100 # number to calculate TPR for and display on map
coords_U = []
coords_I = []

for i in range(num_pos):
    name = place_names[str(place_indices[Target_U[i]]+1)]
    coords_U.append(place_coords[name])
 
print('\nPlace-based Ranking:')
for i in range(num_pos):
    name = place_names[str(place_indices[Target_I[i]]+1)]
    coords_I.append(place_coords[name])
    if i < num_rank:
        print(name+':', GI_Target[Target_I[i]], GI[Target_ID,Target_I[i]])

orig_set = (np.where(R[Target_ID,:]==1)[0])
coords_target = []
for i in orig_set:
    coords_target.append(place_coords[place_names[str(place_indices[i]+1)]])

# True positive rate for user-based recommendations
true_pos_U = []
for i in range(num_pos):
    count = 0
    for j in range(i):
        if Target_U[j] in orig_set:
            count += 1
    true_pos_U.append(count/len(orig_set))

# True positive rate for place-based recommendations
true_pos_I = []
for i in range(num_pos):
    count = 0
    for j in range(i):
        if Target_I[j] in orig_set:
            count += 1
    true_pos_I.append(count/len(orig_set))

random_pos = [i/R.shape[1] for i in range(num_pos)]

# Figure 1: True positive rates
f1 = plt.figure(1)
U_plot = plt.plot(list(range(1,num_pos+1)), true_pos_U, 'b', linewidth=4.0, label='User-based CF', )
I_plot = plt.plot(list(range(1,num_pos+1)), true_pos_I, 'r', linewidth=4.0, label='Place-based CF')
rand_plot = plt.plot(list(range(1,num_pos+1)), random_pos, 'k', linewidth=4.0, label='At Random')
plt.legend(loc='upper left')
plt.title('True Positive Rate for Recommendations')
plt.ylabel('True Positive Rate')
plt.xlabel('Number of Recommendations')

# Figure 2: World map of recommendations
f2 = plt.figure(2)
world_map = Basemap(projection='kav7', resolution = 'i', area_thresh = 10000.0, lat_0=0, lon_0=0)
world_map.drawcountries()
world_map.drawlsmask(land_color='gainsboro',ocean_color='steelblue',lakes=True)

lats = [x[0] for x in coords_target if x is not None]
longs = [x[1] for x in coords_target if x is not None]
lat_set = set(lats); long_set = set(longs)
# Color and size of map markers
c_vals = [(1,0,0)]*len(lats); s_vals = [30]*len(lats)

# Add place-based recommendations to map
for i in range(num_pos):
    if coords_I[i]:
        if (coords_I[i][0] not in lat_set) and (coords_I[i][1] not in long_set):
            lats.append(coords_I[i][0])
            longs.append(coords_I[i][1])
            c_vals.append((0,0,1))
            s_vals.append(30)

# Add user-based recommendations to map
lat_set = set(lats); long_set = set(longs)
for i in range(num_pos):
    if coords_U[i]:
        if (coords_U[i][0] not in lat_set) and (coords_U[i][1] not in long_set):
            lats.append(coords_U[i][0])
            longs.append(coords_U[i][1])
            c_vals.append((0,1,0))
            s_vals.append(30)

x,y = world_map(longs, lats)

world_map.scatter(x, y, c=c_vals, s=s_vals)

plt.show()

# Clustering Study
clusters = fclusterdata(R.T, 40, criterion='distance')
unique_clusters, counts = np.unique(clusters, return_counts=True)

for i,clust in enumerate(unique_clusters):
    if counts[i] >=2 and counts[i] <= 30:
        print('\nCluster:', clust)
        for place in np.where(clusters == clust)[0]:
            print(place_names[str(place_indices[place]+1)])
