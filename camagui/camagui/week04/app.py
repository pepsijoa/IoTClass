from flask import Flask, render_template
import random

temp = [25.5, 33.2, 28.6, 27.3, 29.5, 30.2, 31.7, 32.4, 32.9, 33.0]

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('Transfer2.html', data=temp)

if __name__ == '__main__':
    app.run(debug=True, port=8080)

#host='0.0.0.0', 