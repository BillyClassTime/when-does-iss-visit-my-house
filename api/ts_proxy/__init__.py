import os
from urllib.parse import urlsplit

import azure.functions as func
import requests


BACKEND_BASE_URL = os.environ["BACKEND_API_URL"].rstrip("/")


def _build_target_url(req: func.HttpRequest) -> str:
    parsed = urlsplit(req.url)
    upstream_path = parsed.path.lstrip("/")

    target = BACKEND_BASE_URL
    if upstream_path:
        target = f"{target}/{upstream_path}"

    if parsed.query:
        target = f"{target}?{parsed.query}"

    return target


def _forward_headers(req: func.HttpRequest) -> dict:
    headers = {}
    for key in ("Accept", "Content-Type", "Authorization", "User-Agent"):
        value = req.headers.get(key)
        if value:
            headers[key] = value
    return headers


def _response_headers(upstream: requests.Response) -> dict:
    headers = {}
    content_type = upstream.headers.get("Content-Type")
    if content_type:
        headers["Content-Type"] = content_type
    headers["Access-Control-Allow-Origin"] = "*"
    headers["Cache-Control"] = "no-store"
    return headers


def main(req: func.HttpRequest) -> func.HttpResponse:
    target_url = _build_target_url(req)

    try:
        upstream = requests.request(
            method=req.method,
            url=target_url,
            headers=_forward_headers(req),
            data=req.get_body(),
            timeout=10,
        )
    except requests.RequestException as exc:
        return func.HttpResponse(
            body=f'{{"error":"Proxy function error","details":"{str(exc)}"}}',
            status_code=502,
            mimetype="application/json",
        )

    return func.HttpResponse(
        body=upstream.content,
        status_code=upstream.status_code,
        headers=_response_headers(upstream),
    )
