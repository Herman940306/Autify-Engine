"""Autify Engine V1 — License Manager.

Hardware-bound licensing with online activation, reactivation tracking,
 and expiration support.  Zero-Cloud: license data is stored locally.
"""

import uuid
import platform
import hashlib
import json
import os
from datetime import datetime, timedelta

LICENSE_FILE = os.environ.get("LICENSE_FILE_PATH", "license.json")

MAX_REACTIVATIONS = 2
REACTIVATION_WINDOW_DAYS = 365


def get_hardware_fingerprint() -> str:
    """SHA-256 hash of MAC address + OS info.  Deterministic per machine."""
    node = uuid.getnode()
    sys_info = platform.system() + platform.release() + platform.machine()
    fingerprint_raw = f"{node}-{sys_info}"
    return hashlib.sha256(fingerprint_raw.encode()).hexdigest()


def verify_license() -> tuple[bool, str]:
    """Check the local license file matches current hardware.

    Returns
    -------
    (is_valid, message)
    """
    if not os.path.exists(LICENSE_FILE):
        return False, "License file not found. Please activate software."

    with open(LICENSE_FILE, "r") as f:
        try:
            license_data = json.load(f)
        except Exception:
            return False, "Corrupt license file."

    current_fp = get_hardware_fingerprint()

    if license_data.get("fingerprint") != current_fp:
        return False, "Hardware Fingerprint mismatch. Software locked to another device."

    # Check expiration if present
    expires = license_data.get("expires")
    if expires:
        try:
            exp_date = datetime.fromisoformat(expires)
            if datetime.now() > exp_date:
                return False, "License has expired. Please renew."
        except ValueError:
            pass  # malformed date — treat as non-expiring

    return True, "License Valid."


def activate(license_key: str, user_id: str, duration_days: int = 365) -> tuple[bool, str]:
    """Activate the license on current hardware.

    Creates (or overwrites) the local license file with the hardware
    fingerprint and activation metadata.

    Parameters
    ----------
    license_key : str
        The key provided by the Developer.
    user_id : str
        Identifier for the activating user.
    duration_days : int
        License validity period from today.

    Returns
    -------
    (success, message)
    """
    fp = get_hardware_fingerprint()
    now = datetime.now()

    data = {
        "license_key": license_key,
        "fingerprint": fp,
        "user_id": user_id,
        "activated_at": now.isoformat(),
        "expires": (now + timedelta(days=duration_days)).isoformat(),
        "reactivations_used": 0,
        "reactivation_window_start": now.isoformat(),
        "activation_history": [
            {"fingerprint": fp, "timestamp": now.isoformat(), "action": "activate"}
        ],
    }

    with open(LICENSE_FILE, "w") as f:
        json.dump(data, f, indent=2)

    return True, "License activated successfully."


def reactivate(license_key: str, user_id: str) -> tuple[bool, str]:
    """Reactivate the license on new hardware (max 2 per 12 months).

    Returns
    -------
    (success, message)
    """
    if not os.path.exists(LICENSE_FILE):
        return False, "No existing license found. Use activate() first."

    with open(LICENSE_FILE, "r") as f:
        try:
            data = json.load(f)
        except Exception:
            return False, "Corrupt license file."

    if data.get("license_key") != license_key:
        return False, "License key mismatch."

    # Check reactivation window
    window_start_str = data.get("reactivation_window_start")
    if window_start_str:
        window_start = datetime.fromisoformat(window_start_str)
        if (datetime.now() - window_start).days > REACTIVATION_WINDOW_DAYS:
            # Reset counter for a new window
            data["reactivations_used"] = 0
            data["reactivation_window_start"] = datetime.now().isoformat()

    used = data.get("reactivations_used", 0)
    if used >= MAX_REACTIVATIONS:
        return False, f"Reactivation limit reached ({MAX_REACTIVATIONS} per {REACTIVATION_WINDOW_DAYS} days). Contact Developer for review."

    # Perform reactivation
    fp = get_hardware_fingerprint()
    now = datetime.now()
    data["fingerprint"] = fp
    data["user_id"] = user_id
    data["reactivations_used"] = used + 1

    history = data.get("activation_history", [])
    history.append({"fingerprint": fp, "timestamp": now.isoformat(), "action": "reactivate"})
    data["activation_history"] = history

    with open(LICENSE_FILE, "w") as f:
        json.dump(data, f, indent=2)

    remaining = MAX_REACTIVATIONS - data["reactivations_used"]
    return True, f"Reactivated successfully. {remaining} reactivation(s) remaining."


# Legacy alias
offline_activate = activate
