from os import path

from glob2 import glob

def trim_prefix(prefix, files): 
    trimed = []
    for file in files:
        trimed.append(file[len(prefix) + 1:])
    return trimed

def find_files(folder):
    files = []
    for file in glob(folder + '/**'):
        if not path.isdir(file):
            files.append(file)
    return files
    
def extend(*dicts):
    items = []
    for dict_ in dicts:
        items += dict_.items()
    return dict(items)
        