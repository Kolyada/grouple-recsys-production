from math import log2
from tqdm import tqdm


def _get_unique_items(predictions):
    items = set()
    for p in predictions:
        for pitem in p:
            items.add(pitem)
    return items


def personalization(predictions):
    print('[WARN] Very slow')
    sum_similarity = 0.
    n_similarity = 0
    items_n = len(_get_unique_items(predictions))
    
    def calc_sim(rec1, rec2):
        common_items_n = len(set(rec1).intersection(set(rec2)))
        max_len = max(len(rec), len(rec2))
        return common_items_n / max_len
        
    for i, rec in tqdm(enumerate(predictions[:-1])):
        for j, rec2 in (enumerate(predictions[i+1:], start=i+1)):
            sum_similarity += calc_sim(rec, rec2)
            n_similarity += 1

    return 1 - (sum_similarity / n_similarity)



def novelty(predictions, k):
    predictions = list(map(lambda recs: recs[:k], predictions))
    items = _get_unique_items(predictions)
    set_predictions = list(map(set, predictions))
            
    count_per_user = lambda item: sum([1 if item in recs else 0 for recs in set_predictions])
    consume_list = dict()
    for item in (list(items)):
        consume_list[item] = count_per_user(item)
    
    users_n = len(predictions)
    nov = 0.
    for u, rec in (enumerate(predictions)):
        self_info = sum([-log2(consume_list[item] / users_n) for item in rec])
        self_info /= len(rec)
        nov += self_info

    return nov / users_n


def coverage(predictions, items, k):
    predictions = list(map(lambda recs: recs[:k], predictions))
    pred_items = _get_unique_items(predictions)
    common_items = set(pred_items).intersection(set(items))
    return len(common_items) / len(set(items))



def _avg_precision(recs, gt):
    # rec: list of recommended items
    # gt:  list of gt items
    return len(set(recs).intersection(set(gt))) / len(gt)


def mean_average_presision_k(recs, gt, k=5):
    # recs: list of lists of recommended items
    # gt:   list of lists of gt items
    assert len(recs) == len(gt)
#     assert len(recs[0]) >= k, 'len recs is %d, k is %d' % (len(recs[0]), k)
    
    ap = 0.
    for i, rec in (enumerate(recs)):
        user_rec = rec[:k]
        user_gt = gt[i][:k]
        ap += _avg_precision(user_rec, user_gt)
    
    return ap / len(recs)



def hitrate_k(recs, gt, k=5):
    assert len(recs) == len(gt)
#     assert len(recs[0]) >= k
    
    corr = 0
    for i, rec in (enumerate(recs)):
        user_rec = rec[:k]
        user_gt = gt[i][:k]
        
        if len(set(user_rec).intersection(set(user_gt))) != 0:
            corr += 1
            
    return corr / len(recs)