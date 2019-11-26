
## Based on some other dudes' work.
## I have made this an api instead of a script.
# I will add scripting functionality to this again. in if __name__ == '__main__'

import os
import sys
if sys.version_info[0] != 3 or sys.version_info[1] < 2:
    print('This version works with Python version 3.2 and above but not Python 2, sorry!')
    sys.exit()
# import argparse
import subprocess
from datetime import datetime

from yaspin import yaspin, spinners

# make sure ffmpeg is installed
# import ffmpeg  # does the import do that? was running without the import!
try:
    # sends command line output to /dev/null when trying to open ffmpeg so it doesn't muck up our beautiful command line
    # was '/dev/null' -- cross platform should be os.devnull
    null = open(os.devnull, "w")
    # it tries to open ffmpeg
    subprocess.Popen("ffmpeg", stdout=null, stderr=null)
    # politely closes /dev/null
    null.close()
except OSError:
    print("ffmpeg was not found. Please install it. Thanks.")
    sys.exit()
except Exception as ex:
    raise ex

# static class Datamosh.run 
class Datamosh:
    def __init__(self):
        raise Exception('Nah, that is not going to work')
    
    # defaults for the static method
    # input_video # get from input to function
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
   

    ## STATIC METHODS
    
    @staticmethod
    def _quit_if_no_video_file(video_file):
        print(video_file)
        if not os.path.isfile(video_file):
            raise Exception("Couldn't find {video_file}. You might want to check the file name?")

    # make sure the output directory exists
    @staticmethod
    def _confirm_output_directory(output_directory):
        if not os.path.exists(output_directory): os.mkdir(output_directory)
        return output_directory
    
    
    # programs get real mad if a video is an odd number of pixels wide (or in height)
    @staticmethod
    def _even_output_width(output_width):
        output_width = int(output_width)
        return output_width if output_width % 2 == 0 else output_width + 1
   

    @staticmethod
    def _clean_input_video_path(input_video):
        # make sure path comes in nice and clean 
        split_file_name = os.path.splitext(os.path.basename(input_video))
        if split_file_name[1] == '.avi':
            Datamosh.skip_conversion = True
            print('should skip initial avi conversion')

        file_name = split_file_name[0]
        just_dirs = input_video.split(file_name)[0]
        # works here what about windows
        if any(c.isspace() for c in just_dirs):
            just_dirs = just_dirs.replace(" ", "\ ")
        input_video = just_dirs + split_file_name[0] + split_file_name[1]
        if any(c.isspace() for c in file_name):
            input_video = f"'{input_video}'"
        return input_video 
   

    ## CLASS METHODS -- 1 or 2 public methods? w/ & w/o bloom
    
    # should this be a method on a class or take a class as input?
    # needs configuration these are the run parameters -- and there can be many more. We should be using objects.
    @classmethod
    def run(cls, input_video, start_sec, end_sec, start_effect_sec, end_effect_sec, repeat_p_frames, output_width, output_dir):
        # reset and validate the class data MVC...
        cls.input_video = cls._clean_input_video_path(input_video)
        cls.start_sec=start_sec
        cls.end_sec=end_sec
        cls.start_effect_sec=start_effect_sec
        cls.end_effect_sec=end_effect_sec
        cls.repeat_p_frames=repeat_p_frames
        cls.output_width = cls._even_output_width(output_width)
        cls.output_directory = output_dir if output_dir else cls.output_directory
        cls.output_directory = cls._confirm_output_directory(cls.output_directory)
        #cls.fps=cls.fps
        # this fails when spaces in path or file name - even after clean up above
        # cls._quit_if_no_video_file(cls.input_video)
        
        # MUNGE some of the data - WHY?
        end_effect_hold = end_effect_sec - start_effect_sec
        cls.start_effect_sec = start_effect_sec - start_sec
        cls.end_effect_sec = start_effect_sec + end_effect_hold
        if start_effect_sec > end_effect_sec:
            print("No moshing will occur because --start_effect_sec begins after --end_effect_sec")
            sys.exit()
        
        file_name = os.path.splitext( os.path.basename(input_video) )[0].replace(' ', '_')
        cls.input_avi =  os.path.join(cls.output_directory, 'datamoshing_input.avi')
        cls.output_avi = os.path.join(cls.output_directory, 'datamoshing_output.avi')
        cls.output_video = os.path.join(cls.output_directory, f'moshed_{file_name}.mp4')
       
        ### EVERYTHING ABOVE IN THIS METHOD IS JUST SETUP

        #print("D A T A M O S H I N G  .  .  .\n\n\n\n\n\n\n\n\n\n")
        with yaspin(spinners.Spinners.pong, text="  m o s h i n g  .  .  .") as sp:
            startTime = datetime.now()
            cls._convert_input_to_avi()  # avi for iframes is essential
            aviEndTime = datetime.now() 
            
            #cls._i_frame_removal_mosh()
            cls._mosh_with_bloom() # mosh converted avi
            
            moshEndTime = datetime.now() 
            cls._convert_datamosh_to_mp4()
            
            sp.write(f'\nA V I   T I M E      :  {(aviEndTime-startTime).total_seconds()}')
            sp.write(f"M O S H   T I M E    :  {(moshEndTime-aviEndTime).total_seconds()}")
            sp.write(f'M P 4   T I M E      :  {(datetime.now() - moshEndTime).total_seconds()}')
            sp.write(f'T O T A L   T I M E  :  {(datetime.now() - startTime).total_seconds()}')
        print('\nD A T A M O S H   C O M P L E T E')
  
    @classmethod
    def _convert_input_to_avi(c):
        ffmpeg_to_avi = (f'ffmpeg -loglevel error -y -i {c.input_video} -crf 0 -pix_fmt yuv420p'
                         f' -r {c.fps} -ss {c.start_sec} -to {c.end_sec} {c.input_avi}')
        subprocess.call(ffmpeg_to_avi, shell=True)

    @classmethod
    def _mosh_with_bloom(cls):
        with open(cls.input_avi, 'rb') as in_file, open(cls.output_avi, 'wb') as out_file:
            frames = in_file.read().split(cls.END_OF_FRAME)
            mosh_start = int(cls.start_effect_sec * cls.fps)
            mosh_stop = int(cls.end_effect_sec * cls.fps)
            # We want at least one i-frame before the glitching starts
            i_frame_yet = False
            for i, frame in enumerate(frames):
                if  (i_frame_yet == False or i < mosh_start or i > mosh_stop):
                    out_file.write(frame + cls.END_OF_FRAME)          # add the end frame back from the split above
                    if frame[5:8] == cls.IFRAME: i_frame_yet = True   # found an i-frame, let the glitching begin
                else:
                    if frame[5:8] != cls.IFRAME:  # while we're moshing we're repeating p-frames and multiplying i-frames
                        for i in range(cls.repeat_p_frames):
                            out_file.write(frame + cls.END_OF_FRAME)
        os.remove(cls.input_avi)  # converted avi has been moshed

    @classmethod
    def _convert_datamosh_to_mp4(c):
        ## TRYING TO ADD A SPEED UP TOO! Couldn't really tell if it works.
        #### The idea is that the video is slowed down by blooming
        #### You could optionally speed up the video at the same time
        ## -filter:v "setpts={c.repeat_p_frames}*PTS" 
        avi_to_mp4 = (f'ffmpeg -loglevel error -y -i {c.output_avi} -crf 18 -pix_fmt yuv420p -vcodec libx264 -acodec aac -r {c.fps}'
                      f' -vf "scale={c.output_width}:-2:flags=lanczos" -ss {c.start_sec} -to {c.end_sec} {c.output_video}')
        subprocess.call(avi_to_mp4, shell=True)
        os.remove(c.output_avi)  # output_avi has been converted
    
    
    @classmethod
    def _i_frame_removal_mosh(cls):
        """This worked last I tried. Should be an option in the gui and run method?"""
        with open(cls.input_avi, 'rb') as in_file, open(cls.output_avi, 'wb') as out_file:
            frames = in_file.read().split(cls.END_OF_FRAME)
            i_frame_yet = False
            for f in frames:
                if not i_frame_yet and f[5:8] == cls.IFRAME:
                    out_file.write(f+cls.END_OF_FRAME)  # WHY NOT REMOVE THIS TOO?
                    i_frame_yet = True
                else:
                    if f[5:8] == cls.IFRAME:
                        out_file.write(cls.END_OF_FRAME) # remove the frame
                    else:
                        out_file.write(f+cls.END_OF_FRAME)
        os.remove(cls.input_avi)  # converted avi has been moshed
                        

