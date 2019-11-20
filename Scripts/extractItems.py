import sys
import re
import os
import csv
import fnmatch
import xml.etree.ElementTree as ET

########
# Globals

folderMods='/home/martin/ParadisoORCS/Config/*CubeBlocks*.sbc'
folderGame='/home/martin/ParadisoORCS/Scripts/*CubeBlocks*.sbc'
configFile='Sandbox_config.sbc'

########
# methods

def getFiles( subfolder, wildch ):
    splitName = wildch.split('/')
    mypath = os.getcwd()
    pureWildch = splitName.pop()
    fullPath = '/'.join(splitName)+'/'+subfolder
    filtered = []

    for root, dirnames, filenames in os.walk(fullPath):
        for filename in fnmatch.filter(filenames, pureWildch):
            filtered.append(os.path.join(root, filename))

    return filtered

def getNodes(tree, path):
    return tree.getroot().findall(path)

def getModList():
    tree = ET.parse(configFile)
    mods = getNodes(tree, './/ModItem')
    modList = []

    for mod in mods:
        if 'FriendlyName' in mod.attrib:
            modList.append({ 'name': mod.attrib['FriendlyName'], 'id': mod.find('PublishedFileId').text, 'source': 'WEB' })
        else:
            modList.append({ 'name': mod.find('Name').text, 'source': 'local' })
    return modList

def getBlockList(mods):
    def findFilesAndReport(name, subfolder, folder):
        print('Probing '+name)
        fileNames = getFiles(subfolder, folder)
        print('found: '+str(len(fileNames))+' CubeBlocks files.')
        return fileNames

    def getBlockListPart(mod, fileNames):
        allBlocks = []
        for fileName in fileNames:
            tree = ET.parse(fileName)
            blocks = getNodes(tree, './/CubeBlocks/Definition')
            for block in blocks:
                newBlock = dict()
                newBlock['mod'] = mod
                newBlock['file'] = fileName
                newBlock['type'] = block.find('Id/TypeId').text
                newBlock['subtype'] = block.find('Id/SubtypeId').text
                newBlock['name'] = block.find('DisplayName').text
                newBlock['size'] = block.find('CubeSize').text
                newBlock['pair'] = block.find('BlockPairName').text
                allBlocks.append(newBlock)
        return allBlocks

    blocks = []
    fileNames = findFilesAndReport('GAME', '', folderGame)
    blocks = blocks + getBlockListPart({'source': 'game'}, fileNames)
    return blocks
########
# code

mods = getModList()
#print(mods)

blocks = getBlockList(mods)
print blocks
