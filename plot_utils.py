#####
##To plot the interactive vegaplots for html, as you would within a notebook, see 
##https://github.com/altair-viz/altair/issues/329#issuecomment-473524751
##basically, run:
##jupyter nbconvert --to html --template nbconvert_template_altair.tpl <YOUR_NOTEBOOK.ipynb>
#####


import altair as alt
import pandas as pd
import numpy as np
from scipy.stats import beta

import sem_utils

sort=['AR1_Bayes', 'BlockAveraging', 'Sokal', 'Chodera', 'AR1_correction', 'Naive']
col = alt.Color('methodName:N', sort=sort, legend=alt.Legend(title="SEM method"))

##Data preprocessing:
z95 = 1.959963984540054
results = pd.read_csv('./sem_results.csv', index_col=0)
method_names = results['methodName'].unique()
timeseries_lengths = results['timeSeriesLength'].unique()


#calculate which experiments had the true mean within the estimatimed_mean +/- abs(SEM)
###If using the frequentist CI below, calculate a rate instead of a count:
#results['rate'] = results.apply(lambda row: float(np.abs(row['estMean']) < z95*row['SEM'])*0.01, axis=1)
results['rate'] = results.apply(lambda row: 0.01*float(np.sign(np.array([row['mean_low'], row['mean_high']])).sum()==0), axis=1)

##Calculate size of the CI:
results['ci_size'] = results.apply(lambda row: row['mean_high']-row['mean_low'], axis=1)

#group by all the experimental conditions, sum the number of correct SEMs per condition,
#then flatten into long format with reset index:
data = pd.DataFrame(results.groupby(['methodName', 'timeSeriesLength', 'trueRho'])['rate'].sum()).reset_index()

#calculate confidence intervals for proportions:
##This uses standard binomial confidence interval:
##(equivalent to from statsmodels.stats.proportion import proportion_confint)
data['confInt'] = data.apply(lambda row: 1.96*np.sqrt(row['rate']*(1-row['rate'])/100), axis=1).fillna(0)

##Alternatively, can calculate the CI using a bayesian conjugate prior (beta distribution)
##I am using a beta(1,1) prior, hence the '+1's. Statsmodels has the Jeffreys interval which uses (0.5,0.5)
data['confIntLow'] = data.apply(lambda row: beta.ppf(0.025, 100*row['rate']+1, 100-100*row['rate']+1), axis=1)
data['confIntHigh'] = data.apply(lambda row: beta.ppf(0.975, 100*row['rate']+1, 100-100*row['rate']+1), axis=1)

#This is simply to avoid formatting the faceted plot later:
data['trueRho'] =data.apply(lambda row: 'ρ='+str(row['trueRho']),axis=1)


##calculate empirical time constants of various series lengths:
import sem_utils
gs = dict()
for ac in [0.1, 0.3, 0.5, 0.7, 0.9, 0.99]:
    c = sem_utils.gen_correlated_curve(ac, 1000000)
    g = sem_utils.statistical_inefficiency(c)
    gs[ac]=g
data['taus'] = data.apply(lambda row: row['timeSeriesLength']/gs[float(row['trueRho'][2:])], axis=1)



def plot_results_static():
    # the base chart
    base = alt.Chart(data).transform_calculate(
        x_jittered = '0.15*(random()-0.5)*datum.timeSeriesLength+datum.timeSeriesLength',
        ymin="datum.confIntLow",
        ymax="datum.confIntHigh",
        goal='0.95')

    #generate the scatter points:
    points = base.mark_point(filled=True).encode(
        x=alt.X('x_jittered:Q', scale=alt.Scale(type='log'), title='Length of Timeseries'),
        y=alt.Y('rate:Q', scale=alt.Scale(domain=[0,1.04]), title='Rate of correct SEM'),
        size=alt.value(80),
        #color=alt.Color('methodName', sort=sort, legend=alt.Legend(title="SEM method")))
        color=col)
    
    #generate the scatter points:
    line = base.mark_line().encode(
        x=alt.X('x_jittered:Q'),
        y=alt.Y('rate:Q'),
        color=col)
    
    #generate the 95% mark:
    rule = base.mark_rule(color='black').encode(
        alt.Y('goal:Q'))

    errorbars = base.mark_rule(strokeWidth=3).encode(
        alt.X("x_jittered:Q"),
        alt.Y("ymin:Q", title=''),
        alt.Y2("ymax:Q"),
        color=col)

    chart = alt.layer(errorbars,
                      points,
                      line,
                      rule,).properties(
        width=250,
        height=200).facet(facet=alt.Facet('trueRho:N',title='Autocorrelation parameter (ρ)'), columns=3)

    chart = chart.configure_header(titleColor='darkred',
                       titleFontSize=16,
                      labelColor='darkred',
                      labelFontSize=14)

    chart = chart.configure_legend(
        strokeColor='gray',
        fillColor='#EEEEEE',
        padding=10,
        cornerRadius=10,
        orient='top'
        )    
    return chart