## TODO:
    # ADD IF NAME MAIN CHECK - RUN AS SCRIPT - BRING BACK ARGPARSE


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

# FFMPEG CALL 1 -- INPUT TO AVI

# replaced by use of formate string then ffmpeg module... idk why... and then back to format strings
# subprocess.call('ffmpeg -loglevel error -y -i ' + input_video + ' ' +
# 				' -crf 0 -pix_fmt yuv420p -r ' + str(fps) + ' ' +
# 				' -ss ' + str(start_sec) + ' -to ' + str(end_sec) + ' ' +
# 				input_avi, shell=True)

#ffmpeg_to_avi = (f'ffmpeg -loglevel error -y -i {input_video} -crf 0 -pix_fmt yuv420p'
#                 f' -r {fps} -ss {start_sec} -to {end_sec} {input_avi}')
#subprocess.call(ffmpeg_to_avi, shell=True)

        # (ffmpeg.input(input_video)
        # .filter('loglevel', 'error')
        # .filter('y').filter('crf', 0)
        # .filter('pix_fmt', 'yub420p')
        # .filter('r', fps)
        # .filter('ss', start_sec)
        # .filter('to', end_sec)
        # .output(input_avi)
        # .run())


# FFMPEG CALL 2 -- AVI TO MP4

# replaced by use of formate string then ffmpeg module... idk why... and then back to format strings
# subprocess.call('ffmpeg -loglevel error -y -i ' + output_avi + ' ' +
# 				' -crf 18 -pix_fmt yuv420p -vcodec libx264 -acodec aac -r ' + str(fps) + ' ' +
# 				' -vf "scale=' + str(output_width) + ':-2:flags=lanczos" ' + ' ' +
# 				' -ss ' + str(start_sec) + ' -to ' + str(end_sec) + ' ' +
# 				output_video, shell=true)

# avi_to_mp4 = (f'ffmpeg -loglevel error -y -i {output_avi} -crf 18 -pix_fmt yuv420p -vcodec libx264 -acodec aac -r {fps}'
# 			  f' -vf "scale={output_width}:-2:flags=lanczos" -ss {start_sec} -to {end_sec} {output_video}')

# subprocess.call(avi_to_mp4, shell=True)
        # (ffmpeg.input(output_avi)
        # .filter('loglevel', 'error')
        # .filter('y').filter('crf', 18)
        # .filter('pix_fmt', 'yub420p')
        # .filter('vf', f"scale={output_width}:-2:flags=lanczos")
        # .filter('ss', start_sec)
        # .filter('to', end_sec)
        # .output(input_avi, vcodec='libx264', acodec='aac' r=fps)
        # .run())



    # Convert avi to mp4. If you want a different format try changing the output variable's file extension
    # and commenting out the rest of the line after -crf. If that doesn't work you'll be making friends with ffmpeg's options.
    # The -t option specifies the duration of the final video and usually helps avoid the malformed headers at the end.



