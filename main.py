import os
import json
import requests
import sqlite3
import asyncio

from PIL import Image
from io import BytesIO
from datetime import datetime
from dotenv import load_dotenv

import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Button, View

from search import getMovies
from makeRoom import make_room


load_dotenv('envBot.env')
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
W2G_API_KEY = os.getenv('W2G_API_KEY')


conn = sqlite3.connect('movies.db')
c = conn.cursor()


c.execute('''CREATE TABLE IF NOT EXISTS movies (
                guild_id TEXT NOT NULL,
                user_id TEXT,
                movie_name TEXT,
                date_added TEXT
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
    embed.add_field(name="/addmovie", value="Add a movie to your plan to watch list", inline=False)
    embed.add_field(name="/deletemovie", value="Delete a movie from your plan to watch list", inline=False)
    embed.add_field(name="/clearmovies", value="Clear your plan to watch list", inline=False)
    embed.add_field(name="/listmovies", value="List all movies in your plan to watch list", inline=False)
    embed.add_field(name="/search", value="Search for movies & Make Watch2gether room", inline=False)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name='addmovie', description='Add a movie to your plan to watch list')
async def add_movie(interaction: discord.Interaction, movie_name: str):
    user_id = str(interaction.user.id)
    date_added = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    guild_id = str(interaction.guild.id)  
    c.execute("INSERT INTO movies (guild_id, user_id, movie_name, date_added) VALUES (?, ?, ?, ?)", (guild_id, user_id, movie_name, date_added))  # Add guild_id parameter
    conn.commit()
    embed = discord.Embed(title="Movie Added", description=f'"{movie_name}" has been added to your plan to watch list!', color=discord.Color.blue())
    await interaction.response.send_message(embed=embed)
    print(f'Added "{movie_name}" to user {user_id} list')

@bot.tree.command(name='deletemovie', description='Delete a movie from your plan to watch list')
async def delete_movie(interaction: discord.Interaction, movie_name: str):
    user_id = str(interaction.user.id)
    guild_id = str(interaction.guild.id)
    c.execute("DELETE FROM movies WHERE user_id = ? AND movie_name = ? AND guild_id = ?", (user_id, movie_name,guild_id))
    conn.commit()
    if c.rowcount > 0:
        embed = discord.Embed(title="Movie Removed", description=f'"{movie_name}" has been removed from your plan to watch list!', color=discord.Color.orange())
        await interaction.response.send_message(embed=embed)
        print(f'Removed "{movie_name}" from user {user_id} list')
    else:
        embed = discord.Embed(title="Not Found", description=f'"{movie_name}" is not in your plan to watch list!', color=discord.Color.red())
        await interaction.response.send_message(embed=embed)

@bot.tree.command(name='clearmovies', description='Clear your plan to watch list')
async def clear_movies(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    guild_id = str(interaction.guild.id)
    c.execute("DELETE FROM movies WHERE user_id = ? AND guild_id = ?", (user_id,guild_id))
    conn.commit()
    embed = discord.Embed(title="List Cleared", description='Your plan to watch list has been cleared!', color=discord.Color.purple())
    await interaction.response.send_message(embed=embed)
    print(f'Cleared list for user {user_id}')

@bot.tree.command(name='listmovies', description='List all movies in your plan to watch list')
async def list_movies(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    guild_id = str(interaction.guild.id)
    c.execute("SELECT movie_name, date_added FROM movies WHERE user_id = ? AND guild_id = ?", (user_id,guild_id))
    movies = c.fetchall()
    if not movies:
        embed = discord.Embed(title="No Movies", description='Your plan to watch list is empty!', color=discord.Color.red())
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

@bot.tree.command(name='search', description='search for movies')
async def search(interaction: discord.Interaction, query:str):
    try:
        user_id = str(interaction.user.id)
        results = getMovies(query)
        await interaction.response.send_message("Searching ...", ephemeral=True)
        
        images = [Image.open(BytesIO(requests.get(movie['cover']).content)) for movie in results]
        combined_image = MovieView.combine_images(images)
        view = discord.ui.View()

        with BytesIO() as image_binary:
            combined_image.save(image_binary, "JPEG")
            image_binary.seek(0)
            file=discord.File(fp=image_binary, filename='combined_image.jpg')
            embed = discord.Embed(title="Search Results", description=f"Here are the search results for '{query}':", color=discord.Color.green())
        for result in results:
            if result['type'] == 'MOVIE':
                embed.add_field(name=result['title'] + " duration: " + result['duration'] + "year:  "+result['year'], value=f"[Room For {result['title']}]({make_room(result['link'])})", inline=False)
            else:
                embed.add_field(name=result['title'] + " " + result['type'] + "episodes: " +result['episodes'], value=f"[Room For {result['title']}]({make_room(result['link'])})", inline=False)
            
        await interaction.followup.send(file=file, embed=embed, view = view)
        
        print(f'search from {user_id}')
    except Exception as e:
        print(f'Error in search command: {e}')

if DISCORD_TOKEN:
    bot.run(DISCORD_TOKEN)
else:
    print("No Discord token provided. Please set the DISCORD_TOKEN environment variable.")
