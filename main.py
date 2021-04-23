import discord
import os
import json
from replit import db
from keep_alive import keep_alive

#######################################
# 3 .env variables
# TOKEN: token of this app
# CUR_ADMIN: user_id of the current administrator of the game
# DEPOSITE_CHANNEL: channel_id which the bot stores all backup information and/or evidence
#######################################

client = discord.Client()
incomplete_data = {}
image_types = ["png", "jpeg", "jpg"]
image_name = {}
tournament = {
  1:"Doodle 2018 pvp single round",
  2:"Sketchful.io pair game",
  3:"2048 single round"
}

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    cmd = message.content
    user_name = message.author.name

    if cmd.startswith('$set_game_id'):
      game_id_string = cmd.split("$set_game_id ",1)[1]
      if game_id_string.isdecimal()==False:
        await message.channel.send("{}, please enter a positive integer as game_id".format(user_name))
        return
      game_id = int(game_id_string)
      if(game_id<=0):
        await message.channel.send("{}, the game_id is smaller than 0!".format(user_name))
      if(game_id>len(tournament)):
        await message.channel.send("{}, the game_id is larger than {},but it will be processed anyway!".format(user_name, len(tournament)))
      await message.channel.send(set_game_id(user_name,game_id))
      await message.channel.send("{}, the game_id updated is successfully. Your current game_id is {}.".format(user_name, game_id))

    elif cmd.startswith('$set_score'):
      score_string = cmd.split("$set_score ",1)[1]
      if(score_string.isdecimal()==False):
        await message.channel.send("{}, please enter a positive integer as score".format(user_name))
        return
      score = int(score_string)
      if(score>0):
        await message.channel.send(set_score(user_name,score))
        await message.channel.send("{}, the score of {} is updated successfully.".format(user_name, score))
      else:
        await message.channel.send("{}, the score should be positive. Please kindly try again".format(user_name))

    elif cmd.startswith('$get_entry'):
      if (incomplete_data.get(user_name)==None
      and (image_name.get(user_name)==None or image_name.get(user_name)=="")):
        await message.channel.send("{}, there is no data yet".format(user_name))
        return 
      if incomplete_data.get(user_name)!=None:
        await message.channel.send(incomplete_data[user_name])
      if(image_name.get(user_name)!=None and image_name.get(user_name)!=""):
        await message.channel.send("Found an image")
        await message.channel.send(file = discord.File(image_name[user_name]))

    elif cmd.startswith('$pic'):
      # https://www.reddit.com/r/Discord_Bots/comments/eojofe/py_saving_posted_images/
      for attachment in message.attachments:
        for image_type in image_types:
          if attachment.filename.lower().endswith(image_type):
            if(image_name.get(user_name)!=None and image_name.get(user_name)!=""):
              await message.channel.send("Deleting previous image")
              await message.channel.send(file = discord.File(image_name[user_name]))
              os.remove(image_name[user_name])
              image_name[user_name] = ""
            pic = "{}.{}".format(user_name,image_type)
            await attachment.save(pic)
            image_name[user_name] = pic
            await message.channel.send("The new image is added successfully")
               
    elif cmd.startswith('$submit'):
      if(incomplete_data.get(user_name)==None
      or incomplete_data[user_name].get("game_id")==None 
      or incomplete_data[user_name].get("score")==None 
      or incomplete_data[user_name]["game_id"]<=0
      or incomplete_data[user_name]["score"]<=0
      or image_name.get(user_name)==None 
      or image_name.get(user_name)==""):
        await message.channel.send("{}, there is something not right. Make sure to include a picture as well entering reasonable data".format(user_name))
      else:
        await message.channel.send("Processing... ")
        entries = db['entries']
        i = len(entries)
        #entries: user_name, game_id, score
        entries.append([])
        entries[i].append(user_name)
        entries[i].append(incomplete_data[user_name]["game_id"])
        entries[i].append(incomplete_data[user_name]["score"])
        db["entries"]=entries
        strt = "ENTRY {} with user {}".format(i,user_name)
        s_game_id = "game_id: {}".format(entries[i][1])
        s_score = "score: {}".format(entries[i][2])
        output_text = strt + "\n" + s_game_id + "\n" + s_score + "\n" + 'END ENTRY'
        print(output_text)
        depo_channel =  client.get_channel(int(os.environ['DEPOSITE_CHANNEL']))
        await depo_channel.send(output_text)
        await depo_channel.send(file = discord.File(image_name[user_name]))
        os.remove(image_name[user_name])
        image_name[user_name] = ""
        incomplete_data[user_name]["game_id"] = -1
        incomplete_data[user_name]["score"] = 0
        await message.channel.send("{}'s entry is displayed in {}".format(user_name,depo_channel.name))

    elif cmd.startswith("$export"):
      await message.channel.send("send by DM")
      entries = db['entries']
      if(os.path.exists("entries.json")):
        os.remove("entries.json")
      for i in range(len(entries)):
        entry = entries[i]
        with open('entries.json', 'a') as file:
          if(i==0):
            file.write('[')
          file.write(json.dumps(list(entry)))
          if(i!=len(entries)-1):
            file.write(",\n")
          else:
            file.write("]")
      if(os.path.exists("entries.json")):
        await message.author.send(file = discord.File("entries.json"))
      else:
        await message.author.send("no submitted entries yet")

    elif cmd.startswith('$message_admin'):
      adm = await client.fetch_user(int(os.environ['CUR_ADMIN']))
      msg = cmd.split("$message_admin ",1)[1]
      await adm.send('{}: {}'.format(user_name,msg))
      await message.channel.send("{}, your message is received".format(user_name))

    elif cmd.startswith('$lucky'):
      if(message.author.id!=int(os.environ['CUR_ADMIN'])):
        return
      print("HI")
      lucky_id_string = cmd.split("$lucky ",1)[1]
      if lucky_id_string.isdecimal()==False:
        await message.channel.send("{}, please enter a positive integer as lucky_id".format(user_name))
        return
      lucky_id = int(lucky_id_string)
      entry = db['entries'][lucky_id]
      await message.channel.send(list(entry))

    elif cmd.startswith('$set_leaderboard'):
      if(message.author.id!=int(os.environ['CUR_ADMIN'])):
        return
      for attachment in message.attachments:
        print(attachment.filename)
        if attachment.filename == "leaderboard.json":
          if(os.path.exists("leaderboard.json")):
            os.remove("leaderboard.json")
          await attachment.save(attachment.filename)
          await message.channel.send("The new leaderboard is added successfully")
          

    elif cmd.startswith("$get_leaderboard"):
      if(os.path.exists("leaderboard.json")==False):
        await message.channel.send("Leaderboard is not updated yet...")
      else:
        await message.channel.send(file = discord.File('leaderboard.json'))
      
    

