"""
Best-effort audit log lookup. Discord doesn't push "who did this" on most
events, so we poll the recent audit log and match by target + recency.
"""

import discord


async def find_actor(
    guild: discord.Guild,
    action: discord.AuditLogAction,
    target_id: int,
    *,
    within_seconds: int = 10,
) -> discord.abc.User | None:
    if not guild.me.guild_permissions.view_audit_log:
        return None
    try:
        async for entry in guild.audit_logs(limit=5, action=action):
            if entry.target and entry.target.id == target_id:
                age = discord.utils.utcnow() - entry.created_at
                if age.total_seconds() <= within_seconds:
                    return entry.user
        return None
    except discord.Forbidden:
        return None
