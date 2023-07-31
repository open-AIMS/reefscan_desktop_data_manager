import logging
import threading

import os

from aims.operations.abstract_operation import AbstractOperation
from PyQt5 import QtWebEngineWidgets

import plotly.express as px
import pandas as pd

class ChartOperation(AbstractOperation):
    
    def pie_chart_benthic_groups(self, qtwebengineview_object: QtWebEngineWidgets, coverage_results_file=''):
        ## Do some plotly pie chart
        # df = px.data.tips()
        # fig = px.box(df, x="day", y="total_bill", color="smoker")
        # fig.update_traces(quartilemethod="exclusive") # or "inclusive", or "linear" by default
        
        testpath = 'C:\\Users\\pteneder\\Documents\\reefscan_desktop_integrations\\reefscan_desktop_data_manager\\coverage.csv'

        if not coverage_results_file:
            coverage_results_file = testpath

        df = pd.read_csv(coverage_results_file)
        df = df[df['group'] != 'total']
        fig = px.pie(values=df['pred_percentage'], names=df['group'], title='Percent Cover of Benthic Groups')
        qtwebengineview_object.setHtml(fig.to_html(include_plotlyjs='cdn'))