import os
import discord
from discord.ext import commands
from utils import check_email_in_database
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.guild_id = int(os.getenv('G_ID'))

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Bot is ready as {self.bot.user}')
        print(f"Parsed GUILD_ID: {self.guild_id}")

        guild = discord.utils.get(self.bot.guilds, id=self.guild_id)
        if guild:
            print(f"Guild found: {guild.name} (ID: {guild.id})")
        else:
            print("Guild not found.")

        print("Current guilds:")
        for g in self.bot.guilds:
            print(f"Guild: {g.name} (ID: {g.id})")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.user_id == self.bot.user.id:
            return

        channel = self.bot.get_channel(payload.channel_id)
        if not channel:
            return

        guild = self.bot.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)
        if not member:
            return

        # Verify if the reaction was added in the verification channel
        verification_channel_id = int(os.getenv('VERIFICATION_CHANNEL_ID'))
        if channel.id == verification_channel_id:
            if str(payload.emoji) == '✅':
                verified_role = discord.utils.get(guild.roles, name="v-member")
                if verified_role:
                    await member.add_roles(verified_role)
                    await member.send(f"You are verified ✅; welcome to the {guild.name} community! Now, we need to verify your subscription plan to custom-tailor your experience. Please respond to this message with your email address using the command `!verify your-email@example.com`.")
                    print(f"{member} changed their role to v-member after verification.")

    @commands.command(name="verify")
    async def verify_command(self, ctx, email: str):
        guild = discord.utils.get(self.bot.guilds, id=self.guild_id)
        if not guild:
            await ctx.send("Server not found.")
            return

        member = guild.get_member(ctx.author.id)
        if not member:
            await ctx.send("Server not found.")
            return

        founder_role = discord.utils.get(guild.roles, name="founder-member")
        challenger_role = discord.utils.get(guild.roles, name="challenger")

        if check_email_in_database(email):
            # If the user has the challenger role, remove it
            if challenger_role in member.roles:
                await member.remove_roles(challenger_role)
                print(f"{member} removed the challenger role before becoming a founder-member.")
            role = founder_role
            print(f"{member} changed their role to founder-member after Email verification.")
        else:
            # If the user has the founder-member role, remove it
            if founder_role in member.roles:
                await member.remove_roles(founder_role)
                print(f"{member} removed the founder-member role before becoming a challenger.")
            role = challenger_role
            print(f"{member} changed their role to challenger after Email verification.")

        if role:
            try:
                await member.add_roles(role)
                await ctx.send(f"You have been assigned the role: {role.name}")
            except discord.Forbidden:
                await ctx.send("I don't have permission to assign roles.")
            except discord.HTTPException as e:
                await ctx.send(f"HTTP Exception: {str(e)}")
            except Exception as e:
                await ctx.send(f"Error assigning the role: {str(e)}")
        else:
            await ctx.send("Role not found.")

async def setup(bot):
    await bot.add_cog(Events(bot))