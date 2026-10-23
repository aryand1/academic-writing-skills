# Calibrating low-cost particulate sensors with a humidity correction

## Abstract
Low-cost sensors (LCS) can extend air quality monitoring, but their readings drift with relative humidity. We test a humidity correction against a reference instrument and report the root mean square error (RMSE) before and after correction. A convolutional neural network (CNN) baseline is included for comparison. We also compare against a machine learning (ML) regression.

## Methods
Each sensor was co-located with a reference monitor for 21 days. Readings were averaged to one-hour values, and hours with less than 75 percent data coverage were removed before analysis. Relative humidity was recorded by the internal probe of each sensor and checked against a calibrated hygrometer once per week.

## Results
The humidity correction reduced the RMSE from 9.1 to 6.0 micrograms per cubic meter. The CNN baseline reached 6.4, and the ML regression reached 6.8.
