from keras.models import load_model
from neural_network.nn import *
import pickle
import random
from eli5.sklearn import PermutationImportance
import warnings
warnings.filterwarnings("ignore")

df = pd.read_csv('data/weather_with_area_with_factories_sectors_final_preprocessed_6.csv')
for col in df.columns:
    if col.startswith('Unnamed'):
        del df[col]

model = load_model('model')
train_data, test_data = train_test_split(df, test_size=0.05, random_state=random.randint(1, 50))
train_x, train_y = train_data.drop(columns=['aqi']), train_data['aqi']
test_x, test_y = test_data.drop(columns=['aqi']), test_data['aqi']
perm = PermutationImportance(model, random_state=random.randint(1, 50), scoring="neg_mean_squared_error").\
    fit(test_x, test_y)
with open(f'importances_final/imp.pickle', 'wb') as f:
    pickle.dump(zip(list(perm.results_[0]), list(test_x.columns.tolist())), f)
