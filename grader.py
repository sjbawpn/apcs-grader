#!/usr/bin/python
import os
import sys
from optparse import OptionParser
import subprocess

parser = OptionParser()
parser.add_option("-l", "--lab", dest="labname", help="assignment to grade", metavar="LAB")

#TODO Use these options instead of the hard code booleans (debug and printSrc)
#parser.add_option("-d", "--debug", dest="debug", help="Enable debug mode: prints report to the command line", metavar="DEBUG")
#parser.add_option("-is", "--includesource", dest="incSrc", help="Append the assignemnts source code at the end of the report", metavar="INCSRC")

(options, args) = parser.parse_args()

#TODO Use options for the next two settings.
# Enabling debug prints the report to the command line
debug = False

# Enabling printSrc appends the java source file
printSrc = True

# Class to represent the student's report file.
# methods: flag(), add(message), submit()
class Report:
	filename = "default.txt"
	flagged = False
	content = []
	
	# Set the assignment as flagged. The flag being on affects the report name
	def flag(self):
		self.flagged = True

	# construct with the report filename
	def __init__(self, filename):
		self.filename = filename
		self.content = []
	
	# add a line to the report
	def add(self, message):
		if debug:
			print(message)
		self.content.append(message + "\n")
	
	# submit the report and save the file
	def submit(self):
		if self.flagged:
			self.filename = "FLAGGED_" + self.filename
		currdir = os.getcwd()
		with file(os.path.join(currdir,"reports", self.filename), "w") as f :
			f.writelines(self.content)

#TODO logic to parse code could could be moved to a CodeParser class
	
currdir = os.getcwd()

#TODO Create dirs and extract assignments programatically.

# directory where the extracted assignments reside
problemsdir = os.path.join(currdir,"problems")

# directory where the assignments will be compiled, run and unit tested 1 by 1.
javadir = os.path.join(currdir,"java")


submissions = os.listdir(problemsdir)
for submission in submissions:
	fname, fext = os.path.splitext(submission)
	studentName, javaName, x = fname.split("_")
	print(studentName)
	report = Report(studentName.lower().replace(" ","_") + ".txt")

	if not fext == ".java":
		report.add("ERROR: File extension: {0}, expected: .java".format(fext))
		report.flag()
		report.submit()
		continue	
	lines = []
	comments = []
	mainClass = ""
	functions = []
	issues = []
	with file(os.path.join(problemsdir, submission) ,"r") as f:
		lines = f.readlines()

	#
	# find the main class name
	#
	#TODO A better way to parse the file is to create a class tree but that seems overkill for this project
	for line in lines:
		line = line.strip()
		code = line.split("//")[0] 
		if mainClass == "" and "class" in code:
			prefix = code.split("(")[0]
			words = prefix.split()
			idx = words.index("class")
			if idx >= 0:
				mainClass = words[idx+1]

	# Exit if the main class could not be determined	
	if mainClass == "":
		report.add("ERROR: Could not determine main class name")
		report.flag()
		report.submit()
		continue	

	# re-write the source file in a more script friendly way.
	newlines = []
	for line in lines:
		# Comment out the package name (everything will be in the default package for now)
		if line.startswith("package"):
			line = "//" + line
		# replace every reference of the main class with the lab name.
		newlines.append(line.replace(mainClass, options.labname))
	
	# rename the file to match the lab name.
	with file(os.path.join(javadir, options.labname + ".java"), "w") as f:
		f.writelines(newlines)

	# 
	# Compile and run	
	currdir = os.getcwd()
	os.chdir(javadir)
	# Right now, runner.sh must be modified to compile the lab name.
	# This needs to be done once for the entire assignment
	#TODO do this programatically. 
	#TODO Should runner.sh be a python script? Keeping it outsite this script allows to re-compile an individual assignment without running the whole script.
	subprocess.call([os.path.join(javadir, "runner.sh"), ">> build.log"])
	os.chdir(currdir)

	# Report the unit test results. These are stored in result.log in the "java" sub directory
	report.add("------ Functional Results -----")
	runlog = os.path.join(javadir,"result.log")
	if os.path.exists(runlog):
		with file(runlog, "r") as f:
			res = f.readlines()
		for line in res:
			report.add("\t" + line)
	report.add("")

	#
	# crawl for functions
	# Look for "{" in each file and the first line of text that preceeds the line with "{"
	# (if the curly brace is not on it's own line, the function prototype is in that line)
	# skip lines that start with words in the "blockedKeyworkds" list. (not exhaustive)
	blockedKeywords = ["for", "while", "try", "catch", "if", "while", "class"]

	i = 0;
	while i < len(lines):
		line = lines[i].strip()
		if line.startswith("//") or not "{" in line:
			i = i + 1
			continue	
		
		func = ""
		if line.startswith("{"):
			n = 1
			while i - n >= 0 and len(func) == 0:
				func = lines[i-n].strip()
				n = n + 1
		else:
			func = line.replace("{", "") # remove "{" for readability
		
		words = func.replace("("," ").split()
		if words[0] not in blockedKeywords:
			functions.append(func)
		i = i + 1
	
	#
	# crawl for comments
	#TODO handle empty lines between comments and logic (basically skip them)
	#
	i = 0;
	while i < len(lines):
		line = lines[i].strip()
		# Single comments
		if "//" in line and not line.startswith("//"):
			comment = []
			if i > 0:
				comment.append("    " + lines[i-1])
			comment.append("--->" + lines[i])
			if i + 1 < len(lines):
				comment.append("    " + lines[i+1])
			comments.append(comment)
			i = i + 1
			continue
		
		# Block comments (//)
		comment = []
		while line.startswith("//"):
			comment.append(line)
			i = i + 1
			if i == len(lines):
				break
			line = lines[i].strip()
		if len(comment) > 0:
			if i + 1 < len(lines):
				comment.append(lines[i+1])
			comments.append(comment)
		#TODO handle /* */ comments
		i = i + 1
	
	# Issue checker: If source file name does not match the class
	if not mainClass == javaName:
		issues.append("Java file name: \"{0}\" does not match class name : \"{1}\"!".format(javaName, mainClass))

	# Report on the issues
	if len(issues) > 0:
		report.add("------ !! ISSUES !! -----")
		for issue in issues:
			report.add("\t" + issue)
	report.add("------ Main class -----")
	report.add("\tName = {0}".format(mainClass))

	# Report on the functions
	report.add("")
	report.add("------ FUNCTIONS ----- (count={0})".format(len(functions)))
	i = 1
	for function in functions:
		report.add("\t-function {0}:".format(i))
		report.add("\t\t"+function.strip())
		i = i + 1

	# Report on the comments
	report.add("")
	report.add("------ COMMENTS ----- (count={0})".format(len(comments)))
	i = 1
	for comment in comments:
		report.add("\t-Comment {0}:".format(i))
		for line in comment:
			report.add("\t\t"+line.strip())
		i = i + 1
	
	# If enabled, append the source code to the end of the report.
	if printSrc:
		report.add("")
		report.add("")
		report.add("-"*20)
		for line in lines:
			report.add(line)
	report.submit()