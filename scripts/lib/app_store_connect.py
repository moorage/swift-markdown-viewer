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
BUNDLE_ID_PLATFORMS = {"IOS", "MAC_OS"}


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


def lookup_bundle_id(identifier: str) -> dict[str, Any] | None:
    payload = api_request("GET", "/v1/bundleIds", [f"filter[identifier]={identifier}"], None)
    bundle_ids = payload.get("data", [])
    if not bundle_ids:
        return None
    return bundle_ids[0]


def cmd_inspect_bundle_id(args: argparse.Namespace) -> int:
    identifier = (
        args.identifier
        or os.environ.get("APP_BUNDLE_IDENTIFIER_OVERRIDE")
        or os.environ.get("BUNDLE_IDENTIFIER")
    )
    if not identifier:
        raise SystemExit("bundle id not provided and BUNDLE_IDENTIFIER is not exported")

    bundle = lookup_bundle_id(identifier)
    if not bundle:
        print(json.dumps({"count": 0, "bundleIds": []}, indent=2))
        return 0

    summary = {
        "count": 1,
        "bundleIds": [
            {
                "id": bundle.get("id"),
                "identifier": bundle.get("attributes", {}).get("identifier"),
                "name": bundle.get("attributes", {}).get("name"),
                "platform": bundle.get("attributes", {}).get("platform"),
            }
        ],
    }
    print(json.dumps(summary, indent=2))
    return 0


def cmd_ensure_bundle_id(args: argparse.Namespace) -> int:
    platform = args.platform.upper()
    if platform not in BUNDLE_ID_PLATFORMS:
        supported = ", ".join(sorted(BUNDLE_ID_PLATFORMS))
        raise SystemExit(f"invalid bundle-id platform '{args.platform}'; expected one of: {supported}")

    existing = lookup_bundle_id(args.identifier)
    if existing:
        summary = {
            "created": False,
            "bundleId": {
                "id": existing.get("id"),
                "identifier": existing.get("attributes", {}).get("identifier"),
                "name": existing.get("attributes", {}).get("name"),
                "platform": existing.get("attributes", {}).get("platform"),
            },
        }
        print(json.dumps(summary, indent=2))
        return 0

    body = json.dumps(
        {
            "data": {
                "type": "bundleIds",
                "attributes": {
                    "identifier": args.identifier,
                    "name": args.name,
                    "platform": platform,
                },
            }
        }
    )
    created = api_request("POST", "/v1/bundleIds", [], body)
    summary = {
        "created": True,
        "bundleId": {
            "id": created.get("data", {}).get("id"),
            "identifier": created.get("data", {}).get("attributes", {}).get("identifier"),
            "name": created.get("data", {}).get("attributes", {}).get("name"),
            "platform": created.get("data", {}).get("attributes", {}).get("platform"),
        },
    }
    print(json.dumps(summary, indent=2))
    return 0


def patch_resource(resource_type: str, resource_id: str, attributes: dict[str, Any]) -> int:
    body = json.dumps(
        {
            "data": {
                "type": resource_type,
                "id": resource_id,
                "attributes": {key: value for key, value in attributes.items() if value is not None},
            }
        }
    )
    payload = api_request("PATCH", f"/v1/{resource_type}/{resource_id}", [], body)
    print(json.dumps(payload, indent=2))
    return 0


def upload_bytes(url: str, method: str, headers: dict[str, str], payload: bytes) -> None:
    request = urllib.request.Request(url, data=payload, method=method.upper(), headers=headers)
    with urllib.request.urlopen(request):
        return None


def poll_asset_delivery(path: str, timeout_seconds: int, poll_interval_seconds: float) -> dict[str, Any]:
    deadline = time.time() + timeout_seconds
    while True:
        payload = api_request("GET", path, [], None)
        state = (
            payload.get("data", {})
            .get("attributes", {})
            .get("assetDeliveryState", {})
            .get("state")
        )
        if state == "COMPLETE":
            return payload
        if state in {"FAILED", "ERROR"}:
            print(json.dumps(payload, indent=2), file=sys.stderr)
            raise SystemExit(1)
        if time.time() >= deadline:
            print(json.dumps(payload, indent=2), file=sys.stderr)
            raise SystemExit(f"timed out waiting for asset delivery at {path}")
        time.sleep(poll_interval_seconds)


