# Config description

Use this for changing configuration of server. Restart server (see `deploy.md`) to apply new settings

## Fields

### Boot params
- path - path to csv user-item-rate table
- explorations_path - path to precalculated cold-start recommendations
- port - server web port


### Model-specific
- regularization - regularization for matrixes in matrix factorization
- alpha - coefficient of implicit feedback importance
- factors - latent dimesion size
- iterations - number of training iterations

### Site-specific
- site_id - local site id
- name - site name

### Data-preprocessing
- recalculate_user_every_n - number of likes for user after which model will recalculate his recommendation
- min_user_views - lower bound of user's actions. If user has less rates, recommendation system will not know him
- cut_last_k_views - how many user rates recommender system will use to calculate user's preferences. If user has more rates, older will be thrown out
