# This program finds folders containing image files and combines sequences of images into movies using ffmpeg
# The images are set up in groups of a specified size (call it n).  So the 1st image is part of a sequence with
# the n+1, 2n+1, 3n+1, . . .  images, etc.

# The program will traverse all folders below the specified path to find images.

# To run the program, use python stich_images.py <insert file path to top of file structure containing the images>

# Notes:
# - Currently the program only works with JPEG images

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
import ImageFont, ImageDraw

##################################################
# Settings

# Number of positions - how many images form a single sequence
positions = 15;

# Prefix for image files 
image_file_prefix = "IMG_"

# Types of file extensions used to find images
alist_filter = ['JPG','jpg'] 


##################################################


# Set up command line arguments
parser = argparse.ArgumentParser()
parser.add_argument("path", help="top level file path that contains the image folders")
parser.add_argument("-p", "--prefix", help="image file prefix (default is '%s')" % image_file_prefix)


args = parser.parse_args()
rootDir = args.path
if args.prefix:
	image_file_prefix = args.prefix

print "\nThe file path is: '%s'\nThe image file prefix is: '%s'" % (rootDir, image_file_prefix)


if not os.path.exists(rootDir):
	print "\nError: The specified file path does not exist.  Exiting the program\n"
	sys.exit(0)


# Start walking through the file tree starting at the specified file path
for dirName,subdirList,fileList in os.walk( rootDir ) :
  
	print "Found directory:" , dirName
	#for fname in fileList :
	#   print "-" , fname

	# For each directory, create an array containing empty sub-arrays
	picture_list = []
	for i in range(positions):
		picture_list.append(list())
		
	counter = 0;
	
	# Look through all the images
	# Add image files matching the prefix and file extensions to the appropriate
	# place in the array
	for file in fileList:
		counter = counter % positions
		if file.startswith(image_file_prefix) and file[-3:] in alist_filter:
			# Save the picture paths in an array
			path_to_file = os.path.join(dirName,file)
			picture_list[counter].append(path_to_file)	
			print "  %d) added file %s" % (counter+1, path_to_file)
			counter = counter + 1


	# After all the matching files in the directory have been organized
	# Loop through each set of files, creating soft links to the files
	# The soft links are used to create properly numbered sequences
	image_sequence = 0
	for image_sets in picture_list:

		print "\nNow processing image sequence %d" % (image_sequence+1)
		
		# Make sure to remove any pre-existing links to images
		for i in glob.glob('img*.jpg'):
  			os.unlink (i)
		
		sequence_dir = os.path.join(dirName,"Seq_%02d" % (image_sequence+1))
		os.mkdir(sequence_dir)
		
		counter = 0
		for image in image_sets:
			# Make a symlink
			symlink_filepath = os.path.join(sequence_dir, "img%010d.jpg" % counter)
			os.symlink(image, symlink_filepath) 
			counter = counter+1
			print "     adding image: %s" % image
		
		# Now process a single image sequence
		ffmpeg_arguments = "ffmpeg -r 2 -i %s/img%%010d.jpg drawtext=\"fontfile=arial.ttf:text='blah':draw='eq(n,1)'\" -sameq -r 2  -vcodec mjpeg   ./seq%03d.mov" % (sequence_dir, image_sequence)
		subprocess.call(ffmpeg_arguments, shell=True)    
		
		image_sequence = image_sequence + 1
	
    
# Make sure all temp links to images are removed
#for i in glob.glob('img*.jpg'):
#	os.unlink (i)