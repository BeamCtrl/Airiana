#!/usr/bin/python
import threading
import numpy
def mean(data):
	sum=0
	for each in data:
		sum+= each
	return sum/len(data)
def stddev(data):
	ave =  mean(data)
	dev = int()
	for each in data:
		dev += (each-ave)**2
	return ave, numpy.sqrt(dev/len(data))
class threaded_mean(threading.Thread):
	#self.__init__(self)
	def run (self):
		self.data
		self.mean=mean(self.data)
		print "threaded mean:",self.mean
class threaded_stddev(threading.Thread):
	def run(self):
		self.data
		self.dev = stddev(self.data)
		print "threaded stddev:",self.dev
if __name__ == "__main__":
	data = [0,123,242,32342,4234,54234,334,74234,8423,944,14234]
	print "mean:", mean(data)
	print "stddev:",stddev(data)
	thread= threaded_mean()
	thread.data = data
	thread.start()
	dev_thread=threaded_stddev()
	dev_thread.data=data
	dev_thread.start()
