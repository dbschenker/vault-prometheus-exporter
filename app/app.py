from flask import Flask
from prometheus_client import generate_latest
import os
import cachetools.func
from lib import logger
from lib import healthcheck
from metrics import vault


metric_update_interval = int(os.environ.get('METRIC_UPDATE_INTERVAL', 300))


""" Setup root logger """
logger.setup()


app = Flask(__name__)


@app.route("/status")
def status():
    return healthcheck.status()


@app.route('/metrics')
@cachetools.func.ttl_cache(ttl=metric_update_interval)
def metrics():
    vault.update_metrics()
    return generate_latest()


@app.route('/')
def root():
    return '😀'


if __name__ == "__main__":
    """ Development entry point """
    app.run(threaded=True, debug=True, host="0.0.0.0", port=8080)
