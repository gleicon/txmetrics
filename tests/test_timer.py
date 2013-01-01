import sys, os                                                                                                                                                                  
sys.path.append(os.path.join(sys.path[0], '..'))

from twisted.internet import defer                                              
from twisted.trial import unittest                                              

import txredisapi as redis                                                      
import txmetrics

redis_host = "localhost"                                                        
redis_port = 6379

class TestTimer(unittest.TestCase):

    def test_timer(self):
        db = yield redis.Connection(redis_host, redis_port, reconnect=False)
        rf = txmetrics.TxMetricsFactory("metrics_test", redis=db)                  
        self.timer = rf.new_timer("a_timer") 
        yield self.timer.start() 
        time.sleep(5)
        yield self.timer.stop()
        v = yield self.timer.get_value()
        self.assertEqual(v, 5)
        yield self.rf.unregister_instance(self.timer)
        yield db.disconnect()

if __name__ == '__main__':
    unittest.main()
