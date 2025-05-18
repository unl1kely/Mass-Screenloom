from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip
from make_webcam_component import *
from tkinter import filedialog
from datetime import datetime
import subprocess
import logging
import json
import sys
import os

from mask_generator import mask_generate
from GUI_auto_screenshots import Leadlist, SCREEN_FILEPATH_KEY

# Settings
COMPOSE_WITH_MOVIPY = False
COMPOSE_WITH_FFMPEG = True
VERBOSE = True
TESTING = False

# VARS
MACHINE = None
WEBCAM_VIDEO_PATH = str()
OUTPUT_DIR = str()
SCREENSHOTS_DIR = str()
LOOM_FILEPATH_KEY = "loom_filepath"

now = datetime.now()
formatted_date = now.strftime("%y.%m.%d")
OUTPUT_FILENAME_FORMAT = formatted_date+"_loom_%.mp4"

if TESTING:
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

def prompt_screenshots_folder():
    global SCREENSHOTS_DIR
    while not SCREENSHOTS_DIR:
        SCREENSHOTS_DIR = filedialog.askdirectory(title="Select the screenshots folder...")

def extract_thumbnail(video_path:str, thumbnail_path:str, time:int=1)->str|None:
    """Extract a thumbnail from a video at a specified time (in seconds) using FFmpeg."""
    if not thumbnail_path.endswith(('.jpg', '.jpeg')):
        thumbnail_path = thumbnail_path + ".jpg"
    command = [
        'ffmpeg',
        '-ss', str(time),  # Seek to the specified time
        '-i', video_path,  # Input video file
        '-vframes', '1',   # Output one frame
        thumbnail_path # Output thumbnail file as JPEG
    ]
    process = subprocess.run(command, capture_output=True, text=True)
    # Check if the command was successful
    if process.returncode != 0:
        print("Error:", process.stderr)  # Print the error message
        return None
    else:
        if VERBOSE: print("Thumbnail extracted successfully.")
        return thumbnail_path



