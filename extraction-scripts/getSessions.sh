#!/bin/bash

# First get listing of all folders in directory of recordings.
# shopt commands allow proper treatment of empty list.
# (See "http://stackoverflow.com/questions/18884992/how-do-i-assign-ls-to-an-array-in-linux-bash")

# First, set up location
BASEDIR="/home/ARTSRN/timills/av/backup-mwe"
DIRLIST=`ls $BASEDIR`

# Next, iterate over directory contents
for ITEM in $DIRLIST; do
	# Build full path to idemt
	FOLDERNAME="$BASEDIR/$ITEM"
	# We're only interested in directories
	if [ -d "$FOLDERNAME" ]; then
		# Find and count all the sounds and textgrids
		# (The OIFS and IFS deals with delimiters.)
		OIFS="$IFS"
		IFS="\n"
		SOUNDS=$(find $FOLDERNAME -name '*.wav')
		SOUNDLIST=( $SOUNDS )
		NUMSOUNDS=${#SOUNDLIST[@]}
		TEXTGRIDS=$(find $FOLDERNAME -name '*.TextGrid')
		TEXTGRIDLIST=( $TEXTGRIDS )
		NUMTEXTGRIDS=${#TEXTGRIDLIST[@]}
		IFS="$OIFS"
		# Single out only those directories that contain at least 
		# one sound and one textgrid file.
		# Exclude the directory we're using for the sorted files!
		if [ $NUMSOUNDS -gt 0 ] && [ $NUMTEXTGRIDS -gt 0 ] && [ $ITEM != "tim-clean" ]; then
			echo "$FOLDERNAME has <$NUMSOUNDS> sounds and <$NUMTEXTGRIDS> TextGrids"
			# This is where stuff happens
			# Locate/create corresponding directory in "tim-clean"
			TARGETDIR="$BASEDIR/tim-clean/$ITEM"
			echo "Target: <$TARGETDIR>"
			if [ ! -e "$TARGETDIR" ]; then
				mkdir $TARGETDIR
			fi
			# Copy sounds and textgrids across
			for SOUNDFILE in "${SOUNDLIST[@]}"; do
				echo "Copying <$SOUNDFILE>"
				cp $SOUNDFILE $TARGETDIR/
			done
			for TEXTGRIDFILE in $TEXTGRIDLIST; do
				cp $TEXTGRIDFILE $TARGETDIR/
			done
		#else
		#	echo "$FOLDERNAME lacks either sounds or TextGrids"
		fi
		#echo $FOLDERNAME
		# Check if folder already exists at current location
		#if [ -e "$FOLDERNAME" ]
		#then
		#	echo "Folder already exists. Continuing ..."
		#else
		#	echo "Creating a folder ..."
		#	mkdir $FOLDERNAME
		#fi
	#else
	#	echo "'$ITEM' is not a directory."
	fi
done
