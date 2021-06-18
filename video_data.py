# code to access data from excel sheet and write it in format for database
import pandas as pd
import simplejson as simplejson

data = pd.read_csv('video_data.csv')
del data['v_id']
data.fillna("NULL", inplace=True)
data_tuple = tuple(data.itertuples(index=False, name=None))

with open("data_video.txt", "w") as f:
    for tuple_each in data_tuple:
        y = list(tuple_each)
        y[2] = y[2].replace("'", '"')
        simplejson.dump(y, f)
        print(len(y))
        f.write('\n')
