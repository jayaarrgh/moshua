
# This is a script I found on github for datamoshing. I made the UX a little better.
# I added yaspin and timing. Unneccesary but fun.
# I used this script as the basis for the datamosh_api.py module

import sys
if sys.version_info[0] != 3 or sys.version_info[1] < 2:
	print('This version works with Python version 3.2 and above but not Python 2, sorry!')
	sys.exit()
import os
import argparse
import subprocess
from datetime import datetime
from yaspin import yaspin, spinners

# make sure ffmpeg is installed
try:
	# sends command line output to /dev/null when trying to open ffmpeg so it doesn't muck up our beautiful command line
	null = open("/dev/null", "w")
	# it tries to open ffmpeg
	subprocess.Popen("ffmpeg", stdout=null, stderr=null)
	# politely closes /dev/null
	null.close()
except OSError:
	print("ffmpeg was not found. Please install it. Thanks.")
	sys.exit()


start_sec = 0
start_effect_sec = 3
end_effect_sec   = 12
end_sec = 60
repeat_p_frames = 5
output_width = 480
fps = 25
output_directory = 'moshed_videos'
# - designator for start of i-frame: 0x0001B0 & p-frame: 0x0001B6
# - designator for end of any frame: 0x30306463 & usually seen as ASCII 00dc & '0x' is a common way to say that a number is in hexidecimal format.
IFRAME = bytes.fromhex('0001B0')
END_OF_FRAME = bytes.fromhex('30306463')

