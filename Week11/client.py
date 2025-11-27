from flask import Flask, request

app = Flask(__name__)

@app.route('/callback', methods=['POST'])
def callback():
    print("\n[WEBHOOK RECEIVED] Library Server Called")
    print("Received Payload:", request.json)
    return "OK", 200

if __name__ == '__main__':
    app.run(port=6000)