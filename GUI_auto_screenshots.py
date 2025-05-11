from pyperclip import copy as copy_to_clipboard
from tkinter import filedialog
import urllib.parse
import subprocess
import pyautogui
import requests
import platform
import time
import csv

VERBOSE = True
WEBPAGE_LOADING_TIME = "10" # int
MODIFIER_KEY = str()
LEADLIST = None
SCREENSHOTS_DIR = str()
SCREEN_FILEPATH_KEY = "screen_filepath"
LEADS_FILEPATH = str()

guidelines = """Make sure your browser is already logged in to these platforms: Twitter/X, Facebook, LinkedIn.
Make sure you have your browser active with ONLY one tab being : the agency website.
Close any Facebook discussion bubble you have in your account.
"""

class Leadlist:
	def __init__(self, filepath:str):
		self.filepath = filepath
		with open(filepath, 'r', errors='ignore', encoding="utf-8-sig") as file:
			# Use the first line to detect the delimiter
			first_line = file.readline()
			delimiter_counts = {delimiter: first_line.count(delimiter) for delimiter in [',', ';', '\t', '|']}
			detected_delimiter = max(delimiter_counts, key=delimiter_counts.get)
			if VERBOSE: print(f"Detected delimiter for lead-list is **{detected_delimiter}**")
			file.seek(0)
			# Set up the CSV reader with the detected delimiter
			csvFile = csv.DictReader(file, delimiter=detected_delimiter)
			if VERBOSE: print("Created instance of csv.DictRead(file, delimiter)")
			# Read the CSV data into a list of dictionaries
			self.csv_data = [line for line in csvFile]

	def getShortestKey(self, keyword):
		filtered_keys = [key for key in self.csv_data[0].keys() if keyword in key.lower()]
		if filtered_keys:
			# Return the key with the lowest number of characters
			return min(filtered_keys, key=len)
		else:
			raise IndexError(f"Key {keyword} not found!")

	def verify(self)->list[dict]:
		REQUIRED_COLUMNS = ['WEBSITE', 'EMAIL']
		PROHIBITED_COLUMNS = []
		if len(self.csv_data)==0:
			raise ValueError(f"{self.filepath} is empty.")
		# checking columns
		self.columns_upper = [k.upper() for k in self.csv_data[0].keys()]
		# REQUIRED_COLUMNS
		if not all(any(column_name in column for column in self.columns_upper) for column_name in REQUIRED_COLUMNS):
			error_message = f"Error while verifying csv {self.filepath} IN First dict of loaded list : {self.csv_data[0]} does not contain at least one of the required columns {REQUIRED_COLUMNS}!"
			raise Exception(error_message)
		else:
			self.website_key = self.getShortestKey("website")
			self.email_key = self.getShortestKey("email")
			self.name_key = self.getShortestKey("company name")
		# PROHIBITED_COLUMNS
		if any(column_name in self.columns_upper for column_name in PROHIBITED_COLUMNS):
			print("Prohibited column detected. Aborting...")
			pyautogui.alert(
					title="Error",
					text=f"Prohibited column detected in {self.filepath}\nPlease remove it and try again!",
					button='OK')
			raise SyntaxError(f"Prohibited column detected in {self.filepath}")
		# EMPTY LINES
		empty_lines_count = 0
		while True:
			if not ''.join(self.csv_data[-1].values()):
				# empty
				empty_lines_count += 1
				self.csv_data.pop(-1)
			else:
				break
		if empty_lines_count:
			if VERBOSE: print(f"Detected & Cleaned {empty_lines_count} empty lines from csv file {self.filepath}")
			if not len(self.csv_data):
				message = f"Cleaned {empty_lines_count} empty lines leaving {self.filepath} empty!"
				raise ValueError(message)
		last_v = list(self.csv_data[-1].values())
		if last_v[0] and  ''.join(map(str, last_v[1:]))=='':
			self.csv_data.pop(-1)
			if VERBOSE: print("Found bad last line, removed it.")
		if VERBOSE: print(f"{self.filepath} verified successfully.")
		return self.csv_data

	def update_csv(self):
		if len(self.csv_data)==0:
			if VERBOSE: print(f"update_csv: Empty lead list. Clearing {self.filepath}")
			with open(self.filepath, 'w') as fd:
				fd.write("\n")
			return None
		with open(self.filepath, 'w', newline='') as csvfile:
			writer = csv.DictWriter(csvfile, fieldnames=self.csv_data[0].keys())
			writer.writeheader()
			writer.writerows(self.csv_data)


def load_leadlist()->list[dict]:
	global LEADS_FILEPATH # input
	global LEADLIST # Object
	while not bool(LEADS_FILEPATH):
		LEADS_FILEPATH = filedialog.askopenfilename(
			title="Select a lead list",
			filetypes=[('csv files', '*.csv')]
		)
	LEADLIST = Leadlist(LEADS_FILEPATH)
	LEADLIST.verify()

# Detect the operating system
def detect_modifier_key():
	global MODIFIER_KEY
	if platform.system() == "Darwin":  # macOS
		MODIFIER_KEY = 'command'
	else:  # Assume Windows or other OS
		MODIFIER_KEY = 'ctrl'

