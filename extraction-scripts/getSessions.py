#!/usr/bin/python3

# Curate collection of annotated recordings.
#
# 1. Identify source & destination directories.
# 2. For each subdirectory in the source, determine whether it has
#    both sound and textgrid files.
# 3. For those that have both, create/locate a destination subdirectory 
#    and copy all sound and textgrid files there.
#
# Report progress/status at each directory & file.

import os
import glob
import shutil

print("\nRunning Python script ...\n\n")
# First, set up locations
baseDir = "/home/ARTSRN/timills/av/backup-mwe"
destDir = baseDir + "/tim-clean"

print("Base directory = <" + baseDir + ">")
print("Destination = <" + destDir + ">")

baseContents = glob.glob(baseDir + "/20*")
baseContents.remove(destDir)

for item in baseContents:
	print("Processing <" + item + ">")

	# Is it an accessible directory?
	if os.path.isdir(item):
		# Make list of all .wav; make list of all .TextGrid:
		sounds, textgrids = [], []
		for (maindir, _, filenames) in os.walk(item):
			for f in filenames:
				if f.lower()[-4:] == ".wav":
					fullfile = os.path.join(maindir, f)
					sounds.append(fullfile)
				elif f.lower()[-9:] == ".textgrid":
					fullfile = os.path.join(maindir, f)
					textgrids.append(fullfile)

		# Does it have sounds & textgrids?
		if(len(sounds) > 0 and len(textgrids) > 0):
			#print(str(len(sounds)) + " sounds")
			#print(str(len(textgrids)) + " annotations")

			# Locate/create dest folder
			subfolderName = os.path.split(item)[1]
			destSubdir = os.path.join(destDir, subfolderName)
			if(not(os.path.exists(destSubdir))):
				os.mkdir(destSubdir)
			# Move all sounds there
			for soundfile in sounds:
				print("Copying <" + soundfile + ">")
				shutil.copy(soundfile, destSubdir)
			# Move all textgrids there
			for textgridfile in textgrids:
				print("Copying <" + textgridfile + ">")
				shutil.copy(textgridfile, destSubdir)
	print("Done processing <" + item + ">")

print("\n\n... Python script complete!\n")
