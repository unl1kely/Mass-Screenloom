from moviepy.editor import VideoFileClip
from moviepy.video.VideoClip import ColorClip
from moviepy.video.fx.all import crop
import numpy as np

# Settings
SHOW_CLI_COMMAND = True

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

def crop_video(height=300, src="sample_SD.mp4"):
    webcam = VideoFileClip(src).resize(height=height)
    min_dim = min(webcam.size)
    x_center = webcam.size[0] // 2
    y_center = webcam.size[1] // 2

    # Crop square center
    webcam = crop(webcam, width=min_dim, height=min_dim, x_center=x_center, y_center=y_center)
    webcam = make_circle_mask(webcam)
    return webcam

def save_videoClip(object_, dest="webcam_circle.mov"):
    # Export as .mov with transparency
    object_.write_videofile(dest, codec="png", fps=24)

# for some reason, moviepy can't export transparent-background videos. the code above does not work.

def mask_cropper(webcam_mp4="sample.mp4", mask_filename="mask_300.png"):
    return f"""ffmpeg -i {webcam_mp4} -i {mask_filename} \
-filter_complex "[0:v]crop=300:300:(in_w-300)/2:(in_h-300)/2,format=rgba[vid]; \
[1:v]format=rgba[mask]; \
[vid][mask]alphamerge[out]" \
-map "[out]" -c:v libvpx -auto-alt-ref 0 -crf 30 -b:v 1M circular_webcam.webm
"""
    #return f"""ffmpeg -i sample_SD.mp4 -i {mask_filename} -filter_complex "[0:v]scale=300:300,format=rgba[vid];[1:v]format=rgba[mask];[vid][mask]alphamerge" -c:v libvpx -auto-alt-ref 0 -crf 30 -b:v 1M circular_webcam.webm"""
    #return """ffmpeg -i sample_SD.mp4 -i mask_300.png -filter_complex "[0:v]scale=300:300,format=rgba[vid];[1:v]format=rgba[mask];[vid][mask]alphamerge" -c:v libvpx -auto-alt-ref 0 -crf 30 -b:v 1M circular_webcam.webm"""

def pre_crop(webcam_mp4, precrop_result):
    return """ffmpeg -i sample_SD.mp4 -filter_complex "[0:v]scale=300:300,format=rgba,drawbox=x=0:y=0:w=300:h=300:color=black@0.0:t=fill,geq='r=if(lt((X-150)*(X-150)+(Y-150)*(Y-150),22500),255,0)':g=if(lt((X-150)*(X-150)+(Y-150)*(Y-150),22500),255,0):b=if(lt((X-150)*(X-150)+(Y-150)*(Y-150),22500),255,0),alphaextract[output]" -map "[output]" -c:v libvpx -pix_fmt yuva420p -b:v 1M circular_webcam.webm\n"""
    #return f"ffmpeg -i {webcam_mp4} -vf \"scale=300:300,drawbox=x=0:y=0:w=300:h=300:color=black@0.0:t=fill,geq=r='if((X-150)*(X-150)+(Y-150)*(Y-150)<22500,255,0)':g='if((X-150)*(X-150)+(Y-150)*(Y-150)<22500,255,0)':b='if((X-150)*(X-150)+(Y-150)*(Y-150)<22500,255,0)'\" -c:v libx264 -preset ultrafast -crf 28 {precrop_result}"

if SHOW_CLI_COMMAND:
    #print("mask_cropper\t"+mask_cropper("mask_300.png")+'\n')
    pass

