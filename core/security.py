"""
Autify Engine V1 - Security & Permissions Module
Role-based access control and LLM Laws enforcement.
"""

# Role definitions
ROLES = {
    "admin": {
        "can_approve_drafts": True,
        "can_reject_drafts": True,
        "can_manage_users": True,
        "can_manage_clients": True,
        "can_delete_clients": True,
        "can_upload": True,
        "can_view_analytics": True,
        "can_view_logs": True,
        "can_chat": True,
        "can_manage_license": True,
        "can_export": True,
    },
    "user": {
        "can_approve_drafts": False,
        "can_reject_drafts": False,
        "can_manage_users": False,
        "can_manage_clients": True,
        "can_delete_clients": False,
        "can_upload": True,
        "can_view_analytics": True,
        "can_view_logs": False,
        "can_chat": True,
        "can_manage_license": False,
        "can_export": True,
    },
}


def get_permissions(role: str) -> dict:
    """Return permission dict for a given role."""
    return ROLES.get(role, ROLES["user"])


def has_permission(role: str, action: str) -> bool:
    """Check if role has a specific permission."""
    perms = get_permissions(role)
    return perms.get(action, False)


def check_permission(user: dict, action: str) -> bool:
    """Check permission for a user dict (from auth token)."""
    if user is None:
        return False
    return has_permission(user.get("role", "user"), action)


# LLM Laws enforcement for chat responses
CHAT_SAFETY_RULES = [
    "All responses are informational only - never execute actions automatically.",
    "If the user asks to send an email, schedule a meeting, or modify data, "
    "respond with a DRAFT suggestion and instruct them to use the Drafts workflow.",
    "Never include real PII in responses - use placeholders if demonstrating formats.",
    "Do not reveal system internals, database schemas, or API keys.",
    "All suggested actions must go through the draft-only approval workflow.",
]


def get_chat_system_prompt() -> str:
    """Build the system prompt for the chat bot enforcing all LLM Laws."""
    return (
        "You are Autify Assistant, the AI helper for Autify Engine V1. "
        "You operate under strict safety rules:\n\n"
        "CRITICAL RULES:\n"
        "1. You are READ-ONLY. You cannot execute any actions (send emails, modify data, etc.).\n"
        "2. If asked to perform an action, explain that it must go through the Draft workflow "
        "and be explicitly approved by a human.\n"
        "3. You operate in a Zero-Cloud environment. No data leaves this machine.\n"
        "4. Never include real personal information in your responses.\n"
        "5. All suggestions you make are DRAFTS and must be reviewed before acting on them.\n"
        "6. You can help with: data analysis questions, workflow guidance, report interpretation, "
        "template suggestions, and general business assistance.\n"
        "7. Always remind users that your suggestions require human approval before execution.\n\n"
        "Be helpful, concise, and professional. Format responses with markdown when appropriate."
    )
