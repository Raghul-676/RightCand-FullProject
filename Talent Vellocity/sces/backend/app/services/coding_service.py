import requests
from fastapi import HTTPException
from datetime import datetime
import re
import hashlib

def fetch_leetcode(username: str) -> dict:
    query = """
    query($username: String!) {
      allQuestionsCount {
        difficulty
        count
      }
      matchedUser(username: $username) {
        username
        profile { ranking }
        submitStats {
          acSubmissionNum { difficulty count }
        }
        tagProblemCounts {
          advanced { tagName problemsSolved }
          intermediate { tagName problemsSolved }
          fundamental { tagName problemsSolved }
        }
      }
      userContestRanking(username: $username) {
        rating attendedContestsCount globalRanking topPercentage totalParticipants
      }
      userContestRankingHistory(username: $username) {
        rating
      }
      recentAcSubmissionList(username: $username, limit: 20) {
        timestamp
      }
    }
    """
    try:
        r = requests.post(
            "https://leetcode.com/graphql",
            json={"query": query, "variables": {"username": username}},
            headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"},
            timeout=10,
        )
        r.raise_for_status()
        data = r.json().get("data", {})
        user = data.get("matchedUser")
        if not user:
            raise HTTPException(404, "LeetCode user not found")

        total_questions = {q["difficulty"]: q["count"] for q in data.get("allQuestionsCount", [])}
        ac = {s["difficulty"]: s["count"] for s in user["submitStats"]["acSubmissionNum"]}
        contest = data.get("userContestRanking") or {}
        
        # Calculate highest rating
        history = data.get("userContestRankingHistory") or []
        highest_rating = round(max([h.get("rating", 0) for h in history if h.get("rating")], default=0))
        if highest_rating == 0 and contest.get("rating"):
            highest_rating = round(contest["rating"])

        # Topic breakdown
        tag_counts = {}
        for group in ("fundamental", "intermediate", "advanced"):
            for t in (user.get("tagProblemCounts") or {}).get(group, []):
                tag_counts[t["tagName"]] = tag_counts.get(t["tagName"], 0) + t["problemsSolved"]
        top_topics = dict(sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:8])

        # Consistency
        recent = data.get("recentAcSubmissionList") or []
        active_days = len({int(s["timestamp"]) // 86400 for s in recent})
        last_active_ts = int(recent[0]["timestamp"]) if recent else None

        return {
            "username": user["username"],
            "ranking": user["profile"].get("ranking", 0),
            "total_solved": ac.get("All", 0),
            "easy_solved": ac.get("Easy", 0),
            "medium_solved": ac.get("Medium", 0),
            "hard_solved": ac.get("Hard", 0),
            "total_easy": total_questions.get("Easy", 956),
            "total_medium": total_questions.get("Medium", 2091),
            "total_hard": total_questions.get("Hard", 958),
            "contest_rating": round(contest.get("rating", 0)),
            "highest_rating": highest_rating,
            "contests_attended": contest.get("attendedContestsCount", 0),
            "global_ranking": contest.get("globalRanking", 0),
            "top_percentage": contest.get("topPercentage", 0.0),
            "total_participants": contest.get("totalParticipants", 0),
            "topic_breakdown": top_topics,
            "active_days_last20": active_days,
            "last_active_ts": last_active_ts,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"LeetCode fetch error: {e}")


def fetch_codeforces(handle: str) -> dict:
    try:
        r = requests.get(f"https://codeforces.com/api/user.info?handles={handle}", timeout=10)
        r.raise_for_status()
        data = r.json()
        if data.get("status") != "OK":
            raise HTTPException(404, "Codeforces user not found")
        u = data["result"][0]

        # Fetch solved problems for rating distribution + total solved + topic breakdown
        rating_dist = {}
        total_solved = 0
        topic_counts = {}
        try:
            sub_r = requests.get(
                f"https://codeforces.com/api/user.status?handle={handle}&from=1&count=1000",
                timeout=10
            )
            if sub_r.status_code == 200:
                subs = sub_r.json().get("result", [])
                seen = set()
                for s in subs:
                    if s.get("verdict") == "OK":
                        prob = s.get("problem", {})
                        pid = f"{prob.get('contestId')}{prob.get('index')}"
                        if pid not in seen:
                            seen.add(pid)
                            total_solved += 1
                            # Rating distribution
                            rating = prob.get("rating")
                            if rating:
                                bucket = str((rating // 200) * 200)
                                rating_dist[bucket] = rating_dist.get(bucket, 0) + 1
                            # Topic breakdown from tags
                            for tag in prob.get("tags", []):
                                topic_counts[tag] = topic_counts.get(tag, 0) + 1
        except Exception:
            pass

        top_topics = dict(sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:8])

        # Consistency — unique active days from last 100 submissions
        active_days = 0
        try:
            sub_r2 = requests.get(
                f"https://codeforces.com/api/user.status?handle={handle}&from=1&count=100",
                timeout=10
            )
            if sub_r2.status_code == 200:
                subs2 = sub_r2.json().get("result", [])
                active_days = len({s["creationTimeSeconds"] // 86400 for s in subs2})
        except Exception:
            pass

        # Contest count (from rating history)
        contests_attended = 0
        try:
            rating_r = requests.get(f"https://codeforces.com/api/user.rating?handle={handle}", timeout=10)
            if rating_r.status_code == 200:
                contests_attended = len(rating_r.json().get("result", []))
        except Exception:
            pass

        cf_last_active = None
        if subs:
            cf_last_active = subs[0].get("creationTimeSeconds")

        return {
            "handle": u.get("handle"),
            "rating": u.get("rating", 0),
            "max_rating": u.get("maxRating", 0),
            "rank": u.get("rank", "unrated"),
            "max_rank": u.get("maxRank", "unrated"),
            "avatar": u.get("titlePhoto"),
            "total_solved": total_solved,
            "topic_breakdown": top_topics,
            "rating_distribution": dict(sorted(rating_dist.items(), key=lambda x: int(x[0]))),
            "active_days_last100": active_days,
            "contests_attended": contests_attended,
            "last_active_ts": cf_last_active,
        }
    except HTTPException:
        raise
        raise HTTPException(500, f"Codeforces fetch error: {e}")


def fetch_github(username: str) -> dict:
    import os
    token = os.getenv("GITHUB_TOKEN")
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"

    try:
        r = requests.get(
            f"https://api.github.com/users/{username}",
            headers=headers,
            timeout=10,
        )
        if r.status_code == 403:
            return {
                "username": username,
                "name": username,
                "avatar": f"https://github.com/identicons/{username}.png",
                "public_repos": 0,
                "followers": 0,
                "following": 0,
                "profile_url": f"https://github.com/{username}",
                "active_days_last30": 0,
                "last_active_ts": None,
                "rate_limited": True
            }
        if r.status_code == 404:
            raise HTTPException(404, "GitHub user not found")
        r.raise_for_status()
        d = r.json()

        # Commit consistency — events from last 30 days
        active_days = 0
        try:
            ev_r = requests.get(
                f"https://api.github.com/users/{username}/events?per_page=100",
                headers=headers,
                timeout=10,
            )
            if ev_r.status_code == 200:
                from datetime import datetime, timezone, timedelta
                cutoff = datetime.now(timezone.utc) - timedelta(days=30)
                push_days = set()
                gh_last_active = None
                evs = ev_r.json()
                if evs:
                    try:
                        created_str = evs[0].get("created_at")
                        if created_str:
                            from datetime import datetime, timezone
                            dt = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
                            gh_last_active = int(dt.timestamp())
                    except:
                        pass
                for ev in evs:
                    if ev.get("type") == "PushEvent":
                        created = datetime.fromisoformat(ev["created_at"].replace("Z", "+00:00"))
                        if created >= cutoff:
                            push_days.add(created.date())
                active_days = len(push_days)
        except Exception:
            pass

        return {
            "username": d.get("login"),
            "name": d.get("name"),
            "avatar": d.get("avatar_url"),
            "public_repos": d.get("public_repos", 0),
            "followers": d.get("followers", 0),
            "following": d.get("following", 0),
            "profile_url": d.get("html_url"),
            "active_days_last30": active_days,
            "last_active_ts": gh_last_active,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"GitHub fetch error: {e}")


def compute_talent_score(lc: dict, cf: dict, gh: dict) -> int:
    score = 0
    if lc:
        score += min(lc.get("total_solved", 0) // 5, 30)
        score += min(lc.get("hard_solved", 0) * 2, 20)
        
        # Rating reliability increases with contest count
        lc_contests = lc.get("contests_attended")
        if not lc_contests:
            lc_contests = 0
        if lc_contests < 15:
            trust = lc_contests / 15
        else:
            trust = 1.0
        
        rating_score = min(lc.get("contest_rating", 0) // 100, 20)
        score += rating_score * trust
    if cf:
        # Rating reliability increases with contest count
        cf_contests = cf.get("contests_attended")
        if not cf_contests:
            cf_contests = 0
        if cf_contests < 15:
            trust = cf_contests / 15
        else:
            trust = 1.0
            
        rating_score = min(cf.get("rating", 0) // 100, 20)
        score += rating_score * trust
    if gh:
        score += min(gh.get("public_repos", 0) * 2, 10)
    return min(round(score), 100)


def sync_student_coding_stats(user_id: int, db):
    from app.models.models import CodingProfile, CodingStats

    
    profile = db.query(CodingProfile).filter(CodingProfile.user_id == user_id).first()
    if not profile:
        return None

    stats = db.query(CodingStats).filter(CodingStats.student_id == user_id).first()
    if not stats:
        stats = CodingStats(student_id=user_id)
        db.add(stats)

    lc, cf, gh = {}, {}, {}
    timestamps = []

    # Fetch Leetcode
    if profile.leetcode_username:
        try:
            lc = fetch_leetcode(profile.leetcode_username)
            stats.leetcode_solved = lc.get("total_solved", 0)
            stats.leetcode_hard_solved = lc.get("hard_solved", 0)
            stats.leetcode_rating = lc.get("contest_rating", 0)
            stats.leetcode_contests = lc.get("contests_attended", 0)
            if lc.get("last_active_ts"):
                timestamps.append(lc["last_active_ts"])
        except Exception:
            pass

    # Fetch Codeforces
    if profile.codeforces_handle:
        try:
            cf = fetch_codeforces(profile.codeforces_handle)
            stats.codeforces_rating = cf.get("rating", 0)
            stats.codeforces_contests = cf.get("contests_attended", 0)
            if cf.get("last_active_ts"):
                timestamps.append(cf["last_active_ts"])
        except Exception:
            pass

    # Fetch GitHub
    if profile.github_username:
        try:
            gh = fetch_github(profile.github_username)
            if gh.get("last_active_ts"):
                timestamps.append(gh["last_active_ts"])
        except Exception:
            pass

    # Compute last_active_at
    if timestamps:
        latest_ts = max(timestamps)
        stats.last_active_at = datetime.utcfromtimestamp(latest_ts)
    else:
        stats.last_active_at = profile.updated_at or datetime.utcnow()

    db.commit()
    db.refresh(stats)
    return stats
