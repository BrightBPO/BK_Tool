from flask import Flask, render_template
import case_manager

app = Flask(__name__)

app.register_blueprint(case_manager.case_blueprint)

@app.route("/hello")
def hello():
    return "<h1 style='color:blue'>Hello There!</h1>"

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)