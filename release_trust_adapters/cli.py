"""Provider-neutral command line uploader for Runner API v1."""
import argparse
import json
import os
import sys

from .client import RunnerApiClient, RunnerApiError


def _payload(value):
    if value.startswith("@"):
        with open(value[1:], encoding="utf-8") as source: return json.load(source)
    return json.loads(value)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Release Trust Runner API v1 uploader")
    parser.add_argument("--base-url", default=os.getenv("HORIZON_API_URL", "http://localhost:8000/pipeline/api"))
    parser.add_argument("--authorization", default=os.getenv("HORIZON_AUTHORIZATION"))
    parser.add_argument("--timeout", type=float, default=float(os.getenv("HORIZON_TIMEOUT_SECONDS", "15")))
    parser.add_argument("--retries", type=int, default=int(os.getenv("HORIZON_RETRIES", "3")))
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("create-release", "upload-evidence", "publish-event", "update-status"):
        command = sub.add_parser(name); command.add_argument("payload", help="JSON value or @path.json")
        if name != "create-release": command.add_argument("release_id")
    sub.add_parser("get-status").add_argument("release_id")
    args = parser.parse_args(argv); client = RunnerApiClient(args.base_url, args.authorization, args.timeout, args.retries)
    try:
        if args.command == "create-release": result = client.create_release(_payload(args.payload))
        elif args.command == "upload-evidence": result = client.upload_evidence(args.release_id, _payload(args.payload))
        elif args.command == "publish-event": result = client.publish_event(args.release_id, _payload(args.payload))
        elif args.command == "update-status": result = client.update_status(args.release_id, _payload(args.payload))
        else: result = client.get_status(args.release_id)
        print(json.dumps(result, indent=2, sort_keys=True)); return 0
    except (RunnerApiError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr); return 1


if __name__ == "__main__": raise SystemExit(main())
