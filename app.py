from flask import Flask, render_template

import case_manager
import admin
import pacer

app = Flask(__name__)

app.config["JSON_SORT_KEYS"] = False # Disable Flask's automatic JSON sorting for debugging

app.register_blueprint(case_manager.case_blueprint)
app.register_blueprint(admin.admin_blueprint)
app.register_blueprint(pacer.pacer_blueprint)

@app.route("/hello")
def hello():
    return "<h1 style='color:blue'>Hello There!</h1>"

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/')
def login():
    return render_template('dashboard.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)