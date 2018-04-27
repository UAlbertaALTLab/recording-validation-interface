#!/usr/local/bin/python3

# CreateHTML.py
#
# - Read in tab-delimited text files (for words and sentences)
# - Parse files
# - Generate an HTML file with a (long) table in the following structure:
#
#  +-----------+---------------+--------------+-----------------+--------------------+--------------+
#  | ==Cree==  | == English == | Word samples | Sentence (Cree) | Sentence (English) | Samples      |
#  +-----------+---------------+--------------+-----------------+--------------------+--------------+
#  | Cree word | English gloss | Spkr1 <link> | Cree text       | English gloss      | Spkr1 <link> |
#  +-----------+---------------+--------------+-----------------+--------------------+--------------+
#  |           |               | Spkr2 <link> |                 |                    | Spkr2 <link> |
#  +-----------+---------------+--------------+-----------------+--------------------+--------------+
#  | CreeWord2 | English gloss | Spkr1 <link> | Cree text 2     | English gloss      | Spkr1 <link> |
#  +-----------+---------------+--------------+-----------------+--------------------+--------------+
#  |           |               | Spkr2 <link> |                 |                    | Spkr2 <link> |
#  +-----------+---------------+--------------+-----------------+--------------------+--------------+
#  ...
#

import os       # For efficient processing of directory and file names.
#import HTML    # To efficiently generate HTML code around Python objects.

# Set file and folder locations
#mainFolder = "C:\\Users\\Timothy\\Documents\\Altlab\\MaskwacisRecordings\\Extracted"
mainFolder = "/Users/timills/Google Drive/Research/Altlab/Maskwacis-recs/Extracted"
wordsFolder = os.path.join(mainFolder, "words")
sentencesFolder = os.path.join(mainFolder, "sentences")

# These files should be encoded in utf-8 (Unicode)
wordsFilename = "word_codes.txt"
sentencesFilename = "sentence_codes.txt"

htmlFilename = "MaskwacisTable.html"

# Open Words and Sentences tables
wordsFullFilename = os.path.join(wordsFolder, wordsFilename)
wordsFile = open(wordsFullFilename, 'r', encoding='utf-16')
sentencesFullFilename = os.path.join(sentencesFolder, sentencesFilename)
sentencesFile = open(sentencesFullFilename, 'r', encoding='utf-16')
htmlFullFilename = os.path.join(mainFolder, htmlFilename)
htmlFile = open(htmlFullFilename, 'w', encoding='utf-8')

# Generate blank dictionary
soundFileDict = {}

# Build dictionary:
#
#  {CreeWord : {"English":EnglishGloss,
#               "words":[(speakercode, filename),(speakercode, filename),...],
#               "sentences":[(sentenceText, EnglishGloss, speakercode, filename),
#                           (sentenceText, EnglishGloss, speakercode, filename),...]}}
#
# Main key is Cree word.
# Inside is dict with "English" and one or both of "words" and "sentences".
# Each of those points to a list of tuples. Each tuple is one instance of that word or sentence.
# Tuples contain main information about each sound file.

# Loop through rows of Words table.
wordEntries = wordsFile.readlines()
for row in wordEntries:

    # Parse fields out of row
    row = row.strip('\n')
    #print(row)
    rowFields = row.split('\t')
    #print(len(rowFields))
    #print(rowFields)
    currentCreeWord = rowFields[0]
    if 1:
        currentEnglishGloss = rowFields[1]
        currentSpeakerCode = rowFields[2]
        currentFullFilename = rowFields[5]
    else:
        currentEnglishGloss = "null"
        currentSpeakerCode = "AAA"
        currentSessionCode = "NoSession"
        currentFullFilename = "C:\\Users\\Public\\spam.wav"

    #print(currentCreeWord)

    plainFilename = os.path.basename(currentFullFilename)
    # Form tuple containing information
    itemTuple = (currentSpeakerCode, plainFilename)
    # Add row to dictionary:
    if currentCreeWord in soundFileDict.keys():
        soundFileDict[currentCreeWord]["word"].append(itemTuple)
    else:
        soundFileDict[currentCreeWord] = {"English": currentEnglishGloss, "word": [itemTuple]}

