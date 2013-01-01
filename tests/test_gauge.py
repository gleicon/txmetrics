import sys, os                                                                                                                                                                  
sys.path.append(os.path.join(sys.path[0], '..'))

from twisted.internet import defer                                              
from twisted.trial import unittest                                              

import txredisapi as redis                                                      
import txmetrics

redis_host = "localhost"                                                        
redis_port = 6379

class TestGauge(unittest.TestCase):
    def test_gauge(self):
        db = yield redis.Connection(redis_host, redis_port, reconnect=False)
        self.rf = txmetrics.TxMetricsFactory("metrics_test", redis=db)                  
        self.gauge = self.rf.new_gauge("a_gauge") 
        yield self.gauge.set(10)
        v  = self.gauge.get()
        self.assertEqual(v, 10)
        yield self.rf.unregister_instance(self.gauge)
        yield db.disconnect()

if __name__ == '__main__':
    unittest.main()
