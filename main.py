import GUI_auto_screenshots
import renderer
import drive

def preparation():
	# screenshots prep
	GUI_auto_screenshots.load_leadlist()
	GUI_auto_screenshots.prompt_screenshots_folder()
	GUI_auto_screenshots.detect_modifier_key()
	GUI_auto_screenshots.prompt_wait_time()
	# render prep
	# SCREENSHOTS_DIR, WEBCAM_VIDEO_PATH, OUTPUT_DIR, OUTPUT_FILENAME_FORMAT
	renderer.SCREENSHOTS_DIR = GUI_auto_screenshots.prompt_screenshots_folder()
	renderer.prompt_webcam_file() # WEBCAM_VIDEO_PATH
	renderer.prompt_output_folder() # renderer.OUTPUT_DIR
	# OUTPUT_FILENAME_FORMAT (already setup in renderer)
	machine = renderer.Machine(
		renderer.SCREENSHOTS_DIR,
		renderer.WEBCAM_VIDEO_PATH,
		renderer.OUTPUT_DIR,
		renderer.OUTPUT_FILENAME_FORMAT
	)
	machine.getDuration()
	# upload prep
	drive.authenticate_oauth() # SERVICE auth google account & Mass Screenloom app
	drive.prompt_uploading_folder_link() # UPLOADING_FOLDER_ID

def upload_and_link():
	pass

def autopilot():
	# screens
	GUI_auto_screenshots.launch_loop(shutdown=False)
	# rendering
	machine.launch()
	# uploading

def main():
	preparation()
	autopilot()

if __name__ == '__main__':
	preparation()