def cmd_upload_screenshot(args: argparse.Namespace) -> int:
    file_path = os.path.abspath(args.file)
    file_name = args.file_name or os.path.basename(file_path)
    file_size = os.path.getsize(file_path)

    body = json.dumps(
        {
            "data": {
                "type": "appScreenshots",
                "attributes": {
                    "fileName": file_name,
                    "fileSize": file_size,
                },
                "relationships": {
                    "appScreenshotSet": {
                        "data": {
                            "type": "appScreenshotSets",
                            "id": args.set_id,
                        }
                    }
                },
            }
        }
    )
    reservation = api_request("POST", "/v1/appScreenshots", [], body)
    screenshot = reservation.get("data", {})
    screenshot_id = screenshot.get("id")
    upload_operations = screenshot.get("attributes", {}).get("uploadOperations", [])

    with open(file_path, "rb") as handle:
        file_bytes = handle.read()

    for operation in upload_operations:
        offset = int(operation.get("offset", 0))
        length = int(operation.get("length", len(file_bytes) - offset))
        chunk = file_bytes[offset:offset + length]
        headers = {
            header["name"]: header["value"]
            for header in operation.get("requestHeaders", [])
        }
        upload_bytes(operation["url"], operation["method"], headers, chunk)

    api_request(
        "PATCH",
        f"/v1/appScreenshots/{screenshot_id}",
        [],
        json.dumps(
            {
                "data": {
                    "type": "appScreenshots",
                    "id": screenshot_id,
                    "attributes": {
                        "uploaded": True,
                    },
                }
            }
        ),
    )

    completed = poll_asset_delivery(
        f"/v1/appScreenshots/{screenshot_id}",
        timeout_seconds=args.timeout_seconds,
        poll_interval_seconds=args.poll_interval_seconds,
    )
    print(json.dumps(completed, indent=2))
    return 0


def cmd_patch_app_info_localization(args: argparse.Namespace) -> int:
    return patch_resource(
        "appInfoLocalizations",
        args.id,
        {
            "name": args.name,
            "subtitle": args.subtitle,
            "privacyPolicyUrl": args.privacy_policy_url,
        },
    )


def cmd_patch_version_localization(args: argparse.Namespace) -> int:
    return patch_resource(
        "appStoreVersionLocalizations",
        args.id,
        {
            "description": args.description,
            "keywords": args.keywords,
            "marketingUrl": args.marketing_url,
            "promotionalText": args.promotional_text,
            "supportUrl": args.support_url,
            "whatsNew": args.whats_new,
        },
    )


def cmd_patch_review_detail(args: argparse.Namespace) -> int:
    return patch_resource(
        "appStoreReviewDetails",
        args.id,
        {
            "contactFirstName": args.contact_first_name,
            "contactLastName": args.contact_last_name,
            "contactPhone": args.contact_phone,
            "contactEmail": args.contact_email,
            "demoAccountName": args.demo_account_name,
            "demoAccountPassword": args.demo_account_password,
            "demoAccountRequired": args.demo_account_required,
            "notes": args.notes,
        },
    )


