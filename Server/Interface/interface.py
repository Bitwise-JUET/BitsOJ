import time 
import sys
import json
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon, QPalette, QColor, QPixmap
from PyQt5.QtSql import QSqlTableModel, QSqlDatabase, QSqlQueryModel
from PyQt5.QtCore import pyqtSlot, pyqtSignal, QObject, QTimer, Qt, QModelIndex, qInstallMessageHandler
from Interface.ui_classes import *
from Interface.problem_ui import *
from Interface.submission_ui import *
from Interface.accounts_edit_ui import *
from Interface.password_change_ui import *
from Interface.query_reply_ui import *
from Interface.new_accounts_ui import *
from Interface.ie_accounts_ui import *
from Interface.rejudge_problem_ui import *
from init_server import initialize_server, save_status
from database_management import user_management, submissions_management, query_management, scoreboard_management, client_authentication

# This is to ignore some warnings which were thrown when gui exited and 
# python deleted some assests in wrong order
# Nothing critical :)
def handler(msg_type, msg_log_context, msg_string):
	pass
qInstallMessageHandler(handler)

# This class handles the main window of server
class server_window(QMainWindow):
	def __init__(self, data_changed_flags2, task_queue, log_queue):
		super().__init__()
		# Set app icon
		self.setWindowIcon(QIcon('Elements/logo.png'))
		# Set window title
		self.setWindowTitle('BitsOJ v1.0.1 [ SERVER ]')

		# Make  the app run full-screen
		# Initialize status bar (Bottom Bar)
		self.status = self.statusBar()
		self.resize(1024, 768)

		# Timer to update GUI and broadcast scoreboard
		self.timer = QTimer()
		self.timer.timeout.connect(self.update_data)
		self.timer.start(1000)
		
		self.scoreboard_timer = QTimer()
		self.scoreboard_timer.timeout.connect(self.broadcast_scoreboard)
		self.scoreboard_timer.start(300000)

		# make data_changed_flag accessible from the class methods
		self.data_changed_flags = data_changed_flags2
		self.task_queue = task_queue
		self.log_queue = log_queue
		self.log('  [ START ] Interface subprocess started.')
		
		###########################################################
		self.db = self.init_qt_database()
		self.submissions_query = "SELECT run_id, client_id, problem_code, language, timestamp, verdict, sent_status, judge FROM submissions ORDER BY run_id DESC"
			# Default leaderboard query
		self.leaderboard_query = "SELECT * FROM scoreboard ORDER BY score DESC, total_time ASC"

		###########################################################
		self.config = initialize_server.read_config()
		self.contest_set_time = self.config['Contest Set Time']
		self.duration = self.config['Contest Duration']
		self.contest_start_time = ''
		###########################################################
		self.admin_password = self.read_password()
		###########################################################
		# Define Sidebar Buttons and their actions
		button_width = 200
		button_height = 50

		self.button_0 = QPushButton('Accounts', self)
		self.button_0.setFixedSize(button_width, button_height)
		self.button_0.clicked.connect(self.manage_accounts)
		self.button_0.setObjectName("sidebar_button")

		self.button_1 = QPushButton('Submissions', self)
		self.button_1.setFixedSize(button_width, button_height)
		self.button_1.clicked.connect(self.view_submissions)
		self.button_1.setObjectName("sidebar_button")

		self.button_2 = QPushButton('Judges', self)
		self.button_2.setFixedSize(button_width, button_height)
		self.button_2.clicked.connect(self.manage_judges)
		self.button_2.setObjectName("sidebar_button")

		self.button_3 = QPushButton('Clients', self)
		self.button_3.setFixedSize(button_width, button_height)
		self.button_3.clicked.connect(self.manage_clients)
		self.button_3.setObjectName("sidebar_button")

		self.button_4 = QPushButton('Queries', self)
		self.button_4.setFixedSize(button_width, button_height)
		self.button_4.clicked.connect(self.manage_queries)
		self.button_4.setObjectName("sidebar_button")

		self.button_5 = QPushButton('Leaderboard', self)
		self.button_5.setFixedSize(button_width, button_height)
		self.button_5.clicked.connect(self.manage_leaderboard)
		self.button_5.setObjectName("sidebar_button")

		self.button_6 = QPushButton('Problems', self)
		self.button_6.setFixedSize(button_width, button_height)
		self.button_6.clicked.connect(self.manage_problems)
		self.button_6.setObjectName("sidebar_button")

		self.button_7 = QPushButton('Statistics', self)
		self.button_7.setFixedSize(button_width, button_height)
		self.button_7.clicked.connect(self.show_stats)
		self.button_7.setObjectName("sidebar_button")

		self.button_8 = QPushButton('Settings', self)
		self.button_8.setFixedSize(button_width, button_height)
		self.button_8.clicked.connect(self.contest_settings)
		self.button_8.setObjectName("sidebar_button")

		self.button_9 = QPushButton('About', self)
		self.button_9.setFixedSize(button_width, button_height)
		self.button_9.clicked.connect(self.show_about)
		self.button_9.setObjectName("sidebar_button")

		self.button_10 = QPushButton('Lock', self)
		self.button_10.setFixedSize(button_width, button_height)
		self.button_10.clicked.connect(self.set_lock)
		self.button_10.setObjectName("sidebar_button")

		###########################################################

		###########################################################
		# Manage tabs on the right window
		# Each tab is an object returned by the respective function associated with its UI
		# Tab UI are managed by interface_packages/ui_classes.py file 
		self.tab0, self.account_model, self.delete_account_button = ui_widgets.accounts_ui(self)
		self.tab1, self.sub_model, self.allow_sub_button = ui_widgets.submissions_ui(self)
		self.tab2, self.judge_model = ui_widgets.judge_ui(self)
		self.tab3, self.client_model, self.allow_login_button = ui_widgets.client_ui(self)
		self.tab4, self.query_model = ui_widgets.query_ui(self)
		self.tab5, self.score_model, self.scoring_type_label = ui_widgets.leaderboard_ui(self)
		self.tab6, self.problem_model = ui_widgets.problem_ui(self)
		
		self.tab7 = ui_widgets.stats_ui(self)

		(
			self.tab8, self.contest_time_entry, self.change_time_entry, self.set_button, 
			self.start_button, self.update_button, self.stop_button, self.account_reset_button, 
			self.submission_reset_button, self.query_reset_button, self.client_reset_button, 
			self.server_reset_button, self.timer_reset_button
		) = ui_widgets.settings_ui(self)

		self.tab9 = ui_widgets.about_us_ui(self)
		self.tab10 = ui_widgets.lock_ui(self)
		
		###########################################################
		# Initialize GUI elements
		server_window.init_UI(self)
		# Load previous state in case of server restart
		server_window.load_previous_state(self)
		return

	def log(self, message):
		self.log_queue.put(message)

	def init_UI(self):
		self.set_status('SETUP')
		# Define Layout for sidebar
		side_bar_layout = QVBoxLayout()

		# Add buttons to our layout
		side_bar_layout.addWidget(self.button_0)
		side_bar_layout.addWidget(self.button_1)
		side_bar_layout.addWidget(self.button_2)
		side_bar_layout.addWidget(self.button_3)
		side_bar_layout.addWidget(self.button_4)
		side_bar_layout.addWidget(self.button_5)
		side_bar_layout.addWidget(self.button_6)
		side_bar_layout.addWidget(self.button_7)
		side_bar_layout.addWidget(self.button_8)
		side_bar_layout.addWidget(self.button_9)
		# Add some spacing for lock button
		side_bar_layout.addStretch(33)
		side_bar_layout.addWidget(self.button_10)


		# Set stretch and spacing
		side_bar_layout.addStretch(1)
		side_bar_layout.setSpacing(0)

		# Define our sidebar widget and set side_bar_layout to it.
		side_bar_widget = QWidget()
		side_bar_widget.setLayout(side_bar_layout)
		side_bar_widget.setFixedWidth(215)
		side_bar_widget.setObjectName("sidebar")

		#Define our top bar
		logo = QLabel(self)
		logo_image = QPixmap('Elements/bitwise_header.png')
		logo_image2 = logo_image.scaledToWidth(104)
		logo.setPixmap(logo_image2)

		self.timer_widget = QLCDNumber()
		self.timer_widget.setSegmentStyle(QLCDNumber.Flat)
		self.timer_widget.setDigitCount(8)
		self.timer_widget.display('00:00:00')
		self.timer_widget.setFixedSize(150,40)
		

		top_bar_layout = QHBoxLayout()
		top_bar_layout.setContentsMargins(15, 5, 20, 0);
		top_bar_layout.addWidget(logo)
		top_bar_layout.addWidget(self.timer_widget)
		top_bar_layout.setStretch(0, 70)
		

		top_bar_widget = QWidget()
		top_bar_widget.setLayout(top_bar_layout)
		top_bar_widget.setObjectName('top_bar')

		# Define our right side screens corresponding to buttons on the sidebar
		# Basically right screens are tab widgets whose tabs are hidden, 
		# and we map sidebar buttons to each tab switch :)
		# Since sidebars are not natively supported by pyqt5
		self.right_widget = QTabWidget()
		self.right_widget.addTab(self.tab0, '')
		self.right_widget.addTab(self.tab1, '')    # tab names are '' because we don't want them to show up in our screen
		self.right_widget.addTab(self.tab2, '')
		self.right_widget.addTab(self.tab3, '')
		self.right_widget.addTab(self.tab4, '')
		self.right_widget.addTab(self.tab5, '')
		self.right_widget.addTab(self.tab6, '')
		self.right_widget.addTab(self.tab7, '')
		self.right_widget.addTab(self.tab8, '')
		self.right_widget.addTab(self.tab9, '')
		self.right_widget.addTab(self.tab10, '')
		self.right_widget.setObjectName("main_tabs")
	
		# Screen 1 will be our initial screen 
		self.right_widget.setCurrentIndex(0)

		# Define the combined layout for sidebar + right side screens
		main_layout = QHBoxLayout()
		main_layout.addWidget(side_bar_widget)
		main_layout.addWidget(self.right_widget)

		# setstretch( index, stretch_value )
		main_layout.setStretch(0, 0)
		main_layout.setStretch(1, 90)
		# Define our main wideget = sidebar + windows
		main_widget = QWidget()
		main_widget.setObjectName("screen_widget")
		main_widget.setLayout(main_layout)


		#Define top_layout = logo_bar + main_layout
		top_layout = QVBoxLayout()
		top_layout.addWidget(top_bar_widget)
		top_layout.addWidget(main_widget)
		top_layout.setContentsMargins(1, 0, 1, 1)
		top_layout.setStretch(0, 8)
		top_layout.setStretch(1, 100)

		top_widget = QWidget()
		top_widget.setLayout(top_layout)
		top_widget.setObjectName("main_widget")

		# Set top_widget as our central widget
		self.setCentralWidget(top_widget)
		return

	def read_password(self):
		return self.config['Admin Password']

	@pyqtSlot()
	def manage_accounts(self):
		if self.data_changed_flags[24] != 1:
			self.right_widget.setCurrentIndex(0)

	@pyqtSlot()
	def view_submissions(self):
		if self.data_changed_flags[24] != 1:
			self.right_widget.setCurrentIndex(1)

	@pyqtSlot()
	def manage_judges(self):
		if self.data_changed_flags[24] != 1:
			self.right_widget.setCurrentIndex(2)

	@pyqtSlot()
	def manage_clients(self):
		if self.data_changed_flags[24] != 1:
			self.right_widget.setCurrentIndex(3)

	@pyqtSlot()
	def manage_queries(self):
		if self.data_changed_flags[24] != 1:
			self.right_widget.setCurrentIndex(4)

	@pyqtSlot()
	def manage_leaderboard(self):
		if self.data_changed_flags[24] != 1:
			self.right_widget.setCurrentIndex(5)

	@pyqtSlot()
	def manage_problems(self):
		if self.data_changed_flags[24] != 1:
			self.right_widget.setCurrentIndex(6)

	@pyqtSlot()
	def show_stats(self):
		if self.data_changed_flags[24] != 1:
			self.right_widget.setCurrentIndex(7)

	@pyqtSlot()
	def contest_settings(self):
		if self.data_changed_flags[24] != 1:
			self.right_widget.setCurrentIndex(8)

	@pyqtSlot()
	def show_about(self):
		if self.data_changed_flags[24] != 1:
			self.right_widget.setCurrentIndex(9)

	@pyqtSlot()
	def set_lock(self):
		print('[ GUI ][ LOCK ] Server GUI has been locked.')
		self.log('[ GUI ][ LOCK ] Server GUI has been locked.')
		self.data_changed_flags[24] = 1
		self.right_widget.setCurrentIndex(10)

	####################################################
	# Functions related to GUI updates
	def load_previous_state(self):
		server_window.set_leaderboard_behavior(self)
		if self.config["Contest Status"] == "RUNNING":
			server_window.set_button_behavior(self, 'RUNNING')
		elif self.config["Contest Status"] == "STOPPED":
			server_window.set_button_behavior(self, 'STOPPED')
		elif self.config["Contest Status"] == "SETUP":
			server_window.set_button_behavior(self, 'SETUP')

		# TODO: When server restarts, pop up a new notification about contest status
		return

	def broadcast_scoreboard(self):
		# If scoreboard broadcast is allowed
		if self.data_changed_flags[15] == 1:
			# Just set this flag, update data will take care of it
			self.data_changed_flags[18] = 1
			print('[ EVENT ] Scoreboard broadcast to clients ( Time Out )')
			self.log('[ EVENT ] Scoreboard broadcast to clients ( Time Out )')
			
	def update_data(self):
		try:
			# If data has changed in submission table
			# Update submission table
			if self.data_changed_flags[0] == 1:
				self.sub_model.setQuery(self.submissions_query)
				# self.sub_model.select()
				self.data_changed_flags[0] = 0
			# Update connected clients table
			if self.data_changed_flags[1] == 1:
				self.client_model.select()
				self.data_changed_flags[1] = 0
			# Update problems table
			if self.data_changed_flags[22] == 1:
				self.problem_model.select()
				self.data_changed_flags[22] = 0
			# Update accounts table
			if self.data_changed_flags[5] == 1:
				self.account_model.select()
				self.data_changed_flags[5] = 0
			# Update Query table
			if self.data_changed_flags[9] == 1:
				self.query_model.select()
				self.data_changed_flags[9] = 0
			# Update judge view
			if self.data_changed_flags[13] == 1:
				self.judge_model.select()
				self.data_changed_flags[13] = 0
			# Update scoreboard view
			if self.data_changed_flags[16] == 1:
				self.score_model.setQuery(self.leaderboard_query)
				self.data_changed_flags[16] = 0
			# System EXIT
			if self.data_changed_flags[7] == 1:
				sys.exit()

			if self.data_changed_flags[19] == 1:
				self.data_changed_flags[19] = 0
				# Broadcast UPDATE signal
				total_time = self.contest_set_time
				current_time = time.time()
				remaining_time = time.strftime('%H:%M:%S', time.gmtime(total_time - current_time ))

				message = {
				'Code' : 'UPDATE',
				'Time' : remaining_time
				}
				message = json.dumps(message)
				self.task_queue.put(message)

			if self.data_changed_flags[18] == 1:
				print('[ SCOREBOARD ][ BROADCAST ]')
				self.data_changed_flags[18] = 0
				# Broadcast scoreboard
				scoreboard = scoreboard_management.get_scoreboard()
				data = str(scoreboard)
				message = {
					'Code':'SCRBD',
					'Data' : data
				}
				message = json.dumps(message)
				self.task_queue.put(message)

			# While contest is RUNNING
			# This block is last as it may cause a return call and not allow further function block executions
			if self.data_changed_flags[10] == 1:
				# Find time elapsed since contest start
				total_time = self.contest_set_time
				current_time = time.time()
				time_difference = total_time - current_time
				remaining_time = time.strftime('%H:%M:%S', time.gmtime(time_difference))

				# When remaining time is less than 0, contest has ended
				if time_difference < 0:
					# Contest time ended
					self.timer_widget.display('00:00:00')
					self.process_event('STOP', 'None')
					return
				
				# Update timer
				self.timer_widget.display(remaining_time)

		except Exception as error:
			print('[ ERROR ] Interface updation error: ' + str(error))
			self.log('[ ERROR ] Interface updation error: ' + str(error))
			
		return

	def convert_to_seconds(time_str):
		h, m, s = time_str.split(':')
		return int(h) * 3600 + int(m) * 60 + int(s)

	def set_leaderboard_behavior(self):
		if self.data_changed_flags[17] == 1:
			# ACM style leaderboard
			pass
		elif self.data_changed_flags[17] == 3:
			# Long style ranklist
			self.leaderboard_query = (
				"SELECT user_name, problems_solved, score FROM scoreboard ORDER BY score DESC, total_time ASC"
			)
			self.score_model.setQuery(self.leaderboard_query)
			self.score_model.setHeaderData(0, Qt.Horizontal, 'Team Name')
			self.score_model.setHeaderData(1, Qt.Horizontal, 'Problems Solved')
			self.score_model.setHeaderData(2, Qt.Horizontal, 'Score')
		else:
			# IOI style ranklist DEFAULT
			self.leaderboard_query = (
				"SELECT user_name, problems_solved, score, total_time  FROM scoreboard ORDER BY score DESC, total_time ASC"
			)
			self.score_model.setQuery(self.leaderboard_query)
			self.score_model.setHeaderData(0, Qt.Horizontal, 'Team Name')
			self.score_model.setHeaderData(1, Qt.Horizontal, 'Problems Solved')
			self.score_model.setHeaderData(2, Qt.Horizontal, 'Score')
			self.score_model.setHeaderData(3, Qt.Horizontal, 'Total Time')


		# Refresh leaderboard
		self.data_changed_flags[16] == 1


	def set_button_behavior(self, status):
		if status == "SETUP":
			self.set_status('SETUP')
			self.setWindowTitle('BitsOJ v1.0.1 [ SERVER ][ SETUP ]')
			self.data_changed_flags[10] = 0
			contest_duration = '00:00:00'
			self.timer_widget.display(contest_duration)
			self.contest_time_entry.setReadOnly(0)
			self.contest_time_entry.setToolTip('You will not be able to edit this when contest starts.')
			self.change_time_entry.setReadOnly(False)
			self.change_time_entry.setToolTip('You will be able to use it when contest is STARTED')
			self.set_button.setEnabled(True)
			self.set_button.setToolTip('Set contest time.\nThis does NOT broadcast to clients.')
			self.start_button.setEnabled(True)
			self.start_button.setToolTip('START the contest and broadcast to all clients.')
			self.stop_button.setEnabled(False)
			self.stop_button.setToolTip('STOP the contest and broadcast to all clients.\nDisabled until contest Starts')
			self.update_button.setEnabled(False)
			self.update_button.setToolTip('UPDATE contest time and broadcast to all clients.\nDisabled until contest Starts')
			self.server_reset_button.setEnabled(True)
			self.server_reset_button.setToolTip('RESET the server.')
			self.account_reset_button.setEnabled(True)
			self.submission_reset_button.setEnabled(True)
			self.query_reset_button.setEnabled(True)
			self.client_reset_button.setEnabled(True)
			self.delete_account_button.setEnabled(True)
			self.timer_reset_button.setEnabled(False)
			self.timer_reset_button.setToolTip('You can reset timer when contest is STOPPED.')

		if status == "RUNNING":
			self.set_status('RUNNING')
			self.setWindowTitle('BitsOJ v1.0.1 [ SERVER ][ RUNNING ]')
			self.data_changed_flags[10] = 1
			self.contest_time_entry.setReadOnly(1)
			self.contest_time_entry.setToolTip('Contest has STARTED.\nYou can\'t edit this value now.')
			self.change_time_entry.setReadOnly(False)
			self.change_time_entry.setToolTip('Extend/Shorten contest (in minutes).\nPress UPDATE to confirm.')
			self.set_button.setEnabled(False)
			self.set_button.setToolTip('Contest has STARTED.\nYou can not set time now!')
			self.start_button.setEnabled(False)
			self.start_button.setToolTip('Contest is already running!')
			self.stop_button.setEnabled(True)
			self.stop_button.setToolTip('STOP the contest.')
			self.update_button.setEnabled(True)
			self.update_button.setToolTip('Update the contest.')
			self.server_reset_button.setEnabled(False)
			self.server_reset_button.setToolTip('RESET the server.\nCan only be used when contest\nis not RUNNING.')
			self.account_reset_button.setEnabled(False)
			self.submission_reset_button.setEnabled(False)
			self.query_reset_button.setEnabled(False)
			self.client_reset_button.setEnabled(True)
			self.delete_account_button.setEnabled(False)
			self.timer_reset_button.setEnabled(False)
			# Allow submissions now
			self.allow_sub_button.setChecked(True)
			self.data_changed_flags[3] = 1
			# Allow logins now
			self.allow_login_button.setChecked(True)
			self.data_changed_flags[2] = 1

		elif status == "STOPPED":
			self.set_status('STOPPED')
			self.setWindowTitle('BitsOJ v1.0.1 [ SERVER ][ STOPPED ]')
			self.data_changed_flags[10] = 2
			self.contest_time_entry.setReadOnly(1)
			self.contest_time_entry.setToolTip('Contest has STOPPED.\nYou can\'t edit this value now.')
			self.update_button.setEnabled(False)
			self.update_button.setToolTip('Contest has STOPPED.\nYou can not extend it now.')
			self.stop_button.setEnabled(False)
			self.stop_button.setToolTip('Contest has already STOPPED!')
			self.start_button.setEnabled(False)
			self.start_button.setToolTip('Contest has STOPPED!')
			self.set_button.setEnabled(False)
			self.set_button.setToolTip('Contest has STOPPED!')
			self.change_time_entry.setReadOnly(True)
			self.change_time_entry.setToolTip('Contest has STOPPED.\nYou can not change time now!')
			self.server_reset_button.setEnabled(True)
			self.server_reset_button.setToolTip('RESET the server.')
			self.account_reset_button.setEnabled(True)
			self.submission_reset_button.setEnabled(True)
			self.query_reset_button.setEnabled(True)
			self.client_reset_button.setEnabled(True)
			self.delete_account_button.setEnabled(True)
			self.timer_reset_button.setEnabled(True)
			self.timer_reset_button.setToolTip('Reset Contest timer')
			# Don't allow submissions now
			self.allow_sub_button.setChecked(False)
			self.data_changed_flags[3] = 0
			# Don't allow logins now
			self.allow_login_button.setChecked(False)
			self.data_changed_flags[2] = 0
		return

	def process_event(self, data, extra_data):
		if data == 'SET':
			print('[ SET ] Contest Duration : ' + str(extra_data))
			self.log('[ SET ] Contest Duration : ' + str(extra_data))
			save_status.update_entry('Contest Duration', str(extra_data))
			self.timer_widget.display(extra_data)
			self.duration = str(extra_data)

		elif data == 'START':
			current_time = time.localtime()
			self.contest_start_time = time.time()
			self.contest_duration_seconds = server_window.convert_to_seconds(self.duration)
			self.contest_set_time = self.contest_duration_seconds + self.contest_start_time
			contest_end_time = time.strftime("%H:%M:%S", time.localtime(self.contest_set_time))
			contest_start_time = time.strftime("%H:%M:%S", time.localtime(self.contest_start_time))
			message = {
			'Code' : 'START',
			'Duration' : extra_data,
			'Start Time' : contest_start_time,
			'End Time' : contest_end_time
			}
			message = json.dumps(message)
			# Put START message in task_queue so that it is broadcasted to all the clients.
			self.task_queue.put(message)

			# Update GUI
			server_window.set_button_behavior(self, 'RUNNING')

			# Update config file
			current_time = str(time.strftime("%H:%M:%S", current_time))
			save_status.update_entry('Contest Start Time', current_time)
			save_status.update_entry('Contest Status', 'RUNNING')
			save_status.update_entry('Contest Duration', extra_data)
			save_status.update_entry('Contest Set Time', self.contest_set_time)
			save_status.update_entry('Contest End Time', contest_end_time)

			# Broadcast Scoreboard
			self.data_changed_flags[18] = 1

		elif data == 'STOP':
			current_time = time.localtime()
			message = {
				'Code' : 'STOP'
			}

			message = json.dumps(message)
			self.task_queue.put(message)

			# Update GUI
			self.set_button_behavior('STOPPED')
			# Update config file
			current_time = str(time.strftime("%H:%M:%S", current_time))
			save_status.update_entry('Contest End Time', current_time)
			save_status.update_entry('Contest Status', 'STOPPED')

		elif data == 'UPDATE':
			# Send UPDATE signal
			print('[ UPDATE ] Contest time ' + str(extra_data))
			self.log('[ UPDATE ] Contest time ' + str(extra_data))
			self.contest_set_time = self.contest_set_time + int(extra_data) * 60
			# self.data_changed_flags[19] = 1
			message = {
			'Code' : 'EXTND',
			'Time' : extra_data
			}
			message = json.dumps(message)
			self.task_queue.put(message)

			prev_duration = self.duration
			new_duration = server_window.convert_to_seconds(prev_duration) + (int(extra_data) * 60)
			new_duration = server_window.convert_to_hhmmss(new_duration)

			new_end_time = time.strftime("%H:%M:%S", time.localtime(self.contest_set_time))
			save_status.update_entry('Contest Set Time', self.contest_set_time)
			save_status.update_entry('Contest End Time', new_end_time)
			save_status.update_entry('Contest Duration', new_duration)
		return

	def convert_to_hhmmss(seconds):
		seconds = int(seconds)
		h = int(seconds / 3600)
		m = int((seconds % 3600) / 60)
		s = int(((seconds % 3600) % 60))
		if h <= 9:
			h = '0' + str(h)
		if m <= 9:
			m = '0' + str(m)
		if s <= 9:
			s = '0' + str(s)
		return str(h) + ':' + str(m) + ':' + str(s)

	def allow_login_handler(self, state):
		if(state == Qt.Checked):
			# Allow logins
			self.set_flags(2, 1)
		else:
			# Stop logins
			self.set_flags(2, 0)
		return

	def allow_judge_login_handler(self, state):
		if(state == Qt.Checked):
			# Allow logins
			self.set_flags(12, 1)
		else:
			# Stop logins
			self.set_flags(12, 0)
		return

	def allow_submissions_handler(self, state):
		if(state == Qt.Checked):
			# Allow submissions
			self.set_flags(3, 1)
		else:
			# Stop submissions
			self.set_flags(3, 0)
		return

	def manual_reviews_handler(self, state):
		if(state == Qt.Checked):
			# Allow submissions
			self.set_flags(20, 1)
		else:
			# Stop submissions
			self.set_flags(20, 0)
		return

	def allow_scoreboard_update_handler(self, state):
		if(state == Qt.Checked):
			# Allow scoreboard update
			self.set_flags(15, 1)
		else:
			# Stop scoreboard update
			self.set_flags(15, 0)
		return

	def check_login_allowed(self):
		if self.data_changed_flags[2] == 1:
			return True
		return False

	def check_judge_login_allowed(self):
		if self.data_changed_flags[12] == 1:
			return True
		return False

	def check_submission_allowed(self):
		if self.data_changed_flags[3] == 1:
			return True
		return False

	def check_scoreboard_update_allowed(self):
		if self.data_changed_flags[15] == 1:
			return True
		return False

	def check_manual_review_allowed(self):
		if self.data_changed_flags[20] == 1:
			return True
		return False

	def set_flags(self, index, value):
		self.data_changed_flags[index] = value
		return


	#####################################################
	# Databse related functions
	def init_qt_database(self):
		try:
			db = QSqlDatabase.addDatabase('QSQLITE')
			db.setDatabaseName('server_database.db')
			return db
		except:
			print('[ CRITICAL ] Database loading error!')
			self.log('[ CRITICAL ] Database loading error!')


	def manage_models(self, db, table_name):
		if db.open():
			model = QSqlTableModel()
			model.setTable(table_name)
			model.setEditStrategy(QSqlTableModel.OnFieldChange)
			model.select()
			return model
		else:
			print('[ CRITICAL ] Model Error: DB is not open')
			self.log('[ CRITICAL ] Model Error: DB is not open')
			return None

	def manage_leaderboard_model(self, db, table_name):
		if db.open():
			model = QSqlQueryModel()
			# model.setEditStrategy()
			return model
		else:
			print('[ CRITICAL ] Model Error: DB is not open')
			self.log('[ CRITICAL ] Model Error: DB is not open')
			return None

	def manage_submissions_model(self, db, table_name):
		if db.open():
			model = QSqlQueryModel()
			model.setQuery(self.submissions_query)
			# model.setEditStrategy()
			return model
		else:
			print('[ CRITICAL ] Model Error: DB is not open')
			self.log('[ CRITICAL ] Model Error: DB is not open')
			return None

	def generate_view(self, model):
		table = QTableView()
		table.setModel(model)
		# Enable sorting in the table view
		table.setSortingEnabled(True)
		# Enable Alternate row colors for readablity
		table.setAlternatingRowColors(True)
		# Select whole row when clicked
		table.setSelectionBehavior(QAbstractItemView.SelectRows)
		# Allow only one row to be selected
		table.setSelectionMode(QAbstractItemView.SingleSelection)
		# fit view to whole space
		table.resizeColumnsToContents()
		# Make table non-editable
		table.setEditTriggers(QAbstractItemView.NoEditTriggers)
		# Set view to delete when gui is closed
		table.setAttribute(Qt.WA_DeleteOnClose)

		horizontal_header = table.horizontalHeader()
		horizontal_header.setSectionResizeMode(QHeaderView.Stretch)
		vertical_header = table.verticalHeader()
		vertical_header.setVisible(False)
		return table

	@pyqtSlot()
	def manage_submission(self, selected_row):
		if self.data_changed_flags[8] == 0:
			# CRITICAL section flag set
			self.data_changed_flags[8] = 1
			try:
				# Get data from selected row
				#  run_id, client_id, problem_code, language, timestamp, verdict, sent_status

				run_id = self.sub_model.index(selected_row, 0).data()
				client_id = self.sub_model.index(selected_row, 1).data()
				problem_code = self.sub_model.index(selected_row, 2).data()
				language = self.sub_model.index(selected_row, 3).data()
				timestamp = self.sub_model.index(selected_row, 4).data()
				verdict = self.sub_model.index(selected_row, 5).data()
				sent_status = self.sub_model.index(selected_row, 6).data()

				if client_id == None:
					pass
				else:
					self.window = manage_submission_ui(
						self.data_changed_flags,
						self.task_queue,
						run_id,
						client_id,
						problem_code,
						language,
						timestamp,
						verdict,
						sent_status
					)
					self.window.show()

			except Exception as error: 
				print('[ ERROR ] : ' + str(error))
				self.log('[ ERROR ] : ' + str(error))
			finally:
				return
		else:
			return

	@pyqtSlot()
	def query_reply(self, selected_row):
		if self.data_changed_flags[8] == 0:
			# CRITICAL section flag set
			self.data_changed_flags[8] = 1
			try:
				# Get data from selected row
				query = self.query_model.index(selected_row, 2).data()
				client_id = self.query_model.index(selected_row, 1).data()
				query_id = self.query_model.index(selected_row, 0).data()
				
				if client_id == None or query_id == None or query_id == 0:
					self.data_changed_flags[8] = 0
					return
				
				self.window = query_reply_ui(self.data_changed_flags,self.task_queue ,query,client_id, query_id)
				self.window.show()

			except Exception as error: 
				print('[ ERROR ] : ' + str(error))
				self.log('[ ERROR ] : ' + str(error))
			finally:
				return
		else:
			return

	@pyqtSlot()
	def announcement(self):
		if self.data_changed_flags[8] == 0:
			# CRITICAL section flag set
			self.data_changed_flags[8] = 1
			try:
				query = 'Announcement'
				client_id = -1
				query_id = -1
				self.window = query_reply_ui(self.data_changed_flags,self.task_queue ,query,client_id, query_id)
				self.window.show()

			except Exception as error: 
				print('[ ERROR ] : ' + str(error))
				self.log('[ ERROR ] : ' + str(error))
			finally:
				return
		else:
			return

	@pyqtSlot()
	def create_accounts(self):
		if self.data_changed_flags[4] == 0:
			# CRITICAL section flag set
			self.data_changed_flags[4] = 1
			self.window = new_accounts_ui(self.data_changed_flags)
			self.window.show()			
		else:
			pass
		return

	@pyqtSlot()
	def rejudge_problem(self):
		if self.data_changed_flags[25] == 0:
			# CRITICAL section flag set
			self.data_changed_flags[25] = 1
			codes = self.config['Problem Codes']
			client_list = []
			client_list = client_authentication.get_connected_clients()
			self.window = rejudge_problem_ui(self.data_changed_flags, self.task_queue, codes, client_list)
			self.window.show()			
		else:
			pass
		return

	@pyqtSlot()
	def import_export_accounts(self):
		if self.data_changed_flags[4] == 0:
			# CRITICAL section flag set
			self.data_changed_flags[4] = 1
			self.window = ie_accounts_ui(self.data_changed_flags)
			self.window.show()			
		else:
			pass
		return

	@pyqtSlot()
	def password_verification(self):
		password = self.admin_password
		input_dialog = QInputDialog()
		input_dialog.setFixedSize(600, 400)
		
		user_input, button_pressed_flag = input_dialog.getText(
				self, "Authentication", "Enter Contest Password: ", QLineEdit.Password, ""
			)
		if button_pressed_flag:
			if self.validate_password(user_input):
				return 1
			else:
				self.log('[ SECURITY ] Password verification failed.')
				return 0
		return 2	

	def validate_password(self, input):
		if input == self.admin_password:
			return 1
		return 0


	@pyqtSlot()
	def delete_account(self, selected_rows):
		if self.data_changed_flags[6] == 0:
			# Set critical flag
			self.data_changed_flags[6] = 1
		else:
			# If one data deletion window is already opened, process it first.
			return
		# If no row is selected, return
		try:
			username = str(selected_rows[0].data())
		except: 
			# Reset data_changed_flag for deletion of account
			self.data_changed_flags[6] = 0
			return
		message = "Are you sure you want to delete : " + username + " ? "
		custom_box = QMessageBox()
		custom_box.setIcon(QMessageBox.Critical)
		custom_box.setWindowTitle('Confirm Deletion')
		custom_box.setText(message)

		custom_box.setStandardButtons(QMessageBox.Yes|QMessageBox.No)
		custom_box.setDefaultButton(QMessageBox.No)

		button_yes = custom_box.button(QMessageBox.Yes)
		button_yes.setText('Yes')
		button_no = custom_box.button(QMessageBox.No)
		button_no.setText('No')

		button_yes.setObjectName("close_button_yes")
		button_no.setObjectName("close_button_no")

		button_yes.setStyleSheet(open('Interface/style.qss', "r").read())
		button_no.setStyleSheet(open('Interface/style.qss', "r").read())

		custom_box.exec_()

		if custom_box.clickedButton() == button_yes:
			# Delete from accounts table and connected clients table
			user_management.delete_user(username)
			# Broadcast this user disconnection
			message = {
			'Code' : 'DSCNT',
			'Mode' : 1,
			'Client' : username
			}
			message = json.dumps(message)
			self.task_queue.put(message)
			# Update Accounts and connected clients View
			self.data_changed_flags[5] = 1
			self.data_changed_flags[1] = 1
		elif custom_box.clickedButton() == button_no : 
			pass

		# Reset critical flag
		self.data_changed_flags[6] = 0

		return

	@pyqtSlot()
	def edit_client(self, selected_row):
		if self.data_changed_flags[14] == 0:
			# Set critical flag
			self.data_changed_flags[14] = 1
		else:
			# If one client edit window is already opened, process it first.
			return
		# If no row is selected, return
		try:
			client_id = self.client_model.index(selected_row, 0).data()
			username = self.client_model.index(selected_row, 1).data()
			password = self.client_model.index(selected_row, 2).data()
			ip = self.client_model.index(selected_row, 3).data()
			state = self.client_model.index(selected_row, 4).data()

			if username == None or client_id == None or password == None or state == None:
				self.data_changed_flags[14] = 0
				pass
			else:
				self.edit_window = account_edit_ui(self.data_changed_flags, self.task_queue, client_id, username, password, state, ip)
				self.edit_window.show()
			
		except Exception as error: 
			print('[ ERROR ]' + str(error))
			self.log('[ ERROR ]' + str(error))
			self.data_changed_flags[14] = 0
		finally:
			return

	@pyqtSlot()
	def edit_account(self, selected_row):
		if self.data_changed_flags[14] == 0:
			# Set critical flag
			self.data_changed_flags[14] = 1
		else:
			# If one client edit window is already opened, process it first.
			return
		# If no row is selected, return
		try:
			username = self.account_model.index(selected_row, 0).data()
			password = self.account_model.index(selected_row, 1).data()
			ctype = self.account_model.index(selected_row, 2).data()

			if username == None or password == None or ctype == None:
				self.data_changed_flags[14] = 0
				pass
			else:
				# print("Sending ", username, password, ctype)
				self.edit_window = password_change_ui(self.data_changed_flags, username, password, ctype)
				self.edit_window.show()
			
		except Exception as error: 
			print('[ ERROR ][ EDIT ] ' + str(error))
			self.log('[ ERROR ][ EDIT ] ' + str(error))
			self.data_changed_flags[14] = 0
		finally:
			return

	@pyqtSlot()
	def view_problem(self, selected_row):
		if self.data_changed_flags[14] == 0:
			# Set critical flag
			self.data_changed_flags[14] = 1
		else:
			# If one client edit window is already opened, process it first.
			return
		# If no row is selected, return
		try:
			problem = self.problem_model.index(selected_row, 0).data()
			code = self.problem_model.index(selected_row, 1).data()
			test_files = self.problem_model.index(selected_row, 2).data()
			time_limit = self.problem_model.index(selected_row, 3).data()

			if problem == None:
				self.data_changed_flags[14] = 0
				pass
			else:
				self.edit_window = problem_edit_ui(self.data_changed_flags, self.task_queue, problem, code, test_files, time_limit)
				self.edit_window.show()
			
		except Exception as error: 
			print('[ ERROR ]' + str(error))
			self.log('[ ERROR ]' + str(error))
			self.data_changed_flags[14] = 0
		finally:
			return

	def reset_accounts(self):
		if self.data_changed_flags[11] == 0:
			# Set critical flag
			self.data_changed_flags[11] = 1
		else:
			# If one data deletion window is already opened, process it first.
			return
		# If no row is selected, return
		try:
			message = "Are you sure you want to DELETE ALL accounts?"
		
			custom_close_box = QMessageBox()
			custom_close_box.setIcon(QMessageBox.Critical)
			custom_close_box.setWindowTitle('Confirm RESET')
			custom_close_box.setText(message)

			custom_close_box.setStandardButtons(QMessageBox.Yes|QMessageBox.No)
			custom_close_box.setDefaultButton(QMessageBox.No)

			button_yes = custom_close_box.button(QMessageBox.Yes)
			button_yes.setText('Yes')
			button_no = custom_close_box.button(QMessageBox.No)
			button_no.setText('No')

			button_yes.setObjectName("close_button_yes")
			button_no.setObjectName("close_button_no")

			button_yes.setStyleSheet(open('Interface/style.qss', "r").read())
			button_no.setStyleSheet(open('Interface/style.qss', "r").read())

			custom_close_box.exec_()

			if custom_close_box.clickedButton() == button_yes:
				user_management.delete_all()
				# Update Accounts View
				self.data_changed_flags[5] = 1
			elif custom_close_box.clickedButton() == button_no : 
				pass
		except:
			print('[ ERROR ] Could not reset database!')
			self.log('[ ERROR ] Could not reset database!')

		finally:
			# Reset critical flag
			self.data_changed_flags[11] = 0
			return

	
	def reset_submissions(self):
		if self.data_changed_flags[11] == 0:
			# Set critical flag
			self.data_changed_flags[11] = 1
		else:
			# If one data deletion window is already opened, process it first.
			return
		# If no row is selected, return
		try:
			message = "Are you sure you want to DELETE ALL submissions?"
		
			custom_close_box = QMessageBox()
			custom_close_box.setIcon(QMessageBox.Critical)
			custom_close_box.setWindowTitle('Confirm RESET')
			custom_close_box.setText(message)

			custom_close_box.setStandardButtons(QMessageBox.Yes|QMessageBox.No)
			custom_close_box.setDefaultButton(QMessageBox.No)

			button_yes = custom_close_box.button(QMessageBox.Yes)
			button_yes.setText('Yes')
			button_no = custom_close_box.button(QMessageBox.No)
			button_no.setText('No')

			button_yes.setObjectName("close_button_yes")
			button_no.setObjectName("close_button_no")

			button_yes.setStyleSheet(open('Interface/style.qss', "r").read())
			button_no.setStyleSheet(open('Interface/style.qss', "r").read())

			custom_close_box.exec_()

			if custom_close_box.clickedButton() == button_yes:
				submissions_management.delete_all()
				# Update Submissions View
				self.data_changed_flags[0] = 1
			elif custom_close_box.clickedButton() == button_no : 
				pass
		except Exception as error:
			print('Could not reset database : ' + str(error))
			self.log('Could not reset database : ' + str(error))

		finally:
			# Reset critical flag
			self.data_changed_flags[11] = 0
		return

	def reset_queries(self):
		if self.data_changed_flags[11] == 0:
			# Set critical flag
			self.data_changed_flags[11] = 1
		else:
			# If one data deletion window is already opened, process it first.
			return
		# If no row is selected, return
		try:
			message = "Are you sure you want to DELETE ALL queries?"
		
			custom_close_box = QMessageBox()
			custom_close_box.setIcon(QMessageBox.Critical)
			custom_close_box.setWindowTitle('Confirm RESET')
			custom_close_box.setText(message)

			custom_close_box.setStandardButtons(QMessageBox.Yes|QMessageBox.No)
			custom_close_box.setDefaultButton(QMessageBox.No)

			button_yes = custom_close_box.button(QMessageBox.Yes)
			button_yes.setText('Yes')
			button_no = custom_close_box.button(QMessageBox.No)
			button_no.setText('No')

			button_yes.setObjectName("close_button_yes")
			button_no.setObjectName("close_button_no")

			button_yes.setStyleSheet(open('Interface/style.qss', "r").read())
			button_no.setStyleSheet(open('Interface/style.qss', "r").read())

			custom_close_box.exec_()

			if custom_close_box.clickedButton() == button_yes:
				query_management.delete_all()
				# Update Queriess View
				self.data_changed_flags[9] = 1
			elif custom_close_box.clickedButton() == button_no : 
				pass
		except Exception as error:
			print('Could not reset database : ' + str(error))
			self.log('Could not reset database : ' + str(error))

		finally:
			# Reset critical flag
			self.data_changed_flags[11] = 0
		return

	def reset_server(self):
		if self.data_changed_flags[11] == 0:
			# Set critical flag
			self.data_changed_flags[11] = 1
		else:
			# If one data deletion window is already opened, process it first.
			return
		# If no row is selected, return
		try:
			message = "Are you sure to RESET the server?\nContest Information will be lost"
			extra_data = "You should create the contest report first!"
		
			custom_close_box = QMessageBox()
			custom_close_box.setIcon(QMessageBox.Critical)
			custom_close_box.setWindowTitle('SERVER RESET')
			custom_close_box.setText(message)

			custom_close_box.setStandardButtons(QMessageBox.Yes|QMessageBox.No)
			custom_close_box.setDefaultButton(QMessageBox.No)

			button_yes = custom_close_box.button(QMessageBox.Yes)
			button_yes.setText('Yes')
			button_no = custom_close_box.button(QMessageBox.No)
			button_no.setText('No')

			button_yes.setObjectName("close_button_yes")
			button_no.setObjectName("close_button_no")

			button_yes.setStyleSheet(open('Interface/style.qss', "r").read())
			button_no.setStyleSheet(open('Interface/style.qss', "r").read())

			custom_close_box.exec_()

			if custom_close_box.clickedButton() == button_yes:
				print('[ EVENT ] SERVER RESET TRIGGERED')
				self.log('[ EVENT ] SERVER RESET TRIGGERED')
				print('[ RESET ] Disconnecting all clients...')
				self.log('[ RESET ] Disconnecting all clients...')
				# TODO : Broadcast this to all clients...
				message = {
				'Code' : 'DSCNT',
				'Mode' : 2
				}
				message = json.dumps(message)
				self.task_queue.put(message)
				# Set DISCONNECTED to all connected clients
				user_management.disconnect_all()
				self.data_changed_flags[1] = 1

				print('[ RESET ] Disconnecting all Judges...')
				self.log('[ RESET ] Disconnecting all Judges...')
				# Update judges view
				self.data_changed_flags[13] = 1
				# TODO Broadcast this to all judges

				print('[ RESET ] Clearing scoreboard...')
				self.log('[ RESET ] Clearing scoreboard...')
				self.data_changed_flags[16] = 1

				print('[ RESET ] Resetting Accounts...')
				self.log('[ RESET ] Resetting Accounts...')
				user_management.delete_all()
				# Update Accounts View
				self.data_changed_flags[5] = 1
				print('[ RESET ] Resetting Submissions...')
				self.log('[ RESET ] Resetting Submissions...')
				submissions_management.delete_all()
				# Update Submissions View
				self.data_changed_flags[0] = 1
				print('[ RESET ] Resetting Queries...')
				self.log('[ RESET ] Resetting Queries...')
				query_management.delete_all()
				# Update Queriess View
				self.data_changed_flags[9] = 1
				print('[ RESET ] Reset environment...')
				self.log('[ RESET ] Reset environment...')
				server_window.set_button_behavior(self, 'SETUP')
				save_status.update_entry('Contest Duration', '00:00:00')
				save_status.update_entry('Contest Status', 'SETUP')
				save_status.update_entry('Contest Start Time', '00:00:00')
				save_status.update_entry('Contest End Time', '00:00:00')
				save_status.update_entry('Contest Set Time', 0)

			
			elif custom_close_box.clickedButton() == button_no : 
				pass
		except Exception as error:
			print('[ ERROR ] Could not reset server : ' + str(error))
			self.log('[ ERROR ] Could not reset server : ' + str(error))

		finally:
			# Reset critical flag
			self.data_changed_flags[11] = 0
		return

	def reset_timer(self):
		if self.data_changed_flags[11] == 0:
			# Set critical flag
			self.data_changed_flags[11] = 1
		else:
			# If one data deletion window is already opened, process it first.
			return
		# If no row is selected, return
		try:
			message = "Are you sure to RESET the timer?"
			
			custom_close_box = QMessageBox()
			custom_close_box.setIcon(QMessageBox.Critical)
			custom_close_box.setWindowTitle('TIMER RESET')
			custom_close_box.setText(message)

			custom_close_box.setStandardButtons(QMessageBox.Yes|QMessageBox.No)
			custom_close_box.setDefaultButton(QMessageBox.No)

			button_yes = custom_close_box.button(QMessageBox.Yes)
			button_yes.setText('Yes')
			button_no = custom_close_box.button(QMessageBox.No)
			button_no.setText('No')

			button_yes.setObjectName("close_button_yes")
			button_no.setObjectName("close_button_no")

			button_yes.setStyleSheet(open('Interface/style.qss', "r").read())
			button_no.setStyleSheet(open('Interface/style.qss', "r").read())

			custom_close_box.exec_()

			if custom_close_box.clickedButton() == button_yes:
				print('[ EVENT ] TIMER RESET TRIGGERED')
				self.log('[ EVENT ] TIMER RESET TRIGGERED')
				print('[ RESET ] Reset environment...')
				self.log('[ RESET ] Reset environment...')
				server_window.set_button_behavior(self, 'SETUP')
				save_status.update_entry('Contest Duration', '00:00:00')
				save_status.update_entry('Contest Status', 'SETUP')
				save_status.update_entry('Contest Start Time', '00:00:00')
				save_status.update_entry('Contest End Time', '00:00:00')
				save_status.update_entry('Contest Set Time', 0)

			elif custom_close_box.clickedButton() == button_no : 
				pass
		except Exception as error:
			print('[ ERROR ] Could not reset timer : ' + str(error))
			self.log('[ ERROR ] Could not reset timer : ' + str(error))

		finally:
			# Reset critical flag
			self.data_changed_flags[11] = 0
		return

	def disconnect_all(self):
		if self.data_changed_flags[11] == 0:
			# Set critical flag
			self.data_changed_flags[11] = 1
		else:
			# If one data deletion window is already opened, process it first.
			return

		status = self.password_verification()
		if status == 1:
			pass
		elif status == 2:
			self.data_changed_flags[11] = 0 
			return
		else:
			self.data_changed_flags[11] = 0
			QMessageBox.about(self, "Access Denied!", "Authentication failed!")
			return

		# If no row is selected, return
		try:
			message = "Are you sure to DISCONNECT all clients?\nClients will be able to login again\nif permitted."
			
			custom_close_box = QMessageBox()
			custom_close_box.setIcon(QMessageBox.Critical)
			custom_close_box.setWindowTitle('Disconnect Clients')
			custom_close_box.setText(message)

			custom_close_box.setStandardButtons(QMessageBox.Yes|QMessageBox.No)
			custom_close_box.setDefaultButton(QMessageBox.No)

			button_yes = custom_close_box.button(QMessageBox.Yes)
			button_yes.setText('Yes')
			button_no = custom_close_box.button(QMessageBox.No)
			button_no.setText('No')

			button_yes.setObjectName("close_button_yes")
			button_no.setObjectName("close_button_no")

			button_yes.setStyleSheet(open('Interface/style.qss', "r").read())
			button_no.setStyleSheet(open('Interface/style.qss', "r").read())

			custom_close_box.exec_()

			if custom_close_box.clickedButton() == button_yes:
				print('[ EVENT ] CLIENT DISCONNECT TRIGGERED')
				self.log('[ EVENT ] CLIENT DISCONNECT TRIGGERED')
				print('[ EVENT ][ RESET ] Disconnecting all clients...')
				self.log('[ EVENT ][ RESET ] Disconnecting all clients...')
				message = {
				'Code' : 'DSCNT',
				'Mode' : 2
				}
				message = json.dumps(message)
				self.task_queue.put(message)
				# Set DISCONNECTED to all connected clients
				user_management.disconnect_all()
				self.data_changed_flags[1] = 1
			
			elif custom_close_box.clickedButton() == button_no : 
				pass
		except Exception as error:
			print('Could not reset database : ' + str(error))
			self.log('Could not reset database : ' + str(error))
		finally:
			# Reset critical flag
			self.data_changed_flags[11] = 0
		return


		

	###################################################
	
	###################################################
	def set_status(self, message = 'SETUP'):
		self.status.showMessage('BitsOJ > ' + message)
	###################################################

	def closeEvent(self, event):
		# if lock is set, ignore
		if self.data_changed_flags[24] == 1:
			QMessageBox.about(self, "Access Denied", "Server is locked!")
			self.log('[ SECURITY ] Server Close attempt -> Denied: Server was locked.')
			event.ignore()
			return

		# if contest is running,
		if self.data_changed_flags[10] == 1:
			status = self.password_verification()
			if status == 1:
				pass
			elif status == 2: 
				event.ignore()
				return
			else:
				QMessageBox.about(self, "Access Denied", "Authentication failed!")
				self.log('[ SECURITY ] Server Close attempt -> Denied: Password mismatch.')
				event.ignore()
				return


		message = "Pressing 'Yes' will SHUT the Server."
		detail_message = "Server will not process any request while it is closed. You should not do this when any contest is running.\n\nAre you sure you want to exit?"
		
		custom_close_box = QMessageBox()
		custom_close_box.setIcon(QMessageBox.Critical)
		custom_close_box.setWindowTitle('Warning!')
		custom_close_box.setText(message)
		custom_close_box.setInformativeText(detail_message)

		custom_close_box.setStandardButtons(QMessageBox.Yes|QMessageBox.No)
		custom_close_box.setDefaultButton(QMessageBox.No)

		button_yes = custom_close_box.button(QMessageBox.Yes)
		button_yes.setText('Yes')
		button_no = custom_close_box.button(QMessageBox.No)
		button_no.setText('No')

		button_yes.setObjectName("close_button_yes")
		button_no.setObjectName("close_button_no")

		button_yes.setStyleSheet(open('Interface/style.qss', "r").read())
		button_no.setStyleSheet(open('Interface/style.qss', "r").read())

		custom_close_box.exec_()

		if custom_close_box.clickedButton() == button_yes:
			self.data_changed_flags[7] = 1
			self.log('[ SECURITY ] Server Close attempt -> Accepted.')
			event.accept()
		elif custom_close_box.clickedButton() == button_no : 
			event.ignore()


class init_gui(server_window):
	def __init__(self, data_changed_flags, task_queue, log_queue):
		# make a reference of App class
		app = QApplication(sys.argv)
		app.setStyle("Fusion")
		app.setStyleSheet(open('Interface/style.qss', "r").read())
		# If user is about to close window
		app.aboutToQuit.connect(self.closeEvent)
		
		server_app = server_window(data_changed_flags, task_queue, log_queue)

		# Splash screen
		# splash = QSplashScreen(QPixmap("Elements/bitwise.png"))
		# splash.show()
		# splash.finish(server_app)
		# Splash ends

		server_app.showMaximized()

		# Execute the app mainloop
		app.exec_()
		return