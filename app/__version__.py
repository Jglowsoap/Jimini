"""
Jimini version information.
"""
from typing import Any

__version__ = "0.2.0"
__version_info__ = (0, 2, 0)

# Version components
MAJOR = 0
MINOR = 2  
PATCH = 0
PRE_RELEASE: str | None = None  # None, "alpha", "beta", "rc"
PRE_RELEASE_NUM: int | None = None

# Build metadata
BUILD_DATE = "2025-01-16"
BUILD_COMMIT: str | None = None  # Will be set by CI/CD

def get_version() -> str:
    """Get the current version string."""
    version = f"{MAJOR}.{MINOR}.{PATCH}"
    
    if PRE_RELEASE:
        version += f"-{PRE_RELEASE}"
        if PRE_RELEASE_NUM:
            version += f".{PRE_RELEASE_NUM}"
    
    return version

def get_version_info() -> dict[str, Any]:
    """Get detailed version information."""
    return {
        "version": get_version(),
        "version_info": __version_info__,
        "major": MAJOR,
        "minor": MINOR,
        "patch": PATCH,
        "pre_release": PRE_RELEASE,
        "pre_release_num": PRE_RELEASE_NUM,
        "build_date": BUILD_DATE,
        "build_commit": BUILD_COMMIT,
    }

# Ensure consistency
assert __version__ == get_version(), "Version mismatch between __version__ and get_version()"