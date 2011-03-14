### From: http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/435883

__all__ = ['makeRequests', 'NoResultsPending', 'NoWorkersAvailable',
  'ThreadPool', 'WorkRequest', 'WorkerThread']

__author__ = "Christopher Arndt"
__version__ = "1.1"
__date__ = "2005-07-19"

import threading, Queue
import time

import sys
import os

if "popen5" not in sys.path:
	sys.path.append("popen5")

if "utils/popen5" not in sys.path:
	sys.path.append("utils/popen5")

import subprocess
import cstats

rtLock = threading.Lock()
runningThreads = []
#TIMEOUT = 25.0 # seconds
TIMEOUT = 50000.0 # seconds
WDOGPERIOD = 15.0 # seconds

workerThreads = []
wtLock = threading.Lock()

LOGFILE_PREFIX = "##!#~@$@"
SUMMARY_PREFIX = "?@-#2!"

class NoResultsPending(Exception):
    """All work requests have been processed."""
    pass
class NoWorkersAvailable(Exception):
    """No worker threads available to process remaining requests."""
    pass

class WorkerThread(threading.Thread):
    """Background thread connected to the requests/results queues.

    A worker thread sits in the background and picks up work requests from
    one queue and puts the results in another until it is dismissed.
    """

    def __init__(self, requestsQueue, resultsQueue, stdoutlock, **kwds):
        """Set up thread in damonic mode and start it immediatedly.

	global wtLock, workerThreads

        requestsQueue and resultQueue are instances of Queue.Queue passed
        by the ThreadPool class when it creates a new worker thread.
        """
        threading.Thread.__init__(self, **kwds)
        self.setDaemon(1)
        self.workRequestQueue = requestsQueue
        self.resultQueue = resultsQueue
        self._dismissed = threading.Event()
        self.stdoutlock = stdoutlock

	self.stime = 0
	#self.stimeLock = threading.Lock()

	self.runningJob = 0	

	#print id(self)

	self.statsLock = threading.Lock()
	self.init_stats()

	wtLock.acquire()
	workerThreads.append(self)
	wtLock.release()

	self.testid = 0
	self.projectid = 0
	self.testerid = 0
	self.timediff = 0

        self.start()

    def init_stats(self):
        self.stats = { "Waiting_Time": cstats.CStats(bKeepValues = False, bAutoComputeStats = False), \
                       "Run_Time": cstats.CStats(bKeepValues = False, bAutoComputeStats = False), \
                       "Response_Time": cstats.CStats(bKeepValues = False, bAutoComputeStats = False), \
                       "Time_To_Job_Completion": cstats.CStats(bKeepValues = False, bAutoComputeStats = False), \
                       "Time_To_Job_Failure": cstats.CStats(bKeepValues = False, bAutoComputeStats = False) }

	self.lastOK = time.time()
	self.lastFailed = time.time()

    def get_stats(self):
	self.statsLock.acquire()
	x = self.stats
	t = (id(self), x, self.lastOK, self.lastFailed, self.testid, self.projectid, self.testerid, self.timediff)

	self.init_stats()

	self.statsLock.release()

	return t


    def run(self):
        """Repeatedly process the job queue until told to exit.
        """

        while not self._dismissed.isSet():
            # thread blocks here, if queue empty
            request = self.doSomething1()
            if self._dismissed.isSet() and request != None:
                # return the work request we just picked up
                self.gotDismissed(request)
                break # and exit
            # XXX catch exceptions here and stick them to request object
            self.doSomething2(request)

        self.doSomething2(None)

        #wtLock.acquire()
	#workerThreads.remove(self)
        #wtLock.release()

    def gotDismissed(self, x):
        self.workRequestQueue.put(x)

    def doSomething1(self):
	return self.workRequestQueue.get()

    def runningProcess(self, Command, app_times):
	global rtLock

	rtLock.acquire()
	self.pid = 0
	startTime = time.time()
	runningThreads.append((startTime, self))
	rtLock.release()

	app_times['start'] = time.time()
	app_times['threadid'] = id(self)
	process = subprocess.Popen(Command, stdout = subprocess.PIPE, stderr = subprocess.STDOUT,shell=True)
	self.pid = process.pid

	#retcode = -1

	try:
		retcode = process.wait()
	except:
		retcode = process.returncode

	app_times['exit'] = time.time()

	rtLock.acquire()
	runningThreads.remove((startTime, self))
	rtLock.release()

	# update stats

	self.statsLock.acquire()

	self.testid = app_times['testid']
	self.projectid = app_times['projectid']
	self.testerid = app_times['testerid']
	self.timediff = app_times['timediff']

	if (retcode == 0): # finished OK
		waitTime = 0.0
		respTime = app_times['exit'] - app_times['submit']
		runTime = respTime - waitTime
		ttjc = app_times['exit'] - self.lastOK

		if (ttjc < 0.0):
			ttjc = 0.0

		self.stats['Waiting_Time'].addValue(waitTime)
		self.stats['Response_Time'].addValue(respTime)
		self.stats['Run_Time'].addValue(runTime)
		self.stats['Time_To_Job_Completion'].addValue(ttjc)
		
		self.lastOK = app_times['exit']

	else: # failed
		ttjf = app_times['exit'] - self.lastFailed

		if (ttjf < 0):
			ttjf = 0.0

		self.stats['Time_To_Job_Failure'].addValue(ttjf)

		self.lastFailed = app_times['exit']

	self.statsLock.release()

	# get output

	try:
		output = process.stdout.read()
	except:
		output = ""

	return (retcode, output)

    def doSomething2(self, x):
	if (x == None):
		return None

	#print str(id(self)) + ": job=" + str(x)

	args = x.args[0]
	#print x.args
	#print args
	#print x.kwds
	args['runningProcess'] = self.runningProcess

	result = x.callable(*x.args, **x.kwds)

	#print str(id(self)) + ": job finished -> pid=" + str(process.pid) + " ; retcode=" + str(retcode) + " ; remaining output=" + self.process.stdout.read()

        self.resultQueue.put((x, result))

    def dismiss(self):
        """Sets a flag to tell the thread to exit when done with current job.
        """

        self._dismissed.set()
	
        self.stdoutlock.acquire()
        print str(id(self)) + ": being dismissed"
        self.stdoutlock.release()

