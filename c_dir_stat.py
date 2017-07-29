'''
Brief:
    Fun little script to do something sort-of like windirstat... but not nearly as nice looking

Author(s):
    Charles Machalow
'''
import argparse
import collections
import multiprocessing
import os
import time

from pprint import pprint

class File(object):
    def __init__(self, path):
        self.path = path
        self.fileSizeBytes = os.stat(path).st_size
        self.extension = os.path.splitext(path)[-1]

    def __str__(self):
        retStr = "%s" % (self.path)
        return retStr

def getSizeString(fileSizeBytes):
    kb = fileSizeBytes / 1024.0
    mb = kb / 1024.0
    gb = mb / 1024.0
    retStr = ''
    if gb > 0:
        retStr += '%.4f Gigabytes' % gb
    elif mb > 0:
        retStr += '%.4f Megabytes' % mb
    elif kb > 0:
        retStr += '%.4f Kilobytes' % kb
    else:
        retStr += '%.4f Bytes' % fileSizeBytes

    return retStr

def processFilesInFolder(root, files):
    retFiles = []
    for name in files:
        fullPath = os.path.abspath(os.path.join(root, name))
        try:
            retFiles.append(File(fullPath))
        except OSError:
            pass

    return retFiles

def getInfoList(rootDir):
    retList = []
    tasks = []

    pool = multiprocessing.Pool(4)
    for root, dirs, files in os.walk(rootDir):
        tasks.append(pool.apply_async(processFilesInFolder, (root, files), callback= lambda items: retList.extend(items)))

    for i in tasks:
        i.wait()

    pool.close()
    pool.join()

    return retList

def qualifyInfoList(infoList, directory):
    sortedByFileSize = sorted(infoList, key=lambda x: x.fileSizeBytes, reverse=True)
    sortedByFilePathLength = sorted(infoList, key=lambda x: len(x.path), reverse=True)
    extensionCounter = collections.Counter(x.extension for x in infoList)

    print ("Directory Info For: %s" % directory)
    print ("=" * 60)
    print ('Largest File: %s (%s)' % (sortedByFileSize[0], getSizeString(sortedByFileSize[0].fileSizeBytes)))
    print ('Longest Path: %s (%d characters)' % (sortedByFilePathLength[0], len(sortedByFilePathLength[0].path)))
    print ('Most Common Extension: %s (%d files)' % (extensionCounter.most_common()[0][0], extensionCounter.most_common()[0][1]))
    print ('')
    print ('Total Number of Files: %d' % len(infoList))
    print ('Total Size of Files: %s' % (getSizeString(sum(x.fileSizeBytes for x in infoList))))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--directory', type=str)
    args = parser.parse_args()

    if not args.directory:
        args.directory = os.getcwd()
    args.directory = os.path.abspath(args.directory)

    start = time.time()
    infoList = getInfoList(args.directory)
    end = time.time()
    print ('getInfoList(%s) took %.2f seconds' % (args.directory, end - start))
    qualifyInfoList(infoList, args.directory)