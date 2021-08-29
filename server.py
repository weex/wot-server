#!/usr/bin/env python3
from flask import Flask
from flask import request
from flask import abort, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import and_

from settings import DATABASE_URI, DATA_DIR, SERVER_PORT, DEBUG
import os
import json
import random
import time
import string
import requests

from models import *


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# start time
start_time = time.time()
stored = 0

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

@app.route('/request')
def create_user():
    '''Creates user account (unverified).'''
    # extract account address from client request
    username = request.args.get('username')
    public_key = request.args.get('public_key')

    # check if user exists
    o = db.session.query(User).filter(User.public_key == public_key).first()
    print(o)
    if o is None:
        # create them
        o = User(username, public_key)
        print(o)
        db.session.add(o)
        db.session.commit()

        body = json.dumps({'result': 'success'},
                           indent=2)
    else:
        body = json.dumps({'result': 'error',
                           'message': 'Public key already exists.'},
                           indent=2)

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
    except:
        return ("JSON Decode failed", 400, {'Content-Type':'text/plain'})

    s = in_obj['source']          # source user's id
    t = in_obj['target']          # target user's id
    v = in_obj['value']           # integer value for rating

    trust = db.session.query(Trust).filter(and_(Trust.user_id == s, Trust.user_id2 == t)).first()
    if trust is None:
        trust = Trust(s, t, v)
        db.session.add(trust)
        db.session.commit()
    else:
        trust.value = v
        db.session.commit()
    
    body = json.dumps({'result': 'success'})
    code = 201
    
    return (body, code, {'Content-length': len(body),
                         'Content-type': 'application/json',
                        }
    )

@app.route('/delete', methods=['POST'])
def delete():
    '''Delete a key-value pair.'''
    # Validate JSON body w/ API params
    try:
        body = request.data.decode('utf-8')
        in_obj = json.loads(body)
    except:
        return ("JSON Decode failed", 400, {'Content-Type':'text/plain'})

    k = in_obj['key']
    d = in_obj['address']
    n = in_obj['nonce']
    s = in_obj['signature']

    # check signature
    owner = Owner.query.filter_by(delegate=d).first()
    if owner.nonce not in n or verify(o, k + o + n, s):
        body = json.dumps({'error': 'Incorrect signature.'})
        code = 401
    else:
        # check if key already exists and is owned by the same owner
        kv = db.session.query(Kv).filter_by(key=k).filter_by(owner=o).first()
        if kv is None:
            body = json.dumps({'error': 'Key not found or not owned by caller.'})
            code = 404
        else:
            # free up storage quota and remove kv
            size = len(kv.value)
            sale_id = kv.sale
            s = db.session.query(Sale).get(sale_id)
            s.bytes_used = s.bytes_used - size
            db.session.delete(kv)
            db.session.commit()
            body = json.dumps({'result': 'success'})
            code = 200
    
    return (body, code, {'Content-length': len(body),
                         'Content-type': 'application/json',
                        }
           )

@app.route('/get')
def get():
    '''Get ratings for the current user.'''
    
    user_id = request.args.get('source')

    trusts = Trust.query.filter_by(user_id=user_id).all()

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
