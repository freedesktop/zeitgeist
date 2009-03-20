## Copyright (C) 2004  Julien Herbin

## This program is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License
## as published by the Free Software Foundation; either version 2
## of the License, or (at your option) any later version.

## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.

## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.

## Julien Herbin <julien@ecranbleu.org>

import threading
import time

class ThreadPool(threading.Thread):
	"""
	This class is a Thread pool manager. Tasks to perform must inherit the
	ThreadPoolTask class defined later.
	The pool size can be specified to the constructor. The default value is 4.
	It determines the number of tasks to execute work concurrently.
	"""
	
	
	def __init__(self, pool_size=4, check_freed_thread_every = 0.5, name=None, verbose=False):
		"""ThreadPool constructor"""
		threading.Thread.__init__(self, target=self.__run, name=name, args=())
		self.__pool_size = pool_size
		self.__stop = 0
		self.__tasks_queued=[]
		self.__tasks_running=[]
		self.__check_freed_thread_every = check_freed_thread_every
		self.__next_task_nb = 1
		self.__verbose = verbose
		return
	
	def __len__(self):
		"""
		Queue length 
		"""
		return len(self.__tasks_queued) + len(self.__tasks_running)

	def __run(self):
		"""Main method call with start since ThreadPool extends threading.Thread"""
		while not (self.__stop and len(self) == 0) :
			time.sleep(self.__check_freed_thread_every)
			if self.__verbose==True:
				print self.queueSize(), " task(s) queued."
				print self.nbTasksRunning(), " task(s) running."

			# Check if some tasks ended
			for task in self.__tasks_running:
				if not task.isAlive():
					self.__tasks_running.remove(task)
					if self.__verbose==True:
						print "Task : " + task.__str__() + " terminated."
					
			# If pool is not empty, run new tasks until it is or no task queued
			while self.nbTasksRunning() < self.__pool_size and not self.queueEmpty():
				task_to_run = self.__getNextTask()
				task_to_run.setTaskName(self.__next_task_nb)
				self.__next_task_nb += 1
				self.__tasks_running.append(task_to_run)
				task_to_run.initThread()
				task_to_run.start()
			
			if not self.queueEmpty():
				if self.__verbose==True:
					print "Some tasks are queued, but pool is empty... waiting..."
	
	def queueSize(self):
		return len(self.__tasks_queued)
	
	def queueEmpty(self):
		return self.queueSize() == 0

	def nbTasksRunning(self):
		return len(self.__tasks_running)
	
	def taskRunning(self):
		return self.nbTasksRunning()!=0
	
	def addTask(self, task,priority = 10):
		if isinstance(task, ThreadPoolTask):
			self.__tasks_queued.append([task,priority])
			return 1
		else:
			return 0
	
	def __getNextTask(self):
		"""
		This method browse the tasks_queued array and check which process
		is the most urgent ! (ie with the biggest priority)
		"""
		if self.queueSize() != 0:
			prioMax=0
			for task in self.__tasks_queued:
				if task[1] > prioMax:
					prioMax = task[1]
					priotaryTask = task
			self.__tasks_queued.remove(priotaryTask)
			return priotaryTask[0]
		else:
			return None
	
	def terminate(self):
		self.__stop = 1


class ThreadPoolTask(threading.Thread):
	def __init__(self, task_nb = " name unset"):
		self.setTaskName(task_nb)
		return

	def initThread(self):
		threading.Thread.__init__(self, target=self.run, name= self.getTaskName(), args=())
	
	def setTaskName(self, task_nb):
		self.task_name = "Task " + str(task_nb)
		return

	def getTaskName(self):
		return self.task_name

	def _action():
		pass

	def run(self):
		self._action()
		

class MyLongTask(ThreadPoolTask):
	""" This class is here for tests """
	def __init__(self, intMax):
		ThreadPoolTask.__init__(self)
		self.intMax = intMax

	def _action(self):
		print "Starting MyLongTask : intMax = ", self.intMax
		self.intArithmetic()
		print "MyLongTask Ended : intMax = ", self.intMax

	def intArithmetic(self):
		"""
		From the code found at http://www.ocf.berkeley.edu/~cowell/research/benchmark/code/Benchmark.py
		"""
		startTime = time.clock()
		
		i = 1
		intResult = 1
		while i < self.intMax:
			intResult = intResult - i
			i = i + 1
			intResult = intResult + i
			i = i + 1
			intResult = intResult * i
			i = i + 1
			intResult = intResult / i
			i = i + 1

		stopTime = time.clock()
		elapsedTime = (stopTime - startTime) * 1000 # convert from secs to millisecs.
		print "Int arithmetic elapsed time:", elapsedTime, "ms with intMax of", intMax
		
		print " i:", i
		print " intResult:", intResult
		return elapsedTime


if __name__ == "__main__":
	intMax = 500000
	mytask1 = MyLongTask(intMax/2)
	mytask2 = MyLongTask(intMax)
	mytask3 = MyLongTask(intMax*1.5)
	mytask4 = MyLongTask(intMax/2+43)
	mytask5 = MyLongTask(intMax-1)
	tp = ThreadPool(2, verbose=True)
	tp.addTask(mytask2, 2)
	tp.addTask(mytask3, 7)
	tp.addTask(mytask1, 1)
	tp.addTask(mytask4, 9)
	tp.addTask(mytask5, 6)
	tp.start()
	time.sleep(2)
	mytask6 = MyLongTask(300000)
	mytask7 = MyLongTask(intMax-1)
	tp.addTask(mytask6, 4)
	tp.addTask(mytask7, 20)
	tp.terminate()
	print "Main program ended"
