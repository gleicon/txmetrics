#encoding: utf-8

try:
    import cyclone.redis as redis
except Exception, e:
    import txredisapi as redis

import time, os
from pds_redis import Enum
from twisted.internet import defer

class BaseMetrics(object):
    def __init__(self, appname, name, redis, timeout, unique_pid):
        
        self._appname = appname
        self._timeout = timeout
        self._redis = redis

        _klass = self.__class__.__name__.lower()
        self._instances_per_metric_index = "retrics:index:%s:%s" % (appname,
                                                                    _klass)
        if unique_pid is True:
            self._name = "%s:%d" % (name, os.getpid())
        else:
            self._name = name
        self._register()

    @defer.inlineCallbacks
    def _register(self):
        d = yield self._redis.zadd(self._instances_per_metric_index, 1.0, self._name)

    @defer.inlineCallbacks
    def _unregister(self):
        try:
            yield self._redis.zrem(self._instances_per_metric_index, self._name)
            yield self.clear()
        except Exception, e:
            print "Exception %s" % e

    def clear(self):
        pass

class TxMetricsGauge(BaseMetrics):
    """
    A gauge is an instantaneous measurement of a value. For example, we may
    want to measure the number of pending jobs in a queue
    """
    @defer.inlineCallbacks
    def set(self, value):
        d = yield self._redis.set("retrics:gauge:%s:%s" % (self._appname, self._name),
                value)
    
    @defer.inlineCallbacks
    def get(self):
        r = yield self._redis.get("retrics:gauge:%s:%s" % (self._appname,
            self._name))
        if r is None: r = 0
        defer.returnValue(int(r))
    
    @defer.inlineCallbacks
    def clear(self):
        yield self._redis.delete("retrics:gauge:%s:%s" % (self._appname, self._name))

class TxMetricsCounter(BaseMetrics):
    """
    A counter is just a gauge for an AtomicLong instance. You can increment
    or decrement its value. For example, we may want a more efficient way of
    measuring the pending job in a queue
    """
    @defer.inlineCallbacks
    def incr(self, val = 1):
        yield self._redis.incr("retrics:counter:%s:%s" % (self._appname, self._name), val)
    
    @defer.inlineCallbacks
    def decr(self, val = 1):
        yield self._redis.decr("retrics:counter:%s:%s" % (self._appname, self._name), val)
    
    @defer.inlineCallbacks
    def reset(self):
        yield self._redis.set("retrics:counter:%s:%s" % (self._appname, self._name), 0)
    
    @defer.inlineCallbacks
    def clear(self):
        yield self._redis.delete("retrics:counter:%s:%s" % (self._appname, self._name))

    @defer.inlineCallbacks 
    def get_value(self):
        r = yield self._redis.get("retrics:counter:%s:%s" % (self._appname,
            self._name))
        if r is None: r = 0
        defer.returnValue(int(r))

