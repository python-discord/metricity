"""An ext to listen for member events and syncs them to the database."""

import contextlib

import discord
from asyncpg.exceptions import UniqueViolationError
from discord.ext import commands
from sqlalchemy import update

from metricity.bot import Bot
from metricity.config import BotConfig
from metricity.database import async_session
from metricity.models import User


class MemberListeners(commands.Cog):
    """Listen for member events and sync them to the database."""

    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member) -> None:
        """On a user leaving the server mark in_guild as False."""
        await self.bot.sync_process_complete.wait()

        if member.guild.id != BotConfig.guild_id:
            return

        async with async_session() as sess:
            await sess.execute(
                update(User).where(User.id == str(member.id)).values(in_guild=False),
            )
            await sess.commit()

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        """On a user joining the server add them to the database."""
        await self.bot.sync_process_complete.wait()

        if member.guild.id != BotConfig.guild_id:
            return

        async with async_session() as sess:
            if await sess.get(User, str(member.id)):
                await sess.execute(update(User).where(User.id == str(member.id)).values(
                    id=str(member.id),
                    name=member.name,
                    avatar_hash=getattr(member.avatar, "key", None),
                    guild_avatar_hash=getattr(member.guild_avatar, "key", None),
                    joined_at=member.joined_at,
                    created_at=member.created_at,
                    is_staff=BotConfig.staff_role_id in [role.id for role in member.roles],
                    public_flags=dict(member.public_flags),
                    pending=member.pending,
                    in_guild=True,
                ))
            else:
                with contextlib.suppress(UniqueViolationError):
                    sess.add(User(
                        id=str(member.id),
                        name=member.name,
                        avatar_hash=getattr(member.avatar, "key", None),
                        guild_avatar_hash=getattr(member.guild_avatar, "key", None),
                        joined_at=member.joined_at,
                        created_at=member.created_at,
                        is_staff=BotConfig.staff_role_id in [role.id for role in member.roles],
                        public_flags=dict(member.public_flags),
                        pending=member.pending,
                        in_guild=True,
                    ))

            await sess.commit()

    @commands.Cog.listener()
    async def on_member_update(self, _before: discord.Member, member: discord.Member) -> None:
        """When a member updates their profile, update the DB record."""
        await self.bot.sync_process_complete.wait()

        if member.guild.id != BotConfig.guild_id:
            return

        # Joined at will be null if we are not ready to process events yet
        if not member.joined_at:
            return

        roles = {role.id for role in member.roles}

        async with async_session() as sess:
            if db_user := await sess.get(User, str(member.id)):
                if (
                    db_user.name != member.name or
                    db_user.avatar_hash != getattr(member.avatar, "key", None) or
                    db_user.guild_avatar_hash != getattr(member.guild_avatar, "key", None) or
                    (BotConfig.staff_role_id in roles) != db_user.is_staff
                    or db_user.pending is not member.pending
                ):
                    await sess.execute(update(User).where(User.id == str(member.id)).values(
                        id=str(member.id),
                        name=member.name,
                        avatar_hash=getattr(member.avatar, "key", None),
                        guild_avatar_hash=getattr(member.guild_avatar, "key", None),
                        joined_at=member.joined_at,
                        created_at=member.created_at,
                        is_staff=BotConfig.staff_role_id in roles,
                        public_flags=dict(member.public_flags),
                        in_guild=True,
                        pending=member.pending,
                    ))
            else:
                with contextlib.suppress(UniqueViolationError):
                    sess.add(User(
                        id=str(member.id),
                        name=member.name,
                        avatar_hash=getattr(member.avatar, "key", None),
                        guild_avatar_hash=getattr(member.guild_avatar, "key", None),
                        joined_at=member.joined_at,
                        created_at=member.created_at,
                        is_staff=BotConfig.staff_role_id in roles,
                        public_flags=dict(member.public_flags),
                        in_guild=True,
                        pending=member.pending,
                    ))

            await sess.commit()



async def setup(bot: Bot) -> None:
    """Load the MemberListeners cog."""
    await bot.add_cog(MemberListeners(bot))
