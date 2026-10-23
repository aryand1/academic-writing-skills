# Fast anomaly detection for streaming sensor data with sketch-based summaries

## Abstract
We present SketchAD, a method that detects anomalies in high-rate sensor streams using compact sketch-based summaries. SketchAD keeps memory constant regardless of stream length and flags anomalies within one window of their onset. On two public benchmarks it matches the accuracy of exact methods while using a fraction of their memory.

## Introduction
Sensor networks now produce data faster than most anomaly detectors can process it. Exact methods store every reading in a window, which limits them to small deployments. We ask whether a compact summary of each window can support accurate detection.

## Method
SketchAD maintains a count-min sketch of quantized readings for each sliding window. An incoming reading is scored by comparing its estimated frequency with the expected frequency under the previous window. Readings whose score exceeds a threshold are reported as anomalies.

## Evaluation
We evaluated SketchAD on two public benchmarks with labeled anomalies. SketchAD reached an F1 score within two points of the exact baseline on both benchmarks while using less than five percent of its memory.

## Conclusion
Sketch-based summaries make streaming anomaly detection practical for large sensor deployments. Future work will test SketchAD on real deployments and study how the threshold should adapt over time.

## References
[1] G. Cormode and S. Muthukrishnan. An improved data stream summary: the count-min sketch and its applications. Journal of Algorithms, 2005.