class TxMetricsMeter(BaseMetrics):
    """
    A meter measures the rate of events over time (e.g., “requests per
    second”). In addition to the mean rate, meters also track 1-, 5-, and
    15-minute moving averages.
    """
    def __init__(self, appname, name, redis, timeout, unique_pid):
        super(TxMetricsMeter, self).__init__(appname, name, redis, timeout, unique_pid)
        self._last_t = time.time()

    def _ns(self, key):
        """
        takes care of namespace
        """
        return "retrics:meter:%s:%s:%s"% (self._appname, self._name, key)

    @defer.inlineCallbacks
    def start(self):
        yield self.reset()
        self._last_t = time.time()

    @defer.inlineCallbacks 
    def reset(self):
        self._last_t = time.time()
        zeroes = [0 for x in xrange(60)]
        yield self._redis.lpush(self._ns('seconds'), zeroes)
        yield self._redis.lpush(self._ns('l5min'), zeroes[0:4])
        yield self._redis.lpush(self._ns('l15min'), zeroes[0:14])
        yield self._redis.set(self._ns('curr_second'), 0)
        yield self._redis.set(self._ns('1minute'), 0)
        yield self._redis.set(self._ns('5minute'), 0)
        yield self._redis.set(self._ns('15minute'), 0)

    @defer.inlineCallbacks 
    def _update(self, ts):
        if int(self._last_t) == int(ts):
            yield self._redis.incr(self._ns('curr_second'))
        else:
            self._last_t = ts
            v = yield self._redis.get(self._ns('curr_second'))
            if v is None: v=0
            v = int(v)
            yield self._redis.set(self._ns('curr_second'), 1)

            yield self._redis.lpush(self._ns('seconds'), v)
            yield self._redis.ltrim(self._ns('seconds'), 0, 60)
            l = yield self._redis.lrange(self._ns('seconds'), 0, 60)
            one_min = reduce(lambda x,y: int(x) + int(y), l)/60

            yield self._redis.set(self._ns('1minute'), one_min)
            yield self._redis.lpush(self._ns('l5min'), one_min)
            yield self._redis.lpush(self._ns('l15min'), one_min)
            yield self._redis.ltrim(self._ns('l5min'), 0, 5)
            yield self._redis.ltrim(self._ns('l15min'), 0, 15)

            l5 = yield self._redis.lrange(self._ns('l5min'), 0, 60)
            l15 = yield self._redis.lrange(self._ns('l15min'), 0, 60)

            five_min = reduce(lambda x,y: int(x) + int(y), l5)/5
            yield self._redis.set(self._ns('5minute'), five_min)

            fifteen_min = reduce(lambda x,y: int(x) + int(y), l15)/15
            yield self._redis.set(self._ns('15minute'), fifteen_min)
    
    @defer.inlineCallbacks 
    def get_value(self):
        one = yield self._redis.get(self._ns('1minute'))
        five = yield self._redis.get(self._ns('5minute'))
        fifteen = yield self._redis.get(self._ns('15minute'))
        defer.returnValue([self._last_t, one, five, fifteen])

    @defer.inlineCallbacks 
    def mark(self):
        yield self._update(time.time())
    
    @defer.inlineCallbacks 
    def clear(self):
        yield self._redis.delete(self._ns("1minute"))
        yield self._redis.delete(self._ns("5minute"))
        yield self._redis.delete(self._ns("15minute"))
        yield self._redis.delete(self._ns("seconds"))
        yield self._redis.delete(self._ns("curr_second"))
        yield self._redis.delete(self._ns("l1min"))
        yield self._redis.delete(self._ns("l5min"))
        yield self._redis.delete(self._ns("l15min"))

class TxMetricsHistogram(BaseMetrics):
    """
    A histogram measures the statistical distribution of values in a stream
    of data. In addition to minimum, maximum, mean, etc., it also measures
    median, 75th, 90th, 95th, 98th, 99th, and 99.9th percentiles.
    """
    def __init__(self, appname, name, redis, timeout, unique_pid):
        super(TxMetricsHistogram, self).__init__(appname, name, redis, timeout, unique_pid)
        self._list_name = "retrics:histogram:%s:%s" % (self._appname, self._name)
        self._e = Enum([])

    @defer.inlineCallbacks 
    def update(self, val):
        assert(type(val) is int or type(val) is float)
        yield self._redis.lpush(self._list_name, val)
        self._load_list()

    def percentile(self, p):
        """
        Percentile of the Histogram list
        """
        assert(type(p) is float)
        return self._e.percentile(p)
    
    def standard_deviation(self):
        """
        standard deviation of the Histogram list
        """
        return self._e.standard_deviation()

    def median(self):
        """
        Median (50% Percentile) of the Histogram list
        """
        return self._e.median()
    
    def mean(self):
        """
        Mean of the Histogram list
        """
        return self._e.mean()

    @defer.inlineCallbacks 
    def _load_list(self):
        l = yield self._redis.lrange(self._list_name, 0, -1)
        l = map(lambda x: float(x), l) #oh god why
        self._e.reload(l)
   
    @defer.inlineCallbacks 
    def reset(self):
        yield self._redis.delete(self._list_name)
        self._e = Enum([])

    @defer.inlineCallbacks 
    def clear(self):
        yield self.reset()