# Loop through rows of Sentences table.
sentenceEntries = sentencesFile.readlines()
for row in sentenceEntries:

    # Parse fields out of row
    row = row.strip('\n')
    rowFields = row.split('\t')
    (currentCreeSentence, currentEnglishGloss, keyword, currentSpeakerCode, currentSessionCode, currentFullFilename) = \
        (rowFields[0], rowFields[1], rowFields[2], rowFields[3], rowFields[5], rowFields[6])
    plainFilename = os.path.basename(currentFullFilename)
    # Form tuple containing information
    itemTuple = (currentCreeSentence, currentEnglishGloss, currentSpeakerCode, plainFilename)
    # Add row to dictionary:
    if keyword in soundFileDict.keys():
        if "sentences" in soundFileDict[keyword]:
            soundFileDict[keyword]["sentences"].append(itemTuple)
        else:
            soundFileDict[keyword]["sentences"] = [itemTuple]
    else:
        soundFileDict[keyword] = {"English": currentEnglishGloss, "sentences": [itemTuple]}

#print(soundFileDict.keys())

# Generate HTML header
htmlOpening = """<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Title of the document</title>
</head>

<body>
"""
htmlFile.write(htmlOpening)

# Start table
tableStart = "<table border=1>"
tableEnd = "</table>"
tableRowStart = "<tr>"
tableRowEnd = "</tr>"
tableCellStart = "<td>"
tableCellEnd = "</td>"

htmlFile.write(tableStart)
# for each entry in dictionary (alphabetized):
allWords = sorted(soundFileDict)
#print(allWords)
for word in allWords:
    #   Get information that I need for the table.
    currentEntry = soundFileDict[word]
    currentEnglishGloss = soundFileDict[word]["English"]

    htmlFile.write(tableRowStart)
    # Populate the start of the table row: Cree word and English gloss
    htmlFile.write(tableCellStart + word + tableCellEnd + '\n')
    htmlFile.write(tableCellStart + currentEnglishGloss + tableCellEnd + '\n')
    # Cell for word examples
    htmlFile.write(tableCellStart)
    if "word" in soundFileDict[word].keys():
        # Build the cell contents from the list of items
        cellContents = ""

        # This loop works. What would need to change to allow me to alphabetize the results by speaker?
        currentWordInstances = soundFileDict[word]["word"]
        for instance in currentWordInstances:
            currentSpeakerCode = instance[0]
            currentSoundFilename = instance[1]
            cellContents = cellContents + '<a href="words/' + currentSoundFilename + '">' + currentSpeakerCode + "</a><br>"
            #cellContents = cellContents + "<audio controls>"
            #cellContents = cellContents + '<source src="words/' + currentSoundFilename + '" type="audio/wav"> '
            #cellContents = cellContents + "Audio element unsupported. </audio> "
        htmlFile.write(cellContents + '\n')
    htmlFile.write(tableCellEnd)
    # Cells for sentence examples
    if "sentences" in soundFileDict[word].keys():
        htmlFile.write(tableCellStart)
        cellContents = ""
        currentSentenceInstances = soundFileDict[word]["sentences"]
        cellContents = cellContents + tableStart
        for instance in currentSentenceInstances:
            currentCreeSentence = instance[0]
            currentEnglishSentence = instance[1]
            currentSpeakerCode = instance[2]
            currentSoundFilename = instance[3]
            cellContents = cellContents + tableRowStart
            cellContents = cellContents + tableCellStart + currentCreeSentence + tableCellEnd
            cellContents = cellContents + tableCellStart + currentEnglishSentence + tableCellEnd
            cellContents = cellContents + tableCellStart + \
                           '<a href="sentences/' + currentSoundFilename + '">' + currentSpeakerCode + "</a>" + \
                           tableCellEnd + tableRowEnd
        cellContents = cellContents + tableEnd
        htmlFile.write(cellContents + '\n')

        htmlFile.write(tableCellEnd)
    else:
        # If none, just bookend the two blank cells
        htmlFile.write(tableCellStart + tableCellEnd)

    htmlFile.write(tableCellEnd)
    htmlFile.write(tableRowEnd)
# Close table
htmlFile.write(tableEnd)
# Generate HTML closing
htmlclosing = """
</body>

</html>
"""