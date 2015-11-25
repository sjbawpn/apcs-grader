#!/usr/bin/python

from inc.assignment import Assignment
from inc.report import Report
from inc.java import JavaFile
import os
import shutil
import sys
from optparse import OptionParser
import subprocess
import json
from pprint import pprint
from xml.dom import minidom
##
#	Helper function to resolve a given path
##
def getPath(path):
	currdir = os.getcwd()
	result = path
	if not os.path.isabs(result):
		result = os.path.join(currdir, result)
	return result

##
#	Helper function to report function test results
##
def reportTestResults(report, results):
	report.addTitle("Functional Results")
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

##
#	Helper function to report code style test results
##
def reportStyleResults(report, results):
	report.addTitle("Style Results")
	xmldoc = minidom.parse(results)
	files = xmldoc.getElementsByTagName("file")
	i = 1
	for f in files:
		name = f.attributes["name"].value
		errors = f.getElementsByTagName("error")
		status = "Passed"
		if len(errors) > 0:
			status = "Failed"
		report.add("\t{0}- \"{1}\" : {2}!".format(i, name, status))

		for error in errors:
			line = error.attributes["line"].value
			column = error.attributes["column"].value
			severity = error.attributes["severity"].value
			message = error.attributes["message"].value
			# source = error.attributes["source"].value # (Unused)
			report.add("\t\t{0}: {1} in line:{2}, column:{3}".format(severity.capitalize(),message,line,column))
		i = i + 1

##
#	Main
##
parser = OptionParser()
parser.add_option("-c", "--config", dest="config", help="assignment config file name (default=assignment.json)", default="assignment.json", metavar="CONFIG")

(options, args) = parser.parse_args()

currdir = os.getcwd()

jsonpath = getPath(options.config)
if not os.path.exists(jsonpath):
	parser.error("Could not determine json path")
with open(jsonpath) as f:
	data = json.load(f)

##
# Initialize
##
submissionsdir = os.path.join(currdir,"submissions") # directory where submissions will be placed
srcdir = os.path.join(currdir, "src") # directory where the assignments will be compiled, run and unit tested 1 by 1.
javadir = os.path.join(srcdir,"main","java")
testdir = os.path.join(srcdir,"test","java")

# check submissions directory already exit
if os.path.exists(submissionsdir):
	delete = raw_input("submissions directory exists and must be deleted before proceeding. Do you wish to delete it (Y, N)? Y: ")
	if delete.lower() != "n":
		shutil.rmtree(submissionsdir)
	else:
		sys.exit("Program terminated")
os.mkdir(submissionsdir)

# check src directory already exit
srcdir = os.path.join(currdir, "src")
if os.path.exists(srcdir):
	delete = raw_input("src directory exists and must be deleted before proceding. Do you wish to delete it (Y, N)? Y: ")
	if delete.lower() != "n":
		shutil.rmtree(srcdir)
	else:
		sys.exit("Program terminated")

##
# Parse JSON file
##
assignmentType = "default"
assignments = {}
if "type" in data:
	assignmentType = data["type"]

##
# Parse test files
##
if "tests" not in data:
	sys.exit("Error: \"tests\" section missing in config. No unit tests defined")

testFiles = []
for f in data["tests"]:
	testFiles.append(getPath(f))

##
# Parse support files
##
supportFiles = []
if "supportFiles" in data:
	for f in data["supportFiles"]:
		supportFiles.append(getPath(f))

# Handle moodle assignment
if assignmentType == "moodle":
	if "zip" not in data:
		 parser.error("Assignment type is \"moodle\" but \"zip\" was not defined".format(zippath))
	zippath = getPath(data["zip"])
	if not os.path.exists(zippath):
		 parser.error("{0} does not exist".format(zippath))
	if not os.path.splitext(zippath)[1] == ".zip":
		parser.error("{0} not a zip file".format(zippath))
	args = ["unzip","-d", submissionsdir, zippath]
	subprocess.call(args)
	submissions = os.listdir(submissionsdir)
	students = []
	for submission in submissions:
		fname, fext = os.path.splitext(submission)
		studentName, javaName, x = fname.split("_")
		if studentName not in students:
			students.append(studentName)
	for student in students:
		javaFiles = [os.path.join(submissionsdir,submission) for submission in submissions if submission.startswith(student)]
		assignments[student] = Assignment(javaFiles, supportFiles, testFiles)
