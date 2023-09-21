import logging
import threading

import os

from aims.operations.abstract_operation import AbstractOperation

import plotly.express as px
import pandas as pd

class ChartOperation(AbstractOperation):
    
    def create_pie_chart_benthic_groups(self, coverage_results_file=''):
        df = pd.read_csv(coverage_results_file)
        df = df[df['group'] != 'total']
        fig = px.pie(values=df['pred_percentage'], names=df['group'], title='Percent Cover of Benthic Groups')
        
        
        return fig.to_html(include_plotlyjs='cdn')
