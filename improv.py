
from sanic import Sanic
from sanic import response
from jwt import jwk_from_pem
from requests.auth import HTTPBasicAuth
from util import io
import requests, json, urllib, pymongo, sys, secrets

app = Sanic()
with open("config.json", 'r') as config_file:
    client_config = json.load(config_file)
with open("private-key.pem", 'rb') as priv_key_file:
    priv_key = jwk_from_pem(priv_key_file.read())
http_auth_username = client_config['HTTP_AUTH_USERNAME']
http_auth_secret = client_config['HTTP_AUTH_SECRET']
http_auth = HTTPBasicAuth(http_auth_username, http_auth_secret)
app.config['SESSION_TYPE'] = 'mongodb'
app.config['GITHUB_CLIENT_ID'] = client_config['GITHUB_CLIENT_ID']
app.config['GITHUB_CLIENT_SECRET'] = client_config['GITHUB_CLIENT_SECRET']


@app.route("/webhook", methods=['POST'])
async def test(request):
    if request.json is None:
        print("NULL REQUEST: " + request.headers, file=sys.stderr)
        return response.json({}, status=400)

    elif "action" not in request.json and request.headers['X-GitHub-Event'] == "ping":
        # POST request has initial webhook and repo details
        client = pymongo.MongoClient()
        pr_db = client.im_database
        # Insert init repo info into DB
        pr_db.webhook_init.insert_one(request.json)
        return response.json({}, status=200)

    elif request.json.get("action", None) == "created" and request.headers['X-GitHub-Event'] == "installation":
        client = pymongo.MongoClient()
        pr_db = client.im_database
        # Insert init repo info into DB
        pr_db.app_init.insert_one(request.json)
        return response.text('Install successful', status=200)

    elif request.json.get("action", None) == "opened" and request.headers['X-GitHub-Event'] == "pull_request":
        parsed_json = request.json
        is_private_repo = request.json["pull_request"]["base"]["repo"]["private"]
        pr_num = parsed_json["pull_request"]["number"]
        pr_id = parsed_json["pull_request"]["id"]
        repo_id = parsed_json["pull_request"]["base"]["repo"]["id"]



        if "installation" in request.json:
            pr_comment_url = 'https://api.github.com/repos/%s/issues/%s/comments' % (parsed_json["pull_request"]["base"]["repo"]["full_name"], pr_num)
            pr_comment_payload = json.dumps({"body": "### Improv Reviewability Report"
                                                     "\n\n*Major deterrents to the reviewability of this pull request:*\n"
                                                     ":x: Factor One\n"
                                                     "\n\n*Factors that might impair the reviewability of this pull request:*\n"
                                                     ":large_orange_diamond: Factor Two\n"
                                                     "\n\n*Factors that improve the reviewability of this pull request:*\n"
                                                     ":heavy_check_mark: Factor Three\n"
                                                     ":heavy_check_mark: Factor Four\n"
                                             })
            r = requests.post(pr_comment_url, data=pr_comment_payload, headers=io.get_auth_header(request.json["installation"]["id"], priv_key))
        else:
            return response.text("Authentication error", status=500)
        if not is_private_repo:
            io.download_patch(parsed_json["pull_request"]["patch_url"], http_auth, pr_id, repo_id)
        return response.text("OK")
    else:
        return response.text("Request not handled", status=202)


@app.route("/callback", methods=['POST'])
def callback(request):
    client = pymongo.MongoClient()
    pr_db = client.im_database


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=60004)