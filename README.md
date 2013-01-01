# TxMetrics

    Redis backed metrics library ported to twisted. Compatible with https://github.com/gleicon/pymetrics. Implements part of the famous Metrics library. Data is interchangeable between both libraries (you can have a traditional python app with pymetrics and a twisted based app sharing data, etc)

# Classes

    TxMetricsGauge(BaseMetrics) - Single value gauge
    TxMetricsCounter(BaseMetrics) - Simple counter with incr and decr methods
    TxMetricsMeter(BaseMetrics) - Time series data, with 1, 5 and 15 minutes avg
    TxMetricsHistogram(BaseMetrics) - Histogram with percentile, mean, median and std deviation methods 
    TxMetricsTimer(BaseMetrics) - Timer (wallclock)

    The main class to look for is TxMetricsFactory - Metrics factory 

# Hierarchy

    Basically we register an application and its metrics instances in the following order:
        Application -> Metrics -> Instances of metrics

    The important thing to monitor is that each metric will have an internal name based on the application + metric name + pid.
    By looking at the way the name is composed it's easy to interchange data between processes.

# Examples:
    
    There is an example/ directory with the general outline for each kind of metric.
    Run all tests with trial tests/

# Depends on
    Twisted and txredisapi https://github.com/fiorix/txredisapi
    
