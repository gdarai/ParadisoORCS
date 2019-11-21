import sys
import re
import os
import csv
import fnmatch
import xml.etree.ElementTree as ET

########
# Globals

folder = dict()
folder['local'] = '/home/martin/ParadisoORCS/Config/*.sbc'
folder['WEB'] = '/home/martin/ParadisoORCS/Config/*.sbc'
folder['game'] = '/home/martin/ParadisoORCS/Scripts/Game/*.sbc'
configFile='Sandbox_config_small.sbc'
game = { 'source': 'game', 'idx': 1000 }
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

def getModList(game):
    tree = ET.parse(configFile)
    mods = getNodes(tree, './/ModItem')
    modList = []

    for mod in mods:
        idx = game['idx']+len(modList)+1
        if 'FriendlyName' in mod.attrib:
            modList.append({ 'name': mod.attrib['FriendlyName'], 'id': mod.find('PublishedFileId').text, 'source': 'WEB', 'idx':idx })
        else:
            modList.append({ 'name': mod.find('Name').text, 'id':mod.find('Name').text, 'source': 'local', 'idx':idx })
    return modList

def getBlockList(mods, game):
    def findFilesAndReport(name, subfolder, folder):
        fileNames = getFiles(subfolder, folder)
        print('('+str(len(fileNames))+') Probing '+name)
        return fileNames

    def getBlockListPart(mod, fileNames):
        allBlocks = []
        for fileName in fileNames:
            tree = ET.parse(fileName)
            blocks = getNodes(tree, './/CubeBlocks/Definition')
            print('\t('+str(len(blocks))+' blocks) '+fileName);
            for block in blocks:
                pairBlockElement = block.find('BlockPairName')
                pairBlock = block.find('Id/SubtypeId').text
                if (pairBlockElement != None):
                    pairBlock = block.find('BlockPairName').text

                newBlock = dict()
                newBlock['mod'] = mod
                newBlock['file'] = fileName
                newBlock['type'] = block.find('Id/TypeId').text
                newBlock['subtype'] = block.find('Id/SubtypeId').text
                newBlock['name'] = block.find('DisplayName').text
                newBlock['size'] = block.find('CubeSize').text
                newBlock['pair'] = pairBlock
                allBlocks.append(newBlock)
        mod['blocks'] = allBlocks
        return allBlocks

    blocks = []
    fileNames = findFilesAndReport('GAME', '', folder['game'])
    blocks = blocks + getBlockListPart(game, fileNames)
    for mod in mods:
        source = mod['source']
        fileNames = findFilesAndReport('MOD ('+source+') '+mod['name'], mod['id'], folder[source])
        blocks = blocks + getBlockListPart(mod, fileNames)

    return blocks

def makeRootNode(rootName):
    Tree = ET.Element(rootName)
    Tree.set('xmlns:xsd', 'http://www.w3.org/2001/XMLSchema')
    Tree.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
    return Tree

def buildResearchList(mods, game):
    print('Building ResearchGroups')
    Tree = makeRootNode('Definitions')
    Groups = ET.SubElement(Tree, 'ResearchGroups')
    if (len(game['blocks']) > 0):
        print('\tPrinting block for vanilla')
        makeResearchGroup(Groups, str(game['idx']), game['blocks'])
    for mod in mods:
        if (len(mod['blocks']) > 0):
            print('\tPrinting block for mod: '+mod['name'])
            makeResearchGroup(Groups, str(mod['idx']), mod['blocks'])
    return ET.ElementTree(Tree)

def makeResearchGroup(Groups, id, blocks):
    Group = ET.SubElement(Groups, 'ResearchGroup')
    Group.set('xsi:type', 'ResearchGroup')
    Id = ET.SubElement(Group, 'Id')
    Id.set('Type', 'MyObjectBuilder_ResearchGroupDefinition')
    Id.set('Subtype', id)
    Members = ET.SubElement(Group, 'Members')
    for block in blocks:
        BlockId = ET.SubElement(Members, 'BlockId')
        BlockId.set('Type', 'MyObjectBuilder_'+block['type'])
        BlockId.set('Subtype', block['subtype'])
    return Group

def makeUnlockByGroupTag(LockGroups, mod):
    Lock = ET.SubElement(LockGroups, 'GroupSubtype')
    Lock.text = str(mod['idx'])
    return Lock

def buildResearchBlock(mods, game):
    print('Building ResearchGroupBlocks')
    Tree = makeRootNode('Definitions')
    Blocks = ET.SubElement(Tree, 'ResearchBlocks')
    Block = ET.SubElement(Blocks, 'ResearchBlock')
    BlockId = ET.SubElement(Block, 'Id')
    BlockId.set('Type', 'MyObjectBuilder_TerminalBlock')
    BlockId.set('Subtype', 'ControlPanel')
    LockGroups = ET.SubElement(Block, 'UnlockedByGroups')
    if (len(game['blocks']) > 0):
        print('\tAdding vanilla')
        makeUnlockByGroupTag(LockGroups, game)
    for mod in mods:
        if (len(mod['blocks']) > 0):
            print('\tAdding mod: '+mod['name'])
            makeUnlockByGroupTag(LockGroups, mod)
    return ET.ElementTree(Tree)

########
# code

print('Analyzing mods')
print('============================')
mods = getModList(game)
blocks = getBlockList(mods, game)
print('Building research group lists')
print('=============================')
resFile = buildResearchList(mods, game)
resBlockFile = buildResearchBlock(mods, game)

resFile.write('_outGroups.xml')
resBlockFile.write('_outGroupBlocks.xml')
