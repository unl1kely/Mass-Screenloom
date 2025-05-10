import GUI_auto_screenshots
import renderer
import drive
import re

LOOM_LINK_KEY = "loom_link"
TESTING = True

def init():
	# screenshots init
	GUI_auto_screenshots.init()
	# render init
	renderer.init(screenshots_dir=GUI_auto_screenshots.SCREENSHOTS_DIR)
	# upload init
	drive.init()


def make_shared_loom_name(lead:dict)->str:
	email_domain = lambda email : email.split('@')[-1]
	clear_whitespaces = lambda string : re.sub(r'\s+', '', string)
	upload_name = str()
	# last piece missing.
	filename_pattern = "for %.mp4"
	variables = [
		lead[GUI_auto_screenshots.LEADLIST.name_key]
		, email_domain(lead[GUI_auto_screenshots.LEADLIST.email_key])
		, lead[GUI_auto_screenshots.LEADLIST.email_key]
	]
	for unique_idf in variables:
		if clear_whitespaces(unique_idf):
			upload_name = filename_pattern.replace('%', unique_idf)
			return upload_name
	if not upload_name:
		raise Exception(f"No valid video name from list : {variables}")

def loom_exists(lead:dict, link:str)->bool:
	# 1. same-website leads duplicate detection logic.
	# 2. loom link fusion in csv_data
	return False # to-do later

def connect_loom_link(lead:dict, link:str):
	if loom_exists(lead=lead, link=link):
		return None
	lead[LOOM_LINK_KEY] = link
	GUI_auto_screenshots.LEADLIST.update_csv()

def empty_loom_link(lead:dict):
	lead[LOOM_LINK_KEY] = ""
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
			# upload failed. VERBOSE in local func.
			empty_loom_link(lead)
	if shutdown:
		GUI_auto_screenshots.shutdown_computer()

def autopilot(testing:bool):
	# screens
	GUI_auto_screenshots.launch_loop(shutdown=False)
	# rendering
	renderer.launch_loop()
	# uploading
	upload_and_link(shutdown = not testing)

def main():
	init()
	autopilot(TESTING)

if __name__ == '__main__':
	main()