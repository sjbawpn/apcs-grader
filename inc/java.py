import os

class JavaFile:
	package = ""
	lines = []
	comments = []
	mainClass = ""
	functions = []
	def __init__(self, source):
		print(source)
		fname, fext = os.path.splitext(source)
		if fext != ".java":
			raise TypeError("ERROR: File extension: {0}, expected: .java".format(fext))
		
		self.lines = []
		self.comments = []
		self.functions = []
		self.mainClass = ""
		with file(source ,"r") as f:
			self.lines = f.readlines()

		# 
		# find the package
		#
		for line in self.lines:
			line = line.strip()
			code = line.split("//")[0]
			if code.startswith("package"):
				packageLine = line.replace("package", "")
				packageLine = packageLine.replace(";", " ").strip()
				self.package = packageLine.split()[0]
			elif len(code) > 0:
				package = "" 
		#
		# find the main class name
		#
		#TODO A better way to parse the file is to create a class tree but that seems overkill for this project
		for line in self.lines:
			line = line.strip()
			code = line.split("//")[0]
			code = code.split("/*")[0] 
			code = code.split("*")[0]
			if self.mainClass == "" and "class" in code:
				prefix = code.split("{")[0]
				words = prefix.split()
				idx = words.index("class")
				if idx >= 0:
					self.mainClass = words[idx+1]
			if self.mainClass == "" and "interface" in code:
				prefix = code.split("{")[0]
				words = prefix.split()
				idx = words.index("interface")
				if idx >= 0:
					self.mainClass = words[idx+1]
			
		# Exit if the main class could not be determined	
		if self.mainClass == "":
			raise ValueError("ERROR: Could not determine main class name")
		#
		# crawl for functions
		# Look for "{" in each file and the first line of text that preceeds the line with "{"
		# (if the curly brace is not on its own line, the function prototype is in that line)
		# skip lines that start with words in the "ignoredKeyworkds" list. (not exhaustive)
		ignoredKeywords = ["for", "while", "try", "catch", "if", "then", "while", "do", "class"]

		i = 0;
		while i < len(self.lines):
			line = self.lines[i].strip()
			if line.startswith("//") or not "{" in line:
				i = i + 1
				continue	
			
			func = ""
			if line.startswith("{"):
				n = 1
				while i - n >= 0 and len(func) == 0:
					func = self.lines[i-n].strip()
					n = n + 1
			else:
				func = line.replace("{", "") # remove "{" for readability
			
			words = func.replace("("," ").split()
			if words[0] not in ignoredKeywords:
				self.functions.append(func)
			i = i + 1
	
		#
		# crawl for comments
		#TODO handle empty lines between comments and logic (basically skip them)
		#
		i = 0;
		while i < len(self.lines):
			line = self.lines[i].strip()
			# Single comments
			if "//" in line and not line.startswith("//"):
				comment = []
				if i > 0:
					comment.append("    " + self.lines[i-1])
				comment.append("--->" + self.lines[i])
				if i + 1 < len(self.lines):
					comment.append("    " + self.lines[i+1])
				self.comments.append(comment)
				i = i + 1
				continue
			
			# Block comments (//)
			comment = []
			while line.startswith("//"):
				comment.append(line)
				i = i + 1
				if i == len(self.lines):
					break
				line = self.lines[i].strip()
			if len(comment) > 0:
				if i + 1 < len(self.lines):
					comment.append(self.lines[i+1])
				self.comments.append(comment)
			#TODO handle /* */ comments
			i = i + 1
	
	def getLines(self):
		return self.lines
	def getFunctions(self):
		return self.functions
	def getComments(self):
		return self.comments	
	def getMainClass(self):
		return self.mainClass
	def getPackage(self):
		return self.package

	def write(self, path):
		packagedir = path
		if self.package != "":
			packageList = self.package.split(".")
			packagedir = os.path.join(packagedir, *packageList)
				
		if not os.path.exists(packagedir):
			os.makedirs(packagedir)

		# rename the file to match the class name.
		with file(os.path.join(packagedir, self.mainClass + ".java"), "w") as f:
			f.writelines(self.lines)
	
	def getFullName(self):
		if self.package == "":
			return self.mainClass
		else:
			return self.package + "." + self.mainClass
