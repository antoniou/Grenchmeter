
import sys
import os
import time

def main(argv):
	if (len(argv) < 1):
		cnt = 20
	cnt = int(argv[0])

	print "pid=" + str(os.getpid()) + " pgid=" + str(os.getpgrp())

	if (cnt > 0):
		print "spawning new child"

		for i in range(1, 4096):
			print "x"

		pip = os.popen("python ../exec_wrapper.py " + str(cnt - 1))
		print pip.read(15)

	time.sleep(0.2)

if __name__ == "__main__":
	main(sys.argv[1:])