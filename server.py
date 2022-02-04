#!/usr/bin/env python3
from flask import Flask
from flask import request
from flask import abort, url_for
#from flask_sqlalchemy import SQLAlchemy
#from sqlalchemy import and_

from settings import DATABASE_URI, DATA_DIR, SERVER_PORT, DEBUG
import os
import json
import random
import time
import string
import requests

#from models import *

from weboftrust import (load_data, calc_paths_and_ranks, get_capacity,
                       derive_capacities, calculate_score, calculate_score_for_all,
                       update_scores_from_one_trust)

app = Flask(__name__)
#app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
#app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
#db = SQLAlchemy(app)

# start time
start_time = time.time()
stored = 0

trusts, G = load_data("testdata/test01.csv")
ownidentity = "0"
paths, ranks = calc_paths_and_ranks(G, trusts, ownidentity)
capacities = derive_capacities(ranks)
scores = calculate_score_for_all(G, paths, capacities, ownidentity)

@app.route('/')
@app.route('/help')
def home():
    '''Home endpoint'''
    home_obj = [{"name": "wot-server",
                 "description": "Server to support moderation via web-of-trust. Visit github.com/weex/wot-server for more info."
                }
               ]

    body = json.dumps(home_obj, indent=2)

    return (body, 200, {'Content-length': len(body),
                        'Content-type': 'application/json',
                       }
                       )

@app.route('/status')
def status():
    '''Return general info about server instance. '''
    uptime = str(int(time.time() - start_time))
    st = os.statvfs(DATA_DIR)
    free = st.f_bavail * st.f_frsize
    body = json.dumps({'uptime': uptime,
                       'free': str(free/1024/1024) + " Mb",
                      }, indent=2
                     )
    return (body, 200, {'Content-length': len(body),
                        'Content-type': 'application/json',
                       }
           )

#rate
@app.route('/trust', methods=['POST'])
def put():
    '''Store a rating pair.'''

    try:
        body = request.data.decode('utf-8')
        in_obj = json.loads(body)
        source = in_obj['source']          # source user's id
        target = in_obj['target']          # target user's id
        value = in_obj['value']           # float value for rating
    except:
        body = '{"message": "JSON Decode failed"}'
        return (body, 400, {'Content-length': 0,
                            'Content-Type':'text/plain'})

    global scores
    scores = update_scores_from_one_trust(G, trusts, paths, ranks, capacities, scores, ownidentity, source, target, value) 

    print(scores)

    #trust = db.session.query(Trust).filter(and_(Trust.user_id == s, Trust.user_id2 == t)).first()
    #if trust is None:
    #    trust = Trust(s, t, v)
    #    db.session.add(trust)
    #    db.session.commit()
    #else:
    #    trust.value = v
    #    db.session.commit()
    
    return ('', 200, {'Content-length': 0,
                      'Content-type': 'application/json',
                     })


@app.route('/score')
def get():
    '''Get trusted status of target user from source's perspective.'''
    
    source = request.args.get('source')
    target = request.args.get('target')

    trusts = Trust.query.filter_by(user_id=source).all()

    if trusts is None:
        body = json.dumps({'error': 'User not found.'})
        code = 404
    else:
        body = json.dumps(trusts)
        code = 200

    return (body, code, {'Content-length': len(body),
                         'Content-type': 'application/json',
                        }
           )

def has_no_empty_params(rule):
    '''Testing rules to identify routes.'''
    defaults = rule.defaults if rule.defaults is not None else ()
    arguments = rule.arguments if rule.arguments is not None else ()
    return len(defaults) >= len(arguments)

@app.route('/info')
def info():
    '''Returns list of defined routes.'''
    links = []
    for rule in app.url_map.iter_rules():
        # Filter out rules we can't navigate to in a browser
        # and rules that require parameters
        if "GET" in rule.methods and has_no_empty_params(rule):
            url = url_for(rule.endpoint, **(rule.defaults or {}))
            links.append(url)

    return json.dumps(links, indent=2)


if __name__ == '__main__':
    if DEBUG:
        app.debug = True

    app.run(host='0.0.0.0', port=(os.environ.get('SERVER_PORT', SERVER_PORT)))
    #app.run(host='127.0.0.1', port=SERVER_PORT)
