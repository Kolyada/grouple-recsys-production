import aiohttp
import asyncio
import logging
from time import sleep
from tqdm import tqdm
import pymongo
import requests
from grouple_session import GroupleSession
from arqtty_scrapper import requester
from parser import Parser
import page_classifier

logging.basicConfig(level=logging.INFO)


USERS = 1695000 # 06.01.2020

# Database
def get_coll(client, db_name, coll_name):
    db = client[db_name]
    coll = db[coll_name]
    return coll
def push_batch(collection, batch, ids):
    for i in range(len(batch)):
        key = ids[i]
        batch[i]['_id'] = key
        try:
            collection.insert_one(batch[i])
        except pymongo.errors.DuplicateKeyError:
            logging.error("Duplicating mongo key %d" % key)
def get_last_item_id():
    return coll.find().sort('_id', -1).next()['_id'] + 1
            
    
DB_NAME = 'groupLe'
COLLECTION_NAME = 'users_manga_rates'
client = pymongo.MongoClient('mongodb://localhost:27017')
coll = get_coll(client, DB_NAME, COLLECTION_NAME)

# Create necessary instances
def load_proxies():
    proxies = []
    with open('proxylist.txt', 'r') as fin:
        for line in fin:
            values = line.strip().split(':')
            fields = 'address port login password'.split()
            proxy = {key: val for key, val in zip(fields, values)}
            proxies.append(proxy)
    return proxies
            
# Create authenticated session
print('Creating sessions')
sessions = [GroupleSession(proxy) for proxy in load_proxies()]
parser = Parser()

# problem with 50313 - 67k datapoints
# from begin: stop at 78270

# LOADED:
# 1 - 486319  # 25000 missing

ban_guard = False
print('Start crawling')
for u in range(get_last_item_id(), USERS, len(sessions)):
    sleep(0.6)
    url = 'https://grouple.co/user/{}/bookmarks'

    urls_batch = [url.format(id) for id in range(u, u+len(sessions))]
    logging.info("Start load users %d-%d" % (u, u+len(sessions)))
    
    data = requester.load_users(sessions, urls_batch)
    parsed = [parser.parse(data[i][0]) for i in range(len(sessions))]
    print(' '.join(['OK' if item['username'] else 'BAN' for item in parsed]))

    # if all proxy are banned
    if ban_guard:
        if len(set(list(map(str, parsed)))) == 1 and parsed[0]['username'] == None:
            print("Stop due banned proxies")
            break

    push_batch(coll, parsed, [x for x in range(u, u+len(sessions))])
