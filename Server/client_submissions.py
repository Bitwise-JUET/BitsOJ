from database_management import submissions_management, query_management
global query_id_counter

class submission():
	run_id = 0
	# Manage a new submission
	def new_submission(client_id, problem_code, language, time_stamp, source_code):
		client_id = str(client_id)
		print("[ SUBMIT ] "+ str(client_id) + " for problem " + problem_code)
		run_id = submission.generate_run_id()
		temp_file_name = str(run_id)
		file_name = submission.make_local_source_file(temp_file_name, source_code, language)
		print ("[ FILE ] New file created for client : "+ str(client_id) + " File name:  " + file_name)
		return run_id, file_name

	# Make a local backup file for the client run id
	def make_local_source_file(file_name, source_code, language):
		if language == "CPP":
			file_extension = ".cpp"
		elif language == "GCC":
			file_extension = ".c"
		elif language == "PY2":
			file_extension = ".py"
		elif language == "PY3":
			file_extension = ".py"
		elif language == "JVA":
			file_extension = ".java"
		else:
			file_extension = ".temp"

		# w : Write mode, + : Create file if not exists
		new_file_name = file_name + file_extension
		print("[ WRITE ] Write a new file : " + new_file_name)
		client_local_file = open("Client_Submissions/" + new_file_name, "w+")
		client_local_file.write(source_code)
		client_local_file.close()
		return new_file_name

	def init_run_id():
		run = submissions_management.init_run_id()
		submission.run_id = run
		return run

	def generate_run_id():
		run_id = submission.run_id 
		submission.run_id += 1
		return run_id

	def generate_query_id():
		query_id = query_management.generate_new_query_id()
		return query_id
