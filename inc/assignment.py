import os

class Assignment:
	main = []
	tests = []
	support = []
	def __init__(self, main, support, tests):
		#TODO check input
		for fpath in main:
			if not os.path.exists(fpath):
				raise IOError("Error: Java file \"{0}\" does not exist".format(fpath))
		for fpath in support:
			if not os.path.exists(fpath):
				raise IOError("Error: Support file \"{0}\" does not exist".format(fpath))
		for fpath in tests:
			if not os.path.exists(fpath):
				raise IOError("Error: Test file \"{0}\" does not exist".format(fpath))


		self.main = list(main)
		self.support = list(support)
		self.tests = list(tests)
		
