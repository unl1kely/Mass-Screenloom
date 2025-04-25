from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip
from moviepy.video.VideoClip import ColorClip
from make_webcam_component import *
from moviepy.video.fx.all import crop
#from moviepy.video.fx import Crop as crop
import numpy as np
import sys
import os
import subprocess
import json

from mask_generator import mask_generate

# Settings
COMPOSE_WITH_MOVIPY = False
COMPOSE_WITH_FFMPEG = True

# Paths
if len(sys.argv)>1 and (sys.argv[1] in os.listdir()):
    video_path = sys.argv[1]
else:
    video_path = "sample.mp4"
print("Selected webcam video :", video_path)
cropped_SD = "webcam_circle_SD.mov"
screenshots_dir = "screenshots"
output_dir = "output"
os.makedirs(output_dir, exist_ok=True)

# Load webcam video (before)
#webcam_clip = VideoFileClip(video_path).resize(height=300)  # Resize to smaller thumbnail



#webcam_clip = crop_video(height=300, src="sample_SD.mp4")
webcam_clip = VideoFileClip("webcam_circle_SD.mov", has_mask=True)



class Machine:
    def __init__(self, screenshots_dir, webcam_filename, output_format):
        self.screenshots_dir = screenshots_dir
        self.webcam_filename = webcam_filename
        self.output_format = output_format
        self.duration = None

    def getDuration(self):
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries',
             'format=duration', '-of', 'json', self.webcam_filename],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        self.duration = float(json.loads(result.stdout)['format']['duration'])
        print(self.duration)
    @staticmethod    
    def cli_cmd(screen_bg, webcam_mp4, output_mp4, duration):
        return f'ffmpeg -loop 1 -t {duration} -i {screen_bg} -i {webcam_mp4} -filter_complex "[1:v]scale=-1:300[cam];[0:v][cam]overlay=10:H-h-10:shortest=1" -c:v libx264 -preset superfast -crf 26 -pix_fmt yuv420p {output_mp4}'
        #return f'ffmpeg -i {screen_bg} -stream_loop -1 -i {webcam_mp4} -filter_complex "[1:v]scale=-1:300[cam];[0:v][cam]overlay=10:H-h-10:shortest=1" -c:v libx264 -preset ultrafast -crf 23 -pix_fmt yuv420p {output_mp4}'
        #return f'ffmpeg -loop 1 -t 40 -i {screen_bg} -i {webcam_mp4} -filter_complex "[1:v]scale=-1:300[cam];[0:v][cam]overlay=10:H-h-10:shortest=1" -c:v libx264 -preset ultrafast -crf 23 -pix_fmt yuv420p {output_mp4}'

    def generate(self, screenshot_path, video_number:int):
        print(screenshot_path+"...")
        if COMPOSE_WITH_MOVIPY:
            screenshot_clip = ImageClip(screenshot_path).set_duration(webcam_clip.duration)
            # Overlay webcam video on bottom-left corner
            composite = CompositeVideoClip([
                screenshot_clip,
                webcam_clip.set_position(("left", "bottom"))
            ])
            print("composed.")
            output_path = os.path.join(output_dir, self.output_format(video_number))
            composite.write_videofile(output_path, codec="mpeg4", fps=24
                #, bitrate="8000k"
                )
        elif COMPOSE_WITH_FFMPEG:
            # Prepare mask
            print("cli_cmd\t"+cli_cmd(
                "screenshots/sample.png"
                , video_path
                , self.output_format(video_number))+"\n"
                , duration=self.duration
            )

    def launch(self):
        # Process each screenshot
        for i, screenshot_file in enumerate(sorted(os.listdir(self.screenshots_dir))):
            if not screenshot_file.lower().endswith(('.png', '.jpg', '.jpeg')):
                continue
            screenshot_path = os.path.join(self.screenshots_dir, screenshot_file)

            self.generate(
                screenshot_path=screenshot_path,
                video_number=i+1
            )

machine = Machine(screenshots_dir, video_path, lambda i : f"output/test_machine{i}.mp4")
machine.getDuration()
machine.launch()

 