with yaspin(spinners.Spinners.pong, text="  p r o c e s s i n g  .  .  .") as sp:
	# this makes sure the video file exists. It is used below in the 'input_video' argparse
	def quit_if_no_video_file(video_file):
		if not os.path.isfile(video_file):
			raise argparse.ArgumentTypeError("Couldn't find {}. You might want to check the file name??".format(video_file))
		else:
			return video_file
	
	# make sure the output directory exists
	def confirm_output_directory(output_directory):
		if not os.path.exists(output_directory): os.mkdir(output_directory)
		return output_directory
	
	# programs get real mad if a video is an odd number of pixels wide (or in height)
	def even_output_width(output_width):
		output_width = int(output_width)
		return output_width if output_width % 2 == 0 else output_width + 1
	
	# this makes the options available at the command line nicely and with help!
	parser = argparse.ArgumentParser() 
	parser.add_argument('input_video', type=quit_if_no_video_file, help="File to be moshed")
	parser.add_argument('--start_sec',        default = start_sec,        type=float,                    help="Time the video starts on the original footage's timeline. Trims preceding footage.")
	parser.add_argument('--end_sec',    	  default = end_sec,          type=float,                    help="Time on the original footage's time when it is trimmed.")
	parser.add_argument('--start_effect_sec', default = start_effect_sec, type=float,                    help="Time the effect starts on the trimmed footage's timeline. The output video can be much longer.")
	parser.add_argument('--end_effect_sec',   default = end_effect_sec,   type=float,                    help="Time the effect ends on the trimmed footage's timeline.")
	parser.add_argument('--repeat_p_frames',  default = repeat_p_frames,  type=int,                      help="If this is set to 0 the result will only contain i-frames. Possibly only a single i-frame.")
	parser.add_argument('--output_width',     default = output_width,     type=even_output_width,        help="Width of output video in pixels. 480 is Twitter-friendly.")
	parser.add_argument('--fps',              default = fps,              type=int,                      help="The number of frames per second the initial video is converted to before moshing.")
	parser.add_argument('--output_dir',       default = output_directory, type=confirm_output_directory, help="Output directory")
	
	# this makes sure the local variables are up to date after all the argparsing
	globals().update( parser.parse_args().__dict__.items() )
	
	end_effect_hold = end_effect_sec - start_effect_sec
	start_effect_sec = start_effect_sec - start_sec
	end_effect_sec = start_effect_sec + end_effect_hold
	if start_effect_sec > end_effect_sec:
		print("No moshing will occur because --start_effect_sec begins after --end_effect_sec")
		sys.exit()



	# where we make new file names - could fail here?

	# basename seperates the file name from the directory it's in so /home/user/you/video.mp4 becomes video.mp4
	# splitext short for "split extension" splits video.mp4 into a list ['video','.mp4'] and [0] returns 'video' to file_name
	file_name = os.path.splitext( os.path.basename(input_video) )[0]
	# path.join pushes the directory and file name together and makes sure there's a / between them
	input_avi =  os.path.join(output_dir, 'datamoshing_input.avi')  # must be an AVI so i-frames can be located in binary file
	output_avi = os.path.join(output_dir, 'datamoshing_output.avi')
	# {} is where 'file_name' is put when making the 'output_video' variable
	output_video = os.path.join(output_dir, 'moshed_{}.mp4'.format(file_name))  # this ensures we won't over-write your original video
	
	sp.write("\nD A T A M O S H I N G  .  .  .\n")
	startTime = datetime.now()
	
	# ffmpeg command converts original file to avi -- creates input_avi file
	ffmpeg_to_avi = (f'ffmpeg -loglevel error -y -i {input_video} -crf 0 -pix_fmt yuv420p'
					 f' -r {fps} -ss {start_sec} -to {end_sec} {input_avi}')
	subprocess.call(ffmpeg_to_avi, shell=True)
	
	sp.write(f'A V I   T I M E      :  {(datetime.now()-startTime).total_seconds()}')
	moshStartTime = datetime.now()
	
	# open up the new files so we can read and write bytes to them
	in_file  = open(input_avi,  'rb')
	out_file = open(output_avi, 'wb')
	# because we used 'rb' above when the file is read the output is in byte format instead of Unicode strings
	in_file_bytes = in_file.read()
	# I think this should be in a while loop and you look for ends of frames and remove them
	frames = in_file_bytes.split(END_OF_FRAME)
	
	# We want at least one i-frame before the glitching starts
	i_frame_yet = False
	for index, frame in enumerate(frames):
		if  i_frame_yet == False or index < int(start_effect_sec * fps) or index > int(end_effect_sec * fps):
			out_file.write(frame + END_OF_FRAME)          # add the end frame back from the split above
			if frame[5:8] == IFRAME: i_frame_yet = True   # found an i-frame, let the glitching begin
		else:
			if frame[5:8] != IFRAME:  # while we're moshing we're repeating p-frames and multiplying i-frames
				for i in range(repeat_p_frames):
					out_file.write(frame + END_OF_FRAME)
	
	sp.write(f"M O S H   T I M E    :  {(datetime.now()-moshStartTime).total_seconds()}")
	convertStartTime=datetime.now()
	
	in_file.close()
	out_file.close()
	
	# Convert avi to mp4. If you want a different format try changing the output variable's file extension
	# and commenting out the rest of the line after -crf. If that doesn't work you'll be making friends with ffmpeg's options.
	# The -t option specifies the duration of the final video and usually helps avoid the malformed headers at the end.
	avi_to_mp4 = (f'ffmpeg -loglevel error -y -i {output_avi} -crf 18 -pix_fmt yuv420p -vcodec libx264 -acodec aac -r {fps}'
				  f' -vf "scale={output_width}:-2:flags=lanczos" -ss {start_sec} -to {end_sec} {output_video}')
	subprocess.call(avi_to_mp4, shell=True)
	
	sp.write(f'M P 4   T I M E      :  {(datetime.now() - convertStartTime).total_seconds()}')
	sp.write(f'T O T A L   T I M E  :  {(datetime.now() - startTime).total_seconds()}')
	
	# gets rid of the in-between files so they're not crudding up your system
	os.remove(input_avi)
	os.remove(output_avi)
	
