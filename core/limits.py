# limits.py

FREE_LIMITS = {
    "youtube_download": 1,
    "music_download": 6,
    "tiktok_download": 5,
    "yt_archive": 2,
}

VIP_LIMITS = {
    "youtube_download": 20,
    "music_download": 20,
    "tiktok_download": 30,
    "yt_archive": 20,
}


def get_limit(key: str, is_vip: int) -> int:
    limits = VIP_LIMITS if is_vip == 1 else FREE_LIMITS
    return limits[key]
