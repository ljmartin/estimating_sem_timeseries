# Intro to confidence intervals for time series 

This page compares different methods of calculating the SEM for a stationary time series. 

It compares the popular 'block average' to several alternatives. Bayes model of an AR(1) process fares best in cases of limited data.


```python
import plot_utils
from altair_saver import save
#plot_utils.plot_results_interactive()
chart = plot_utils.plot_results_static()
save(chart, 'chart.png')
```

![title](./chart.png)