def plot_results_interactive():
    # the base chart
    base = alt.Chart(data).transform_calculate(
        x_jittered = '0.15*(random()-0.5)*datum.timeSeriesLength+datum.timeSeriesLength',
        ymin="datum.confIntLow",
        ymax="datum.confIntHigh",
        goal='0.95')

    selector = alt.selection_single(
        fields=['methodName'], 
        empty='all',
        bind='legend')
    opacity = alt.condition(selector, alt.value(1.0), alt.value(0.5))

    #generate the scatter points:
    points = base.mark_point(filled=True).add_selection(selector).encode(
        x=alt.X('x_jittered:Q', scale=alt.Scale(type='log'), title='Length of Timeseries'),
        y=alt.Y('rate:Q', scale=alt.Scale(domain=[0,1.04]), title='Rate of correct SEM'),
        size=alt.value(80),
        #color=alt.condition(selector, 'methodName:N', alt.value('lightgrey')),
        color=alt.condition(selector, col, alt.value('lightgrey'),legend=alt.Legend(title='SEM Method-Click to highlight')),
        opacity=opacity,
        tooltip=['methodName:N'],)
    
    selector = alt.selection_single(
        fields=['methodName'], 
        empty='all',
        bind='legend')
    
    #generate the lines:
    line = base.mark_line().add_selection(selector).encode(
        x=alt.X('x_jittered:Q'),
        y=alt.Y('rate:Q'),
        color=alt.condition(selector, col, alt.value('lightgrey')),
        opacity=opacity)

    #generate the 95% mark:
    rule = base.mark_rule(color='black').encode(
        alt.Y('goal:Q'))

    selector = alt.selection_single(
        fields=['methodName'], 
        empty='all',
        bind='legend')

    errorbars = base.mark_rule(strokeWidth=3).add_selection(selector).encode(
        alt.X("x_jittered:Q"),
        alt.Y("ymin:Q", title=''),
        alt.Y2("ymax:Q"),
        color=alt.condition(selector, col, alt.value('lightgrey')),
        opacity=opacity)

    chart = alt.layer(
        errorbars,
        points,
        line,
        rule,).properties(
        width=250,
        height=200).facet(facet=alt.Facet('trueRho:N', title='Autocorrelation parameter (ρ)'), columns=3)

    chart = chart.configure_header(titleColor='darkred',
                       titleFontSize=16,
                      labelColor='darkred',
                      labelFontSize=14)

    chart = chart.configure_legend(
        strokeColor='gray',
        fillColor='#EEEEEE',
        padding=10,
        cornerRadius=10,
        orient='top')

    return chart.interactive()
    

def plot_mean_ci_width_static():
    data2 = pd.DataFrame(results.groupby(['methodName', 'timeSeriesLength', 'trueRho'])['ci_size'].mean()).reset_index()

    # the base chart
    base = alt.Chart(data2).transform_calculate(
        x_jittered = '0.05*random()*datum.timeSeriesLength+datum.timeSeriesLength',
        ymin = "datum.confIntLow",#"(1.95996*datum.std / 100)",
        ymax = "datum.confIntHigh",#"(1.95996*datum.std / 100)",
        )
    
    selector = alt.selection_single(
        fields=['methodName'],
        empty='all',
        bind='legend')
    opacity = alt.condition(selector, alt.value(1.0), alt.value(0.5))

    #generate the scatter points:
    points = base.mark_point(filled=True).add_selection(selector).encode(
        x=alt.X('x_jittered:Q',scale=alt.Scale(type='log'),title='Length of Timeseries'),
        y=alt.Y('ci_size:Q',scale=alt.Scale(type='log'),title='Mean width of the CI'),
        size=alt.value(80),
        color=alt.condition(selector, col, alt.value('lightgrey')),
        opacity=opacity)

    selector = alt.selection_single(
        fields=['methodName'],
        empty='all',
        bind='legend')
    opacity = alt.condition(selector, alt.value(1.0), alt.value(0.5))


    #generate the scatter points:
    line = base.mark_line().add_selection(selector).encode(
        x=alt.X('x_jittered:Q'),
        y=alt.Y('ci_size:Q'),
        color=alt.condition(selector, col, alt.value('lightgrey')),
        opacity=opacity)
    
    chart = alt.layer(
        points,
        line).properties(
        width=250,
        height=200
        ).facet(facet=alt.Facet('trueRho:N',title='Autocorrelation parameter (ρ)'), columns=3)

    chart = chart.configure_header(titleColor='darkred',
                                   titleFontSize=16,
                                   labelColor='darkred',
                                   labelFontSize=14)

    chart = chart.configure_legend(
        strokeColor='gray',
        fillColor='#EEEEEE',
        padding=10,
        cornerRadius=10,
        orient='top')

    return chart


