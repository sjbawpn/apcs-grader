#!/usr/bin/python
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

def getPath(path):
	currdir = os.getcwd()
	result = path
	if not os.path.isabs(result):
		result = os.path.join(currdir, result)
	return result

def reportTestResults(report, results):
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

def reportStyleResults(report, results):
	report.add("------ Style Results -----")
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

reportsdir = os.path.join(currdir,"reports")
detaileddir = os.path.join(reportsdir, "detailed")


submissions = os.listdir(submissionsdir)
students = []
for submission in submissions:
	fname, fext = os.path.splitext(submission)
	studentName, javaName, x = fname.split("_")
	if studentName not in students:
		students.append(studentName)
javaFiles = {}
for student in students:
	javaFiles[student] = [submission for submission in submissions if submission.startswith(student)]
		
for student in students:
	print(student)
	studentNameStr = student.lower().replace(" ","_")
	report = Report(studentNameStr + ".txt", data["verbose"])
	submissions = javaFiles[student]
	for submission in submissions:
		fname, fext = os.path.splitext(submission)
		studentName, javaName, x = fname.split("_")

		submissionFile = os.path.join(submissionsdir, submission)
		try:
			javaFile = JavaFile(submissionFile)
		except (TypeError, ValueError) as err:
			report.add(str(err))
			report.flag()
			report.submit()
			continue

		# re-write the source file in a more script friendly way.
		newlines = []
		for line in javaFile.getLines():
			# Comment out the package name (everything will be in the default package for now)
			if line.startswith("package"):
				line = "//" + line
			newlines.append(line)
	
		# rename the file to match the class name.
		with file(os.path.join(javadir, javaFile.getMainClass() + ".java"), "w") as f:
			f.writelines(newlines)
		issues = []
		# Issue checker: If source file name does not match the class
		if not javaFile.getMainClass() == javaName:
			issues.append("Java file name: \"{0}\" does not match class name : \"{1}\"!".format(javaName, javaFile.getMainClass()))
		report.add(" **************** " + javaFile.getMainClass() + ".java *************")
		# Report on the issues
		if len(issues) > 0:
			report.add("------ !! ISSUES !! -----")
			for issue in issues:
				report.add("\t" + issue)

		report.add("------ Main class -----")
		report.add("\tName = {0}".format(javaFile.getMainClass()))

		# Report on the functions
		report.add("")
		report.add("------ FUNCTIONS ----- (count={0})".format(len(javaFile.getFunctions())))
		i = 1
		for function in javaFile.getFunctions():
			report.add("\t-function {0}:".format(i))
			report.add("\t\t"+function.strip())
			i = i + 1

		# Report on the comments
		report.add("")
		report.add("------ COMMENTS ----- (count={0})".format(len(javaFile.getComments())))
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
			report.add("-"*20)
			for line in javaFile.getLines():
				report.add(line)

	# 
	# Compile and run	
	currdir = os.getcwd()
	print "building..."
	args = ["gradle", "build"]

	retcode = subprocess.call(args)
	if retcode == 0:
		junitFname = os.path.split(junitpath)[-1]
		junitName = os.path.splitext(junitFname)[0]

		buildPath = os.path.join(currdir, "build")
		testResultsPath = os.path.join(buildPath, "test-results")
		buildReportPath = os.path.join(buildPath, "reports/")
		styleReportPath = os.path.join(buildReportPath, "checkstyle")

		# If "reports/detailed" directory does not exist, create it
		if not os.path.exists(detaileddir):
			os.makedirs(detaileddir)
		zipFile = os.path.join(detaileddir, studentNameStr + ".zip")
		args = ["zip", "-r", zipFile, buildReportPath]
		subprocess.call(args)

		# Parse the test results XML
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
		report.add("Error building the project!")
		report.flag()

	report.add("")

	# Clean build
	print "cleaning..."
	args = ["gradle", "clean"]
	subprocess.call(args)	

	report.submit()
	sys.exit()
