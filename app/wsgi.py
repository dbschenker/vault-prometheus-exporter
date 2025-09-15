from app import app

if __name__ == "__main__":
    """ Entrypoint for k8s application with gunicorn """
    app.run(threaded=True, debug=False)
