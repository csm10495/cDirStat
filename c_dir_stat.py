'''
Brief:
    Fun little script to do something sort-of like windirstat... but not nearly as nice looking

Author(s):
    Charles Machalow
'''
import argparse
import collections
import multiprocessing
import operator
import os
import time

from pprint import pprint

class File(object):
    def __init__(self, path):
        self.path = path.encode('utf-8')
        self.fileSizeBytes = os.stat(path).st_size
        self.extension = os.path.splitext(path)[-1]
        if os.name == 'nt':
            self.extension = self.extension.lower() # On Windows, files are case-insensitive
        if len(self.extension) == 0:
            self.extension = '<No Extension>'

    def __str__(self):
        retStr = "%s" % (self.path)
        return retStr

def getSizeString(fileSizeBytes):
    kb = fileSizeBytes / 1024.0
    mb = kb / 1024.0
    gb = mb / 1024.0
    tb = gb / 1024.0
    retStr = ''
    if tb > 1:
        retStr += '%.4f Terabytes' % tb
    elif gb > 1:
        retStr += '%.4f Gigabytes' % gb
    elif mb > 1:
        retStr += '%.4f Megabytes' % mb
    elif kb > 1:
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

def getFileExtensionToSize(infoList):
    retDict = {}
    for file in infoList:
        if file.extension in retDict:
            retDict[file.extension] += file.fileSizeBytes
        else:
            retDict[file.extension] = file.fileSizeBytes

    return retDict

def qualifyInfoList(infoList, directory):
    sortedByFileSize = sorted(infoList, key=lambda x: x.fileSizeBytes, reverse=True)
    sortedByFilePathLength = sorted(infoList, key=lambda x: len(x.path), reverse=True)
    extensionCounter = collections.Counter(x.extension for x in infoList)
    fileExtensionToSize = getFileExtensionToSize(infoList)
    largestSizeExtension = max(fileExtensionToSize.items(), key=operator.itemgetter(1))[0]

    print ("Directory Info For: %s" % directory)
    print ("=" * 60)
    print ('Largest File: %s (%s)' % (sortedByFileSize[0], getSizeString(sortedByFileSize[0].fileSizeBytes)))
    print ('Longest Path: %s (%d characters)' % (sortedByFilePathLength[0], len(sortedByFilePathLength[0].path)))
    print ('Most Common Extension: {} ({:,} files)'.format(extensionCounter.most_common()[0][0], extensionCounter.most_common()[0][1]))
    print ('Most Data In Use For An Extension: %s (%s)' % (largestSizeExtension, getSizeString(fileExtensionToSize[largestSizeExtension])))
    print ('')
    print ('Total Number of Files: {:,}'.format(len(infoList)))
    print ('Total Size of Files: %s' % (getSizeString(sum(x.fileSizeBytes for x in infoList))))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--directory', type=str, nargs='+')
    args = parser.parse_args()

    if not args.directory:
        args.directory = [os.getcwd()]

    start = time.time()
    infoList = []
    for idx, itm in enumerate(args.directory):
        args.directory[idx] = os.path.abspath(itm)
        infoList += getInfoList(itm)
    end = time.time()
    print ('getInfoList() for %s took %.2f seconds' % (args.directory, end - start))
    if infoList:
        qualifyInfoList(infoList, args.directory)
    else:
        print ("No files found")