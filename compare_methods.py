import sem_utils

import numpy as np
import pandas as pd


##setup search parameters:
timeseries_lengths = np.array([30,100,300,1000,3000])
timeseries_rhos = np.array([0.1, 0.3, 0.5, 0.7, 0.9])
numrpts = 1


##setup names and estimation functions
method_names = ['BlockAveraging', 'Chodera', 'Sokal', 'AR1_correction', 'AR1_Bayes']
method_functions = [sem_utils.sem_from_blockAveraging,
                    sem_utils.sem_from_chodera,
                    sem_utils.sem_from_sokal, 
                    sem_utils.sem_from_autoregressive_correction,
                    sem_utils.sem_from_bayesian_estimation]

##setup df to store the results (we are using long format here due to the complicated structure of the search grid)
df = pd.DataFrame(columns=['methodName', 'trueRho', 'timeSeriesLength', 'estMean', 'SEM'])
row_num = 0

##do the measurements:
for rho in timeseries_rhos:
    for datasize in timeseries_lengths:
        for rpt in range(numrpts):
            timeseries = sem_utils.gen_correlated_curve(rho, datasize)
            estimated_mean = timeseries.mean()
            
            for methodName, function in zip(method_names, method_functions):
                sem = function(timeseries)
                results = [methodName, rho, datasize, estimated_mean, sem]
                print(results)
                df.loc[row_num] = results
                row_num += 1

##save the csv file:
df.to_csv('sem_results.csv')
