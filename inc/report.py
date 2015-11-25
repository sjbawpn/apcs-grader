#!/usr/bin/python
import os

# Class to represent the student's report file.
# methods: flag(), add(message), submit()
class Report:
	filename = "default.txt"
	flagged = False
	content = []
	verbose = False
	
	# Set the assignment as flagged. The flag being on affects the report name
	def flag(self):
		self.flagged = True

	# construct with the report filename
	def __init__(self, filename, verbose = False):
		self.filename = filename
		self.content = []
		self.verbose = verbose
	
	# add a line to the report
	def add(self, message):
		if self.verbose:
			print(message)
		self.content.append(message + "\n")
	
	# submit the report and save the file
	def submit(self):
		if self.flagged:
			self.filename = "FLAGGED_" + self.filename
		currdir = os.getcwd()
		reportsdir = os.path.join(currdir,"reports")

		# If "reports" directory does not exist, create it
		if not os.path.exists(reportsdir):
			os.mkdir(reportsdir)

		with file(os.path.join(currdir,"reports", self.filename), "w") as f :
			f.writelines(self.content)
