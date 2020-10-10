import sys
import os
from datetime import datetime
import pandas as pd
from tqdm import tqdm
from flask import Flask, request, jsonify, render_template
from yamlparams.utils import Hparam
import gc

from metrics import mean_average_presision_k, hitrate_k, novelty, coverage
from dataloader import Loader
from preprocessor import Preprocessor
from model import ImplicitALS
from read_dump import read_dump



def prepare_model(train_df, config):
    preprocessor = Preprocessor()

#     train_df = preprocessor.filter_zeros(train_df)
    train_df = preprocessor.filter_lazy_users(train_df, 0)
    preprocessor.build_mappers(train_df)

    train_df.user_id  = train_df.user_id.apply(preprocessor.get_user_ix)
    train_df.item_id = train_df.item_id.apply(preprocessor.get_item_ix)
    print('Train df contains', train_df.shape[0], 'items')

    model = ImplicitALS(train_df, config)
    model.fit()

    return preprocessor, model


def get_top_popular(n):
    return top_popular[:n]
def calc_top_popular(df):
    N = 70
    populars = df.groupby('item_id').count()['rate'].sort_values(ascending=False)
    populars = populars.index.tolist()
    return populars[:N]
    

from datetime import datetime as dt
time = lambda: '[%s]' % dt.now().strftime('%H:%M:%S')


app = Flask(__name__)

@app.route('/')
def f():
    return render_template('index.html')


@app.route("/recommend")
def hello():
    # Recommends n_recs items to user with id user_id. Fallbacks to top popular recommendation
    
    # Process request arguments
    uid = request.args.get('user_id', None)
    n_rec = int(request.args.get('n_recs', 5))
    
    with open(config.name+'-usage.log', 'a') as f:
        f.write('[%s] /recommend user_id=%s n_recs=%s\n' % (time(), str(uid), str(n_rec)))
    
    if not uid:
        return jsonify({'error': 'no user_id provided', 'args': request.args})
    if not all(list(map(str.isdigit, uid))):
        return jsonify({'error': 'given user_id is not numeric', 'args': request.args})
    
    # Handle broken user_id
    make_item = lambda idx, score: {'itemId': idx, 'siteId': config.site_id, 'score': float(score)}
    is_top_popular = 0
    recs = []
    try:
        uix = mapper.get_user_ix(int(uid))
        # Calculate recommendations
        items = model.recommend_user(uix, n_rec, return_scores=True)
        # to real ids
        items = [(mapper.get_item_id(idx), score) for idx, score in items]
        # to response format
        recs = [make_item(idx, score) for idx, score in items]
    except KeyError:
        is_top_popular = 1
        recs = [make_item(idx, 1) for idx in get_top_popular(n_rec)]
    
    return jsonify({'isTopPop': is_top_popular, 'items': recs, 'args': request.args})


@app.route('/recalculate')
def recalc():
    # Updates recommender model and top popular list
    
    global loader, model, mapper, top_popular, config

    # if current views table is too old, recalc dump and fetch fresh data from it
    curr_timestamp = int(datetime.now().timestamp())
    last_modified = int(os.path.getmtime(config.path))
    if curr_timestamp - last_modified < 3600: # older then 1 hour
        os.system("mysqldump -uroot -proot recom all_recomm > /data/groupLe_recsys/all/raw/all-recommender-users.sql")
        os.system("python3 ../unpack_data.py")
        
    # delete huge data to avoid memory overhead    
    del df
    gc.collect()
    
    # recalc top populars and model
    df = loader.get_views()
    top_popular = calc_top_popular(df)

    # reread config
    config = Hparam(cfg_path)
    mapper, model = prepare_model(df, config)
    return jsonify({'status': 'ok', 'lastDataUpdateTimestamp': last_modified})
    
        

if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise AttributeError('Use config name to define model config and port to define service port')
    cfg_path = sys.argv[1] #'books_big_setting.yml'
    config = Hparam(cfg_path)
    
    loader = Loader(config.path)
    df = loader.get_views()
    top_popular = calc_top_popular(df)
    
    mapper, model = prepare_model(df, config)
    app.run(host='0.0.0.0', port=int(config.port))
