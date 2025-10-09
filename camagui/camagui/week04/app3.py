from flask import Flask, render_template, jsonify
import random

temp = [25.5, 33.2, 28.6, 27.3, 29.5, 30.2, 31.7, 32.4, 32.9, 33.1]

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('Transfer3.html')

@app.route('/data')
def getdata():
    return jsonify(temp)

if __name__ == '__main__':
    app.run(host='192.168.205.126',debug = True, port=8080)