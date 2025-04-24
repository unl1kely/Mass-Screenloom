from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip
from moviepy.video.VideoClip import ColorClip
from moviepy.video.fx.all import crop
#from moviepy.video.fx import Crop as crop
import numpy as np
import sys
import os


# Paths
if len(sys.argv)>1 and (sys.argv[1] in os.listdir()):
    video_path = sys.argv[1]
else:
    video_path = "sample_SD.mp4"
print("Selected webcam video :", video_path)
screenshots_dir = "screenshots"
output_dir = "output"
os.makedirs(output_dir, exist_ok=True)

# Load webcam video (before)
#webcam_clip = VideoFileClip(video_path).resize(height=300)  # Resize to smaller thumbnail

#   CIRCULAR_START
def make_circle_mask(clip):
    size = clip.size
    mask = ColorClip(size, color=(0, 0, 0)).to_mask()
    w, h = size

    def make_frame(t):
        y, x = np.ogrid[:h, :w]
        center = (h / 2, w / 2)
        radius = min(h, w) / 2
        mask_array = ((x - center[1]) ** 2 + (y - center[0]) ** 2) <= radius ** 2
        return mask_array.astype(float)

    mask.get_frame = make_frame
    return clip.set_mask(mask)

# Load webcam video and resize
webcam_clip = VideoFileClip(video_path).resize(height=300)

# Crop to square first before making circle
min_dim = min(webcam_clip.size)
w, h = webcam_clip.size
webcam_clip = crop(webcam_clip, width=min_dim, height=min_dim, x_center=w//2, y_center=h//2)

# Apply circular mask
webcam_clip = make_circle_mask(webcam_clip)

print("Circular end")
#      CIRCULAR_END

# Process each screenshot
for i, screenshot_file in enumerate(sorted(os.listdir(screenshots_dir))):
    if not screenshot_file.lower().endswith(('.png', '.jpg', '.jpeg')):
        continue
    print(screenshot_file+"...")
    screenshot_path = os.path.join(screenshots_dir, screenshot_file)
    screenshot_clip = ImageClip(screenshot_path).set_duration(webcam_clip.duration)

    # Overlay webcam video on bottom-left corner
    composite = CompositeVideoClip([
        screenshot_clip,
        webcam_clip.set_position(("left", "bottom"))
    ])

    output_path = os.path.join(output_dir, f"screenloom_{i+1}.mp4")
    composite.write_videofile(output_path, codec="libx264", fps=24)
