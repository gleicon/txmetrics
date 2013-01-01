import sys, os

sys.path.append(os.path.join(sys.path[0], '..'))

from twisted.internet import defer, reactor
from twisted.python import log
import txredisapi as redis
import txmetrics
import time, random


@defer.inlineCallbacks
def main():
    rc = yield redis.ConnectionPool()
    rf = txmetrics.TxMetricsFactory("metrics_test", redis = rc)

    print 'Histogram test'                                                      
    histogram = rf.new_histogram("a_histogram")                                 
    yield histogram.update(10)                                                        
    yield histogram.update(1)                                                         
    yield histogram.update(50)                                                        
    yield histogram.update(5)                                                         
    yield histogram.update(28)                                                        
    yield histogram.update(12)                                                        
                                                                                
    print histogram.percentile(99.0)                                            
    print histogram.mean()                                                      
    print histogram.median()                                                    
    print histogram.standard_deviation()

    print 'Listing instances per metric for histogram'
    p = yield rf.list_instances_per_metric('histogram')
    print p

    print 'Unregistering all metrics (clears up all data)'
    yield rf.unregister_instance(histogram)

def errback(e):
    print "Error: %s" %e

if __name__ == '__main__':
    log.startLogging(sys.stdout)
    main().addCallback(lambda ign: reactor.stop())
    reactor.run()
