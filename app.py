from flask import Flask, render_template
import case_manager
import admin
import os

app = Flask(__name__)

app.config["JSON_SORT_KEYS"] = False # Disable Flask's automatic JSON sorting for debugging
app.secret_key = os.getenv("SESSION_KEY")  # Required for session handling

admin.login_manager.init_app(app)
admin.login_manager.session_protection = "strong"

app.register_blueprint(case_manager.case_blueprint)
app.register_blueprint(admin.admin_blueprint)

@app.route("/hello")
def hello():
    return "<h1 style='color:blue'>Hello There!</h1>"

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)