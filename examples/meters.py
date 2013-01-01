import sys, os

sys.path.append(os.path.join(sys.path[0], '..'))

from twisted.internet import defer, reactor
from twisted.python import log
import txredisapi as redis
import txmetrics
import time, random

@defer.inlineCallbacks                                                          
def test_meter(meters):                                                         
    last_t = time.time()                                                        
    c = j = 0                                                                   
    while(j < 10):                                                              
        c = c +1                                                                
        if c == random.random() % 10:                                           
            c = 0                                                               
            time.sleep(random.random() % 0.01)                                  
        else:                                                                   
            time.sleep(random.random() % 0.1)                                   

        yield meters.mark()                                                           
        
        v = yield meters.get_value()       
        (last_t, one_min, five_min, fifteen_min) = v

        print "\nlast_t: %f" % last_t                                           
        print "avg 1 min: %s" % one_min                                         
        print "avg 5 min: %s" % five_min                                        
        print "avg 15 min: %s" % fifteen_min                                    
        j = j + 1

@defer.inlineCallbacks
def main():
    rc = yield redis.ConnectionPool()
    rf = txmetrics.TxMetricsFactory("metrics_test", redis = rc)
    
    print 'Meter test'                                                          
    meters = rf.new_meter("a_meter")                                            
    meters.start()
    yield test_meter(meters)  

    print 'Listing instances per metric for meter'
    p = yield rf.list_instances_per_metric('meter')
    print p

    print 'Unregistering all metrics (clears up all data)'
    yield rf.unregister_instance(meters)

def errback(e):
    print "Error: %s" %e

if __name__ == '__main__':
    log.startLogging(sys.stdout)
    main().addCallback(lambda ign: reactor.stop())
    reactor.run()
