from flask import Flask, request
from werkzeug.serving import make_server
from loguru import logger
import json
import util

domain = '127.0.0.1'
port = 3150

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


# Patcher-related
@app.route("/patcher-start", methods=['POST'])
def patcher_start():
    # Patcher has signaled that it has started.
    global threader

    if threader.umaserver:
        threader.umaserver.en_patch_started = True
    return '', 200

@app.route("/patcher-finish", methods=['POST'])
def patcher_finish():
    # Patcher has signaled that it has finished.
    global threader

    json_data = json.loads(request.data.decode('utf-8'))
    if threader.umaserver:
        threader.umaserver.en_patch_success.append(json_data.get('success', False))
        threader.umaserver.en_patch_error = json_data.get('error', "")

    return '', 200


class UmaServer():
    en_patch_success = []

    def __init__(self, incoming_threader):
        global threader
        self.server = None
        threader = incoming_threader

        self.reset_en_patch()
    
    def reset_en_patch(self):
        self.en_patch_started = False
        self.en_patch_success.clear()
        self.en_patch_error = ""

    def run_with_catch(self):
        try:
            self.run()
        except Exception:
            util.show_error_box("Critical Error", "Uma Launcher has encountered a critical error and will now close.")

    def run(self):
        logger.info("Starting server")
        self.server = make_server(domain, port, app)
        self.server.serve_forever()

    def stop(self):
        logger.info("Stopping server")
        if self.server:
            self.server.shutdown()
        logger.info("Server stopped")