class TxMetricsTimer(BaseMetrics):
    """
    A timer measures both the rate that a particular piece of code is called and
    the distribution of its duration.
    """
    @defer.inlineCallbacks 
    def start(self):
        yield self._redis.set("retrics:timer:%s:%s:start" % (self._appname,
            self._name), int(time.time()))

    @defer.inlineCallbacks 
    def stop(self):
        yield self._redis.set("retrics:timer:%s:%s:stop" % (self._appname,
            self._name), int(time.time()))

    @defer.inlineCallbacks
    def get_value(self):
        p = "retrics:timer:%s:%s" % (self._appname, self._name)
        start, stop = yield self._redis.mget(["%s:start" % p, "%s:stop" % p])
        
        if start is None: start = 0
        if stop is None: stop = 0

        defer.returnValue(int(stop) - int(start))

    @defer.inlineCallbacks 
    def reset(self):
        p = "retrics:timer:%s:%s" % (self._appname, self._name)
        yield self._redis.mset({"%s:start" % p: 0, "stop:%s" % p: 0})

    @defer.inlineCallbacks 
    def clear(self):
        p = "retrics:timer:%s:%s" % (self._appname, self._name)
        yield self._redis.delete("%s:start" % p, "%s:stop" % p)

class TxMetricsFactory():
    """
    TxMetrics - Redis based metrics library
    Inspired by coda hale's Metrics

    Create a metrics factory for your application
    rf = TxMetricsFactory("my_application")
    
    Optionally you can pass a global timeout in seconds to keep the database
    clean. No writes to a given metrics ensure its data will be cleaned up

    rf = TxMetricsFactory("my_application", 3600)


    Instrument your code:
        c = rf.new_counter("requests")
        c.incr()
        c.decr()

    Unregister and clean up all data with:
        rf.unregister(c)

    Check the number of instances per metric (if any)

    print rf.list_instances_per_metric('gauge')
    """

    def __init__(self, appname = None, timeout = None, redis=None, unique_pid=False):
        self._appname = appname
        self._timeout = timeout
        self._redis = redis
        self.unique_pid = unique_pid

    def _metric_name(self, metric_name):
        _klass = "txmetrics%s" % metric_name.lower()
        return "retrics:index:%s:%s" % (self._appname, _klass)

    @defer.inlineCallbacks
    def list_instances_per_metric(self, metric_name):
        _klass = "txmetrics%s" % metric_name.lower()
        _instances_per_metric_index = "retrics:index:%s:%s" % (self._appname,
                                      _klass.lower())
        v = yield self._redis.zrange(_instances_per_metric_index,
                                     0, -1)
        defer.returnValue(v)

    @defer.inlineCallbacks
    def unregister_instance(self, kl):
        """
            Expect the metric object itself to clean everything up.
        """
        yield kl._unregister()

    def new_gauge(self, name):
        return TxMetricsGauge(self._appname, name, self._redis, self._timeout,
                self.unique_pid)

    def new_counter(self, name):
        return TxMetricsCounter(self._appname, name, self._redis, self._timeout,
                                self.unique_pid)

    def new_meter(self, name):
        return TxMetricsMeter(self._appname, name, self._redis, self._timeout,
                              self.unique_pid)

    def new_histogram(self, name):
        return TxMetricsHistogram(self._appname, name, self._redis,
                                  self._timeout, self.unique_pid)

    def new_timer(self, name):
        return TxMetricsTimer(self._appname, name, self._redis, self._timeout,
                              self.unique_pid)

    def new_healthcheck(self, name):
        pass
