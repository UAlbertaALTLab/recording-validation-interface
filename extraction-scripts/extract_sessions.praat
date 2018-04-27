# extract_sessions.praat
#
# This script is given a location in which there are
# directories/folders, each of which contains matched 
# sound (*.wav) and annotation (*.TextGrid) files.
#
# The script identifies each pair of files, loads them,
# prompts the user for a speaker ID, and then calls the
# extract_items.praat script to extract word and 
# sentence sound objects and build an informative table
# based on the annotation labels.
#
# Arguments: Master directory
# Behaviour:
####### Test stage 0: report contents of daughter directories
####### Test stage 1: report names of paired files
####### Test stage 2: ask for speaker IDs; report them alongside filenames
#######	Test stage 3: launch extract_items.praat and do the extraction too.

form Identify master directory
	### My Windows laptop
	#sentence master_directory C:\Users\Timothy\Documents\Altlab\MaskwacisRecordings\
	#sentence word_directory C:\Users\Timothy\Documents\Altlab\MaskwacisRecordings\Extracted\words\
	#sentence sentence_directory C:\Users\Timothy\Documents\Altlab\MaskwacisRecordings\Extracted\sentences\
	#sentence session_codes_file ???
	### My office Mac
	sentence master_directory /Users/timills/Google Drive/Research/Altlab/Maskwacis-recs/
	sentence word_directory /Users/timills/Google Drive/Research/Altlab/Maskwacis-recs/Extracted/words/
	sentence sentence_directory /Users/timills/Google Drive/Research/Altlab/Maskwacis-recs/Extracted/sentences/
	sentence session_codes_file /Users/timills/Dropbox/Research/ALTlab/speaker-codes.csv
	### Should be same
	word word_filename word_codes.txt
	word sentence_filename sentence_codes.txt
endform

# Windows
#sep$ = "\"
# Mac
sep$ = "/"

# Get table of sessions and speaker IDs
sessionTableID = Read Table from tab-separated file: session_codes_file$

writeInfoLine: "Scanning directory <", master_directory$, ">"

directoryStringsID = Create Strings as directory list: "directoryList", master_directory$
numberSubdirectories = Get number of strings
for subdirNum from 1 to numberSubdirectories

	# Get list of files in current subdirectory
	currentSubdirName$ = Get string: subdirNum
	fullSubdirName$ = master_directory$ + currentSubdirName$
	#appendInfoLine: "... scanning subdirectory <", fullSubdirName$, ">"
	subdirContentsID = Create Strings as file list: "fileList", fullSubdirName$ + sep$ + "*.TextGrid"
	subDirSize = Get number of strings
	#appendInfoLine: "...... ", string$(subDirSize), " TextGrid files"
	for fileNum from 1 to subDirSize
		fileName$ = Get string: fileNum
		annotationFile$ = fullSubdirName$ + sep$ + fileName$
		appendInfoLine: annotationFile$
		# See if there is a matching sound file
		baseName$ = left$(fileName$, index(fileName$, ".")-1)
		soundFile$ = fullSubdirName$ + sep$ + baseName$ + ".wav"
		###
		# Some sound files are just "Track xxx" without the session date present in the TextGrid files.
		# These sessions are missed because the sound filename doesn't match the TextGrid filename.
		# This kludge gets us past that.
		if not(fileReadable(soundFile$))
			trackIndex = index(soundFile$, "Track")
			soundFileLength = length(soundFile$)
			shorterSoundFile$ = right$(soundFile$, (soundFileLength - trackIndex + 1))
			if fileReadable(shorterSoundFile$)
				soundFile$ = shorterSoundFile$
			endif
		endif
		# end kludge
		###
		if fileReadable (soundFile$)
			appendInfoLine: tab$ + "Matching sound file. Loading both."
			soundID = Open long sound file: soundFile$
			annotationID = Read from file: annotationFile$

			####
			# A subform to elicit the speaker ID.
			####
			#appendInfoLine: "Get speaker info on <" + annotationFile$ + ">"
			#beginPause: "What is the speaker code for <" + annotationFile$ + ">?"
			#	text: "speaker", "abc"
			#	text: "session", currentSubdirName$
			#endPause: "Continue", 1

			###
			# A routine to obtain speaker ID
			###

			finalSubdirLength = length(fullSubdirName$) - rindex(fullSubdirName$, sep$)
			session$ = right$(fullSubdirName$, finalSubdirLength)

			select sessionTableID
			rowNumber = Search column: "SESSION", session$
			if rowNumber == 0
				appendInfoLine: "No matching session found for directory <" + session$ + ">"
			else
				## Get Mic#
				loc = index(baseName$, "Track")
				if loc > 0
					# if "Track_?*", use ? (single character)
					speakerNum$ = mid$(baseName$, loc+6, 1)
				else
					# else use last char of baseName
					speakerNum$ = right$(baseName$, 1)
				endif
				columnName$ = "MIC " + speakerNum$
				## Get speaker ID
				select sessionTableID
				speaker$ = Get value: rowNumber, columnName$

				####
				# A call to the extraction script. Make sure it is in the same directory as this script.
				####
				appendInfoLine: "Extract items from <" + soundFile$ + "> using speaker ID <" + speaker$ + ">"
				#pauseScript: "Is this right?"
				select soundID
				plus annotationID
				runScript: "extract_items.praat", word_directory$, sentence_directory$, word_filename$, sentence_filename$, session$, speaker$

			endif

			select soundID
			plus annotationID
			Remove
			
		else
			#appendInfoLine: tab$ + "No matching sound file."
		endif
		select subdirContentsID
	endfor

	Remove
	select directoryStringsID
endfor

Remove
select sessionTableID
Remove
