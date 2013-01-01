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
    print 'Gauge test'
    gauge = rf.new_gauge("a_gauge")

    gauge.set(10)
    p = yield gauge.get()
#    assert(p == 10)
    print "gauge value: %s" % p

    print 'Listing instances per metric for gauge'
    p = yield rf.list_instances_per_metric('gauge')
    print p

    print 'Unregistering all metrics (clears up all data)'
    yield rf.unregister_instance(gauge)
    #yield gauge._unregister()
    #yield gauge.clear()

def errback(e):
    print "Error: %s" %e

if __name__ == '__main__':
    log.startLogging(sys.stdout)
    main().addCallback(lambda ign: reactor.stop())
    reactor.run()
