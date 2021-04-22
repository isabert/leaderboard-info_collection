import discord
import os
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
has_handle = {}
image_types = ["png", "jpeg", "jpg"]
image_name = {}
tournament = {
  1:"Doodle 2018 pairs",
  2:"Scribble game Quartets 8 rounds",
  3:"2048"
}
verified = {}
total_final_entries = 0
@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # if message.content.startswith('$hello'):
        # await message.channel.send('Hello!')
        # depo_channel =  client.get_channel(int(os.environ['DEPOSITE_CHANNEL']))
        # await depo_channel.send("HI")
        # await message.author.send("HI")
        # the reason we don't use get_user is because it relies on cache, and therefore will return a NONE
        # adm = await client.fetch_user(int(os.environ['CUR_ADMIN']))
        # await adm.send("HELLO")

    cmd = message.content
    user = message.author
    user_name = message.author.name
    user_id = user.id
    if cmd.startswith('$set_handle'):
      handle = cmd.split("$set_handle ",1)[1]
      await message.channel.send(set_handle(handle,user_name))

    elif cmd.startswith('$get_handle'):
      await message.channel.send(get_handle(user_name))

    elif cmd.startswith('$list_handles'):
      if db.get('existing_handles')==None:
        db['existing_handles'] = []
      if db.get('handles') ==None:
        db['handles'] = {}
      await message.channel.send(list(db['existing_handles']))
      await message.channel.send(dict(db['handles']))
      await message.channel.send(has_handle)
      await message.channel.send(verified)

    elif cmd.startswith('$set_game_id'):
      if(has_handle.get(user_name) is None):
        await message.channel.send("{}, please use $set_handle to selete a handle".format(user_name))
        return
      game_id = int(cmd.split("$set_game_id ",1)[1])
      if(game_id<=0):
        await message.channel.send("{}, the game_id is smaller than 0!".format(user_name))
      if(game_id>len(tournament)):
        await message.channel.send("{}, the game_id is larger than {},but it will be processed anyway!".format(user_name, len(tournament)))
      await message.channel.send(set_game_id(user_name,game_id))
      await message.channel.send("{}, the game_id updated is successfully. Your current game_id is {}.".format(user_name, game_id))

    elif cmd.startswith('$set_score'):
      if(has_handle.get(user_name) is None):
        await message.channel.send("{}, please use $set_handle to selete a handle".format(user_name))
        return
      score = int(cmd.split("$set_score ",1)[1])
      if(score>0):
        await message.channel.send(set_score(user_name,score))
        await message.channel.send("{}, the score of {} is updated successfully.".format(user_name, score))
      else:
        await message.channel.send("{}, the score should be positive. Please kindly try again".format(user_name))

    elif cmd.startswith('$get_entry'):
      if (incomplete_data.get(user_name)==None
      and (image_name.get(user_name)==None or image_name.get(user_name)!="")):
        await message.channel.send("{}, there is no data yet".format(user_name))
      elif incomplete_data.get(user_name)!=None:
        await message.channel.send(incomplete_data[user_name])
      elif(image_name.get(user_name)!=None and image_name.get(user_name)!=""):
        await message.channel.send("There is something precious.")
        await message.channel.send(file = discord.File(image_name[user_name]))

    elif cmd.startswith('$pic'):
      # https://www.reddit.com/r/Discord_Bots/comments/eojofe/py_saving_posted_images/
      for attachment in message.attachments:
        for image_type in image_types:
          if attachment.filename.lower().endswith(image_type):
            pic = "{}.{}".format(user_name,image_type)
            await attachment.save(pic)
            image_name[user_name] = pic
            
    elif cmd.startswith('$submit_entry'):
      if(incomplete_data.get(user_name)==None
      or incomplete_data[user_name]["game_id"]<=0
      or incomplete_data[user_name]["score"]<=0
      or image_name.get(user_name)==None 
      or image_name.get(user_name)!=""):
        await message.channel.send("{}, there is something not right. Make sure to include a picture as well entering reasonable data".format(user_name))
      else:
        await message.channel.send("{}, ".format(user_name))

    
    


    
        

def clear_pics():
  files = [f for f in os.listdir('.') if os.path.isfile(f)]
  for f in files:
    if(f!="main.py" or f!="keep_alive.py"):
      os.remove(f)

def set_handle(handle,user_name):
  s = ""
  existing_handles = db["existing_handles"]
  if(verified.get(user_name)==None):
    verified[user_name] = False
  if(handle in existing_handles):
    return "{} is already used by someone else".format(handle)
  if "handles" in db.keys():
    handles = db["handles"]
    if(handles.get(user_name)!=None):
      old_handle = handles[user_name]
      existing_handles.remove(old_handle)
      handles[user_name] = handle
      s = "{} has changed their handle from {} to {}!".format(user_name, old_handle, handle)
    else:
      has_handle[user_name]=True
      handles[user_name] = handle
      s = "{} has added their handle name as {}!".format(user_name, handle)
    db["handles"] = handles

  else:
    db["handles"] = {user_name:handle}
    has_handle[user_name]=True
    s = "{} has added their handle name as {}!".format(user_name, handle)

  existing_handles.append(handle)
  db["existing_handles"] = existing_handles

  return s

def get_handle(user_name):
  if "handles" in db.keys():
    handles = db["handles"]
    if(handles.get(user_name)!=None):
      return "{} has the handle of {}!".format(user_name,handles[user_name] )
    else:
      return "{} does not have a handle!".format(user_name)

  else:
    db["handles"] = {}
    return "{} does not have a handle!".format(user_name)

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
db["existing_handles"] = []
client.run(os.environ['TOKEN'])
