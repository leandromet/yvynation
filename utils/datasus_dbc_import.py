
import datasus_dbc
import os

#folder = os.path.dirname(__file__)
folder = '/home/leandromb/Documents/2025_artigos/2025_toxoplasmose/arquivo/arquivo'
for filename in os.listdir(folder):
    if filename.lower().endswith('.dbc'):
        dbc_path = os.path.join(folder, filename)
        dbf_path = os.path.splitext(dbc_path)[0] + '.dbf'
        datasus_dbc.decompress(dbc_path, dbf_path)