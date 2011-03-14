import os
import sys

def main(argv):
	x = ""

	for i in range(len(argv)):
		x = x + argv[i] + " "

	#print x

	os.setpgid(os.getpid(), 0)

	#print "waiter_pid=" + str(os.getpid()) + " ; waiter_pgid=" + str(os.getpgrp())

	pip = os.popen(x)
	print pip.read()

if __name__ == "__main__":
	main(sys.argv[1:])
