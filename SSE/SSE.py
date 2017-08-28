#-*- coding: utf-8 -*-

import datetime
from flask import Flask, request, session, redirect, Response
import redis


app = Flask(__name__)
app.secret_key = 'test'

# 设置redis链接
r = redis.StrictRedis()

# 消息生成器
def event_stream():
    pubsub = r.pubsub()
    # subscript 'chat' channel
    pubsub.subscribe('chat')
    # start to listen , return the message when the message produced
    for message in pubsub.listen():
        print(message)
        # Server-sent Event ' s Data startswith 'data:'
        yield 'data: {0}\n\n'.format(message['data']).encode()

# event stream
@app.route('/stream')
def stream():
    # return Content-type == 'text/event-stream' SSE
    return Response(event_stream(), mimetype="text/event-stream")

# recive message from javascript's post
@app.route('/post', methods=['POST'])
def post():

    print("=================")
    message = request.form['message']
    user = session.get('user', 'anonymous')
    now = datetime.datetime.now().replace(microsecond=0).time()
    # put message into 'chat' channel
    r.publish('chat', u'[%s] %s: %s'%(now.isoformat(), user, message))
    return Response(status=204)


# login function , login required at the first time broswer
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # logging user ' s message into session
        session['user'] = request.form['user']
        return redirect('/')
    return '<form action="" method="post">user: <input name="user">'


@app.route('/')
def home():
    # check login
    if 'user' not in session:
        return redirect('/login')
    return u"""
        <!doctype html>
        <title>chat</title>
        <script src="http://cdn.staticfile.org/jquery/2.1.1/jquery.min.js"></script>
        <style>body { max-width: 500px; margin: auto; padding: 1em; background: black; color: #fff; font: 16px/1.6 menlo, monospace; }</style>
        <p><b>hi, %s!</b></p>
        <p>Message: <input id="in" /></p>
        <pre id="out"></pre>
        <script>
            function sse() {
                var source = new EventSource('/stream');
                var out = document.getElementById('out');
                source.onmessage = function(e) {
                    out.innerHTML =  e.data + '\\n' + out.innerHTML;
                };
            }
            $('#in').keyup(function(e){
                if (e.keyCode == 13) {
                    $.post('/post', {'message': $(this).val()});
                    $(this).val('');
                }
            });
            sse();
        </script>
    """%session['user']

if __name__ == '__main__':
    app.run(debug=True, threaded=True)


if __name__ == '__main__':
    app.run()
