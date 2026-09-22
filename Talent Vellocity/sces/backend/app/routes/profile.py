from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import User, CodingProfile
from app.schemas.schemas import ProfileSetup, ProfileUpdate, CodingProfileOut
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/api/profile", tags=["profile"])


def _get_or_create_profile(user: User, db: Session) -> CodingProfile:
    profile = db.query(CodingProfile).filter(CodingProfile.user_id == user.id).first()
    if not profile:
        profile = CodingProfile(user_id=user.id)
        db.add(profile)
        db.flush()
    return profile


@router.post("/setup", response_model=CodingProfileOut)
def setup_profile(
    body: ProfileSetup,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = _get_or_create_profile(current_user, db)
    profile.leetcode_username = body.leetcode_username
    profile.codeforces_handle = body.codeforces_handle
    profile.github_username = body.github_username
    current_user.profile_setup_done = 1
    db.commit()
    db.refresh(profile)
    return profile


@router.get("/me", response_model=CodingProfileOut)
def get_my_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = db.query(CodingProfile).filter(CodingProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(404, "Profile not set up yet")
    return profile


@router.put("/update", response_model=CodingProfileOut)
def update_profile(
    body: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = _get_or_create_profile(current_user, db)
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(profile, field, value)
    current_user.profile_setup_done = 1
    db.commit()
    db.refresh(profile)
    return profile


@router.get("/my-stats")
def get_my_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.services.coding_service import sync_student_coding_stats, fetch_leetcode, fetch_codeforces, fetch_github
    profile = db.query(CodingProfile).filter(CodingProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(404, "Profile not set up yet")

    # Sync statistics to the database
    sync_student_coding_stats(current_user.id, db)

    stats, errors = {}, []

    if profile.leetcode_username:
        try:
            stats["leetcode"] = fetch_leetcode(profile.leetcode_username)
        except Exception as e:
            errors.append({"platform": "leetcode", "error": str(e)})

    if profile.codeforces_handle:
        try:
            stats["codeforces"] = fetch_codeforces(profile.codeforces_handle)
        except Exception as e:
            errors.append({"platform": "codeforces", "error": str(e)})

    if profile.github_username:
        try:
            stats["github"] = fetch_github(profile.github_username)
        except Exception as e:
            errors.append({"platform": "github", "error": str(e)})

    # Compile DSA topics spectrum for frontend radar chart
    topics = {}
    if "leetcode" in stats and isinstance(stats["leetcode"], dict):
        lb = stats["leetcode"].get("topic_breakdown") or {}
        for t, val in lb.items():
            topics[t] = topics.get(t, 0) + val
    if "codeforces" in stats and isinstance(stats["codeforces"], dict):
        cb = stats["codeforces"].get("topic_breakdown") or {}
        for t, val in cb.items():
            topics[t] = topics.get(t, 0) + val
            
    # Sort and take top 8 topics to keep chart readable
    stats["topics"] = dict(sorted(topics.items(), key=lambda x: x[1], reverse=True)[:8])

    return {"stats": stats, "errors": errors}

