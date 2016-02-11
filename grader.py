#!/usr/bin/python

from inc.assignment import Assignment
from inc.report import Report
from inc.java import JavaFile
import inc.common as common
import os
import shutil
import sys
from optparse import OptionParser
import subprocess
import json
from pprint import pprint
from xml.dom import minidom
from zipfile import ZipFile
from zipfile import ZIP_DEFLATED
from glob import glob
##
#    Helper function to resolve a given path
##
def getPath(path, root=None):
    if root is None:
        root = os.getcwd()
    result = path
    if not os.path.isabs(result):
        result = os.path.join(root, result)
    return result

##
#    Helper function to report function test results
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
#    Helper function to report code style test results
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
            if "column" in error.attributes.keys():
                column = error.attributes["column"].value
            severity = error.attributes["severity"].value
            message = error.attributes["message"].value
            # source = error.attributes["source"].value # (Unused)
            if "column" in error.attributes.keys():
                report.add("\t\t{0}: {1} in line:{2}, column:{3}".format(severity.capitalize(),message,line,column))
            else:
                report.add("\t\t{0}: {1} in line:{2}".format(severity.capitalize(),message,line))
        i = i + 1

##
#    Main
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

jsondir = os.path.split(jsonpath)[0]

##
# Initialize
##

gradledir = os.path.abspath(common.gradle_path)
submissionsdir = os.path.join(currdir,"submissions") # directory where submissions will be placed
srcdir = os.path.join(currdir, "src") # directory where the assignments will be compiled, run and unit tested 1 by 1.
javadir = os.path.join(srcdir,"main","java")
testdir = os.path.join(srcdir,"test","java")
reportsdir = os.path.join(currdir,"reports")
detaileddir = os.path.join(reportsdir, "detailed")

# Install gradle if it does not exist
if not os.path.exists(os.path.abspath(common.gradle_path)):
    common.install_gradle(currdir)
    
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

# check reports directory already exit
if os.path.exists(reportsdir):
    delete = raw_input("reports directory exists and must be deleted before proceding. Do you wish to delete it (Y, N)? Y: ")
    if delete.lower() != "n":
        shutil.rmtree(reportsdir)
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
    testFiles = testFiles + glob(f)
testFiles = list(set(testFiles))
#create absolute file
testFiles = [getPath(x, root = jsondir) for x in testFiles]

##
# Parse support files
##
supportFiles = []
if "support" in data:
    for f in data["support"]:
        supportFiles = supportFiles + glob(f)
# remove duplicates
supportFiles = list(set(supportFiles))
#create absolute file
supportFiles = [getPath(x, root = jsondir) for x in supportFiles]

# Handle moodle assignment
if assignmentType == "moodle":
    if "submissions" not in data:
         sys.exit("Error: Assignment type is \"moodle\" but \"submissions\" was not defined")
    submissions = data["submissions"]
    if submissions[-1] == "*":
        submissions = submissions + ".zip"
    submissions = glob(submissions)
    if len(submissions) == 0:
        sys.exit("Error: {0} could not resolve to valid file".format(data["submissions"]))
    if len(submissions) > 1:
        print("Warning: multiple files were resolved. Using the first one: {0}".format(submissions[0]))
    submissions = getPath(submissions[0], root = jsondir)
    if not os.path.exists(submissions):
        sys.exit("Error: {0} does not exist".format(submissions))
    if not os.path.splitext(submissions)[1] == ".zip":
        sys.exit("Error: {0} not a zip file".format(submissions))
    
    # Extract
    with ZipFile(submissions, 'r') as archive:
        archive.extractall(submissionsdir)
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
         parser.error("Assignment type is \"default\" but \"submissions\" was not defined")
    javaFiles = []
    for submission in data["submissions"]:
        javaFiles = javaFiles + glob(submission)
    # remove duplicates
    javaFiles = list(set(javaFiles))
    # create absolute file
    javaFiles = [getPath(x, root = jsondir) for x in javaFiles]
    
    # Copy files to submissions dir
    for javaFile in javaFiles:
        fname = os.path.split(javaFile)[-1]
        shutil.copyfile(javaFile, os.path.join(submissionsdir,fname))

    assignments["default"] = Assignment(javaFiles, supportFiles, testFiles)