class WatchDog(WorkerThread):

	def __init__(self, stdoutlock):
		#print "watchdog"
		WorkerThread.__init__(self, None, None, stdoutlock)
		self.resultList = []
		self.rlLock = threading.Lock()

	def gotDismissed(self, x):
		pass

	def doSomething1(self):
		# sleep
		time.sleep(WDOGPERIOD)

	def doSomething2(self, x):
		# do stuff
	
		# kill processes which have been running for too long
	
		global runningThreads, rtLock, TIMEOUT, workerThreads, wtLock

		rtLock.acquire()
		for item in runningThreads:
			stime = item[0]
			pid = item[1].pid

			if time.time() - stime > TIMEOUT:
				self.stdoutlock.acquire()
				print "[watchdog]: " + str(pid) + ": timeout-ed !"
				self.stdoutlock.release()

				#kill the bloody process :)
				killstr = "kill -s 9 -- -" + str(pid)

				self.stdoutlock.acquire()
				print "[watchdog] :" + killstr
				self.stdoutlock.release()

				pip = os.popen(killstr)

				self.stdoutlock.acquire()
				print "[watchdog]: " + pip.read()
				self.stdoutlock.release()

		rtLock.release()

		# get the results from the worker threads

		wtLock.acquire()

		self.stdoutlock.acquire()
		print "[watchdog] Gathering Data"
		self.stdoutlock.release()

		for wth in workerThreads:
			if (wth != self):
				xid, stats, lOK, lFailed, testid, projectid, testerid, timediff = wth.get_stats()
				ctime = time.time()

				if (stats['Time_To_Job_Completion'].NItems + stats['Time_To_Job_Failure'].NItems) > 0:
					# report stats

					for k,v in stats.items():
						v.doComputeStats()
						total = v.Sum

						if (k == 'Time_To_Job_Completion'):
							total = total + ctime - lOK
						elif (k == 'Time_To_Job_Failure'):
							total = total + ctime - lFailed

						sLine = "\n" + LOGFILE_PREFIX + SUMMARY_PREFIX + "\1" + str(testid) + "\1" + str(projectid) + "\1" + str(testerid) + "\1" + str(xid) + \
							"\1" + k + "\1" + str(ctime + float(timediff)) + "\1" + str(v.Min) + "\1" + str(v.Max) + \
							"\1" + str(v.Avg) + "\1" + str(v.StdDev) + "\1" + str(v.COV) + "\1" + str(v.NItems) + "\1" + str(total) + "\n"
					
						self.stdoutlock.acquire()
						sys.stdout.write(sLine)
						self.stdoutlock.release()

		self.stdoutlock.acquire()
		print "[watchdog] Gathered data"
		self.stdoutlock.release()

		wtLock.release()

class WorkRequest:
    """A request to execute a callable for putting in the request queue later.

    See the module function makeRequests() for the common case
    where you want to build several work requests for the same callable
    but different arguments for each call.
    """

    def __init__(self, callable, args=None, kwds=None, requestID=None,
      callback=None):
        """A work request consists of the a callable to be executed by a
        worker thread, a list of positional arguments, a dictionary
        of keyword arguments.

        A callback function can be specified, that is called when the results
        of the request are picked up from the result queue. It must accept
        two arguments, the request object and it's results in that order.
        If you want to pass additional information to the callback, just stick
        it on the request object.

        requestID, if given, must be hashable as it is used by the ThreadPool
        class to store the results of that work request in a dictionary.
        It defaults to the return value of id(self).
        """
        if requestID is None:
            self.requestID = id(self)
        else:
            self.requestID = requestID
        self.callback = callback
        self.callable = callable
        self.args = args or []
        self.kwds = kwds or {}


