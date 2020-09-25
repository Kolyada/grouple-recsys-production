import pandas as pd
from tqdm import tqdm
from flask import Flask, request, jsonify, render_template
from yamlparams.utils import Hparam

from metrics import mean_average_presision_k, hitrate_k, novelty, coverage
from dataloader import Loader
from preprocessor import Preprocessor
from model import ImplicitALS
from read_dump import read_dump



def prepare_model(train_df, config):
    preprocessor = Preprocessor()

    train_df = preprocessor.filter_zeros(train_df)
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
    if not uid:
        return jsonify({'error': 'no user_id provided', 'args': request.args})
    if not all(list(map(str.isdigit, uid))):
        return jsonify({'error': 'given user_id is not numeric', 'args': request.args})
    
    # Handle broken user_id
    try:
        uix = mapper.get_user_ix(int(uid))
    except KeyError:
        return jsonify({'items': get_top_popular(n_rec), 'additional': 'top popular returned', 'args': request.args})
    
    # Calculate recommendations
    items = model.recommend_user(uix, n_rec)
    items = list([mapper.get_item_id(int(x)) for x in items])
    return jsonify({'items': items, 'args': request.args})


@app.route('/recalculate')
def recalc():
    # Updates recommender model and top popular list
    global model, mapper, top_popular
    path = '../data/raw/dorama-recommender-users.sql'
    table = 'dorama_recomm'
    
    # Reformat data from dump
    with open(config.path, 'w') as f:
        f.write(read_dump(path, table).getvalue())
    
    loader = Loader(config.path)
    df = loader.get_views_from_file(config.path)
    top_popular = df.groupby(config.data.item_id_field).count()['rate'].sort_values(ascending=False).index.tolist()[:100]
    
    mapper, model = prepare_model(df, config)
    return jsonify({'status': 'ok'})
    
        

if __name__ == "__main__":
    config = Hparam('./dorama_setting.yml')
#     path = config.path or config.base_path + config.dataset + '/'
    loader = Loader(config.path)
    df = loader.get_views_from_file(config.path)
    top_popular = df.groupby(config.data.item_id_field).count()['rate'].sort_values(ascending=False).index.tolist()[:100]
    
    mapper, model = prepare_model(df, config)
    app.run(host='0.0.0.0')
