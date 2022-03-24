from flask import Flask, render_template, redirect, url_for, request
import os

app = Flask(__name__)

@app.route('/')
def top_page():
    return render_template('default.html')


@app.route('/post_photo', methods=['POST'])
def post_photo():
    # https://qiita.com/ekzemplaro/items/77c0e764b277b0c84b0f
    photos = request.files.getlist('photos')
    print(len(photos))
    print(photos)
    for p in photos:
        print(p.filename)
    return redirect(url_for('top_page'))


if __name__=='__main__':
    app.config.from_object('config')
    app.run(debug=app.config['DEBUG'])
