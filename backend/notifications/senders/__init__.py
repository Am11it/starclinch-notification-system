"""
One small file per channel. Each send function returns (success: bool, detail: str)
so the caller can log the result without caring which provider was used.
"""


def to_result(response):
    """Turn a `requests` response into (success, detail)."""
    return response.ok, f"{response.status_code}: {response.text[:1000]}"
