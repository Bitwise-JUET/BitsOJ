import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon, QPalette, QColor, QPixmap
from PyQt5.QtSql import QSqlTableModel, QSqlDatabase
from PyQt5.QtCore import pyqtSlot, pyqtSignal, QObject, QTimer, Qt, QModelIndex


global current_status 
current_status = "STOPPED"

class server_window(QMainWindow):
	def __init__(self, data_changed_flag):
		super().__init__()
		# Set app icon
		self.setWindowIcon(QIcon('Elements/logo.png'))
		# Set window title
		self.setWindowTitle('BitsOJ v1.0.1 [ SERVER ]')
		# Make  the app run full-screen
		# Initialize status bar (Bottom Bar)
		self.status = self.statusBar()
		self.resize(800, 600)

		self.timer = QTimer()
		self.change_flag = True
		self.timer.timeout.connect(self.update_data)
		self.timer.start(2000)
		
		# make data_changed_flag accessible from the class methods
		self.data_changed_flag2 = data_changed_flag
		
		###########################################################
		# Define Sidebar Buttons and their actions
		button_width = 200
		button_height = 50

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

		self.button_7 = QPushButton('Languages', self)
		self.button_7.setFixedSize(button_width, button_height)
		self.button_7.clicked.connect(self.manage_languages)
		self.button_7.setObjectName("sidebar_button")

		self.button_8 = QPushButton('Statistics', self)
		self.button_8.setFixedSize(button_width, button_height)
		self.button_8.clicked.connect(self.show_stats)
		self.button_8.setObjectName("sidebar_button")

		self.button_9 = QPushButton('Settings', self)
		self.button_9.setFixedSize(button_width, button_height)
		self.button_9.clicked.connect(self.contest_settings)
		self.button_9.setObjectName("sidebar_button")

		self.button_10 = QPushButton('Generate Report', self)
		self.button_10.setFixedSize(button_width, button_height)
		self.button_10.clicked.connect(self.generate_report)
		self.button_10.setObjectName("sidebar_button")

		self.button_11 = QPushButton('About', self)
		self.button_11.setFixedSize(button_width, button_height)
		self.button_11.clicked.connect(self.show_about)
		self.button_11.setObjectName("sidebar_button")

		###########################################################

		###########################################################
		# Manage tabs on the right window
		# Each tab is an object returned by the respective function associated with its UI
		self.tab1 , self.sub_model, self.sub_view = self.submissions_ui()
		self.tab2 = self.judge_ui()
		self.tab3 = self.client_ui()
		self.tab4 = self.query_ui()
		self.tab5 = self.leaderboard_ui()
		self.tab6 = self.problem_ui()
		self.tab7 = self.language_ui()
		self.tab8 = self.stats_ui()
		self.tab9 = self.settings_ui()
		self.tab10 = self.reports_ui()
		self.tab11 = self.about_us_ui()

		###########################################################
		
		# Add widgets to our main window
		server_window.init_UI(self)
		return
	

	def init_UI(self):
		self.set_status()
		# Define Layout for sidebar
		side_bar_layout = QVBoxLayout()

		# Add buttons to our layout
		side_bar_layout.addWidget(self.button_1)
		side_bar_layout.addWidget(self.button_2)
		side_bar_layout.addWidget(self.button_3)
		side_bar_layout.addWidget(self.button_4)
		side_bar_layout.addWidget(self.button_5)
		side_bar_layout.addWidget(self.button_6)
		side_bar_layout.addWidget(self.button_7)
		side_bar_layout.addWidget(self.button_8)
		side_bar_layout.addWidget(self.button_9)
		side_bar_layout.addWidget(self.button_10)
		side_bar_layout.addWidget(self.button_11)

		# Set stretch and spacing
		side_bar_layout.addStretch(1)
		side_bar_layout.setSpacing(1)

		# Define our sidebar widget and set side_bar_layout to it.
		side_bar_widget = QWidget()
		side_bar_widget.setLayout(side_bar_layout)
		side_bar_widget.setObjectName("sidebar")

		#Define our top bar
		logo = QLabel(self)
		logo_image = QPixmap('Elements/bitwise_new.png')
		logo_image2 = logo_image.scaledToWidth(104)
		logo.setPixmap(logo_image2)

		top_bar_layout = QHBoxLayout()
		top_bar_layout.setContentsMargins(15, 5, 1, 0);
		top_bar_layout.addWidget(logo)

		top_bar_widget = QWidget()
		top_bar_widget.setLayout(top_bar_layout)
		top_bar_widget.setObjectName('top_bar')

		# Define our right side screens corresponding to buttons on the sidebar
		# Basically right screens are tab widgets whose tabs are hidden, 
		# and we map sidebar buttons to each tab switch :)
		# Since sidebars are not natively supported by pyqt5
		self.right_widget = QTabWidget()
		self.right_widget.setObjectName("main_tabs")
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
		self.right_widget.addTab(self.tab11, '')

		# Screen 1 will be our initial screen 
		self.right_widget.setCurrentIndex(0)

		# Define the combined layout for sidebar + right side screens
		main_layout = QHBoxLayout()
		main_layout.addWidget(side_bar_widget)
		main_layout.addWidget(self.right_widget)

		# setstretch( index, stretch_value )
		main_layout.setStretch(0, 10)
		main_layout.setStretch(1, 100)
		main_layout.setContentsMargins(10, 1, 10, 1)
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

	def view_submissions(self):
		self.right_widget.setCurrentIndex(0)

	def manage_judges(self):
		self.right_widget.setCurrentIndex(1)

	def manage_clients(self):
		self.right_widget.setCurrentIndex(2)

	def manage_queries(self):
		self.right_widget.setCurrentIndex(3)

	def manage_leaderboard(self):
		self.right_widget.setCurrentIndex(4)

	def manage_problems(self):
		self.right_widget.setCurrentIndex(5)

	def manage_languages(self):
		self.right_widget.setCurrentIndex(6)

	def show_stats(self):
		self.right_widget.setCurrentIndex(7)

	def contest_settings(self):
		self.right_widget.setCurrentIndex(8)

	def generate_report(self):
		self.right_widget.setCurrentIndex(9)

	def show_about(self):
		self.right_widget.setCurrentIndex(10)

	def update_data(self):
		# If data has changed in submission table
		if self.data_changed_flag2.value == 1:
			print('[ DATA CHANGED ]')
			self.sub_model.select()
			# reset data_changed_flag
			print('[ COMMUNICATE ] Changed value of data_changed_flag2 to 0')
			self.data_changed_flag2.value = 0
		return
	
	def update_view(self):
		self.sub_model.select()
		return
	
	#####################################################
	def manage_db(self):
		db = QSqlDatabase.addDatabase('QSQLITE')
		db.setDatabaseName('server_database.db')
		if db.open():
			submission_model = QSqlTableModel()
			submission_model.setTable('submissions')
			submission_model.setEditStrategy(QSqlTableModel.OnFieldChange)
			submission_model.select()
			submission_model.setHeaderData(0, Qt.Horizontal, 'Run ID')
			submission_model.setHeaderData(1, Qt.Horizontal, 'Client ID')
			submission_model.setHeaderData(2, Qt.Horizontal, 'Language')
			submission_model.setHeaderData(3, Qt.Horizontal, 'Source File')
			submission_model.setHeaderData(4, Qt.Horizontal, 'Problem Code')
			submission_model.setHeaderData(5, Qt.Horizontal, 'Verdict')
			submission_model.setHeaderData(6, Qt.Horizontal, 'Time')
			#submission_model.dataChanged.emit(QModelIndex(), QModelIndex())
		return submission_model

	def generate_view(self, model):
		submission_table = QTableView()
		submission_table.setModel(model)
		submission_table.setWindowTitle('Submissions')
		# Enable sorting in the table view
		submission_table.setSortingEnabled(True)
		submission_table.resizeColumnsToContents()
		horizontal_header = submission_table.horizontalHeader()
		horizontal_header.setSectionResizeMode(QHeaderView.Stretch)
		vertical_header = submission_table.verticalHeader()
		#vertical_header.setSectionResizeMode(QHeaderView.Stretch)
		vertical_header.setVisible(False)
		return submission_table

	# Handle UI for various button presses
	def submissions_ui(self):
		heading = QLabel('Submissions')
		heading.setObjectName('main_screen_content')

		submission_model = self.manage_db()
		submission_table = self.generate_view(submission_model)

		
		main_layout = QVBoxLayout()
		main_layout.addWidget(heading)
		main_layout.addWidget(submission_table)
		main_layout.setStretch(0,5)
		main_layout.setStretch(1,95)

		main = QWidget()
		main.setLayout(main_layout)
		main.setObjectName("main_screen");
		main.show()
		return main, submission_model, submission_table


	

	def judge_ui(self):
		main_layout = QVBoxLayout()
		heading = QLabel('Page2')
		heading.setObjectName('main_screen_content')

		main_layout.addWidget(heading)
		main_layout.addStretch(5)

		main = QWidget()
		main.setLayout(main_layout)
		main.setObjectName("main_screen");
		return main

	def client_ui(self):
		main_layout = QVBoxLayout()
		heading = QLabel('Page3')
		heading.setObjectName('main_screen_content')

		main_layout.addWidget(heading)
		main_layout.addStretch(5)
		main = QWidget()
		main.setLayout(main_layout)
		main.setObjectName("main_screen");
		return main

	def query_ui(self):
		main_layout = QVBoxLayout()
		heading = QLabel('Page4')
		heading.setObjectName('main_screen_content')

		main_layout.addWidget(heading)
		main_layout.addStretch(5)
		main = QWidget()
		main.setLayout(main_layout)
		main.setObjectName("main_screen");
		return main

	def leaderboard_ui(self):
		main_layout = QVBoxLayout()
		heading = QLabel('Page5')
		heading.setObjectName('main_screen_content')

		main_layout.addWidget(heading)
		main_layout.addStretch(5)
		main = QWidget()
		main.setLayout(main_layout)
		main.setObjectName("main_screen");
		return main

	def problem_ui(self):
		main_layout = QVBoxLayout()
		heading = QLabel('Page6')
		heading.setObjectName('main_screen_content')

		main_layout.addWidget(heading)
		main_layout.addStretch(5)
		main = QWidget()
		main.setLayout(main_layout)
		main.setObjectName("main_screen");
		return main

	def language_ui(self):
		main_layout = QVBoxLayout()
		heading = QLabel('Page7')
		heading.setObjectName('main_screen_content')

		main_layout.addWidget(heading)
		main_layout.addStretch(5)
		main = QWidget()
		main.setLayout(main_layout)
		main.setObjectName("main_screen");
		return main

	def stats_ui(self):
		main_layout = QVBoxLayout()
		heading = QLabel('Page8')
		heading.setObjectName('main_screen_content')

		main_layout.addWidget(heading)
		main_layout.addStretch(5)
		main = QWidget()
		main.setLayout(main_layout)
		main.setObjectName("main_screen");
		return main

	def settings_ui(self):
		main_layout = QVBoxLayout()
		heading = QLabel('Page9')
		heading.setObjectName('main_screen_content')

		main_layout.addWidget(heading)
		main_layout.addStretch(5)
		main = QWidget()
		main.setLayout(main_layout)
		main.setObjectName("main_screen");
		return main

	def reports_ui(self):
		main_layout = QVBoxLayout()
		heading = QLabel('Page10')
		heading.setObjectName('main_screen_content')

		main_layout.addWidget(heading)
		main_layout.addStretch(5)
		main = QWidget()
		main.setLayout(main_layout)
		main.setObjectName("main_screen");
		return main

	def about_us_ui(self):
		main_layout = QVBoxLayout()
		heading = QLabel('Page11')
		heading.setObjectName('main_screen_content')

		main_layout.addWidget(heading)
		main_layout.addStretch(5)
		main = QWidget()
		main.setLayout(main_layout)
		main.setObjectName("main_screen");
		return main

	###################################################

	def set_status(self):
		global current_status
		self.status.showMessage(current_status)

	def closeEvent(self, event):
		message = "Pressing 'Yes' will SHUT the Server.\nAre you sure you want to exit?"
		detail_message = "Any active contest might end prematurely. "
		
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

		button_yes.setStyleSheet(open('Elements/style.qss', "r").read())
		button_no.setStyleSheet(open('Elements/style.qss', "r").read())

		custom_close_box.exec_()

		if custom_close_box.clickedButton() == button_yes:
			event.accept()
		elif custom_close_box.clickedButton() == button_no : 
			event.ignore()


	def update_gui(self):
		print("[ GUI UPDATE ] Called update_gui()")
			


class init_gui(server_window):
	def __init__(self, data_changed_flag):
		app = QApplication(sys.argv)
		app.setStyle("Fusion")
		app.setStyleSheet(open('Elements/style.qss', "r").read())
		# If user is about to close window
		app.aboutToQuit.connect(self.closeEvent)
		
		# make a reference of App class
		server_app = server_window(data_changed_flag)
		server_app.showMaximized()
		# Close the server as soon as close button is clicked
		app.exec_()
		return
