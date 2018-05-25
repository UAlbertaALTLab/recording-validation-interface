MASTER_RECORDINGS_METADATA = 1SlJRJRUiwXibAxFC0uY2sFXFb4IukGjs7Rg_G1vp_y8
REMOTE_FILENAME := "Master Recordings MetaData"

metadata.csv: 
	gdrive export --force --mime text/csv $(MASTER_RECORDINGS_METADATA)
	mv $(REMOTE_FILENAME).csv $@
