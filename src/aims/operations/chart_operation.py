import logging
import os

import pandas as pd
import plotly.express as px

logger = logging.getLogger("")


class ChartOperation:

    def create_pie_chart_png(self, coverage_results_file, output_png_file):
        df = self.read_csv(coverage_results_file)
        fig = px.pie(values=df['pred_percentage'], names=df['group'], title='Percent Cover of Benthic Groups')
        fig.write_image(output_png_file)
        return output_png_file

    def read_csv(self, coverage_results_file):
        df = pd.read_csv(coverage_results_file)
        df = df[df['group'] != 'total']
        return df

