# Sketch-based anomaly detection for streaming sensor data: adaptive thresholds and a field evaluation

## Abstract
We present SketchAD, a method that detects anomalies in high-rate sensor streams using compact sketch-based summaries. SketchAD keeps memory constant regardless of stream length and flags anomalies within one window of their onset. We add an adaptive threshold and report a six-week field deployment.

## Introduction
Sensor networks now produce data faster than most anomaly detectors can process it. Exact methods store every reading in a window, which limits them to small deployments. We ask whether a compact summary of each window can support accurate detection, and whether that detection holds up outside the lab.

## Method
SketchAD maintains a count-min sketch of quantized readings for each sliding window. An incoming reading is scored by comparing its estimated frequency with the expected frequency under the previous window. Readings whose score exceeds a threshold are reported as anomalies.

## Adaptive threshold
A fixed threshold works poorly when the background rate of rare readings drifts. We replace it with a threshold set from the running distribution of scores, updated once per window with exponential smoothing. The smoothing factor trades reaction speed against false alarms, and we give a bound on the false alarm rate for stationary streams.

## Evaluation
We evaluated SketchAD on two public benchmarks with labeled anomalies. SketchAD reached an F1 score within two points of the exact baseline on both benchmarks while using less than five percent of its memory.

## Field evaluation
We deployed SketchAD on 120 vibration sensors in a water treatment plant for six weeks. Operators labeled 37 events during that period. With the adaptive threshold, SketchAD detected 33 of them and raised 11 false alarms, compared with 24 detections and 29 false alarms using the fixed threshold.

## Conclusion
Sketch-based summaries make streaming anomaly detection practical for large sensor deployments, and an adaptive threshold keeps false alarms low as conditions change in the field.

## References
[1] G. Cormode and S. Muthukrishnan. An improved data stream summary: the count-min sketch and its applications. Journal of Algorithms, 2005.
[2] A. Author and B. Author. Fast anomaly detection for streaming sensor data with sketch-based summaries. In Proceedings of the Conference on Sensor Systems, 2025.
