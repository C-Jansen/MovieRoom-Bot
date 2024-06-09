import os

import requests
import sqlite3

from PIL import Image
from io import BytesIO
from datetime import datetime
from dotenv import load_dotenv

import discord
from discord.ext import commands
from discord import app_commands

from search import searchMovies
from makeRoom import make_room
#from keep_it_alive import keep_alive


load_dotenv('.env')
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
W2G_API_KEY = os.getenv('W2G_API_KEY')

conn = sqlite3.connect('movies.db')
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS movies (
                guild_id TEXT NOT NULL,
                user_id TEXT,
                movie_name TEXT,
                date_added TEXT,
                media_type TEXT
            )''')
conn.commit()

class MyBot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)
        
    async def on_ready(self):
        await self.tree.sync()
        print(f'{self.user} has connected to Discord!')

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            await ctx.send("This command does not exist.")
        else:
            await ctx.send("An error occurred.")
            print(f'Error: {error}')

bot = MyBot()

@bot.tree.command(name='help', description='Show the help message' )
async def help(interaction: discord.Interaction):
    embed = discord.Embed(title="Help", description="Here are the available commands:", color=discord.Color.green())
    embed.add_field(name="/add <media_type: tv/movie> <movie_name: name>", value="Add a movie to your plan to watch list", inline=False)
    embed.add_field(name="/delete <movie_name: name>", value="Delete a movie from your plan to watch list", inline=False)
    embed.add_field(name="/clear", value="Clear your plan to watch list", inline=False)
    embed.add_field(name="/list", value="List all movies in your plan to watch list", inline=False)
    embed.add_field(name="/search <movie_name: name>", value="Search for movies & Make Watch2gether room", inline=False)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name='add', description='Add a movie or tv Show to your plan to watch list')
async def add_movie(interaction: discord.Interaction, media_type: str, movie_name: str):
    if media_type.lower() not in ['tv', 'movie']:
        await interaction.response.send_message('Invalid media type. Please choose either "tv" or "movie".')
        return

    user_id = str(interaction.user.id)
    date_added = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    guild_id = str(interaction.guild.id)  
    c.execute("INSERT INTO movies (guild_id, user_id, movie_name, date_added, media_type) VALUES (?, ?, ?, ?, ?)", (guild_id, user_id, movie_name, date_added, media_type))  # Add guild_id and media_type parameters
    conn.commit()
    embed = discord.Embed(title="Added successfully", description=f'"{movie_name}" ({media_type}) has been added to your plan to watch list!', color=discord.Color.blue())
    await interaction.response.send_message(embed=embed)
    print(f'Added "{movie_name}" ({media_type}) to user {user_id} list')

@bot.tree.command(name='delete', description='Delete a movie or tv show from your plan to watch list')
async def delete_movie(interaction: discord.Interaction, movie_name: str):
    user_id = str(interaction.user.id)
    guild_id = str(interaction.guild.id)
    c.execute("DELETE FROM movies WHERE user_id = ? AND movie_name = ? AND guild_id = ?", (user_id, movie_name,guild_id))
    conn.commit()
    if c.rowcount > 0:
        embed = discord.Embed(title="Removed successfully", description=f'"{movie_name}" has been removed from your plan to watch list!', color=discord.Color.orange())
        await interaction.response.send_message(embed=embed)
        print(f'Removed "{movie_name}" from user {user_id} list')
    else:
        embed = discord.Embed(title="Not Found", description=f'"{movie_name}" is not in your plan to watch list!', color=discord.Color.red())
        await interaction.response.send_message(embed=embed)

@bot.tree.command(name='clearlist', description='Clear your plan to watch list')
async def clear_movies(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    guild_id = str(interaction.guild.id)
    c.execute("DELETE FROM movies WHERE user_id = ? AND guild_id = ?", (user_id,guild_id))
    conn.commit()
    embed = discord.Embed(title="List Cleared", description='Your plan to watch list has been cleared!', color=discord.Color.purple())
    await interaction.response.send_message(embed=embed)
    print(f'Cleared list for user {user_id}')

@bot.tree.command(name='list', description='List all movies or tv show in your plan to watch list')
async def list_movies(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    guild_id = str(interaction.guild.id)
    c.execute("SELECT movie_name, date_added FROM movies WHERE user_id = ? AND guild_id = ?", (user_id,guild_id))
    movies = c.fetchall()
    if not movies:
        embed = discord.Embed(title="Ba7", description='Your plan to watch list is empty!', color=discord.Color.red())
        await interaction.response.send_message(embed=embed)
        print(f'User {user_id} list is empty')
    else:
        movies_list = "\n".join([f"{movie[0]} (Added on {movie[1]})" for movie in movies])
        embed = discord.Embed(title="Your Movies", description=f'Your plan to watch list:\n{movies_list}', color=discord.Color.blue())
        await interaction.response.send_message(embed=embed)
        print(f'Listed movies for user {user_id}')


class MovieView():
    def __init__(self, movies):
        super().__init__()
        self.images = [Image.open(BytesIO(requests.get(movie['cover']).content)) for movie in movies]
        self.combined_image = self.combine_images(self.images)

    @staticmethod
    def combine_images(images):
        widths, heights = zip(*(i.size for i in images))
        total_width = sum(widths)
        max_height = max(heights)
        new_img = Image.new('RGB', (total_width, max_height))
        x_offset = 0
        for img in images:
            img = img.resize((img.width, max_height))
            new_img.paste(img, (x_offset, 0))
            x_offset += img.width
        return new_img

@bot.tree.command(name='search', description='search for movies & make Watch2gether room')
async def search(interaction: discord.Interaction, query: str, season: str = "1", episode: str = "1"):
    try:
        user_id = str(interaction.user.id)
        season = season if season else "1"  
        episode = episode if episode else "1"  
        results = searchMovies(query, season, episode)
        await interaction.response.send_message("Searching ...", ephemeral=True)
        
        images = [Image.open(BytesIO(requests.get(movie['cover']).content)) for movie in results]
        combined_image = MovieView.combine_images(images)
        view = discord.ui.View()

        with BytesIO() as image_binary:
            combined_image.save(image_binary, "JPEG")
            image_binary.seek(0)
            file=discord.File(fp=image_binary, filename='combined_image.jpg')
            embed = discord.Embed(title="Search Results", description=f"Here are the search results for '{query}':", color=discord.Color.green())
            embed.add_field(name="user", value=f"{interaction.user.mention}", inline=False)
        for result in results:
            if result['type'] == 'MOVIE':
                embed.add_field(
                    name=result['title'] + " ( '"+ result['type'] + "' duration: " + result['duration'] + " min / year:  "+result['year']+" )",
                    value=f"[{'Room'}]({make_room(result['link'])})" + " | " + f"[{'Direct link'}]({result['link']})",
                    inline=False
                )
            else:
                embed.add_field(
                    name=result['title'] + " ( seasons: " + result['type'] + " / episodes: " +result['episodes']+" )",
                    value=f"[{'Room'}]({make_room(result['link'])})" + " | " + f"[{'Direct link'}]({result['link']})",
                    inline=False
                )
        await interaction.followup.send(file= file, embed= embed, view= view)
        
        print(f'search from {user_id}')
    except Exception as e:
        embed = discord.Embed(title="Not found", description=f"'{query}' not found; verify the name '{str(e)}'", color=discord.Color.red())
        print(f'this Error in search command: {str(e)}')
        await interaction.followup.send(embed=embed)


if DISCORD_TOKEN:
    bot.run(DISCORD_TOKEN)
else:
    print("No Discord token")
