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
                       'stored': str(st),
                       'free': str(free),
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
@app.route('/rate', methods=['POST'])
def put():
    '''Store a key-value pair.'''
    # get size of file sent
    # Validate JSON body w/ API params
    try:
        body = request.data.decode('utf-8')
        in_obj = json.loads(body)
    except:
        return ("JSON Decode failed", 400, {'Content-Type':'text/plain'})

    k = in_obj['key']
    v = in_obj['value']
    o = in_obj['owner']
    n = in_obj['nonce']
    s = in_obj['signature']
    d = in_obj['signature_address']
    if 'testnet' in in_obj:
        testnet = in_obj['testnet']
    else:
        testnet = False

    owner = Owner.query.filter_by(address=o).first()
    if owner is None:
        body = json.dumps({'error': 'User not found'})
        code = 403
    elif owner.nonce != n:
        body = json.dumps({'error': 'Bad nonce'})
        code = 401
    elif not verify(d, k + v + d + n, s) :
        body = json.dumps({'error': 'Incorrect signature'})
        code = 401
    else:
        size = len(k) + len(v)

        # need to also check that we have an enrollment that makes this a delegate of this owner

        # check if owner has enough free storage
        # get free space from each of owner's buckets
        result = db.engine.execute('select * from sale where julianday("now") - \
                    julianday(sale.created) < sale.term order by sale.created desc')
        # choose newest bucket that has enough space
        sale_id = None
        for row in result:
            if (row[7] + size) < (1024 * 1024):
                sale_id = row[0]
    
        if sale_id is None:     # we couldn't find enough free space
            body = json.dumps({'error': 'Insufficient storage space.'})
            code = 403 
        else:
            # check if key already exists and is owned by the same owner
            kv = db.session.query(Kv).filter(and_(Kv.key == k, Kv.owner == o)).first()
            if kv is None:
                kv = Kv(k, v, o, sale_id, testnet)
                db.session.add(kv)
                db.session.commit()
            else:
                kv.value = v
                db.session.commit()
    
            s = db.session.query(Sale).get(sale_id)
            s.bytes_used = s.bytes_used + size
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
    
    key = request.args.get('key')

    kv = Kv.query.filter_by(key=key).first()

    if kv is None:
        body = json.dumps({'error': 'Key not found.'})
        code = 404
    else:
        body = json.dumps({'key': key, 'value': kv.value})
        code = 200

    # calculate size and check against quota on kv's sale record
    return (body, code, {'Content-length': len(body),
                        'Content-type': 'application/json',
                        }
           )

# login request
@app.route('/nonce')
def nonce():
    '''Return 32-byte nonce for generating non-reusable signatures..'''
    # check if user exists
    o = db.session.query(Owner).get(request.args.get('address'))
    if o is None:
        return abort(500)

    # clear the nonce by sending it to the server
    if request.args.get('clear') and request.args.get('clear') == o.nonce:
        o.nonce = ''
        db.session.commit()
        body = json.dumps({'nonce': o.nonce})
    # if nonce is set for user return it, else make a new one
    elif o.nonce and len(o.nonce) == 32:
        body = json.dumps({'nonce': o.nonce})
    # if not, create one and store it
    else:
        print("storing")
        n = ''.join(random.SystemRandom().choice(string.hexdigits) for _ in range(32))
        o.nonce = n.lower()
        db.session.commit()
        body = json.dumps({'nonce': o.nonce})

    return (body, 200, {'Content-length': len(body),
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
