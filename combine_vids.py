# This program finds folders containing video files and combines them into one video using ffmpeg

# The program will traverse all folders below the specified path to find the videos.

# To run the program, use python combine_vids.py <insert file path to top of file structure containing the videos>

# Andrew Ruether
# Swarthmore College


# Sources used to create program
# http://pythoncentral.org/how-to-traverse-a-directory-tree/
# http://stackoverflow.com/questions/2225564/python-get-a-filtered-list-of-files-in-directory

import os
import subprocess
import glob
import argparse
import sys
import errno
import time

##################################################
# Settings

# Prefix for image files 
video_file_prefix = "M"

# Types of file extensions used to find videos
alist_filter = ['mpg','MPG'] 

# Video size
video_size = "872x480"

# Log file path
log_file_path = "."

# Log file name
log_file_name = "combine_vids_%s.log" % time.strftime("%Y-%m-%d")

# Verbose mode
verbose = True

##################################################

# Print to screen (if in verbose mode) and write to the log file
def update_status(s):
	if verbose:
		print s
	log.write("%s %s\n" % (time.strftime("%H:%M:%S"), s))



# Set up command line arguments
parser = argparse.ArgumentParser()
parser.add_argument("path", help="top level file path that contains the video folders")
parser.add_argument("-p", "--prefix", help="video file prefix (default is '%s')" % video_file_prefix)
parser.add_argument("-l", "--logfilepath", help="log file path (default is '%s')" % log_file_path)
parser.add_argument("-s", "--size", help="video size in pixels in the format WidthxHeight(default is '%s')" % video_size)

args = parser.parse_args()
rootDir = args.path
if args.prefix:
	video_file_prefix = args.prefix
if args.logfilepath:
	log_file_path = args.logfilepath
if args.size:
	video_size = args.size	
	
if not os.path.exists(rootDir):
	print "\nError: The specified file path does not exist.  Exiting the program\n"
	sys.exit(0)


# Make sure path to log file exists before creating the log file
if not os.path.exists(log_file_path):
	print "\nError: The specified log file path does not exist.  Exiting the program\n"
	sys.exit(0)
log = open(os.path.join(log_file_path, log_file_name), 'a+')

update_status("***** Now starting the video combining process *****")
update_status("The file path is: '%s'\nThe video file prefix is: '%s'" % (rootDir, video_file_prefix))

# Start walking through the file tree starting at the specified file path
for dirName,subdirList,fileList in os.walk( rootDir ) :
  
	update_status("Found directory: %s" % dirName)
	# For debugging - print the list of files in the directory
	#for fname in fileList :
	#   print "-" , fname

	# Check to see if this directory is marked as done.  If so, skip to next directory
	if os.path.exists(os.path.join(dirName,"done")):
		update_status("Directory %s marked as done already" % dirName)
		continue;

	# For each directory, create an array containing empty sub-arrays
	video_list = []
	
	# Look through all the videos
	# Add video files matching the prefix and file extensions to the appropriate
	# place in the array
	for file in fileList:
		if file.startswith(video_file_prefix) and file[-3:] in alist_filter:
			# Save the picture paths in an array
			path_to_file = os.path.join(dirName,file)
			video_list.append(path_to_file)	
			update_status( "  Found video file %s" % (path_to_file))
	
	
	# If no matching videos were found, go to the next directory
	if len(video_list) < 1 :
		update_status( "No matching videos found in %s.  Moving to next duirectory" % dirName )
		continue
	
	# After all the matching files in the directory have been organized
	# create the video
	ffmpeg_arguments = "ffmpeg -i concat:\"%s\" -s %s -vcodec mpeg4 -strict -2 -an -sameq combined_video.mp4" 	% ('|'.join(video_list), video_size)
	update_status(ffmpeg_arguments)
	subprocess.call(ffmpeg_arguments, shell=True)    

	# Mark this directory as complete by placing an empty file named "done" in the folder
	done_file = open(os.path.join(dirName, "done"), 'a+')
	done_file.close()
	
	# Done with this directory -- go on to the next one
		
update_status("Complete")
log.close()



