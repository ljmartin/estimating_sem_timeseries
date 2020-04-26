#####
##To plot the interactive vegaplots for html, as you would within a notebook, see 
##https://github.com/altair-viz/altair/issues/329#issuecomment-473524751
##basically, run:
##jupyter nbconvert --to html --template nbconvert_template_altair.tpl <YOUR_NOTEBOOK.ipynb>
#####

import altair as alt
import pandas as pd
import numpy as np
np.seterr(divide='ignore', invalid='ignore')

z95 = 1.959963984540054
results = pd.read_csv('sem_results.csv', index_col=0)
method_names = results['methodName'].unique()
timeseries_lengths = results['timeSeriesLength'].unique()

#calculate which experiments had the true mean within the estimatimed_mean +/- abs(SEM)
results['rate'] = results.apply(lambda row: float(np.abs(row['estMean']) < z95*row['SEM'])*0.01, axis=1)

#group by all the experimental conditions, sum the number of correct SEMs per condition,
#then flatten into long format with reset index:
data = pd.DataFrame(results.groupby(['methodName', 'timeSeriesLength', 'trueRho'])['rate'].sum()).reset_index()

#calculate confidence intervals for proportions:
#(ignore the 'invalid value encountered in sqrt' - this is for rate of '1' which has no confidence interval, 
#hence the fillna(0))
data['confInt'] = data.apply(lambda row: 1.96*np.sqrt(row['rate']*(1-row['rate'])/100), axis=1).fillna(0)

#This is simply to avoid formatting the faceted plot later:
data['trueRho'] =data.apply(lambda row: 'ρ='+str(row['trueRho']),axis=1)

def plot_results_static():
    # the base chart
    base = alt.Chart(data).transform_calculate(
        x_jittered = '0.15*random()*datum.timeSeriesLength+datum.timeSeriesLength',
        ymin="datum.rate-datum.confInt",
        ymax="datum.rate+datum.confInt",
        goal='0.95')

    #generate the scatter points:
    points = base.mark_point(filled=True).encode(
        x=alt.X('x_jittered:Q', scale=alt.Scale(type='log'), title='Length of Timeseries'),
        y=alt.Y('rate:Q', scale=alt.Scale(domain=[0,1.04]), title='Rate of correct SEM'),
        size=alt.value(80),
        color=alt.Color('methodName', legend=alt.Legend(title="SEM method")))
    
    #generate the scatter points:
    line = base.mark_line().encode(
        x=alt.X('x_jittered:Q'),
        y=alt.Y('rate:Q'),
        color='methodName')
    
    #generate the 95% mark:
    rule = base.mark_rule(color='black').encode(
        alt.Y('goal:Q'))

    # generate the error bars (old way):
    # errorbars = base.mark_errorbar().encode(
    #     alt.X("x_jittered:Q"),
    #     alt.Y("ymin:Q", title=''),
    #     alt.Y2("ymax:Q"),
    #     color='methodName')

    errorbars = base.mark_rule(strokeWidth=3).encode(
        alt.X("x_jittered:Q"),
        alt.Y("ymin:Q", title=''),
        alt.Y2("ymax:Q"),
        color='methodName')

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
        x_jittered = '0.15*random()*datum.timeSeriesLength+datum.timeSeriesLength',
        ymin="datum.rate-datum.confInt",
        ymax="datum.rate+datum.confInt",
        goal='0.95')

    selector = alt.selection_single(
        fields=['methodName'], 
        empty='all',
        bind='legend')

    #generate the scatter points:
    points = base.mark_point(filled=True).add_selection(selector).encode(
        x=alt.X('x_jittered:Q', scale=alt.Scale(type='log'), title='Length of Timeseries'),
        y=alt.Y('rate:Q', scale=alt.Scale(domain=[0,1.04]), title='Rate of correct SEM'),
        size=alt.value(80),
        #color=alt.condition(selector, 'methodName:N', alt.value('lightgrey')),
        color=alt.condition(selector, 'methodName:N', alt.value('lightgrey'),legend=alt.Legend(title='SEM Method-Click to highlight!')),
        tooltip=['methodName:N'],)
    
    selector = alt.selection_single(
        fields=['methodName'], 
        empty='all',
        bind='legend')
    
    #generate the lines:
    line = base.mark_line().add_selection(selector).encode(
        x=alt.X('x_jittered:Q'),
        y=alt.Y('rate:Q'),
        color=alt.condition(selector, 'methodName:N', alt.value('lightgrey')))

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
        color=alt.condition(selector, 'methodName:N', alt.value('lightgrey')))

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
    
