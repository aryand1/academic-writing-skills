# Six months of street-level particulate data from a 40-node sensor network

## Abstract
We deployed 40 low-cost sensors (LCS) across one city for six months and applied a humidity correction developed in earlier work. We report the root mean squared error (RMSE) against two regulatory monitors and the mean absolute error (MAE) across the network. An ML model is used to flag faulty nodes.

## Methods
Each sensor was co-located with a reference monitor for 21 days. Readings were averaged to one-hour values, and hours with less than 75 percent data coverage were removed before analysis. After co-location, sensors were mounted on lamp posts at a height of 3 meters.

## Results
The corrected network matched the regulatory monitors with an RMSE of 7.2 micrograms per cubic meter for the first four months. After month four, the correction drifted and the MAE rose by 30 percent.
