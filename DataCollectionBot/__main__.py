import os, aiohttp, base64, math
from aiohttp import web
from gidgethub import routing, sansio
from gidgethub import aiohttp as gh_aiohttp
from pymongo import MongoClient
from datetime import datetime

router = routing.Router()
routes = web.RouteTableDef()

@router.register("push")
async def push_event(event, gh, db, *args, **kwargs):
    print(event.data)


# end of push_event

@router.register("issues", action = "opened")
@router.register("issues", action = "closed")
async def issue_event(event, gh, db, *args, **kwargs):
    print(event)
    print(event.data)


# end of issue_event

@router.register("pull_request", action = "opened")
@router.register("pull_request", action = "reopened")
@router.register("pull_request", action = "closed")
async def pull_request_event(event, gh, db, *args, **kwargs):
    print(event)
    print(event.data)


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
    # connect to test db
    db = client.test

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
