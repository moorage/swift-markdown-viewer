#!/usr/bin/env python3

import argparse
import base64
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


API_BASE = "https://api.appstoreconnect.apple.com"


def require_env(name: str) -> str:
    value = os.environ.get(name)
    if value:
        return value
    raise SystemExit(f"missing required environment variable: {name}")


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def decode_der_length(payload: bytes, index: int) -> tuple[int, int]:
    length = payload[index]
    index += 1
    if not (length & 0x80):
        return length, index
    octet_count = length & 0x7F
    if octet_count == 0 or octet_count > 2:
        raise ValueError("unsupported DER length encoding")
    return int.from_bytes(payload[index:index + octet_count], "big"), index + octet_count


def decode_der_integer(payload: bytes, index: int) -> tuple[int, int]:
    if payload[index] != 0x02:
        raise ValueError("expected DER integer")
    length = payload[index + 1]
    start = index + 2
    end = start + length
    return int.from_bytes(payload[start:end], "big"), end


def der_signature_to_jose(signature: bytes) -> bytes:
    if len(signature) < 8 or signature[0] != 0x30:
        raise ValueError("expected DER sequence")
    sequence_length, index = decode_der_length(signature, 1)
    sequence_end = index + sequence_length
    r, index = decode_der_integer(signature, index)
    s, index = decode_der_integer(signature, index)
    if index != sequence_end:
        raise ValueError("unexpected DER payload")
    return r.to_bytes(32, "big") + s.to_bytes(32, "big")


def create_token() -> str:
    key_id = require_env("ASC_KEY_ID")
    issuer_id = require_env("ASC_ISSUER_ID")
    key_path = require_env("ASC_KEY_PATH")

    now = int(time.time())
    header = {"alg": "ES256", "kid": key_id, "typ": "JWT"}
    payload = {
        "iss": issuer_id,
        "aud": "appstoreconnect-v1",
        "iat": now,
        "exp": now + 900,
    }
    header_bytes = json.dumps(header, separators=(",", ":")).encode("utf-8")
    payload_bytes = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    signing_input = f"{b64url(header_bytes)}.{b64url(payload_bytes)}"
    der_signature = subprocess.check_output(
        ["openssl", "dgst", "-binary", "-sha256", "-sign", key_path],
        input=signing_input.encode("utf-8"),
    )
    jose_signature = der_signature_to_jose(der_signature)
    return f"{signing_input}.{b64url(jose_signature)}"


def api_request(method: str, path: str, query: list[str], body: str | None) -> Any:
    token = create_token()
    url = urllib.parse.urljoin(API_BASE, path)
    if query:
        separator = "&" if "?" in url else "?"
        url = f"{url}{separator}{urllib.parse.urlencode([tuple(item.split('=', 1)) for item in query])}"

    data = body.encode("utf-8") if body is not None else None
    request = urllib.request.Request(
        url,
        data=data,
        method=method.upper(),
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request) as response:
            payload = response.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        payload = error.read().decode("utf-8")
        if payload:
            try:
                parsed = json.loads(payload)
            except json.JSONDecodeError:
                parsed = {"status": error.code, "body": payload}
        else:
            parsed = {"status": error.code, "reason": error.reason}
        print(json.dumps(parsed, indent=2), file=sys.stderr)
        raise SystemExit(1)

    if not payload:
        return {}
    return json.loads(payload)


def cmd_request(args: argparse.Namespace) -> int:
    payload = api_request(args.method, args.path, args.query or [], args.body)
    print(json.dumps(payload, indent=2))
    return 0


def cmd_inspect_app(args: argparse.Namespace) -> int:
    bundle_id = (
        args.bundle_id
        or os.environ.get("APP_BUNDLE_IDENTIFIER_OVERRIDE")
        or os.environ.get("BUNDLE_IDENTIFIER")
    )
    if not bundle_id:
        raise SystemExit("bundle id not provided and BUNDLE_IDENTIFIER is not exported")
    query = [
        f"filter[bundleId]={bundle_id}",
        "limit=5",
    ]
    payload = api_request("GET", "/v1/apps", query, None)
    apps = payload.get("data", [])
    summary = {
        "count": len(apps),
        "apps": [
            {
                "id": app.get("id"),
                "name": app.get("attributes", {}).get("name"),
                "bundleId": app.get("attributes", {}).get("bundleId"),
                "sku": app.get("attributes", {}).get("sku"),
                "primaryLocale": app.get("attributes", {}).get("primaryLocale"),
            }
            for app in apps
        ],
    }
    if args.raw:
        print(json.dumps(payload, indent=2))
    else:
        print(json.dumps(summary, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="App Store Connect helper")
    subparsers = parser.add_subparsers(dest="command", required=True)

    request_parser = subparsers.add_parser("request", help="make a raw App Store Connect API request")
    request_parser.add_argument("method", help="HTTP method, for example GET or POST")
    request_parser.add_argument("path", help="API path, for example /v1/apps")
    request_parser.add_argument("--query", action="append", help="query parameter as key=value")
    request_parser.add_argument("--body", help="raw JSON body")
    request_parser.set_defaults(func=cmd_request)

    inspect_parser = subparsers.add_parser("inspect-app", help="inspect an app record by bundle id")
    inspect_parser.add_argument("--bundle-id", help="bundle id to inspect; defaults to the repo app bundle id")
    inspect_parser.add_argument("--raw", action="store_true", help="print the full API payload")
    inspect_parser.set_defaults(func=cmd_inspect_app)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
