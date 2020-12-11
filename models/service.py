import sys
import json
import os
from datetime import datetime
import pandas as pd
from tqdm import tqdm
from flask import Flask, request, jsonify, render_template
from yamlparams.utils import Hparam
import gc

from implicitALS.dataloader import Loader
from implicitALS.preprocessor import Preprocessor
from implicitALS.model import ImplicitALS


def prepare_model(train_df, config):
    preprocessor = Preprocessor()

    train_df = preprocessor.filter_lazy_users(train_df, 0)
    # copy for filtering already viewd items from recommendations later
    orig_train = train_df.copy()
    
    # apply filters
    train_df = preprocessor.filter_zeros(train_df)
    train_df = preprocessor.cut_last_k_views(train_df, config.cut_last_k_views)

    preprocessor.build_mappers(train_df)
    train_df = preprocessor.map_ids(train_df)
    orig_train=preprocessor.map_ids(orig_train)
    print('Train df contains', train_df.shape[0], 'items')

    model = ImplicitALS(train_df, config, orig_train)
    model.fit()

    return preprocessor, model


def load_explorations_model(path):
    global mapper
    categories = json.load(open(path))
    # map data
    for cat in categories.keys():
        items = list(map(mapper.get_item_ix, categories[cat]))
        items = list(filter(lambda i: i!=-1, items)) # filter unknown items 
        categories[cat] = items
    return categories


def calc_top_popular(df):
    N = 70
    populars = df.groupby('item_id').count()['rate'].sort_values(ascending=False)
    populars = populars.index.tolist()
    return populars[:N]


from datetime import datetime as dt
time = lambda: '[%s]' % dt.now().strftime('%Y-%m-%d %H:%M:%S')


app = Flask(__name__)


def get_top_popular(n):
    return top_popular[:n]
@app.route('/topPopular', methods = ['GET'])
def f():
    # Returns n top popular items. default n=20
    n_recs = int(request.args.get('n_recs', 20))
    
    with open('logs/'+config.name+'-usage.log', 'a') as f:
        f.write('[%s] /topPopular n_recs=%s\n' % (time(), str(n_recs)))
    
    make_item = lambda idx, score: {'itemId': idx, 'siteId': config.site_id, 'score': score,
                                    'item_id': idx, 'site_id': config.site_id}
    items = [make_item(item, None) for item in get_top_popular(n_recs)]
    
    return jsonify({'isTopPop': 1, 'items': items, 'args': request.args,
                    'is_top_pop': 1})



@app.route('/explorations', methods = ['GET'])
def exploration():
    # Returns no-context recommendations based on items smartly groupped by genres
    # If user id provided, returns recommendations without already viewd items
    # explorations format
    # {category_name: [most_viewed_item1, ], }
    
    
    global mapper
    uid = request.args.get('user_id', None)
    uid_camel_case = request.args.get('userId', None)
    if uid_camel_case is not None:
        uid = uid_camel_case

    with open('logs/'+config.name+'-usage.log', 'a') as f:
        f.write('[%s] /explorations user_id=%s\n' % (time(), str(uid)))
    
    make_item = lambda idx, score: {'itemId': idx, 'siteId': config.site_id, 'score': score,
                                    'item_id': idx, 'site_id': config.site_id}
    
    def local2global_ids(expl_obj):
        # maps all items of explorational recs object to global ids
        mapped_expl_obj = dict()
        for cat in expl_obj.keys():
            mapped_expl_obj[cat] = [mapper.get_item_id(idx) for idx in expl_obj[cat]]
        return mapped_expl_obj
    
    def ids2items(expl_obj):
        items_expl_obj = dict()
        for cat in expl_obj.keys():
            items_expl_obj[cat] = [make_item(idx, None) for idx in expl_obj[cat]]
        return items_expl_obj
    
    def cats2list(expl_obj):
        explorations = [{'name': 'smf_%d'%i, 'items': v} for i, (k,v) in enumerate(expl_obj.items())]
        return explorations
    
    if uid is None or not all(map(str.isdigit, str(uid))): # bad or null user_id
        return jsonify(cats2list(ids2items(local2global_ids(explorations_categies))))
    
    uix = mapper.get_user_ix(int(uid))
    if uix == -1: # unknown user
        return jsonify(cats2list(ids2items(local2global_ids(explorations_categies))))
    else: # known user
        viewed_items = set(model.orig_df[model.orig_df.user_id == uix]['item_id'].tolist())
        # delete viewed items and empty categories from categories lists
        filtred_explorations = dict()
        for cat in explorations_categies.keys():
            # categories items are in local ids format. Dont forget to map to foreign ids when responsing
            filtred_items = [idx for idx in explorations_categies[cat] if idx not in viewed_items]
            if len(filtred_items):
                filtred_explorations[cat] = filtred_items
        return jsonify(cats2list(ids2items(local2global_ids(filtred_explorations))))
        
        
        