# Handle individual submissions (default)
elif assignmentType == "default":
	if "submissions" not in data:
		 parser.error("Assignment type is \"default\" but \"submissions\" was not defined".format(zippath))
	for submission in data["submissions"]:
		fname = os.path.split(submission)[-1]
		shutil.copyfile(submission, os.path.join(submissionsdir,fname))
	javaFiles = data["submissions"]
	assignments["default"] = Assignment(javaFiles, supportFiles, testFiles)


reportsdir = os.path.join(currdir,"reports")
detaileddir = os.path.join(reportsdir, "detailed")

for name in assignments.keys():
	if os.path.exists(srcdir):
		shutil.rmtree(srcdir)
	os.makedirs(javadir)
	os.makedirs(testdir)
	print(name)
	reportName = name.lower().replace(" ","_")
	report = Report(reportName + ".txt", data["verbose"])
	assignment = assignments[name]
	
	# Copy support files
	for support in assignment.support:
		try:
			javaFile = JavaFile(support)
			javaFile.write(javadir)
		except (TypeError, ValueError) as err:
			report.add(str(err))
			report.flag()
			report.submit()

	# Copy test files
	junitNames = []
	for test in assignment.tests:
		try:
			javaFile = JavaFile(test)
			javaFile.write(testdir)
			junitNames.append(javaFile.getFullName())
		except (TypeError, ValueError) as err:
			report.add(str(err))
			report.flag()
			report.submit()

	# Handle submission
	submissionFiles = []
	for submission in assignment.main:
		try:
			javaFile = JavaFile(submission)
			javaFile.write(javadir)
			submissionFiles.append(javaFile)
		except (TypeError, ValueError) as err:
			report.add(str(err))
			report.flag()
			report.submit()

	## 
	#	 Compile and run
	##
	currdir = os.getcwd()
	print "building..."
	args = ["gradle", "build"]

	retcode = subprocess.call(args)
	if retcode == 0:
		buildPath = os.path.join(currdir, "build")
		testResultsPath = os.path.join(buildPath, "test-results")
		buildReportPath = os.path.join(buildPath, "reports/")
		styleReportPath = os.path.join(buildReportPath, "checkstyle")

		# If "reports/detailed" directory does not exist, create it
		if not os.path.exists(detaileddir):
			os.makedirs(detaileddir)
		zipFile = os.path.join(detaileddir, reportName + ".zip")
		args = ["zip", "-r", zipFile, buildReportPath]
		subprocess.call(args)

		# Parse the test results XML
		for junitName in junitNames:
			junitResult = os.path.join(testResultsPath, "TEST-{0}.xml".format(junitName))
			if os.path.exists(junitResult):
				reportTestResults(report, junitResult)
			else:
				report.add("\tError: Could not find junit test results. Expected path: {0}".format(junitResult))
				report.flag()
		
		styleResult = os.path.join(styleReportPath, "main.xml")
		if os.path.exists(styleResult):
			reportStyleResults(report, styleResult)
		else:
			report.add("\tError: Could not find  checkstyle results. Expected path: {0}".format(styleResult))
			report.flag()

	else:
		report.addTitle("ERROR")
		report.add("Error building the project!")
		report.flag()

	##
	# 	Clean build
	##
	print "cleaning..."
	args = ["gradle", "clean"]
	subprocess.call(args)	

	##
	#	Submission report
	##

	for javaFile in submissionFiles:
		report.addTitle(javaFile.getMainClass()+".java")

		report.add("Main Class name = {0}".format(javaFile.getMainClass()))

		# Report on the functions
		report.add("")
		report.addHeader("Functions (count={0})".format(len(javaFile.getFunctions())))
		i = 1
		for function in javaFile.getFunctions():
			report.add("\t-function {0}:".format(i))
			report.add("\t\t"+function.strip())
			i = i + 1

		# Report on the comments
		report.add("")
		report.addHeader("Comments (count={0})".format(len(javaFile.getComments())))
		i = 1
		for comment in javaFile.getComments():
			report.add("\t-Comment {0}:".format(i))
			for line in comment:
				report.add("\t\t"+line.strip())
			i = i + 1
	
		# If enabled, append the source code to the end of the report.
		if data["addSrc"]:
			report.add("")
			report.add("")
			report.addHeader("Source")
			for line in javaFile.getLines():
				report.add(line)


	report.submit()

if os.path.exists(srcdir):
	shutil.rmtree(srcdir)
