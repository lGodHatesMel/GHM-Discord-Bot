import discord
from discord.ext import commands
import tweepy
import asyncio
import json
import sqlite3

conn = sqlite3.connect('twitter.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS twitter_users (user_id text)''')
conn.commit()
conn.close()

class TwitterCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        with open('config.json') as f:
            config = json.load(f)

        twitter_config = config['twitter']
        consumer_key = twitter_config['consumer_key']
        consumer_secret = twitter_config['consumer_secret']
        access_token = twitter_config['access_token']
        access_token_secret = twitter_config['access_token_secret']

        self.channel_id = int(config['channel_ids']['TwitterUpdates'])

        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)
        api = tweepy.API(auth)

        conn = sqlite3.connect('twitter.db')
        c = conn.cursor()
        c.execute('SELECT * FROM twitter_users')
        twitter_user_ids = [row[0] for row in c.fetchall()]
        conn.close()

        # Set up Twitter stream for each user
        for twitter_user_id in twitter_user_ids:
            myStreamListener = self.MyStreamListener(self.bot, self.channel_id)
            myStream = tweepy.Stream(auth = api.auth, listener=myStreamListener)
            myStream.filter(follow=[twitter_user_id], is_async=True)

    class MyStreamListener(tweepy.StreamListener):
        def __init__(self, bot, channel_id):
            self.bot = bot
            self.channel_id = channel_id

        def on_status(self, status):
            asyncio.run_coroutine_threadsafe(self.bot.get_channel(self.channel_id).send(f"New tweet from {status.user.name}: {status.text}"), self.bot.loop)

def setup(bot):
    bot.add_cog(TwitterCog(bot))