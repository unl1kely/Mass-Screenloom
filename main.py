from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip
#from moviepy.video.VideoClip import ColorClip
from make_webcam_component import *
#from moviepy.video.fx.all import crop
#from moviepy.video.fx import Crop as crop
#import numpy as np
from tkinter import filedialog
import subprocess
import logging
import json
import sys
import os

from mask_generator import mask_generate
import GUI_auto_screenshots

# Settings
COMPOSE_WITH_MOVIPY = False
COMPOSE_WITH_FFMPEG = True
VERBOSE = True

# VARS
cropped_SD = "webcam_circle_SD.mov"
WEBCAM_VIDEO_PATH = str()
OUTPUT_DIR = str()
SCREENSHOTS_DIR = "screenshots"

# Set up logging
logging.basicConfig(
    filename='Mass-Screenloom.log',  # Log file name
    level=logging.INFO,              # Log level
    format='%(asctime)s - %(levelname)s - %(message)s'  # Log message format
)



# Paths

def prompt_webcam_file():
    global WEBCAM_VIDEO_PATH
    while not bool(WEBCAM_VIDEO_PATH):
        WEBCAM_VIDEO_PATH = filedialog.askopenfilename(
            title="Select the webcam video file...",
            filetypes=[('mp4 files', '*.mp4')
                        ,('avi files', '*.avi')
                        ,('mov files', '*.mov')
                        ,('mkv files', '*.mkv')
                        ,('wmv files', '*.wmv')
                        ,('flv files', '*.flv')
                        ,('webm files', '*.webm')
                        ,('mpeg files', '*.mpeg')
                        ,('mpg files', '*.mpg')
                        ,('3pg files', '*.3pg')
                        ,('vob files', '*.vob')
                    ]
        )
    if VERBOSE: print("Selected webcam video :", WEBCAM_VIDEO_PATH)

def prompt_output_folder():
    global OUTPUT_DIR
    while not OUTPUT_DIR:
        OUTPUT_DIR = filedialog.askdirectory(title="Select where to save the looms...")
#os.makedirs(OUTPUT_DIR, exist_ok=True)

def prompt_screenshots_folder():
    global SCREENSHOTS_DIR
    while not SCREENSHOTS_DIR:
        SCREENSHOTS_DIR = filedialog.askdirectory(title="Select the screenshots folder...")

class Machine:
    def __init__(self, screenshots_dir, webcam_filename, output_dir, output_filename_format):
        self.screenshots_dir = screenshots_dir
        self.webcam_filename = webcam_filename
        self.output_filename_format = output_filename_format
        self.output_dir = output_dir
        self.duration = None

    def output_filename_function(self, video_number:int|str)->str:
        return self.output_dir + '/' + self.output_filename_format.replace('%', str(video_number))
    
    def getDuration(self):
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries',
             'format=duration', '-of', 'json', self.webcam_filename],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        self.duration = float(json.loads(result.stdout)['format']['duration'])
        if VERBOSE: print(f"Loaded Webcam Duration : {self.duration}")
    
    def generate_command(self, screenshot_filepath:str, output_mp4:str):
        # works bottom right (with gaps):
        return f'ffmpeg -loop 1 -t {self.duration} -i {screenshot_filepath} -i {self.webcam_filename} -filter_complex "[1:v]scale=-1:300[cam];[0:v][cam]overlay=W-w-10:H-h-10:shortest=1" -c:v libx264 -preset superfast -crf 26 -pix_fmt yuv420p {output_mp4}'
        # works bottom left (with gaps):
        #return f'ffmpeg -loop 1 -t {self.duration} -i {screenshot_filepath} -i {self.webcam_filename} -filter_complex "[1:v]scale=-1:300[cam];[0:v][cam]overlay=10:H-h-10:shortest=1" -c:v libx264 -preset superfast -crf 26 -pix_fmt yuv420p {output_mp4}'
        #return f'ffmpeg -i {screenshot_filepath} -stream_loop -1 -i {webcam_mp4} -filter_complex "[1:v]scale=-1:300[cam];[0:v][cam]overlay=10:H-h-10:shortest=1" -c:v libx264 -preset ultrafast -crf 23 -pix_fmt yuv420p {output_mp4}'
        #return f'ffmpeg -loop 1 -t 40 -i {screenshot_filepath} -i {webcam_mp4} -filter_complex "[1:v]scale=-1:300[cam];[0:v][cam]overlay=10:H-h-10:shortest=1" -c:v libx264 -preset ultrafast -crf 23 -pix_fmt yuv420p {output_mp4}'

    def generate_with_moviepy(self, screenshot_filepath, video_number:int):
        # Load webcam video (before)
        #webcam_clip = VideoFileClip(WEBCAM_VIDEO_PATH).resize(height=300)  # Resize to smaller thumbnail
        #
        #webcam_clip = crop_video(height=300, src="sample_SD.mp4")
        webcam_clip = VideoFileClip("webcam_circle_SD.mov", has_mask=True)
        if COMPOSE_WITH_MOVIPY:
            screenshot_clip = ImageClip(screenshot_filepath).set_duration(webcam_clip.duration)
            # Overlay webcam video on bottom-left corner
            composite = CompositeVideoClip([
                screenshot_clip,
                webcam_clip.set_position(("left", "bottom"))])
            if VERBOSE: print("composed.")
            output_path = os.path.join(OUTPUT_DIR, self.output_filename_function(video_number))
            composite.write_videofile(output_path, codec="mpeg4", fps=24
                #, bitrate="8000k"
            )

    def generate_loom(self, screenshot_filepath:str, video_number:int):
        output_mp4 = self.output_filename_function(video_number)
        command = self.generate_command(screenshot_filepath, output_mp4)
        if VERBOSE:
            print(screenshot_filepath+"...")
            print(f"Command:\t{command}")
        # Execute the command
        process = subprocess.run(command, shell=True, capture_output=True, text=True)
        # Check if the command was successful
        if process.returncode == 0:
            if VERBOSE: print(f'Successfully created {output_mp4}')
            return 0
        else:
            print(f'Error creating {output_mp4}: {process.stderr}')
            logging.error(f'Error creating {output_mp4}: {process.stderr}')
            return 1

    def launch(self):
        errors_count = 0
        # Process each screenshot
        for i, screenshot_file in enumerate(sorted(os.listdir(self.screenshots_dir))):
            if not screenshot_file.lower().endswith(('.png', '.jpg', '.jpeg')):
                continue
            screenshot_filepath = os.path.join(self.screenshots_dir, screenshot_file)

            OPERATION_STATUS = self.generate_loom(
                screenshot_filepath=screenshot_filepath,
                video_number=i+1
            )
            if OPERATION_STATUS==0:
                errors_count = 0
            else:
                errors_count += 1

            if errors_count >= 3:
                print("Reached 3 errors. Exiting...")
                logging.error("Reached 3 errors. Exiting...")
                return False
        return True


def test():
    prompt_webcam_file()
    prompt_output_folder()
    machine = Machine(SCREENSHOTS_DIR, WEBCAM_VIDEO_PATH, OUTPUT_DIR ,"test_machine_clean_%.mp4")
    machine.getDuration()
    test_bg = os.path.join(SCREENSHOTS_DIR, os.listdir(SCREENSHOTS_DIR)[0])
    machine.generate_loom(test_bg, 12)

def main():
    test()

if __name__ == '__main__':
    main()