@app.route("/rateItem", methods=['POST'])
def rate_item():
    # saves information about user rate action
    # saves locally and writes out once per 30 minutes
    uid = request.args.get('user_id', None)
    iid = request.args.get('item_id', None)
    positive = request.args.get('positive', None)
    rate = request.args.get('rate', None)
    
    is_num = lambda s: all(map(str.isdigit, str(s)))
    if not all(map(is_num, (uid,iid))) or all(map(lambda v: v is None, (positive, rate))):
        return jsonify({'error': 'not all arguments are integers', 'args': request.args})
    
    uid, iid = list(map(int, (uid, iid)))
    uix = mapper.get_user_ix(uid)
    iix = mapper.get_item_ix(iid)
    # rate is binary, system needs 0..10
    if positive is not None:
        rate = float(positive) * 10
    elif rate is not None:
        rate = float(rate) * 10
    else:
        return jsonify({'error': 'rate or positive args should be provided'})
        
    if iix == -1:
        return jsonify({'error': 'unknown item id', 'args': request.args})
    
    if uix == -1: # unknown user
        # add user to mapper and update his data
        print('add user')
        mapper.add_user_id(uid)
        uix = mapper.get_user_ix(uid)
        model.add_user(uid, user_views=None)
    
    view = pd.DataFrame.from_records([(iix, rate, uix)], columns='item_id rate user_id'.split())
    model.orig_df = model.orig_df.append(view, ignore_index=True)
    # appending data to dataframe in runtime allows model to filter its recommendations 
    # to aware already rated items. Nothing writes to filesystem cause of frequent model
    # recalculating. During recalculation, model pulls data from original database which
    # must contains all users rate actions
    
    # Every N user action its recommendations recalculates
    user_views = model.orig_df[model.orig_df.user_id == uix]
    if len(user_views) % config.recalculate_user_every_n == 0:
        print('recalc user')
        model.update_user_data(uix, user_views)
    
    return jsonify({'status': 'ok'})



@app.route("/recommend", methods=['GET'])
def recommend():
    # Recommends n_recs items to user with id user_id. Fallbacks to top popular recommendation
    
    # Process request arguments
    uid = request.args.get('user_id', None)
    n_rec = int(request.args.get('n_recs', 5))
    
    with open('logs/'+config.name+'-usage.log', 'a') as f:
        f.write('[%s] /recommend user_id=%s n_recs=%s\n' % (time(), str(uid), str(n_rec)))
    
    if not uid:
        return jsonify({'error': 'no user_id provided', 'args': request.args})
    if not all(list(map(str.isdigit, uid))):
        return jsonify({'error': 'given user_id is not numeric', 'args': request.args})
    
    # Handle broken user_id
    make_item = lambda idx, score: {'itemId': idx, 'siteId': config.site_id, 'score': score,
                                    'item_id': idx, 'site_id': config.site_id}
    is_top_popular = 0
    recs = []
    try:
        uix = mapper.get_user_ix(int(uid))
        if uix == -1 or uix > model.max_uix: # unknown to service or unknown to model
            raise KeyError
        # Calculate recommendations
        items = model.recommend_user(uix, n_rec, return_scores=True)
        # to real ids
        items = [(mapper.get_item_id(idx), score) for idx, score in items]
        # to response format
        recs = [make_item(idx, float(score)) for idx, score in items]
    except KeyError:
        is_top_popular = 1
        recs = [make_item(idx, None) for idx in get_top_popular(n_rec)]
    
    return jsonify({'isTopPop': is_top_popular, 'items': recs, 'args': request.args,
                    'is_top_pop': is_top_popular})



@app.route('/similarItems', methods=['GET'])
def similar_items():
    iid = request.args.get('item_id', None)
    n_recs = int(request.args.get('n_recs', 10))
    
    with open('logs/'+config.name+'-usage.log', 'a') as f:
        f.write('[%s] /similarItems item_id=%s n_recs=%s\n' % (time(), str(iid), str(n_recs)))

    if iid is None or mapper.get_item_ix(int(iid)) == -1:
        return jsonify({'error': 'invalid item id', 'args': request.args})
    
    iix = mapper.get_item_ix(int(iid))
    
    # Similar items may be anonimized or filtred by user's views
    # If user id provided, return similar items that user havent seen
    uid = request.args.get('user_id', -1)
    uid_camel_case = request.args.get('user_id', -1)
    if uid_camel_case != -1:
        uid = uid_camel_case
    uix = mapper.get_user_ix(int(uid))
    if uix != -1 and uix < model.max_uix: # if model knows this user
        recs = model.similar_items_for_user(iix, uix, n_recs, return_scores=True)
    else:
        recs = model.similar_items(iix, n_recs, return_scores=True)
        
    # map to real ids
    make_item = lambda idx, score: {'itemId': idx, 'siteId': config.site_id, 'score': float(score),
                                    'item_id': idx,'site_id':config.site_id}
    recs = [make_item(mapper.get_item_id(idx), score) for idx, score in recs]
    return jsonify({'items': recs, 'args': request.args})
    
    
        
@app.route('/recalculate')
def recalc():
    # Updates recommender model and top popular list
    
    global loader, model, mapper, top_popular, config, df

    # if current views table is too old, recalc dump and fetch fresh data from it
    curr_timestamp = int(datetime.now().timestamp())
    last_modified = int(os.stat(config.path).st_mtime)
    if abs(curr_timestamp - last_modified) > 3600: # older then 1 hour
        os.system("mysqldump -uroot -proot recom all_recomm > /data/groupLe_recsys/raw/all-recommender-users.sql")
        os.system("mysqldump -uroot -proot recom likes > /data/groupLe_recsys/raw/likes.sql")
        os.system("python3 ../src/features/unpack_data.py")
        
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
    mapper, model = prepare_model(df, config)
    
    explorations_categies = load_explorations_model(config.explorations_path)
    top_popular = calc_top_popular(df)
    
    app.run(host='0.0.0.0', port=int(config.port))
