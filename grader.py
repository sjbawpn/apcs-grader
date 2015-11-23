#!/usr/bin/python
import os
import shutil
import sys
from optparse import OptionParser
import subprocess
import json
from pprint import pprint
from xml.dom import minidom


def getPath(path):
	currdir = os.getcwd()
	result = path
	if not os.path.isabs(result):
		result = os.path.join(currdir, result)
	return result

def reportTestResults(report, results):
	#<testsuite name="TestJunit" tests="1" skipped="0" failures="1" errors="0" timestamp="2015-11-23T21:53:33" hostname="crls" time="0.012">
	report.add("------ Functional Results -----")
	xmldoc = minidom.parse(results)
	testsuite = xmldoc.getElementsByTagName("testsuite")[0]
	tests = testsuite.attributes["tests"].value
	skipped = testsuite.attributes["skipped"].value
	failures = testsuite.attributes["failures"].value
	errors = testsuite.attributes["errors"].value
	report.add("\ttests={0}, skipped={1}, failures={2}, errors={3}".format(tests, skipped, failures, errors))

	if int(failures) > 0 or int(errors) > 0:
		report.add("\tFunctional Test Failed")

	testcaseList = xmldoc.getElementsByTagName("testcase")
	i = 1
	for testcase in testcaseList:
		name = testcase.attributes["name"].value
		failures = testcase.getElementsByTagName("failure")
		status = "Passed"
		if len(failures) > 0:
			status = "Failed"
		report.add("\t{0}- \"{1}\" : {2}!".format(i, name, status))
		
		for failure in failures:
			message = failure.attributes["message"].value
			report.add("\t\tMessage: {0}".format(message))
		i = i + 1

parser = OptionParser()
parser.add_option("-c", "--config", dest="config", help="assignment config file name (default=assignment.json)", default="assignment.json", metavar="CONFIG")

(options, args) = parser.parse_args()

currdir = os.getcwd()

jsonpath = getPath(options.config)
if not os.path.exists(jsonpath):
	parser.error("Could not determine json path")

with open(jsonpath) as f:
	data = json.load(f)

if "test" not in data:
	sys.exit("Error: \"test\" section missing in config. No unit tests defined")
submissionsdir = os.path.join(currdir,"submissions")
if os.path.exists(submissionsdir):
	delete = raw_input("submissions/ directory exists. Do you wish to delete it (Y, N)? Y: ")
	if delete.lower() != "n":
		shutil.rmtree(submissionsdir)

if "zip" in data:
	zippath = getPath(data["zip"])
	if not os.path.exists(zippath):
		 parser.error("{0} does not exist".format(zippath))
	if not os.path.splitext(zippath)[1] == ".zip":
		parser.error("{0} not a zip file".format(zippath))
	if not os.path.exists(submissionsdir):
		os.mkdir(submissionsdir)
	args = ["unzip","-d", submissionsdir, zippath]
	subprocess.call(args)
		
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
		if data["verbose"]:
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

#TODO logic to parse code be moved to a CodeParser class
	


# directory where the extracted assignments reside
submissionsdir = os.path.join(currdir,"submissions")
if not os.path.exists(submissionsdir):
	sys.exit("could not find \"submissions\" directory")

# directory where the assignments will be compiled, run and unit tested 1 by 1.
srcdir = os.path.join(currdir, "src")
if os.path.exists(srcdir):
	delete = raw_input("src/ directory exists and must be deleted before proceding. Delete it (Y, N)? Y: ")
	if delete.lower() != "n":
		shutil.rmtree(srcdir)
	else:
		sys.exit("Program terminated")
javadir = os.path.join(srcdir,"main","java")
testdir = os.path.join(srcdir,"test","java")
os.makedirs(javadir)
os.makedirs(testdir)

if "supportFiles" in data:
	for f in data["supportFiles"]:
		fpath = getPath(f)
		if not os.path.exists(fpath):
			sys.exit("Error: Support file \"{0}\" does not exist".format(fpath))
		shutil.copy(fpath, javadir)

junitpath = getPath(data["test"])
if not os.path.exists(junitpath):
	sys.exit("Error: Junit file \"{0}\" does not exist".format(junitpath))

shutil.copy(junitpath, testdir)

submissions = os.listdir(submissionsdir)
for submission in submissions:
	fname, fext = os.path.splitext(submission)
	studentName, javaName, x = fname.split("_")
	print(studentName)
	studentNameStr = studentName.lower().replace(" ","_")
	report = Report(studentNameStr + ".txt")

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
	with file(os.path.join(submissionsdir, submission) ,"r") as f:
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
		newlines.append(line.replace(mainClass, data["name"]))
	
	# rename the file to match the lab name.
	with file(os.path.join(javadir, data["name"] + ".java"), "w") as f:
		f.writelines(newlines)

	# 
	# Compile and run	
	currdir = os.getcwd()
	print "building..."
	args = ["gradle", "build"]
	subprocess.call(args)
	junitFname = os.path.split(junitpath)[-1]
	junitName = os.path.splitext(junitFname)[0]
	# Parse the test results XML

	buildPath = os.path.join(currdir, "build")
	testResultsPath = os.path.join(buildPath, "test-results")
	buildReportPath = os.path.join(buildPath, "reports/")


	reportsdir = os.path.join(currdir,"reports")
	detaileddir = os.path.join(reportsdir, "detailed")
	# If "reports/detailed" directory does not exist, create it
	if not os.path.exists(detaileddir):
		os.makedirs(detaileddir)
	zipFile = os.path.join(detaileddir, studentNameStr + ".zip")
	args = ["zip", "-r", zipFile, buildReportPath]
	subprocess.call(args)

	print "cleaning..."
	args = ["gradle", "clean"]
	subprocess.call(args)
	
	junitResult = os.path.join(testResultsPath, "TEST-{0}.xml".format(junitName))
	if os.path.exists(junitResult):
		reportTestResults(report, junitResult)
	else:
		report.add("\tError: Could not find junit test results. Expected path: {0}".format(junitResult))
		report.flag()

	#TODO finsh up gradle integration. program has been migrated up till hre
	report.add("")


	#
	# crawl for functions
	# Look for "{" in each file and the first line of text that preceeds the line with "{"
	# (if the curly brace is not on its own line, the function prototype is in that line)
	# skip lines that start with words in the "ignoredKeyworkds" list. (not exhaustive)
	ignoredKeywords = ["for", "while", "try", "catch", "if", "then", "while", "do", "class"]

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
		if words[0] not in ignoredKeywords:
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
	if data["addSrc"]:
		report.add("")
		report.add("")
		report.add("-"*20)
		for line in lines:
			report.add(line)

	report.submit()
