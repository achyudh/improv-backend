
from sanic import Sanic
from sanic.response import json

app = Sanic()


@app.route("/webhook", methods=['POST'])
async def test(request):
    return json({"hello": "world"})


@app.route("/callback", methods=['POST'])
def callback(request):
    client = pymongo.MongoClient()
    pr_db = client.pr_database


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=60004)