class Machine:
    def __init__(self, webcam_filename, output_dir, output_filename_format, leads_from_file=None, leads_from_object=None):
        if leads_from_file and not leads_from_object:
            self.leads_from_file(leads_from_file)
        elif leads_from_object and not leads_from_file:
            self.leads_from_object(leads_from_object)
        elif leads_from_object and leads_from_file:
            raise ValueError("Either pass 'leads_from_file' or 'leads_from_object' but not both.")
        self.webcam_filename = webcam_filename
        self.output_filename_format = output_filename_format
        self.output_dir = output_dir
        self.LEADLIST = None
        self.setDuration()

    def leads_from_file(self, filepath:str)->Leadlist:
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"The file '{filepath}' does not exist.")
        self.LEADLIST = Leadlist(filepath)
        self.LEADLIST.verify()
        return self.LEADLIST

    def leads_from_object(self, obj:Leadlist)->Leadlist:
        if not isinstance(obj, Leadlist):
            raise TypeError(f"Expected an instance of Leadlist, but got {type(obj).__name__}.")
        self.LEADLIST = obj
        return self.LEADLIST

    def output_filename_function(self, video_number:int|str)->str:
        # hour minute second for uniqueness. needs to change if rendering videos in parallel.
        time_now = datetime.now().strftime("h%H.%M.%S")
        return self.output_dir + '/' + self.output_filename_format.replace('%', time_now)
        #return self.output_dir + '/' + self.output_filename_format.replace('%', str(video_number))
    
    def setDuration(self):
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries',
             'format=duration', '-of', 'json', self.webcam_filename],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        self.duration = float(json.loads(result.stdout)['format']['duration'])
        if VERBOSE: print(f"Loaded Webcam Duration : {self.duration}")
    
    def generate_command(self, screenshot_filepath:str, output_filepath:str):
        return f'ffmpeg -loop 1 -t {self.duration} -i {screenshot_filepath} -i {self.webcam_filename} -filter_complex "[1:v]scale=-1:300[cam];[0:v][cam]overlay=W-w:H-h:shortest=1" -c:v libx264 -preset superfast -crf 26 -pix_fmt yuv420p {output_filepath}'
        # works bottom right (with gaps):
        #return f'ffmpeg -loop 1 -t {self.duration} -i {screenshot_filepath} -i {self.webcam_filename} -filter_complex "[1:v]scale=-1:300[cam];[0:v][cam]overlay=W-w-10:H-h-10:shortest=1" -c:v libx264 -preset superfast -crf 26 -pix_fmt yuv420p {output_filepath}'
        # works bottom left (with gaps):
        #return f'ffmpeg -loop 1 -t {self.duration} -i {screenshot_filepath} -i {self.webcam_filename} -filter_complex "[1:v]scale=-1:300[cam];[0:v][cam]overlay=10:H-h-10:shortest=1" -c:v libx264 -preset superfast -crf 26 -pix_fmt yuv420p {output_filepath}'
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

    def connect_local_loom(self, lead:dict, loom_filepath:str)->None:
        lead[LOOM_FILEPATH_KEY] = loom_filepath
        self.LEADLIST.update_csv()

    def no_local_loom(self, lead:dict):
        self.connect_local_loom(lead, "")

    def generate_loom(self, screenshot_filepath:str, video_number:int)->str|None:
        # return output_filepath if success
        output_filepath = self.output_filename_function(video_number)
        command = self.generate_command(screenshot_filepath, output_filepath)
        if VERBOSE:
            screenshot_basename = os.path.basename(screenshot_filepath)
            print(screenshot_basename+" ...")
            print(f"FFMPEG command running...")
        # Execute the command
        process = subprocess.run(command, shell=True, capture_output=True, text=True)
        # Check if the command was successful
        if process.returncode != 0:
            print(f'Error creating {output_filepath}: {process.stderr}')
            logging.error(f'Error creating {output_filepath}: {process.stderr}')
            return None
        # success
        if VERBOSE:
            output_basename = os.path.basename(output_filepath)
            print(f'Successfully created {output_basename}')
        return output_filepath

    def launch(self)->bool:
        if self.LEADLIST==None:
            raise ValueError("Machine.LEADLIST is required and must be loaded before Machine.launch()")
        errors_count = 0
        # Process each screenshot
        for i, lead in enumerate(self.LEADLIST.csv_data):
            screenshot_filepath = lead.get(SCREEN_FILEPATH_KEY)
            if screenshot_filepath==None or not (screenshot_filepath.lower().endswith(('.png', '.jpg', '.jpeg')) and os.path.isfile(screenshot_filepath)):
                continue
            output_filepath = self.generate_loom(
                screenshot_filepath=screenshot_filepath,
                video_number=i+1
            )
            if output_filepath: # SUCCESS
                self.connect_local_loom(lead, output_filepath)
                errors_count = 0
            else:
                self.no_local_loom(lead)
                errors_count += 1

            if errors_count >= 3:
                print("Reached 3 consecutive failed looms. Aborting...")
                logging.error("Reached 3 consecutive failed looms. Aborting...")
                return False
        return True

    def setDir(self, screenshots_dir):
        self.screenshots_dir = screenshots_dir

    def launch_from_dir(self)->bool:
        errors_count = 0
        # Process each screenshot
        for i, screenshot_file in enumerate(sorted(os.listdir(self.screenshots_dir))):
            if not screenshot_file.lower().endswith(('.png', '.jpg', '.jpeg')):
                continue
            screenshot_filepath = os.path.join(self.screenshots_dir, screenshot_file)

            output_filepath = self.generate_loom(
                screenshot_filepath=screenshot_filepath,
                video_number=i+1
            )
            # no connect
            errors_count = 0 if output_filepath != None else errors_count + 1

            if errors_count >= 3:
                print("Reached 3 consecutive failed looms. Aborting...")
                logging.error("Reached 3 consecutive failed looms. Aborting...")
                return False
        return True


def test():
    init()
    MACHINE.leads_from_file(filepath=input("Load from csv : "))

def init():
    global MACHINE
    prompt_webcam_file()
    prompt_output_folder()
    MACHINE = Machine(
        # nodir
        WEBCAM_VIDEO_PATH,
        OUTPUT_DIR,
        OUTPUT_FILENAME_FORMAT
    )

def launch_loop():
    MACHINE.launch()

if __name__ == '__main__':
    test()