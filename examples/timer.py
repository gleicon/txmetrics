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

    print 'Timer test'                                                          
    timer = rf.new_timer("a_timer")                                                                                                                                             
    timer.start()                                                               
    time.sleep(5)                                                               
    timer.stop()                                                                
    v = yield timer.get_value()                                                     
    assert(v == 5) 


    print 'Listing instances per metric for timer'
    p = yield rf.list_instances_per_metric('timer')
    print p

    print 'Unregistering all metrics (clears up all data)'
    yield rf.unregister_instance(timer)

def errback(e):
    print "Error: %s" %e

if __name__ == '__main__':
    log.startLogging(sys.stdout)
    main().addCallback(lambda ign: reactor.stop())
    reactor.run()
