import sys, os                                                                                                                                                                  
sys.path.append(os.path.join(sys.path[0], '..'))

from twisted.internet import defer                                              
from twisted.trial import unittest                                              

import txredisapi as redis                                                      
import txmetrics

redis_host = "localhost"                                                        
redis_port = 6379

import math

class TestHistogram(unittest.TestCase):
    def setUp(self):
        db = yield redis.Connection(redis_host, redis_port, reconnect=False)
        self.rf = txmetrics.TxMetricsFactory("metrics_test", redis=db)                  
        self.histogram = self.rf.new_histogram("a_histogram")
        yield self.histogram.update(10)
        yield self.histogram.update(1)
        yield self.histogram.update(50)
        yield self.histogram.update(5)
        yield self.histogram.update(28)
        yield self.histogram.update(12)

    def test_histogram_percentile(self):
        v = yield self.histogram.percentile(99.0)
        self.assertEqual(round(v, 2), 48.9)
    
    def test_histogram_mean(self):
        v = yield self.histogram.mean()
        self.assertEqual(v, 17.666666666666668)
    
    def test_histogram_median(self):
        v = yield self.histogram.median()
        self.assertEqual(v, 11.0)

    def test_histogram_std_dev(self):
        v = yield self.histogram.standard_deviation()
        self.assertEqual(math.floor(v), 16.0)
    
    def tearDown(self):
        yield self.rf.unregister_instance(self.gauge)
        yield db.disconnect()

if __name__ == '__main__':
    unittest.main()