def init_db(): 
    if db.get('entries') ==None:
      db['entries'] = []

def clear_pics():
  files = [f for f in os.listdir('.') if os.path.isfile(f)]
  for f in files:
      if(f not in ['main.py', 'keep_alive.py', 'pyproject.toml', 'poetry.lock']):
        os.remove(f)

def copy_entries():
  cp = []
  for ety in db['entries']:
    cp_ety = []
    for e in ety:
      cp_ety.append(e)
    cp.append(cp_ety)
  return cp

def get_user_name(submission_id):
  return db["entries"][submission_id][0]
    
def set_game_id(user_name, game_id):
  s = "processing..."
  if(incomplete_data.get(user_name)==None):
    init_cur_game(user_name)
  if(incomplete_data[user_name]["game_id"]!=-1
  and incomplete_data[user_name]['game_id']!=game_id 
  and incomplete_data[user_name]['score']!=0):
    s+="Resetting Score after game_id_change."
    incomplete_data[user_name]["score"]=0

  incomplete_data[user_name]["game_id"] = game_id
  return s

def set_score(user_name,score):
  s = "processing..."
  if(incomplete_data.get(user_name)==None):
    init_cur_game(user_name)
  incomplete_data[user_name]["score"] = score
  return s

def init_cur_game(user_name):
  if(incomplete_data.get(user_name)==None):
    incomplete_data[user_name] = {}
  incomplete_data[user_name]["game_id"] = -1
  incomplete_data[user_name]["score"] = 0

keep_alive()
db.clear()
clear_pics()
init_db()
client.run(os.environ['TOKEN'])