def plot_median_ci_width_static():
    data2 = pd.DataFrame(results.groupby(['methodName', 'timeSeriesLength', 'trueRho'])['ci_size'].median()).reset_index()

    # the base chart
    base = alt.Chart(data2).transform_calculate(
        x_jittered = '0.05*random()*datum.timeSeriesLength+datum.timeSeriesLength',
        ymin = "datum.confIntLow",
        ymax = "datum.confIntHigh",
        )

    selector = alt.selection_single(
        fields=['methodName'],
        empty='all',
        bind='legend')
    opacity = alt.condition(selector, alt.value(1.0), alt.value(0.5))

    #generate the scatter points:
    points = base.mark_point(filled=True).add_selection(selector).encode(
        x=alt.X('x_jittered:Q',scale=alt.Scale(type='log'),title='Length of Timeseries'),
        y=alt.Y('ci_size:Q',scale=alt.Scale(type='log'),title='Median size of the CI'),
        size=alt.value(80),
        color=alt.condition(selector, col, alt.value('lightgrey')),
        opacity=opacity)

    selector = alt.selection_single(
        fields=['methodName'],
        empty='all',
        bind='legend')
    opacity = alt.condition(selector, alt.value(1.0), alt.value(0.5))

    #generate the scatter points:
    line = base.mark_line().add_selection(selector).encode(
        x=alt.X('x_jittered:Q'),
        y=alt.Y('ci_size:Q'),
        color=alt.condition(selector, col, alt.value('lightgrey')),
        opacity=opacity)

    chart = alt.layer(
        points,
        line
        ).properties(
        width=250,
        height=200
        ).facet(facet=alt.Facet('trueRho:N',title='Autocorrelation parameter (ρ)'), columns=3)

    chart = chart.configure_header(titleColor='darkred',
                                   titleFontSize=16,
                                   labelColor='darkred',
                                   labelFontSize=14)

    chart = chart.configure_legend(
        strokeColor='gray',
        fillColor='#EEEEEE',
        padding=10,
        cornerRadius=10,
        orient='top')

    return chart

def plot_results_timeconstant_static():
    # the base chart
    base = alt.Chart(data).transform_calculate(
        x_jittered = '0.15*random()*datum.taus+datum.taus',
        ymin = "datum.confIntLow",
        ymax = "datum.confIntHigh",
        goal='0.95')

    selector = alt.selection_single(
        fields=['methodName'],
        empty='all',
        bind='legend')
    opacity = alt.condition(selector, alt.value(1.0), alt.value(0.5))

    #generate the scatter points:
    points = base.mark_point(filled=True).add_selection(selector).encode(
        x=alt.X('x_jittered:Q', scale=alt.Scale(type='log'), title='Length of Timeseries (τ)'),
        y=alt.Y('rate:Q', scale=alt.Scale(domain=[0,1.04]), title='Rate of correct SEM'),
        size=alt.value(80),
        color=alt.condition(selector, col, alt.value('lightgrey')),
        opacity=opacity)

    selector = alt.selection_single(
        fields=['methodName'],
        empty='all',
        bind='legend')
    opacity = alt.condition(selector, alt.value(1.0), alt.value(0.5))

    #generate the scatter points:
    line = base.mark_line().add_selection(selector).encode(
        x=alt.X('x_jittered:Q'),
        y=alt.Y('rate:Q'),
        color=alt.condition(selector, col, alt.value('lightgrey')),
        opacity=opacity)

    #generate the 95% mark:
    rule = base.mark_rule(color='black').encode(
        alt.Y('goal:Q'))

    selector = alt.selection_single(
        fields=['methodName'],
        empty='all',
        bind='legend')
    opacity = alt.condition(selector, alt.value(1.0), alt.value(0.5))

    errorbars = base.mark_rule(strokeWidth=3).add_selection(selector).encode(
        alt.X("x_jittered:Q"),
        alt.Y("ymin:Q", title=''),
        alt.Y2("ymax:Q"),
        color=alt.condition(selector, col, alt.value('lightgrey')),
        opacity=opacity)

    chart = alt.layer(
        errorbars,
        points,
        line,
        rule,).properties(
        width=250,
        height=200
        ).facet(facet=alt.Facet('trueRho:N', 
                                title='Autocorrelation parameter (ρ)'), columns=3)


    chart = chart.configure_header(titleColor='darkred',
                                   titleFontSize=16,
                                   labelColor='darkred',
                                   labelFontSize=14)
    
    chart = chart.configure_legend(
        strokeColor='gray',
        fillColor='#EEEEEE',
        padding=10,
        cornerRadius=10,
        orient='top')


    return chart
