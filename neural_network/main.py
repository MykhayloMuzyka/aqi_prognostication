from nn import *
import pandas as pd


df = pd.read_csv('data/weather_with_area_with_factories_sectors_final_preprocessed_6.csv')
model = Prognostication(df, 'aqi', test_set_size=0.05, validation_set_size=0.1, first_layer=600,
                        optimizer='adamax', activation_function='relu', pca_components=0, epochs=50, layers=5)
model.training_plot('permutation_importance/model')
print(model.model.summary())
print(f'Bias: {bias(model.test_y.values, model.predicted.reshape(-1))}')
print(f'MAPE: {MAPE(model.test_y.values, model.predicted.reshape(-1))}')
print(f'MAE: {MAE(model.test_y.values, model.predicted.reshape(-1))}')
print(f'RMSE: {RMSE(model.test_y.values, model.predicted.reshape(-1))}')
print(f'Pearson: {pearson(model.test_y.values, model.predicted.reshape(-1))}')