def cmd_create_review_detail(args: argparse.Namespace) -> int:
    body = json.dumps(
        {
            "data": {
                "type": "appStoreReviewDetails",
                "attributes": {
                    key: value
                    for key, value in {
                        "contactFirstName": args.contact_first_name,
                        "contactLastName": args.contact_last_name,
                        "contactPhone": args.contact_phone,
                        "contactEmail": args.contact_email,
                        "demoAccountName": args.demo_account_name,
                        "demoAccountPassword": args.demo_account_password,
                        "demoAccountRequired": args.demo_account_required,
                        "notes": args.notes,
                    }.items()
                    if value is not None
                },
                "relationships": {
                    "appStoreVersion": {
                        "data": {
                            "type": "appStoreVersions",
                            "id": args.app_store_version_id,
                        }
                    }
                },
            }
        }
    )
    payload = api_request("POST", "/v1/appStoreReviewDetails", [], body)
    print(json.dumps(payload, indent=2))
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

    inspect_bundle_id_parser = subparsers.add_parser("inspect-bundle-id", help="inspect a bundle-id record")
    inspect_bundle_id_parser.add_argument("--identifier", help="bundle id identifier; defaults to the repo app bundle id")
    inspect_bundle_id_parser.set_defaults(func=cmd_inspect_bundle_id)

    ensure_bundle_id_parser = subparsers.add_parser("ensure-bundle-id", help="create a bundle id if it does not exist")
    ensure_bundle_id_parser.add_argument("--identifier", required=True, help="bundle id identifier to ensure")
    ensure_bundle_id_parser.add_argument("--name", required=True, help="bundle id display name")
    ensure_bundle_id_parser.add_argument(
        "--platform",
        default="IOS",
        help="bundle id platform, defaults to IOS; valid values: IOS, MAC_OS",
    )
    ensure_bundle_id_parser.set_defaults(func=cmd_ensure_bundle_id)

    app_info_localization_parser = subparsers.add_parser("patch-app-info-localization", help="patch an app info localization")
    app_info_localization_parser.add_argument("--id", required=True, help="appInfoLocalization resource id")
    app_info_localization_parser.add_argument("--name", help="localized app name")
    app_info_localization_parser.add_argument("--subtitle", help="localized app subtitle")
    app_info_localization_parser.add_argument("--privacy-policy-url", help="localized privacy policy URL")
    app_info_localization_parser.set_defaults(func=cmd_patch_app_info_localization)

    version_localization_parser = subparsers.add_parser("patch-version-localization", help="patch an app store version localization")
    version_localization_parser.add_argument("--id", required=True, help="appStoreVersionLocalization resource id")
    version_localization_parser.add_argument("--description", help="localized description")
    version_localization_parser.add_argument("--keywords", help="localized keywords")
    version_localization_parser.add_argument("--marketing-url", help="localized marketing URL")
    version_localization_parser.add_argument("--promotional-text", help="localized promotional text")
    version_localization_parser.add_argument("--support-url", help="localized support URL")
    version_localization_parser.add_argument("--whats-new", help="localized whats-new text")
    version_localization_parser.set_defaults(func=cmd_patch_version_localization)

    review_detail_parser = subparsers.add_parser("patch-review-detail", help="patch an app store review detail")
    review_detail_parser.add_argument("--id", required=True, help="appStoreReviewDetail resource id")
    review_detail_parser.add_argument("--contact-first-name", help="review contact first name")
    review_detail_parser.add_argument("--contact-last-name", help="review contact last name")
    review_detail_parser.add_argument("--contact-phone", help="review contact phone")
    review_detail_parser.add_argument("--contact-email", help="review contact email")
    review_detail_parser.add_argument("--demo-account-name", help="demo account name")
    review_detail_parser.add_argument("--demo-account-password", help="demo account password")
    review_detail_parser.add_argument("--demo-account-required", action="store_true", help="mark demo account as required")
    review_detail_parser.add_argument("--notes", help="review notes")
    review_detail_parser.set_defaults(func=cmd_patch_review_detail)

    create_review_detail_parser = subparsers.add_parser("create-review-detail", help="create an app store review detail")
    create_review_detail_parser.add_argument("--app-store-version-id", required=True, help="appStoreVersion resource id")
    create_review_detail_parser.add_argument("--contact-first-name", help="review contact first name")
    create_review_detail_parser.add_argument("--contact-last-name", help="review contact last name")
    create_review_detail_parser.add_argument("--contact-phone", help="review contact phone")
    create_review_detail_parser.add_argument("--contact-email", help="review contact email")
    create_review_detail_parser.add_argument("--demo-account-name", help="demo account name")
    create_review_detail_parser.add_argument("--demo-account-password", help="demo account password")
    create_review_detail_parser.add_argument("--demo-account-required", action="store_true", help="mark demo account as required")
    create_review_detail_parser.add_argument("--notes", help="review notes")
    create_review_detail_parser.set_defaults(func=cmd_create_review_detail)

    upload_screenshot_parser = subparsers.add_parser("upload-screenshot", help="create, upload, and poll a screenshot asset")
    upload_screenshot_parser.add_argument("--set-id", required=True, help="appScreenshotSet resource id")
    upload_screenshot_parser.add_argument("--file", required=True, help="path to the screenshot file to upload")
    upload_screenshot_parser.add_argument("--file-name", help="optional override for the uploaded file name")
    upload_screenshot_parser.add_argument("--timeout-seconds", type=int, default=300, help="max seconds to wait for asset delivery")
    upload_screenshot_parser.add_argument("--poll-interval-seconds", type=float, default=2.0, help="seconds between delivery-state polls")
    upload_screenshot_parser.set_defaults(func=cmd_upload_screenshot)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
