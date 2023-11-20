import datetime

from keras.callbacks import EarlyStopping
from keras.layers import Dense
from keras.models import Sequential
from pandas import DataFrame
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from matplotlib import pyplot as plt
import numpy as np
import pandas as pd
from accuracy_estimates import *

from math import ceil
from sklearn.decomposition import PCA


class Prognostication:
    def __init__(self, initial_data: DataFrame, target_column: str, layers=5, test_set_size=0.2,
                 validation_set_size=0.2, activation_function='relu', optimizer='adam', pca_components=0,
                 epochs=20, first_layer=200, model_name='model'):
        self.first_layer = first_layer
        self.epochs = epochs
        self.initial_data = initial_data
        if pca_components:
            self.X, self.y = self.initial_data.drop(columns=[target_column]), self.initial_data[target_column]

            pca = PCA(n_components=pca_components)
            princ_df = pd.DataFrame(pca.fit_transform(self.X),
                                    columns=[f'component_{i + 1}' for i in range(pca_components)])
            self.initial_data = pd.concat([princ_df, self.initial_data[[target_column]]], axis=1)
        self.columns = list(self.initial_data.columns)
        self.columns.remove(target_column)
        self.train_data, self.test_data = train_test_split(self.initial_data, test_size=test_set_size, random_state=42)
        self.train_x, self.train_y = self.train_data.drop(columns=[target_column]), self.train_data[target_column]
        self.test_x, self.test_y = self.test_data.drop(columns=[target_column]), self.test_data[target_column]
        self.model = Sequential()
        st = self.first_layer
        self.model.add(Dense(st, activation=activation_function, input_shape=(self.train_x.shape[1],)))
        for i in range(layers - 1):
            st /= 2
            self.model.add(Dense(ceil(st), activation=activation_function))
        self.model.add(
            Dense(1)
        )

        self.model.compile(optimizer=optimizer, loss='mse')
        self.history = self.model.fit(self.train_x, self.train_y, validation_split=validation_set_size,
                                      epochs=self.epochs,
                                      callbacks=[EarlyStopping(patience=5, restore_best_weights=True)])
        self.predicted = self.model.predict(self.test_x)
        self.predict = np.reshape(self.predicted, self.predicted.shape[::-1])[0]
        self.model.save(model_name)

    @property
    def corr(self):
        return pearson(self.predict, self.test_y)

    @property
    def errors(self):
        return [f - d for f, d in zip(self.predict, self.test_y)]

    @property
    def bias(self):
        return sum(self.errors) / len(self.test_y)

    @property
    def mape(self):
        return sum([abs(e) / d for e, d in zip(self.errors, self.test_y)]) / len(self.test_y)

    @property
    def mae(self):
        return sum([abs(e) for e in self.errors]) / len(self.test_y)

    @property
    def rmse(self):
        return (sum([e ** 2 for e in self.errors]) / len(self.test_y)) ** 1 / 2

    def training_plot(self, save_to=None):
        plt.figure()
        plt.plot(self.history.history['loss'])
        plt.plot(self.history.history['val_loss'])
        plt.title('model loss')
        plt.ylabel('loss')
        plt.xlabel('epoch')
        plt.legend(['train', 'test'])
        if save_to:
            plt.savefig(save_to)
        else:
            plt.show()


def date_to_int(str_date: str, date_format: str) -> int:
    str_date = str_date[2:]
    date = datetime.datetime.strptime(str_date, date_format)
    year = date.year
    last_day_of_year = datetime.date(year=year - 1, day=31, month=12)
    diff = datetime.date(year=year, day=date.day, month=date.month) - last_day_of_year
    return diff.days


def prepare_data(initial_df):
    prepared_df = initial_df.dropna()
    prepared_df = pd.get_dummies(prepared_df, columns=['state'])
    prepared_df['hour'] = prepared_df['date'].apply(lambda x: int(x.split(':')[0].split(' ')[-1])
    if not x.split(':')[0].split(' ')[-1].startswith('0') else int(x.split(':')[0].split(' ')[-1][1:]))
    prepared_df['day'] = prepared_df['date'].apply(lambda x: date_to_int(x, '%y-%m-%d %H:%M:%S'))
    del prepared_df['date']
    del prepared_df['Unnamed: 0']
    if 'city_id' in prepared_df.columns:
        del prepared_df['city_id']
    columns = prepared_df.columns
    scaler = MinMaxScaler()
    scaled_df = scaler.fit_transform(prepared_df)
    return pd.DataFrame(scaled_df, columns=columns)


def generate_test_df(initial_df, times):
    states = initial_df['state'].unique().tolist()
    c = len(initial_df[initial_df['state'] == states[0]])
    res_df = initial_df[initial_df['state'] == states[0]].head(c // times)
    for st in states[1:]:
        c = len(initial_df[initial_df['state'] == st])
        res_df = pd.concat([res_df, initial_df[initial_df['state'] == st].head(c // times)])
    return res_df