class ThreadPool:
    """A thread pool, distributing work requests and collecting results.

    See the module doctring for more information.
    """

    def __init__(self, num_workers, stdoutlock, q_size=0):
        """Set up the thread pool and start num_workers worker threads.

        num_workers is the number of worker threads to start initialy.
        If q_size > 0 the size of the work request is limited and the
        thread pool blocks when queue is full and it tries to put more
        work requests in it.
        """

        self.requestsQueue = Queue.Queue(q_size)
        self.resultsQueue = Queue.Queue()
        self.workers = []
        self.workRequests = {}
        self.stdoutlock = stdoutlock
        self.createWorkers(num_workers)

	self.wdog = WatchDog(self.stdoutlock)

    def createWorkers(self, num_workers):
        """Add num_workers worker threads to the pool."""

        for i in range(num_workers):
            self.workers.append(WorkerThread(self.requestsQueue,
              self.resultsQueue, self.stdoutlock))

    def dismissWorkers(self, num_workers):
        """Tell num_workers worker threads to to quit when they're done."""

        for i in range(min(num_workers, len(self.workers))):
            worker = self.workers.pop()
            worker.dismiss()

    def putRequest(self, request):
        """Put work request into work queue and save for later."""

        self.requestsQueue.put(request)
        self.workRequests[request.requestID] = request

    def poll(self, block=False):
        """Process any new results in the queue."""
        while 1:
            try:
                # still results pending?
                if not self.workRequests:
                    raise NoResultsPending
                # are there still workers to process remaining requests?
                elif block and not self.workers:
                    raise NoWorkersAvailable
                # get back next results
                request, result = self.resultsQueue.get(block=block)
                # and hand them to the callback, if any
                if request.callback:
                    request.callback(request, result)

                del self.workRequests[request.requestID]
            except Queue.Empty:
                break

    def wait(self):
        """Wait for results, blocking until all have arrived."""

        while 1:
            try:
                self.poll(True)
            except NoResultsPending:
                break

        self.wdog.dismiss()
        self.wdog.join()

def makeRequests(callable, args_list, callback=None):
    """Convenience function for building several work requests for the same
    callable with different arguments for each call.

    args_list contains the parameters for each invocation of callable.
    Each item in 'argslist' should be either a 2-item tuple of the list of
    positional arguments and a dictionary of keyword arguments or a single,
    non-tuple argument.

    callback is called when the results arrive in the result queue.
    """

    requests = []
    for item in args_list:
        if item == isinstance(item, tuple):
            requests.append(
              WorkRequest(callable, item[0], item[1], callback=callback))
        else:
            requests.append(
              WorkRequest(callable, [item], None, callback=callback))
    return requests


################
# USAGE EXAMPLE
################

if __name__ == '__main__':
    import random
    import time

    # the work the threads will have to do (rather trivial in our example)
    def do_something(data):
        #time.sleep(random.randint(1,5))
        #return round(random.random() * data, 5)
	
	startTime = time.time()
	#process = subprocess.Popen(["python", "../waiter.py", "sleep", "122"], executable="python", stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
	
	result = {}

	(retcode, output) = data['runningProcess'] ("sleep 122", result)

	result = {}
	result['returncode'] = retcode
	result['output'] = output

	return result

    # this will be called each time a result is available
    def print_result(request, result):
        print "Result: %s from request #%s" % (result, request.requestID)

    # assemble the arguments for each job to a list...
    data = [{ 'garbage': random.randint(1,10)} for i in range(20)]
    # ... and build a WorkRequest object for each item in data
    requests = makeRequests(do_something, data, print_result)

    # we create a pool of 10 worker threads
    main = ThreadPool(3, threading.Lock())

    # then we put the work requests in the queue...
    for req in requests:
        main.putRequest(req)
        print "Work request #%s added." % req.requestID
    # or shorter:
    # [main.putRequest(req) for req in requests]

    # ...and wait for the results to arrive in the result queue
    # wait() will return when results for all work requests have arrived
    # main.wait()

    # alternatively poll for results while doing something else:
    i = 0
    while 1:
        try:
            main.poll()
            print "Main thread working..."
            time.sleep(0.5)
            if i == 10:
                print "Adding 3 more worker threads..."
                main.createWorkers(3)
            i += 1
        except (KeyboardInterrupt, NoResultsPending):
            break