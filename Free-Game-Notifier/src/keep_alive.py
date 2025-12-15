from Flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Bot is Running!"
    
def run():
    app.run(host="0.0.0.0", port=1000)

def keep_alive():
    t = Thread(target=run)
    t.start()