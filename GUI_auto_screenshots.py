from pyperclip import copy as copy_to_clipboard
from tkinter import filedialog
import pyautogui
import requests
import time
import csv


VERBOSE = True
WEBPAGE_LOADING_TIME = int()
MODIFIER_KEY = str()
LEADLIST = None
OUTPUT_DIR = str()

LEADS_FILEPATH = str()

guidelines = """Make sure your browser is already logged in to these platforms: Twitter/X, Facebook, LinkedIn.
Make sure you have your browser active with ONLY one tab being : the agency website."""

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
		# Return the key with the lowest number of characters, or None if no such key exists
		return min(filtered_keys, key=len) if filtered_keys else None

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
	import platform
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

def prompt_output_folder():
	global OUTPUT_DIR
	while not OUTPUT_DIR:
		OUTPUT_DIR = filedialog.askdirectory(title="Select where to save the screenshots...")

# Countdown timer to give the user time to select the browser
def countdown(seconds=5):
	for i in range(seconds, 0, -1):
		print(f"Switch to your browser. The script will run in {i} seconds...", end='\r')
		time.sleep(1)
	print()

def blank_tab():
	pyautogui.hotkey(MODIFIER_KEY, 't')

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
	try:
		response = requests.head(link, allow_redirects=True, timeout=5)  # Use HEAD to check the link
		# Check if the status code starts with 2
		if str(response.status_code).startswith('2'):
			return True
		else:
			return False
	except requests.RequestException as e:
		print(f"{link} Error : {e}")
		return None

def get_links(lead:dict):
	valid_links = [v for k, v in lead.items() if is_link(v) and k != LEADLIST.website_key]
	links = [link for link in valid_links if check_link(link)]
	website = lead[LEADLIST.website_key]
	if check_link(website) or len(links)==0:
		links.append(website)
	return links

screenshot_saving_name = lambda lead : OUTPUT_DIR + '/' + lead[LEADLIST.email_key].split('@')[-1] + ".png"

def screenshot_of_lead(lead:dict):
	links = get_links(lead)
	if VERBOSE: print(f"{len(links)} links for this lead ({lead[LEADLIST.website_key]})")
	for link in links:
		open_tab(link)
	time.sleep(WEBPAGE_LOADING_TIME)
	pyautogui.screenshot(screenshot_saving_name(lead))

def launch_loop():
	print("Loading lead list...")
	load_leadlist()
	print("Loading screenshots folder...")
	prompt_output_folder()
	#
	print("Detecting modifier key...")
	detect_modifier_key()
	#
	prompt_wait_time()
	countdown()
	# Assuming the browser is the active window.
	i = 0
	#try:
	if True:
		for lead in LEADLIST.csv_data:
			if VERBOSE: print(f"Processing lead n.{i+1} :\n{lead}\n")
			screenshot_of_lead(lead)
			i += 1
	#except Exception as e:
	else:
		#print(f"Error while looping leads : {e}")
		print(f"Last processed lead : {i}")
	print(f"Done with {i} leads.")

if __name__ == '__main__':
	launch_loop()