print('\nD A T A M O S H   C O M P L E T E\n')

	##############################################################################################################
	##                                           A bit of explanation                                           ##
	##      Datamoshing is a time honored glitching technique discovered by a hero of another era               ##
	##      or perhaps a god. We'll never know who they were but they're probably really old now so             ##
	##      say a prayer for them in your heart. Also consider donating your youthful blood so they             ##
	##      can live forever on Peter Thiel's seastead paradise which is totally a good idea and not the        ##
	##      crackpot idea of a sheltered, solipsistic man with access to billions of other people's dollars.    ##
	##                                                                                                          ##
	##      A common method of datamoshing uses Avidemux which tends to get crashy when you mess with the       ##
	##      internals of video files. If that seems your more likely route to datamosh glory there are lots     ##
	##      of good tutorials on the internet. Have fun, good luck, no I don't know which Avidemux version      ##
	##      you should use.                                                                                     ##
	##                                                                                                          ##
	##      What's happening in the code below is that first your video file is converted to AVI format         ##
	##      which is glitch friendly as it sort-of doesn't care if you delete frames from the middle            ##
	##      willy-nilly (mp4 gets real mad if you delete stuff in a video file).                                ##
	##                                                                                                          ##
	##      There are 2 types of frames that we're dealing with: i-frames and p-frames.                         ##
	##      I-frames (aka key frames) give a full frame's worth of information while p-frames are               ##
	##      used to calculate the difference from frame to frame and avoid storing lots of                      ##
	##      redundant frame information. A video can be entirely i-frames but the file size is much larger      ##
	##      than setting an i-frame every 10 or 20 frames and making the rest p-frames.                         ##
	##                                                                                                          ##
	##      The first i-frame is the only one that's required and after that we use p-frames                    ##
	##      to calculate from frame to frame. The encoding algorithm then makes inter-frame calculations        ##
	##      and sometimes interesting effects happen.                                                           ##
	##                                                                                                          ##
	##      Initially datamoshing was just deleting the extra i-frames maybe smooshing some p-frames            ##
	##      in from another video and seeing what you got. However the glitchers eventually grew bored of       ##
	##      this and discovered if they repeated p-frames that the calculations would cause a blooming          ##
	##      effect and the results were real rowdy. So that's what the repeat_p_frames variable does and        ##
	##      that's why "it sounds like a dying printer"-@ksheely. Because we're repeating p-frames the video    ##
	##      length may get much longer. At ((25fps - 1 i-frame)) * 15 or (24 * 15) a single second of           ##
	##      24 frames turns into 360 frames which is (360 frames / 25 fps) = 14.4 seconds.                      ##
	##                                                                                                          ##
	##      After we're done mucking around with i-frames and p-frames the results are fed to ffmpeg            ##
	##      which locks in the glitches and makes a twitter-ready video to share with your friends              ##
	##      After you share about 10 of these you'll either be better friends with them or they'll stop         ##
	##      acknowledging you and delete you from their social media lifestyle. You will then have more         ##
	##      open slots for all your new good friends who enjoy datamoshing thus giving your peer group          ##
	##      a common bond and sense of purpose as you continue the journey of life together, forever.           ##
	##############################################################################################################

######################################################################################################################
# the code was adapted from https://github.com/amgadani/Datamosh-python/blob/master/standard.py by @amgadani
# which was adapted from https://github.com/grampajoe/Autodatamosh/blob/master/autodatamosh.pl by @joefriedl

# Here comes the disclaimer. This code is under the MIT License. 
# Basically you can include this code in commercial or personal projects and you're welcome to edit the code.
# If it breaks anything it's not my fault and I don't have to help you fix the work computer you broke while 
# glitching on company time.
# Also I'm not obligated to help you fix or change the code but if your request is reasonable I probably will.
# For instance, demanding that I program the next Facebook for free would be an unreasonable request.

#######################################

# replaced cleaner faster method - f string formatting
# subprocess.call('ffmpeg -loglevel error -y -i ' + input_video + ' ' +
# 				' -crf 0 -pix_fmt yuv420p -r ' + str(fps) + ' ' +
# 				' -ss ' + str(start_sec) + ' -to ' + str(end_sec) + ' ' +
# 				input_avi, shell=True)

# subprocess.call('ffmpeg -loglevel error -y -i ' + output_avi + ' ' +
# 				' -crf 18 -pix_fmt yuv420p -vcodec libx264 -acodec aac -r ' + str(fps) + ' ' +
# 				' -vf "scale=' + str(output_width) + ':-2:flags=lanczos" ' + ' ' +
# 				' -ss ' + str(start_sec) + ' -to ' + str(end_sec) + ' ' +
# 				output_video, shell=true)
