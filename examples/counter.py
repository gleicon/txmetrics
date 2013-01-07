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
    print 'Counter test'
    counter = rf.new_counter("a_counter") 
    yield counter.reset() 
    for a in xrange(10):
        yield counter.incr()
    v = yield counter.get_value()
    assert(v, 10)
   
if __name__ == '__main__':
    log.startLogging(sys.stdout)
    main().addCallback(lambda ign: reactor.stop())
    reactor.run()
