# Flask_step1.py > ...

from flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
    return 'Hello World'

@app.route('/LED1on')
def led1on():
    return 'Here is LED1 ON page'

@app.route('/LED1off')
def led1off():
    return 'Here is LED1 OFF page'

@app.route('/LED2on')
def led2on():
    return 'Here is LED2 ON page'

@app.route('/LED2off')
def led2off():
    return 'Here is LED2 OFF page'

@app.route('/read/<id>')
def read(id):
    print(id)
    return 'Read ' + id

if __name__ == '__main__':
    app.run(port=8080, host='0.0.0.0')