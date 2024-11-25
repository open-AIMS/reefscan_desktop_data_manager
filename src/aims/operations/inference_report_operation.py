import logging
import threading

import os

from aims.operations.abstract_operation import AbstractOperation

import plotly.express as px
import pandas as pd
import numpy as np
import seaborn as sns
from tqdm import tqdm
import random
from sklearn.metrics import f1_score
import io

import joblib

from sklearn.model_selection import train_test_split

from cleanlab.outlier import OutOfDistribution 



# this function peppers the training embeddings with noise, and then runs them through a pre trained classifier, as part of this process we measure the KNN distance and F1 scores on the peppered data to get an indication of how ‘this’ pretrained model will work when we go to a new site/capture method etc… 
def permutation_of_random_noise(model, scaler, encoder, X_train, y_train, weights=None, label_flip_percent=0, auglabel="Jumble", perms=1000):

    # X_train_filtered = [x for x in X_train if isinstance(x, (int, float))]
    # y_train_filtered = [y for x, y in zip(X_train, y_train) if isinstance(x, (int, float))]

    # X_train = np.array(X_train_filtered)
    # y_train = np.array(y_train_filtered)


    # Create a mask to identify numeric elements in X_train
    mask = np.array([[isinstance(elem, (int, float)) for elem in row] for row in X_train])

    # Apply the mask to X_train and y_train
    X_train_numeric = X_train[mask.all(axis=1)].astype(float)
    # y_train_numeric = y_train[mask.all(axis=1)].astype(float)

    X_train = X_train_numeric
    # y_train = y_train_numeric

    intensities = np.random.lognormal(.1, 2, perms)

    ood = OutOfDistribution()
    ood_train_feature_scores = ood.fit_score(features=X_train)

    feature_modified_distances = []

    for i in tqdm(range(0, perms)):

        no_of_indexes_to_modify = 1
        j = random.sample(range(0, 3), no_of_indexes_to_modify)[0]
        m = random.sample(range(1, 200), 1)[0]

        #  y_train = encoder.transform(y_train)

        #    X_samp, y_samp = sample_Xy(X_train, y_train, int(len(X_train)*.8))
        X_samp, y_samp = X_train, y_train

        X_res = X_samp.copy()
        y_res = y_samp

        for label in np.unique(y_res):
            indexes = np.where(y_res == label)
            level = intensities[i]
            noise = np.random.uniform(-level, level, 128)
            X_res[indexes] = np.add(X_res[indexes], noise)

        X_res = scaler.fit_transform(X_res, y_res)

        yhat = model.predict(X_res)

        pred = encoder.inverse_transform(yhat)
        #  pred = yhat

        pred_probs = model.predict_proba(X_res)
        print(y_res)
        print(pred)
        f1 = f1_score(y_res, pred, average='weighted')
        confidence = np.average(np.amax(pred_probs, axis=1))


        df1 = {}
        df1["f1_score"] = f1
        df1["cleanlab_global"] = ood.score(features=X_res).mean()
        df1["feature"] = "%s %s" % (str(m), str(m))
        df1["augmentation"] = auglabel
        df1["noise_intensity"] = m
        df1["confidence"] = confidence
        feature_modified_distances.append(df1)

    feature_modified_distance_f1 = pd.DataFrame.from_dict(feature_modified_distances)

    return feature_modified_distance_f1

# Utility function
def get_XY(df, n_features=128, label_col='encoded_label'):
    feat_cols = []
    for i in range(n_features):
        feat_cols.append('feature_vector_{}'.format(i))

    df = df.fillna(0)

    X = df[feat_cols].to_numpy()
    y = df[label_col].to_numpy()

    return X, y

class InferenceReportOperation(AbstractOperation):
    X_train = []
    X_test = []
    X_inf = []
    y_train = []
    y_test = []
    y_inf = []
    features_df = pd.DataFrame()
    training_features_df = pd.DataFrame()
    feature_modified_distance_f1 = pd.DataFrame()
    
    def features_detected(self):
        return not self.features_df.empty

    def perform_analysis(self, features_csv_path, training_csv_path, classifier_path):
        
        df = pd.read_csv(features_csv_path)
        df = df[df['point_human_classification'].notnull()]
        self.features_df = df

        training_df = pd.read_csv(training_csv_path)
        training_df = training_df[training_df['point_human_classification'].notnull()]
        self.training_features_df = training_df


        if not self.features_df.empty:
            ## For the train-val and train-inf distances
            self.dataset_distance_report()

            ## For the f1 correlation plot
            self.perform_threshold_detection(classifier_path)

    def get_distance_report(self):
        distance_data = self.calculate_distance()
        return distance_data

    def get_correlation_plot(self):
        sns_lmplot = sns.lmplot(
            data=self.feature_modified_distance_f1,
            x="cleanlab_global", y="f1_score"
            )
        
        buffer = io.BytesIO()
        sns_lmplot.savefig(buffer, format='png')
        buffer.seek(0)

        return buffer
        
    def dataset_distance_report(self):

        # df = pd.read_csv(features_csv_path)
        # LABEL_KEY = "point_human_classification"

        # df = df.dropna(subset=[LABEL_KEY])

        X_inf, y_inf = get_XY(self.features_df, label_col='point_human_classification')

        tX, ty = get_XY(self.training_features_df, label_col='point_human_classification')  

        X_train, X_test, y_train, y_test = train_test_split(tX, ty, train_size=.8, random_state=42)

        self.X_train = X_train
        self.X_test = X_test
        self.X_inf = X_inf
        self.y_train = y_train
        self.y_test = y_test
        self.y_inf = y_inf

    def calculate_distance(self):
        # prep the OOD detection on the training data
        ood = OutOfDistribution()
        ood_train_scores = ood.fit_score(features=self.X_train)

        # get the train/val distance
        cleanlab_dist_train_val = ood.score(features=self.X_test).mean()

        # get the train/inferenced-data distance
        cleanlab_dist_train_inference = ood.score(features=self.X_inf).mean()

        return (cleanlab_dist_train_val, cleanlab_dist_train_inference)

    def perform_threshold_detection(self, classifier_path):

        classifier = joblib.load(classifier_path)
        model = classifier[0]
        scaler = classifier[1]
        encoder = classifier[2]


        # call the random noise function which takes training embeddings, and a pretrained scikit classifier on those embeddings - will send back a dataframe the F1 scores related to KNN distance
        self.feature_modified_distance_f1 = permutation_of_random_noise(model, scaler, encoder, 
                                                                        self.X_train, self.y_train, 
                                                                        label_flip_percent=0, 
                                                                        auglabel="Gaussian ", perms=100)
