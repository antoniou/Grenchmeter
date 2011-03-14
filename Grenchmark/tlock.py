
import thread
import threading
import time

value = 0
glock = threading.Lock()

class RWThread(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)
		self.dismissed = threading.Event()
		self.count = 0

	def run(self):
		while 1:
			if (self.dismissed.isSet()):
				break
			else:
				self.doStuff()
	
	def dismiss(self):
		self.dismissed.set()

	def doStuff(self):
		pass

class Reader(RWThread):
	def doStuff(self):
		global value, glock

		#time.sleep(0.1)
		#glock.acquire()
		x = value
		#glock.release()
		self.count = self.count + 1

class Writer(RWThread):
	def doStuff(self):
		global value, glock
		#glock.acquire()
		value = value + 1
		#glock.release()
		self.count = self.count + 1

r = Reader()
w = Writer()

r.start()
w.start()

time.sleep(10)

r.dismiss()
w.dismiss()

r.join()
w.join()

print str(r.count) + " reads ;" + str(w.count) + " writes"
