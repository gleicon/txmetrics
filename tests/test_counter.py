import sys, os                                                                                                                                                                  
sys.path.append(os.path.join(sys.path[0], '..'))

from twisted.internet import defer                                              
from twisted.trial import unittest                                              

import txredisapi as redis                                                      
import txmetrics

redis_host = "localhost"                                                        
redis_port = 6379


class TestCounter(unittest.TestCase):

    @defer.inlineCallbacks
    def test_counter(self):
        db = yield redis.Connection(redis_host, redis_port, reconnect=False)
        self.rf = txmetrics.TxMetricsFactory("metrics_test", redis=db)                  
        self.counter = self.rf.new_counter("a_counter") 
        yield self.counter.reset() 
        for a in xrange(10):
            yield self.counter.incr()
        v = yield self.counter.get_value()
        self.assertEqual(v, 10)
        yield self.rf.unregister_instance(self.counter)
        yield db.disconnect()

if __name__ == '__main__':
    unittest.main()
