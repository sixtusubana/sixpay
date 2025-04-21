"""Application entry point."""
from CLIENT import create_app

app = create_app()

if __name__ == "__main__":
    #run on local server
    app.run(host="0.0.0.0", port=5004)

    # run on wifi
    # app.run(host="192.168.43.7", port=5000)
