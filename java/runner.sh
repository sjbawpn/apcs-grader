#!/bin/bash

src="SET YOUR SOURCE FILE HERE"

# Set your junit_path below and testHelp path below
junit_path=/usr/share/java/junit4.jar
testHelp_path=/usr/share/java/testHelp.jar

javac -cp .:$junit_path:/$testHelp_path $src TestJunit.java  TestRunner.java
java -cp .:/$junit_path:/$testHelp_path TestRunner