for name in assignments.keys():
    done = False
    if os.path.exists(srcdir):
        shutil.rmtree(srcdir)
    os.makedirs(javadir)
    os.makedirs(testdir)
    print(name)
    reportName = name.lower().replace(" ","_")
    report = Report(reportName + ".txt", data["verbose"])
    assignment = assignments[name]
    
    package = None
    packagedir = ""
    # Handle submission
    javaFiles = []
    resourceFiles = []
    for submission in assignment.main:
        if os.path.splitext(submission)[-1].lower() == ".java":
            javaFiles.append(submission)
        else:
            resourceFiles.append(submission)

    if len(javaFiles) == 0:
        report.add("Error: No java files found for submission: {0}".format(name))
        report.flag()
        report.submit()
        continue
        
    filesToGrade = []
    
    try:
        for file in javaFiles:
            javaFile = JavaFile(file)
            if package == None:
                package = javaFile.getPackage()
                packagedir = javaFile.getPackagePath()
            elif package != javaFile.getPackage():
                report.add("Error: Package name:{0} does not match a previously resolved package name: {1}".format(javaFile.getPackage(), package))
                javaFile.setPackage(package)
            javaFile.write(javadir)
            filesToGrade.append(javaFile)
    except (TypeError, ValueError) as err:
        report.add(str(err))
        report.flag()
        report.submit()
        continue
    
    for file in resourceFiles:
        path = os.path.join(javadir, packagedir)
        if not os.path.exists(path):
            os.makedirs(path)
        
        fname = os.path.split(file)[-1]
        shutil.copyfile(file, os.path.join(path,fname))
               
    # Copy support files
    javaFiles = []
    resourceFiles = []
    
    # Seperate java files from the rest of the files
    for submission in assignment.support:
        if os.path.splitext(submission)[-1].lower() == ".java":
            javaFiles.append(submission)
        else:
            resourceFiles.append(submission)  
    try:
        for file in javaFiles:
            javaFile = JavaFile(file)
            if javaFile.getPackage() != package:
                javaFile.setPackage(package)
            javaFile.write(javadir)
    except (TypeError, ValueError) as err:
        report.add(str(err))
        report.flag()
        report.submit()
        continue
    
    for file in resourceFiles:
        path = os.path.join(javadir, packagedir)
        if not os.path.exists(path):
            os.makedirs(path)
        
        fname = os.path.split(file)[-1]
        shutil.copyfile(file, os.path.join(path,fname))
    
    # Copy test files
    javaFiles = []
    resourceFiles = []
    junitNames = []
    
     # Seperate java files from the rest of the files
    for submission in assignment.tests:
        if os.path.splitext(submission)[-1].lower() == ".java":
            javaFiles.append(submission)
        else:
            resourceFiles.append(submission)
    
    try:        
        for file in javaFiles:  
            javaFile = JavaFile(file)
            if javaFile.getPackage() != package:
                javaFile.setPackage(package)
            javaFile.write(testdir)
            junitNames.append(javaFile.getFullName())
    except (TypeError, ValueError) as err:
        report.add(str(err))
        report.flag()
        report.submit()
        continue
        
    for file in resourceFiles:
        path = os.path.join(testdir, packagedir)
        if not os.path.exists(path):
            os.makedirs(path)
        
        fname = os.path.split(file)[-1]
        shutil.copyfile(file, os.path.join(path,fname))
            
    ## 
    #     Compile and run
    ##
    currdir = os.getcwd()
    print "building..."
    gradle = os.path.join(gradledir, "bin","gradle")
    if os.name == "nt":
        gradle = gradle + ".bat"
    args = [gradle, "build"]
    retcode = subprocess.call(args)
    if retcode == 0:
        buildPath = os.path.join(currdir, "build")
        testResultsPath = os.path.join(buildPath, "test-results")
        buildReportPath = os.path.join(buildPath, "reports")
        styleReportPath = os.path.join(buildReportPath, "checkstyle")

        # If "reports/detailed" directory does not exist, create it
        if not os.path.exists(detaileddir):
            os.makedirs(detaileddir)
        
        dir = os.path.join(buildPath, "reports")
        zipF = os.path.join(detaileddir, reportName + ".zip")
        with ZipFile(zipF, 'w') as zip:
            for root, dirs, files in os.walk(dir):
                abs_root = os.path.abspath(root)
                relative_root = abs_root[len(buildPath):]
                for f in files:
                    fullpath = os.path.join(abs_root, f)
                    archive_name = os.path.join(relative_root,f)
                    zip.write(fullpath, archive_name, ZIP_DEFLATED)
        
        # Copy src
        zipF = os.path.join(detaileddir, reportName + ".zip")
        with ZipFile(zipF, 'a') as zip:
            for root, dirs, files in os.walk(srcdir):
                abs_root = os.path.abspath(root)
                relative_root = abs_root[len(srcdir):]
                for f in files:
                    fullpath = os.path.join(abs_root, f)
                    archive_name = os.path.join(relative_root,f)
                    zip.write(fullpath, archive_name, ZIP_DEFLATED)
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
    #     Clean build
    ##
    print "cleaning..."
    args = [gradle, "clean"]
    subprocess.call(args)    

    ##
    #    Submission report
    ##

    for javaFile in filesToGrade:
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
