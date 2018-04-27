Extraction scripts architecture and plan
========================================

 - extract_items.praat
 - extract_sessions.praat
 - extractPraat.sh
 - getSessions.py
 - getSessions.sh
 - CreateHTML.py

The extraction as I was setting it up was a two-step process. First, sound files (and related information) were extracted based on annotations done in ELAN. Second, an HTML table was compiled to facilitate surfing of and access to the extracted sound files.

Extraction
----------

This is a multi-stage process. At its core is a Praat script, “extract_items.praat”. This uses Praat to open and parse the ELAN annotation, and then use that annotation to extract words and sentences.

One step up from this is the Praat script “extract_sessions.praat”, which loops across multiple speakers in a session and across multiples sessions, to do a full extraction. It does require user interaction, as I was unable to automatically extract speaker identity. It also fails to identify recordings if the directory structure within a session isn’t exactly right.

The file “extractPraat.sh” was an attempt to wrap the Praat scripts in a shell script, that could be called directly from the command line. (I believe we have the command-line version of Praat installed on the VM.)

I then tried a couple of ways to automatically crawl through directories from the command line (“getSessions.sh”) and Python (“getSessions.py”) and reassemble the relevant material in a more helpful structure for the other scripts. (That is, copy over only what we wanted to a clean directory, that we could then run the Praat script on.) These didn’t work, but I include them here for your reference.

HTML table
----------

This was a very straightforward process, carried out by the “CreateHTML.py” script. It is internally-documented, so I will not expand here.

---

Eddie,

Sorry for not replying earlier. I worked from several scripts to generate that list. I was working on automating the whole process to a single script, but I have been unable to overcome a final issue or two.

The basic idea is to extract the annotation information, which I did via Praat (a scriptable acoustic analysis program used by phoneticians). I then wrapped this in a shell script to iterate over all of the directories with annotations in them. This is where we seemed to develop some gaps, so I don't think my shell is iterating right.

Those scripts output the extracted sound files, plus a table of metadata. I then have a final script to collect that information in the HTML table you saw.

I am going to see if I have a summary document outlining the name, location, and function of each of these scripts. If I do, I'll share it with you. If not, I'll create it and send it your way today.
