from website import create_app
import argparse
from ipaddress import ip_address

parser = argparse.ArgumentParser(
    description="Launches a webserver, capable of automating social media posts"
)
parser.add_argument('--host', type=ip_address, help="host ip adress")
parser.add_argument('--port', type=int, help="host port")
args = parser.parse_args()

if args.host:
    host = str(args.host)
else:
    host = None

if args.port:
    port = args.port
else:
    port = None

app = create_app()

if __name__ == "__main__":
    # url = 'http://127.0.0.1:5001'
    # webbrowser.open_new(url)
    app.run(debug=True, host=host, port=port)