
import csv
import json
import time
import random
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE_URL = "https://codeforces.com/api"

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "codeforces_raw"
OUT_DIR = ROOT / "data" / "codeforces"
CACHE_DIR = RAW_DIR / "cache"

PILOT_SIZE = 100
REQUEST_DELAY_SECONDS = 2.1
SUBMISSION_LIMIT = 1000
RANDOM_SEED = 42

# Known public profiles for pipeline testing and fallback.
SEED_HANDLES = ["tourist", "Petr", "Benq", "Um_nik", "jiangly"]

# Public Codeforces contests to sample participants from.
# The sampler skips contests that fail or return no usable handles.
CONTEST_IDS = [
    2114, 2113, 2112, 2111, 2110,
    2109, 2108, 2107, 2106, 2105,
    2104, 2103, 2102, 2101, 2100,
]

for folder in (RAW_DIR, OUT_DIR, CACHE_DIR):
    folder.mkdir(parents=True, exist_ok=True)


def api_get(method, params):
    """Fetch and cache successful public Codeforces API responses."""
    cache_key = method + "_" + "_".join(
        f"{key}-{value}" for key, value in sorted(params.items())
    )
    cache_path = CACHE_DIR / f"{cache_key}.json"

    if cache_path.exists():
        try:
            return json.loads(cache_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            print(f"Invalid cache; refetching {method}: {params}", flush=True)

    url = f"{BASE_URL}/{method}?{urlencode(params)}"
    request = Request(
        url,
        headers={"User-Agent": "CodeTrack-AI-dataset-pilot/0.2"},
    )

    # Respect Codeforces' public API rate limit.
    time.sleep(REQUEST_DELAY_SECONDS)

    try:
        with urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (
        HTTPError,
        URLError,
        TimeoutError,
        json.JSONDecodeError,
        OSError,
    ) as exc:
        print(f"Request failed: {method} {params}: {exc}", flush=True)
        return None

    if payload.get("status") != "OK":
        print(
            f"API error for {method}: "
            f"{payload.get('comment', 'Unknown error')}",
            flush=True,
        )
        return None

    cache_path.write_text(
        json.dumps(payload, ensure_ascii=False),
        encoding="utf-8",
    )
    return payload


def write_csv(path, rows, columns):
    """Write a CSV with a stable column layout."""
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def collect_handles():
    """Collect unique public participant handles from contest standings."""
    handles = set(SEED_HANDLES)
    rng = random.Random(RANDOM_SEED)

    print("Collecting handles from public contest standings...", flush=True)

    for contest_id in CONTEST_IDS:
        if len(handles) >= PILOT_SIZE:
            break

        print(
            f"Sampling contest {contest_id} "
            f"({len(handles)}/{PILOT_SIZE} handles)",
            flush=True,
        )

        payload = api_get(
            "contest.standings",
            {
                "contestId": contest_id,
                "from": 1,
                "count": 100,
                "showUnofficial": "false",
            },
        )

        if not payload:
            continue

        result = payload.get("result", {})
        rows = result.get("rows", [])
        rng.shuffle(rows)

        for row in rows:
            party = row.get("party", {})
            # Keep actual individual contestants, not team submissions.
            members = party.get("members", [])
            if len(members) != 1:
                continue

            handle = members[0].get("handle")
            if handle:
                handles.add(handle)

            if len(handles) >= PILOT_SIZE:
                break

    selected = sorted(handles)
    if len(selected) < PILOT_SIZE:
        print(
            f"Warning: found only {len(selected)} unique handles. "
            "Add more contest IDs to increase coverage.",
            flush=True,
        )

    return selected[:PILOT_SIZE]


def main():
    handles = collect_handles()

    users = []
    contests = []
    submissions = []

    for index, handle in enumerate(handles, start=1):
        print(
            f"\n[{index}/{len(handles)}] Collecting {handle}",
            flush=True,
        )

        info = api_get("user.info", {"handles": handle})
        history = api_get("user.rating", {"handle": handle})
        status = api_get(
            "user.status",
            {
                "handle": handle,
                "from": 1,
                "count": SUBMISSION_LIMIT,
            },
        )

        if info and info.get("result"):
            user = info["result"][0]
            users.append({
                "handle": user.get("handle"),
                "rating": user.get("rating"),
                "maxRating": user.get("maxRating"),
                "rank": user.get("rank"),
                "maxRank": user.get("maxRank"),
            })

        if history:
            for item in history.get("result", []):
                contests.append({
                    "handle": handle,
                    "contestId": item.get("contestId"),
                    "contestName": item.get("contestName"),
                    "rank": item.get("rank"),
                    "ratingUpdateTimeSeconds": item.get(
                        "ratingUpdateTimeSeconds"
                    ),
                    "oldRating": item.get("oldRating"),
                    "newRating": item.get("newRating"),
                })

        if status:
            for item in status.get("result", []):
                problem = item.get("problem", {})
                author = item.get("author", {})
                submissions.append({
                    "handle": handle,
                    "submissionId": item.get("id"),
                    "contestId": item.get("contestId"),
                    "creationTimeSeconds": item.get(
                        "creationTimeSeconds"
                    ),
                    "problemName": problem.get("name"),
                    "problemIndex": problem.get("index"),
                    "problemRating": problem.get("rating"),
                    "tags": ";".join(problem.get("tags", [])),
                    "language": item.get("programmingLanguage"),
                    "verdict": item.get("verdict"),
                    "participantType": author.get("participantType"),
                })

        # Save progress after each user so an interruption loses little work.
        write_outputs(users, contests, submissions)

    print("\nCollection finished.", flush=True)
    print(f"Users collected: {len(users)}", flush=True)
    print(f"Contest records: {len(contests)}", flush=True)
    print(f"Submission records: {len(submissions)}", flush=True)
    print(f"CSV output: {OUT_DIR}", flush=True)
    print(f"API cache: {CACHE_DIR}", flush=True)


def write_outputs(users, contests, submissions):
    write_csv(
        OUT_DIR / "users.csv",
        users,
        ["handle", "rating", "maxRating", "rank", "maxRank"],
    )
    write_csv(
        OUT_DIR / "contest_history.csv",
        contests,
        [
            "handle",
            "contestId",
            "contestName",
            "rank",
            "ratingUpdateTimeSeconds",
            "oldRating",
            "newRating",
        ],
    )
    write_csv(
        OUT_DIR / "submissions.csv",
        submissions,
        [
            "handle",
            "submissionId",
            "contestId",
            "creationTimeSeconds",
            "problemName",
            "problemIndex",
            "problemRating",
            "tags",
            "language",
            "verdict",
            "participantType",
        ],
    )


if __name__ == "__main__":
    main()
