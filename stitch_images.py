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
# Installing PIL: http://stackoverflow.com/questions/9070074/how-to-install-pil-on-mac-os-x-10-7-2-lion/11368029#11368029
# http://code.activestate.com/recipes/576646-exif-date-based-jpeg-files-rename-using-pil/

import os
import subprocess
import glob
import argparse
import sys
from PIL import Image, ImageDraw, ImageFont
from PIL.ExifTags import TAGS
import errno
import time

##################################################
# Settings

# Number of positions - how many images form a single sequence
positions = 15;

# Prefix for image files 
image_file_prefix = "IMG_"

# Types of file extensions used to find images
alist_filter = ['JPG','jpg'] 

# Output frame rate (frames per second)
frame_rate = 2

# Log file path
log_file_path = "."

# Log file name
log_file_name = "stitch_images_%s.log" % time.strftime("%Y-%m-%d")

# Verbose mode
verbose = True

##################################################

# Print to screen (if in verbose mode) and write to the log file
def update_status(s):
	if verbose:
		print s
	log.write("%s %s\n" % (time.strftime("%H:%M:%S"), s))



# Setup PIL (Python image library)
font = ImageFont.truetype("Arial.ttf", 75)

# Set up command line arguments
parser = argparse.ArgumentParser()
parser.add_argument("path", help="top level file path that contains the image folders")
parser.add_argument("-p", "--prefix", help="image file prefix (default is '%s')" % image_file_prefix)
parser.add_argument("-l", "--logfilepath", help="log file path (default is '%s')" % log_file_path)


args = parser.parse_args()
rootDir = args.path
if args.prefix:
	image_file_prefix = args.prefix
if args.logfilepath:
	log_file_path = args.logfilepath
	
	
if not os.path.exists(rootDir):
	print "\nError: The specified file path does not exist.  Exiting the program\n"
	sys.exit(0)


# Make sure path to log file exists before creating the log file
if not os.path.exists(log_file_path):
	print "\nError: The specified log file path does not exist.  Exiting the program\n"
	sys.exit(0)
log = open(os.path.join(log_file_path, log_file_name), 'a+')

update_status("***** Now starting the image stitch process *****")
update_status("The file path is: '%s'\nThe image file prefix is: '%s'" % (rootDir, image_file_prefix))

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
			update_status( "  %d) added file %s" % (counter+1, path_to_file))
			counter = counter + 1


	# After all the matching files in the directory have been organized
	# Loop through each set of files, creating soft links to the files
	# The soft links are used to create properly numbered sequences
	image_sequence = 0
	for image_sets in picture_list:

		update_status( "Now processing image sequence %d" % (image_sequence+1) )
		
		# If there aren't any images in this set, skip to the next set
		if len(image_sets) < 1 :
			update_status( "No matching images found in sequence %d -- skipping to next sequence" % (image_sequence+1) )
			continue;
		
		
		# Make sure to remove any pre-existing links to images
		#for i in glob.glob('img*.jpg'):
  		#	os.unlink (i)
		
		# Create a directory for the sequence 
		sequence_dir = os.path.join(dirName,"%02d_Seq" % (image_sequence+1))
		if not os.path.exists(sequence_dir):
			os.mkdir(sequence_dir)
	
		counter = 0
		for image in image_sets:
		
			# Make a symlink
			symlink_filepath = os.path.join(sequence_dir, "img%010d.jpg" % counter)
			try:
				os.symlink(image, symlink_filepath)
			except OSError, e:
				if e.errno == errno.EEXIST:
					os.remove(symlink_filepath)
					os.symlink(image, symlink_filepath)
					
			update_status ("     Getting info and creating symlink for image %s" % image)
			
			# Get the timestamp from the image
			# Assume that we don't know it (in case it is unreadable)
			timestamp = "Unknown"
			try:
				im = Image.open(image)
				if hasattr(im, '_getexif'):
					exifdata = im._getexif()
					ctime = exifdata[0x9003]
					timestamp = ctime
			except: 
				_type, value, traceback = sys.exc_info()
				update_status( "Error %r" % value )
       						
			# Add a timestamp image
			img = Image.new('RGBA',(900, 100))
			draw = ImageDraw.Draw(img)
			draw.text((10, 10), timestamp, font=font, fill=(255, 255, 0))
			timestamp_filepath = os.path.join(sequence_dir, "timestamp_%010d.png" % counter)
			img.save(timestamp_filepath, 'PNG')	
			
			counter = counter+1
			
		# Now process a single image sequence
	
		#First make a video file of the timestamps
		ffmpeg_arguments = "ffmpeg -r %s -i \"%s/timestamp_%%010d.png\" -sameq -r %s  -vcodec mjpeg  -y \"%s/_timestamp.mov\"" % (frame_rate, sequence_dir, frame_rate, sequence_dir)
		update_status(ffmpeg_arguments)
		subprocess.call(ffmpeg_arguments, shell=True)    
			
		# Then combine the images with the timestamp video
		#ffmpeg_arguments = "ffmpeg -r 2 -i %s/img%%010d.jpg -sameq -r 2  -vcodec mjpeg   ./seq%03d.mov" % (sequence_dir, image_sequence)
		ffmpeg_arguments = "ffmpeg -r %s -i \"%s/img%%010d.jpg\" -vf \"movie=%s/_timestamp.mov[clip2]; [in][clip2] overlay=0:overlay_h [out]\" -sameq -r %s  -vcodec mjpeg  -y \"%s/_seq%03d.mov\"" % (frame_rate, sequence_dir, sequence_dir, frame_rate, sequence_dir, image_sequence+1)
		update_status(ffmpeg_arguments)
		subprocess.call(ffmpeg_arguments, shell=True)    
		
		# Then remove the timestamp video (if it exists)
		if os.path.exists("%s/_timestamp.mov" % sequence_dir): 
			os.unlink ("%s/_timestamp.mov" % sequence_dir)
		
		# Mark this directory as complete by placing an empty file named "done" in the folder
		done_file = open(os.path.join(sequence_dir, "done"), 'a+')
		done_file.close()
		
		image_sequence = image_sequence + 1
	
	# Mark the top level folder complete by placing an empty file named "done" in the folder
	done_file = open(os.path.join(dirName, "done"), 'a+')
	done_file.close()
		
	

    
# Make sure all temp links to images are removed - Vince wants these left in
#for i in glob.glob('img*.jpg'):
#	os.unlink (i)

update_status("Complete")
log.close()



