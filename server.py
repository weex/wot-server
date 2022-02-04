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
def get_home():
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
def get_status():
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
def post_trust():
    '''Store a rating pair.'''

    try:
        body = request.data.decode('utf-8')
        in_obj = json.loads(body)
        source = in_obj['source']          # source user's id
        target = in_obj['target']          # target user's id
        value = in_obj['value']           # float value for rating
    except:
        body = '{"message": "JSON Decode failed"}'
        return (body, 400, {'Content-length': len(body),
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
                     }
           )


@app.route('/score')
def get_score():
    '''Get trusted status of target user from source's perspective.'''

    try:
        source = str(request.args.get('source')) # ignored for now, assumed to be 0
        target = str(request.args.get('target'))
    except:
        body = '{"message": "Missing one or more required parameters."}'
        return (body, 400, {'Content-length': len(body),
                            'Content-Type':'text/plain'})

    #trusts = Trust.query.filter_by(user_id=source).all()

    global scores
    body = str(target in scores and scores[target] >= 0 )

    return (body, 200, {'Content-length': len(body),
                         'Content-type': 'application/json',
                        }
           )


if __name__ == '__main__':
    if DEBUG:
        app.debug = True

    app.run(host='0.0.0.0', port=(os.environ.get('SERVER_PORT', SERVER_PORT)))
    #app.run(host='127.0.0.1', port=SERVER_PORT)
