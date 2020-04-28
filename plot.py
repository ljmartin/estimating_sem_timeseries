import plot_utils


names = ['results_ci.svg', 'results_mean.svg', 'results_median.svg', 'results_tau.svg']
functions = [plot_utils.plot_results_static, plot_utils.plot_mean_ci_width_static,
          plot_utils.plot_median_ci_width_static, plot_utils.plot_results_timeconstant_static]

for f, name in zip(functions, names):
    chart = f()
    chart.save(name)
