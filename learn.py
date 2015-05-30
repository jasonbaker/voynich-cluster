import contextlib
import sqlite3
import itertools
import matplotlib
import numpy
from scipy.spatial import distance
from scipy.cluster import hierarchy

def cluster(distances):
  names = list(set(itertools.chain.from_iterable(distances)))
  mat = numpy.zeros((len(names), len(names)))

  for i, name_i in enumerate(names):
    for j, name_j in enumerate(names):
      mat[i][j] = distances.get((name_i, name_j)) or distances.get((name_j, name_i)) or 0

  condensed = distance.squareform(mat)
  linkage_matrix = hierarchy.complete(condensed)
  leaves_dict = {}
  traverse_tree(hierarchy.to_tree(linkage_matrix), leaves_dict)
  print(leaves_dict)

  with contextlib.closing(sqlite3.connect('voynich.db')) as connection:
    cursor = connection.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS clusters(name, clusterid)')
    cursor.execute('DELETE FROM clusters')
    for key, values in leaves_dict.items():
      for clusterid in values:
        cursor.execute('INSERT INTO clusters(name, clusterid) VALUES (?, ?)', 
          (names[key], clusterid))
    connection.commit()


  # T = clusters = hierarchy.fcluster(linkage_matrix, criterion='maxclust', t=5)
  # zipped_clusters = zip(names, clusters)
  # with contextlib.closing(sqlite3.connect('voynich.db')) as connection:
  #   cursor = connection.cursor()
  #   connection.execute('CREATE TABLE IF NOT EXISTS clusters (name, clusterid)')
  #   cursor.execute('DELETE FROM clusters')
  #   for name, clusterid in zipped_clusters:
  #     cursor.execute('INSERT INTO clusters(name, clusterid) values (\'%s\', %d)' % (name, clusterid))
  #   connection.commit()

  # hierarchy.dendrogram(linkage_matrix, labels=names)
  # matplotlib.pyplot.show()

def traverse_tree(tree, leaves_dict, cluster_list=()):
  if tree.is_leaf():
    leaves_dict[tree.get_id()] = cluster_list
  else:
    cluster_list = cluster_list + (tree.get_id(),)
    traverse_tree(tree.get_left(), leaves_dict, cluster_list)
    traverse_tree(tree.get_right(), leaves_dict, cluster_list)