def prompt_wait_time():
	global WEBPAGE_LOADING_TIME
	user_input = "0"
	while user_input=="0" or not user_input.isdigit():
		user_input = input("Enter web page loading time (seconds)\n> ")
	WEBPAGE_LOADING_TIME = int(user_input)

def prompt_screenshots_folder():
	global SCREENSHOTS_DIR
	while not SCREENSHOTS_DIR:
		SCREENSHOTS_DIR = filedialog.askdirectory(title="Select where to save the screenshots...")

# Countdown timer to give the user time to select the browser
def countdown(seconds=5):
	for i in range(seconds, 0, -1):
		print(f"Switch to your browser. The script will run in {i} seconds...", end='\r')
		time.sleep(1)
	print()

def blank_tab():
	pyautogui.hotkey(MODIFIER_KEY, 't')

def close_tabs(number_of_tabs:int):
	if number_of_tabs<1:
		raise ValueError("Function parameter <number_of_tabs> must be greater than 0.")
	for i in range(number_of_tabs):
		pyautogui.hotkey(MODIFIER_KEY, 'w')
		time.sleep(0.1)

def select_URL_Bar():
	pyautogui.hotkey(MODIFIER_KEY, 'l')

def paste(text:str):
	copy_to_clipboard(text)
	pyautogui.hotkey(MODIFIER_KEY, 'v')

def press_enter():
	pyautogui.press('enter')

def open_tab(url:str):
	blank_tab()
	select_URL_Bar()
	paste(url)
	press_enter()

is_link = lambda string : string.startswith(('http://', 'https://', 'www.')) and '.' in string

def check_link(link:str)->bool:
	if not is_link(link):
		return False
	try:
		response = requests.head(link, allow_redirects=True, timeout=WEBPAGE_LOADING_TIME)  # Use HEAD to check the link
		# Check if the status code starts with 2
		if str(response.status_code).startswith('2'):
			return True
		else:
			return False
	except requests.RequestException as e:
		print(f"{link} Error : {e}")
		return None

def get_links(lead:dict):
	links = [v for k, v in lead.items() if k != LEADLIST.website_key and check_link(v)]
	popped_facebook = [links.pop(i) for i in range(len(links)) if "facebook.com/" in links[i]]
	website = lead[LEADLIST.website_key]
	if check_link(website):
		links.append(website) # add last to show
	elif len(links)==0:	# no links besides fb
		if popped_facebook:
			links.append(popped_facebook[0])
		else: # no website no fb no links
			# must have something to show. Company Name
			links.append(f"https://www.google.com/search?q={urllib.parse.quote(lead[LEADLIST.name_key])}")
	return links

def screenshot_saving_name(lead:dict)->str:
	return SCREENSHOTS_DIR + '/' + lead[LEADLIST.email_key] + ".png"
	# todo: avoid dupls.

def connect_local_screenshot(lead:dict, screenshot_filepath:str)->None:
	lead[SCREEN_FILEPATH_KEY] = screenshot_filepath
	LEADLIST.update_csv()

def no_local_screenshot(lead:dict):
	connect_local_screenshot(lead, "")

def screenshot_of_lead(lead:dict):
	SCREENSHOT_SUCCESS = None
	links = get_links(lead)
	if VERBOSE: print(f"{len(links)} links for this lead ({lead[LEADLIST.website_key]})")
	for link in links:
		open_tab(link)
	time.sleep(WEBPAGE_LOADING_TIME)
	screenshot_filepath = screenshot_saving_name(lead)
	try:
		pyautogui.screenshot(screenshot_filepath)
		SCREENSHOT_SUCCESS = True
	except Exception as e:
		logging.error(f"Error while taking a screenshot: {e}")
		print(f"Error while taking a screenshot: {e}")
	if SCREENSHOT_SUCCESS:
		connect_local_screenshot(lead, screenshot_filepath)
	else:
		no_local_screenshot(lead)
	close_tabs(len(links))

def shutdown_computer():
	os_type = platform.system()
	try:
		if os_type == "Windows":
			subprocess.run(["shutdown", "/s", "/t", "0"], check=True)
		elif os_type == "Darwin":  # macOS
			subprocess.run(["shutdown", "-h", "now"], check=True)
		elif os_type == "Linux":
			subprocess.run(["shutdown", "now"], check=True)
		else:
			print("Unsupported OS")
	except subprocess.CalledProcessError as e:
		print(f"Error occurred: {e}")

def init():
	print("Loading lead list...")
	load_leadlist()
	print("Loading screenshots folder...")
	prompt_screenshots_folder()
	#
	print("Detecting modifier key...")
	detect_modifier_key()
	#
	prompt_wait_time()

def launch_loop(shutdown:bool):
	countdown()
	# Assuming the browser is the active window.
	i = 0
	#try:
	if True:
		for lead in LEADLIST.csv_data:
			if VERBOSE: print(f"Processing lead n.{i+1} :\n{lead[LEADLIST.email_key]}\n")
			screenshot_of_lead(lead)
			i += 1
	#except Exception as e:
	else:
		#print(f"Error while looping leads : {e}")
		print(f"Last processed lead : {i}")
	print(f"Done with {i} leads.")
	if shutdown: shutdown_computer()

if __name__ == '__main__':
	launch_loop(shutdown=False)