import GUI_auto_screenshots
import renderer
import drive

LOOM_LINK_KEY = "loom_link"

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

def make_shared_loom_name(lead:dict)->str:
	pass

def connect_loom_link(lead:dict, link:str):
	lead[LOOM_LINK_KEY] = link
	GUI_auto_screenshots.LEADLIST.update_csv()

def upload_and_link(shutdown):
	UPLOADED_LOOMS_COUNT = 0
	for lead in GUI_auto_screenshots.LEADLIST.csv_data:
		loom_filepath = lead[GUI_auto_screenshots.LOOM_FILEPATH_KEY]
		shared_loom_name = make_shared_loom_name(lead)
		link = drive.upload_public_video(drive.SERVICE, loom_filepath, drive.UPLOADING_FOLDER_ID, shared_loom_name)
		if link:
			connect_loom_link(lead, link)
			UPLOADED_LOOMS_COUNT += 1
		else:
			# upload failed
			connect_loom_link(lead, "")
	if shutdown:
		GUI_auto_screenshots.shutdown_computer()

def autopilot(testing=True):
	# screens
	GUI_auto_screenshots.launch_loop(shutdown=False)
	# rendering
	machine.launch()
	# uploading
	upload_and_link(not testing)

def main():
	preparation()
	autopilot()

if __name__ == '__main__':
	preparation()