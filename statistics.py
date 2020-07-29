#!/usr/bin/python
import threading
import numpy
import math
def meanAbsError(a,b):
	sum = 0
	for x,y in zip(a,b):
		sum += abs(x-y)
	return sum/len(a)
def meanErrorSq(a,b):
	sum = 0
	for x,y in zip(a,b):
		sum += (x-y)**2
	return sum/len(a)
def rmsError(a,b):
	sum=0
	for x,y in zip(a,b):
		sum += (x-y)**2
	return math.sqrt(sum/len(a))
	
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
	return  ave ,numpy.sqrt(dev/len(data))
def z_test(x,y):
	tx = threaded_stddev()
	tx.data = x
	tx.start()
	ty = threaded_stddev()
	ty.data = y
	ty.start()
	tx.join()
	ty.join()
	Z=(tx.ave-ty.ave)/ty.dev
	return Z
def covariance(x,y):
	tx = threaded_mean()
	tx.data = x
	tx.start()
	ty = threaded_mean()
	ty.data = y
	ty.start()
	tx.join()
	ty.join()
	#xm= mean(x)
	#ym= mean(y)
	sum =0
	for each in range(len(x)):
		sum+= (x[each]-tx.mean)*(y[each]-ty.mean)
	return  float(sum/len(x)-1)
def correlation(x,y):
	tx = threaded_stddev()
	tx.data = x
	tx.start()
	ty = threaded_stddev()
	ty.data = y
	ty.start()
	tx.join()
	ty.join()


	return covariance(x,y)/(tx.dev*ty.dev)

class threaded_mean(threading.Thread):
	#self.__init__(self)
	def run (self):
		self.data
		self.mean=mean(self.data)
		#print "threaded mean:",self.mean
class threaded_stddev(threading.Thread):
	def run(self):
		self.data
		self.ave, self.dev = stddev(self.data)
		#print "threaded stddev:",self.dev
def chi2test(measured, calculated):
	chi = 0
	for x,y in zip( measured, calculated):
		sq = (x-y)*(x-y)
		chi += float(sq)/y
	return chi/len(measured)

if __name__ == "__main__":
	"""datax = [0,123,242,32342,4234,54234,334,74234,8423,944,14234]
	datay = [0,100,200,30000,4000,50000,333,70000,8000,900,14000]
	print "mean:", mean(datax)
	print "stddev:",stddev(datax)
	thread= threaded_mean()
	thread.data = datax
	thread.start()
	dev_thread=threaded_stddev()
	dev_thread.data=datax
	dev_thread.start()
	print "Correlation coef:", correlation(datax,datay)
	print "Z", z_test(datax,datay)
	"""
	chi2test([1,2,3,4],[1,5,2,4])
