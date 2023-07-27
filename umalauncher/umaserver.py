from flask import Flask, request
from werkzeug.serving import make_server
from loguru import logger
import json
import util

app = Flask(__name__)
threader = None

@app.route('/')
def index():
    return 'Hello World!'

# @app.route('/open-skill-window', methods=['OPTIONS'])
# def open_skills_window_options():
#     return '', 200

@app.route('/open-skill-window', methods=['POST'])
def open_skills_window():
    global threader
    if threader.carrotjuicer:
        threader.carrotjuicer.open_skill_window = True

    return '', 200

@app.route('/helper-window-rect', methods=['POST'])
def helper_window_rect():
    global threader
    # Json is sent as text/plain in body.
    json_data = json.loads(request.data.decode('utf-8'))
    
    if threader.carrotjuicer:
        threader.carrotjuicer.last_browser_rect = json_data

    return '', 200

@app.route('/skills-window-rect', methods=['POST'])
def skills_window_rect():
    global threader
    # Json is sent as text/plain in body.
    json_data = json.loads(request.data.decode('utf-8'))
    
    if threader.carrotjuicer:
        threader.carrotjuicer.last_skills_rect = json_data

    return '', 200

class UmaServer():
    def __init__(self, incoming_threader):
        global threader
        self.server = None
        threader = incoming_threader

    def run_with_catch(self):
        try:
            self.run()
        except Exception:
            util.show_error_box("Critical Error", "Uma Launcher has encountered a critical error and will now close.")

    def run(self):
        logger.info("Starting server")
        self.server = make_server('127.0.0.1', 3150, app)
        self.server.serve_forever()

    def stop(self):
        logger.info("Stopping server")
        if self.server:
            self.server.shutdown()
        logger.info("Server stopped")