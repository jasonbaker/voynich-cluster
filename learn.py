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

  global linkage_matrix, T

  condensed = distance.squareform(mat)
  linkage_matrix = hierarchy.complete(condensed)
  clusters = hierarchy.fcluster(linkage_matrix, criterion='maxclust', t=5)
  zipped_clusters = zip(names, clusters)
  with contextlib.closing(sqlite3.connect('voynich.db')) as connection:
    cursor = connection.cursor()
    connection.execute('CREATE TABLE IF NOT EXISTS clusters (name, clusterid)')
    cursor.execute('DELETE FROM clusters')
    for name, clusterid in zipped_clusters:
      cursor.execute('INSERT INTO clusters(name, clusterid) values (\'%s\', %d)' % (name, clusterid))
    connection.commit()

  hierarchy.dendrogram(linkage_matrix, labels=names)
  matplotlib.pyplot.show()
