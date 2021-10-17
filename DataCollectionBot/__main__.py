"""
Project name: Data Collection Bot
Written by: Phillip Tat
Date written: 8/23/21
For: UCF Senior Design Project
Purpose: Collect data into our database whenever there is a push, issue, or pull request event.
"""
import os, aiohttp, base64
from aiohttp import web
from gidgethub import routing, sansio
from gidgethub import aiohttp as gh_aiohttp
from pymongo import MongoClient
from datetime import datetime

router = routing.Router()
routes = web.RouteTableDef()

@router.register("push")
async def push_event(event, gh, db, *args, **kwargs):
    # data collection of push payload
    repo_owner = event.data["repository"]["owner"]["login"]
    repo_full_name = event.data["repository"]["full_name"]
    repo_name = event.data["repository"]["name"]
    repo_id = event.data["repository"]["id"]
    repo_url = event.data["repository"]["html_url"]
    pushes = 1
    issues_opened = 0
    issues_closed = 0
    pull_requests_opened = 0
    pull_requests_merged = 0
    # track number of total commits
    commits = len(event.data["commits"])
    non_distinct_commit = 0

    # only count distinct number of commits
    for comm in event.data["commits"]:
        if not comm["distinct"]:
            non_distinct_commit += 1
    commits = commits - non_distinct_commit

    payload = {
        "repo_owner": repo_owner,
        "repo_full_name": repo_full_name,
        "repo_name": repo_name,
        "repo_id": repo_id,
        "repo_url": repo_url,
        "commits": commits,
        "pushes": pushes,
        "issues_opened": issues_opened,
        "issues_closed": issues_closed,
        "pull_requests_opened": pull_requests_opened,
        "pull_requests_merged": pull_requests_merged
    }

    repo = db.dataBotRepos.find_one({"repo_full_name": repo_full_name})

    if repo == None:
        db.dataBotRepos.insert_one(payload)
    else:
        # increment commits in dataBotRepos collection
        db.dataBotRepos.update_one({
            "repo_full_name": repo_full_name
        }, {"$inc": {
                "commits": commits,
                "pushes": pushes
        }})
# end of push_event

@router.register("issues", action = "opened")
@router.register("issues", action = "closed")
async def issue_event(event, gh, db, *args, **kwargs):
    # data collection of issue payload
    repo_owner = event.data["repository"]["owner"]["login"]
    repo_full_name = event.data["repository"]["full_name"]
    repo_name = event.data["repository"]["name"]
    repo_id = event.data["repository"]["id"]
    repo_url = event.data["repository"]["html_url"]
    commits = 0
    pushes = 0
    issues_opened = 0
    issues_closed = 0
    pull_requests_opened = 0
    pull_requests_merged = 0

    # track issues opened or closed
    if event.data["action"] == "opened":
        issues_opened = 1
    else:
        issues_closed = 1

    payload = {
        "repo_owner": repo_owner,
        "repo_full_name": repo_full_name,
        "repo_name": repo_name,
        "repo_id": repo_id,
        "repo_url": repo_url,
        "commits": commits,
        "pushes": pushes,
        "issues_opened": issues_opened,
        "issues_closed": issues_closed,
        "pull_requests_opened": pull_requests_opened,
        "pull_requests_merged": pull_requests_merged
    }

    repo = db.dataBotRepos.find_one({"repo_full_name": repo_full_name})

    if repo == None:
        db.dataBotRepos.insert_one(payload)
    else:
        # increment commits in dataBotRepos collection
        db.dataBotRepos.update_one({
            "repo_full_name": repo_full_name
        }, {"$inc": {
                "issues_opened": issues_opened,
                "issues_closed": issues_closed
        }})
# end of issue_event

@router.register("pull_request", action = "opened")
@router.register("pull_request", action = "closed")
async def pull_request_event(event, gh, db, *args, **kwargs):
    # data collection of pull request payload
    repo_owner = event.data["repository"]["owner"]["login"]
    repo_full_name = event.data["repository"]["full_name"]
    repo_name = event.data["repository"]["name"]
    repo_id = event.data["repository"]["id"]
    repo_url = event.data["repository"]["html_url"]
    commits = 0
    pushes = 0
    issues_opened = 0
    issues_closed = 0
    pull_requests_opened = 0
    pull_requests_merged = 0

    # track pull requests opened or closed
    if event.data["action"] == "opened":
        pull_requests_opened = 1
    else:
        # check if pull request was merged or closed but not merged
        if event.data["pull_request"]["merged"]:
            pull_requests_merged = 1

    payload = {
        "repo_owner": repo_owner,
        "repo_full_name": repo_full_name,
        "repo_name": repo_name,
        "repo_id": repo_id,
        "repo_url": repo_url,
        "commits": commits,
        "pushes": pushes,
        "issues_opened": issues_opened,
        "issues_closed": issues_closed,
        "pull_requests_opened": pull_requests_opened,
        "pull_requests_merged": pull_requests_merged
    }

    repo = db.dataBotRepos.find_one({"repo_full_name": repo_full_name})

    if repo == None:
        db.dataBotRepos.insert_one(payload)
    else:
        # increment commits in dataBotRepos collection
        db.dataBotRepos.update_one({
            "repo_full_name": repo_full_name
        }, {"$inc": {
                "pull_requests_opened": pull_requests_opened,
                "pull_requests_merged": pull_requests_merged
        }})
# end of pull_request_event

@routes.post("/")
async def main(request):
    # read the github webhook payload
    body = await request.read()

    # our authentication token and secret
    secret = os.environ.get("GH_SECRET")
    oauth_token = os.environ.get("GH_AUTH")
    # our mongodb uri with username and password
    uri = os.environ.get("MONGODB_URI")
    client = MongoClient(uri)
    # connect to githubDB
    db = client.githubDB

    # a representation of github webhook event
    event = sansio.Event.from_http(request.headers, body, secret = secret)

    async with aiohttp.ClientSession() as session:
        gh = gh_aiohttp.GitHubAPI(session, "PtatG", oauth_token = oauth_token)
        await router.dispatch(event, gh, db)

    return web.Response(status = 200)

if __name__ == "__main__":
    app = web.Application()
    app.add_routes(routes)
    port = os.environ.get("PORT")
    if port is not None:
        port = int(port)

    web.run_app(app, port = port)
