#! /usr/bin/env python3

import bz2
import contextlib
import csv
import itertools
import os
import re
import sqlite3

import learn

fnames = os.listdir('./folios')
fnames = [fname for fname in fnames if re.match(r'f\d{1,3}[r|v]\d?\.txt', fname)]

file_contents = {}

for fname in fnames:
  with open('./folios/' + fname, 'rb') as infile:
    # Strip .txt
    fname = fname[:-4]
    file_contents[fname] = infile.read()

file_compression = {}
for fname in file_contents:
  file_compression[fname] = len(bz2.compress(file_contents[fname]))

with open('singlefile.txt', 'w') as singlefile_out:
  for key, value in sorted(file_compression.items()):
    singlefile_out.write('%s: %s\n' % (key, value))

file_combinations = list(itertools.combinations(file_contents, 2))
joint_compression = {}

for f1, f2 in file_combinations:
  compressor = bz2.BZ2Compressor()
  compressor.compress(file_contents[f1])
  compressor.compress(file_contents[f2])
  joint_compression[(f1, f2)] = len(compressor.flush())

with open('jointfile.txt', 'w') as jointfile_out:
  for key, val in joint_compression.items():
    jointfile_out.write('%s: %s\n' % (key, val))

distances = {}
for xfile, yfile in file_combinations:
  zxy = joint_compression[xfile, yfile]
  zx = file_compression[xfile]
  zy = file_compression[yfile]
  minxy = min(zx, zy)
  maxxy = max(zx, zy)
  distances[(xfile, yfile)] = (zxy - minxy) / maxxy

sorted_distances = sorted([(distance, key) for (key, distance) in distances.items()])

with contextlib.closing(sqlite3.connect('voynich.db')) as connection:
  connection.execute('CREATE TABLE IF NOT EXISTS distances(key1, key2, distance)')
  connection.execute('DELETE FROM distances')
  cursor = connection.cursor()
  for (key1, key2), distance in distances.items():
    cursor.execute(
      'INSERT INTO distances(key1, key2, distance) VALUES (?, ?, ?)', 
      (key1, key2, distance))
  connection.commit()

with open('distances.txt', 'w', newline='') as distance_out:
  distancewriter = csv.writer(distance_out, delimiter=',')
  for distance, (key1, key2) in sorted_distances:
    distancewriter.writerow([key1, key2, distance])

nearest_neighbors = {}
def log_neighbor(key, neighbor, score):
  previous_neighbor, previous_score = nearest_neighbors.get(key, ('', 1))
  if score < previous_score:
    nearest_neighbors[key] = neighbor, score

for (f1, f2), score in distances.items():
  log_neighbor(f1, f2, score)
  log_neighbor(f2, f1, score) 

neighbors_list = [(key, neighbor, score) for (key, (neighbor, score)) in nearest_neighbors.items()]
with contextlib.closing(sqlite3.connect('voynich.db')) as connection:
  connection.execute(
    'CREATE TABLE IF NOT EXISTS neighbors(key, neighbor, distance)')
  connection.execute('DELETE FROM neighbors')
  cursor = connection.cursor()
  for t in neighbors_list:
    cursor.execute(
      'INSERT INTO neighbors(key, neighbor, distance) VALUES (?, ?, ?)', t)
  connection.commit()

with open('neighbors.txt', 'w', newline='') as neighbors_out:
  neighbors_writer = csv.writer(neighbors_out, delimiter=',')
  for t in neighbors_list:
    neighbors_writer.writerow(t)


learn.cluster(distances)