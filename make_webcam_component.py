from moviepy.editor import VideoFileClip
from moviepy.video.VideoClip import ColorClip
from moviepy.video.fx.all import crop
import numpy as np

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

def crop_and_save(height=300, src="sample_SD.mp4", dest="webcam_circle_SD.mov"):
    webcam = VideoFileClip(src).resize(height=height)
    min_dim = min(webcam.size)
    x_center = webcam.size[0] // 2
    y_center = webcam.size[1] // 2

    # Crop square center
    webcam = crop(webcam, width=min_dim, height=min_dim, x_center=x_center, y_center=y_center)
    webcam = make_circle_mask(webcam)

    # Export as .mov with transparency
    webcam.write_videofile(dest, codec="png", fps=24)

if __name__ == '__main__':
    crop_and_save()
