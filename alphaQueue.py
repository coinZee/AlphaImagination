import tempfile
import asyncio
import discord
from discord.ext import commands
import requests
import io
from PIL import Image
from discord import app_commands
import aiohttp
import pymongo
import secrets
import os
import UpscalerAi
import random
import VariationAi
import filtuh 
# Set up MongoDB connection
mongo_uri = 'mongodb+srv://coinz:Aung1970@imaginationbawtdb.oozswx8.mongodb.net/'
client = pymongo.MongoClient(mongo_uri)
db = client['ImaginationBawtDB']
users_collection = db['users']

# Initialize the bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)

# Sets bot status and sync commands to discord Server
@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="/imagine & /helpimagine"))
    await bot.tree.sync()

'''
# In case, members can be added to database automatically when they join to server with this method
@bot.event
async def on_member_join(member):
    existing_user = users_collection.find_one({'_id': user_id})

    if existing_user is None:
        # If the user doesn't exist, add them to the database
        user_data = {
            '_id': member.id,
            'plan': 'Free',  # Set the default plan to 'Free'
            'credits': 200,  # Start with 200 credits
            # Add more user properties as needed
        }
        users_collection.insert_one(user_data)
'''
# Hugging Face Inference API details
API_URL = ["https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0",
           "https://api-inference.huggingface.co/models/FFusion/400GB-LoraXL",
           "https://api-inference.huggingface.co/models/inu-ai/niji-diffusion-xl-base-1.0",
           "https://api-inference.huggingface.co/models/emilianJR/HRA_hyperrealism_art"

]
HEADERS = {"Authorization": "Bearer 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"}

# Function to Request to Huggingface Txt2Img model
async def generate_image(ctx, description, fileNameInt):
    
    
    user_id = str(ctx.author.id)
    user = users_collection.find_one({'_id': user_id})
    model = user['chosen_url']
    the_url = API_URL[model]

    options = {
    "use_cache": False,  # You can set this to True or False
    "wait_for_model": True  # You can set this to True or False
}
    payload = {
        "inputs": description,
        "options": options
    }
    # requests to huggingface Txt2img model with user's prompt then returns bytes.
    async with aiohttp.ClientSession() as session:
        async with session.post(the_url, headers=HEADERS, json=payload) as response:
            if response.status == 503:
                raise Exception("Model just loaded, try again in about 10-20 seconds")
            elif response.status == 200:
                # After receiving from Huggingface, converts bytes to Image
                image_bytes = await response.read()
                if image_bytes:
                    try:
                        # Define the file extension
                        file_extension = ".png"
                        # Combine the random string with the file extension to create a unique filename
                        temp_file_path = f"{fileNameInt}{file_extension}"
                        # Save the generated image with the unique filename
                        #image = Image.open(io.BytesIO(image_bytes))
                        image = Image.open(io.BytesIO(image_bytes))
                        image.save(temp_file_path)
                        # Set a timer to delete the temporary file after 5 minutes
                        asyncio.get_event_loop().call_later(300, os.remove, temp_file_path)
                        
                          # Return the path to the temporary image file
                        return image
                    except Exception as e:
                        raise Exception("Failed to save and set a timer for the image: " + str(e))
                            
                else:
                    raise Exception("Empty image bytes received from the API")
            else:
                raise Exception("Failed to retrieve image from the API. Status code: " + str(response.status))

@bot.hybrid_command(name="register", description="registers ur self to use the bot")
async def register(ctx):

    str_id=str(ctx.author.id)
    print(type(str_id), str_id)
    # Check if the user already exists in the database
    existing_user = users_collection.find_one({'_id': str_id})

    if existing_user is None:
        # If the user doesn't exist, add them to the database
        user_data = {
            '_id': str_id,
            'plan': 'Free',  # Sets the default plan to 'Free'
            'credits': 200,  # Starts with 200 credits
            'chosen_url': 0
            # More properties can be Added
        }
        users_collection.insert_one(user_data)
        await ctx.send(f"{ctx.author.mention} has been added to the database.")
    else:
        await ctx.send(f"{ctx.author.mention} is already in the database.")


# Main Command to Image Generation Process 
@bot.hybrid_command(name="imagine", description="generates image")
async def imagine(ctx, *, prompt: str):
    try:

        fileNameInt = random.randint(1, 1000000000)
        # Create buttons
        VariationBtn = discord.ui.Button(label="Variation", style=discord.ButtonStyle.primary)
        UpscaleBtn = discord.ui.Button(label="Upscale", style=discord.ButtonStyle.primary)
        
        # Create a view and add the buttons
        ProView = discord.ui.View()
        ProView.add_item(VariationBtn)

        ProPlusView = discord.ui.View()
        ProPlusView.add_item(VariationBtn)
        ProPlusView.add_item(UpscaleBtn)
            
        UpscaleView = discord.ui.View()
        UpscaleView.add_item(UpscaleBtn)

        async def UpscaleFunc(interaction):
            await interaction.response.send_message("Upscale requested...", ephemeral=True)
            Upscale = await UpscalerAi.UpscaleImg(ctx, prompt=prompt, imagename=fileNameInt)
            if Upscale:
                user['credits'] -= credit_usage[plan]
                users_collection.update_one({'_id': user_id}, {'$set': {'credits': user['credits']}})
                await ctx.reply(f"Used {credit_usage[plan]} credits. Remaining credits: {user['credits']} and here is what I imagined:", file=discord.File(UpscalerAi.temp_file_path, filename='generated_image.png'))
        UpscaleBtn.callback = UpscaleFunc

        async def VariationFunc(interaction):
            await interaction.response.send_message("Variation requested...")
            Variate = await VariationAi.Variation(ctx, prompt=prompt, imagename=fileNameInt)
            
            if Variate:
                user['credits'] -= credit_usage[plan]
                users_collection.update_one({'_id': user_id}, {'$set': {'credits': user['credits']}})
                await ctx.reply(f"Used {credit_usage[plan]} credits. Remaining credits: {user['credits']} and here is what I imagined:", file=discord.File(VariationAi.temp_file_path, filename='generated_image.png'), view=UpscaleView)

        VariationBtn.callback = VariationFunc
        


        user_id = str(ctx.author.id)
        user = users_collection.find_one({'_id': user_id})
        if user:
            plan = user['plan']
            credits = user['credits']

            official_server_id = 871643533646372954  # Replace with your official server's ID
            if plan == "ProPlus" or (ctx.guild and ctx.guild.id == official_server_id):
                credit_usage = {
                    'Free': 6,
                    'Pro': 3,
                    'ProPlus': 1,
                }

                if credits >= credit_usage[plan]:
                    # Check if any NSFW word is exactly present in the description
                    nsfw_word_found = any(word.lower() in map(str.lower, filtuh.filter_keywords) for word in prompt.split())

                    if nsfw_word_found:
                        await ctx.channel.send(f"{ctx.author.mention} no NSFW, bro. Chill.")
                        await ctx.message.delete()
                            
                        return False
                    else:
                        # NSFW check passed, continue with image generation
                        # Now start better NSFW Checker

                        
                        await ctx.reply(f"{ctx.author.mention} ok im imagining, mmm...", ephemeral=True)
                        # call image generation function using user prompt
                        image = await generate_image(ctx, description=prompt, fileNameInt=fileNameInt)
                            
                        if image:
                                    # Deduct credits after a successful response
                            user['credits'] -= credit_usage[plan]
                            users_collection.update_one({'_id': user_id}, {'$set': {'credits': user['credits']}})
                            
                            # Save the image to a temporary file
                            image_temp_file = io.BytesIO()
                            image.save(image_temp_file, format='PNG')
                            image_temp_file.seek(0)
                            # reply the image
                            if plan == "Free":
                                await ctx.reply(f"Used {credit_usage[plan]} credits. Remaining credits: {user['credits']} and here is what I imagined:", file=discord.File(image_temp_file, filename='generated_image.png'))
                                
                            elif plan == "Pro":
                                await ctx.reply(f"Used {credit_usage[plan]} credits. Remaining credits: {user['credits']} and here is what I imagined:", file=discord.File(image_temp_file, filename='generated_image.png'), view=ProView)
                                
                            elif plan == "ProPlus":
                                await ctx.reply(f"Used {credit_usage[plan]} credits. Remaining credits: {user['credits']} and here is what I imagined:", file=discord.File(image_temp_file, filename='generated_image.png'), view=ProPlusView)
                                

                            else:
                                await ctx.reply("smth happened and u cant get the image. type /register and try again ")
                        else:
                            await ctx.reply("You are not registered. type ```/register to register```")

                        
                
                else:
                    await ctx.reply("Insufficient credits.", ephemeral=True)
            else:
                UnAllowed_Private_embed = discord.Embed(title="You're not alllowd to use the bot in dm", description=f"```\nFree users are not allowed to use the bot in DM. You can Upgrade to ProPlus Plan to do so, by using /upgrade command in official ImaginationBawt server```", color=0xFF0000)
                await ctx.reply(embed=UnAllowed_Private_embed, ephemeral=True)

        else:
            await ctx.reply("You are not registered. type ```/register to register```")
        
    except Exception as e:
        await ctx.reply(f"An error occurred while generating the image: {str(e)}", ephemeral=True)


#command to check user Plan & Credits
@bot.hybrid_command(name="profile", description="shows ur credits and plan")
async def profile(ctx):
    
    try:
        # Create buttons
        UpgradeBtn = discord.ui.Button(label="Upgrade", style=discord.ButtonStyle.primary)

        # Define callback functions for each button
        async def callback1(interaction):
            await interaction.response.send_message("Check your DM", ephemeral=True)
            await interaction.user.send("Upgraded")

        # Add the callbacks to the buttons
        UpgradeBtn.callback = callback1

        # Create a view and add the buttons
        view = discord.ui.View()
        view.add_item(UpgradeBtn)


        user_id = str(ctx.author.id)
        user = users_collection.find_one({'_id': user_id})
        plan = user['plan']
        credits = user['credits']
        model = user['chosen_url']
        model_name = ['SDXL', 'Realistic', 'niji(Anime style)', "Hyper realism art"]
        chosed_model = model_name[model]
        if not plan == "ProPlus":
            free_embed = discord.Embed(title="Plan Information", description=f"Current plan: {plan} plan\nSelected model: {chosed_model}\nCredit: {credits}\nIf you're interested in Paid plans Click the button below to Upgrade.", color=0x1a75ff)
            await ctx.reply(embed=free_embed, view=view, ephemeral=True)
        else:
            ProPlus_embed = discord.Embed(title="Plan Information", description=f"Current plan: {plan} plan\nSelected model: {chosed_model}\ncredit: {credits}", color=0x5c00e6)
            await ctx.reply(embed=ProPlus_embed, ephemeral=True)

    except Exception as e:
        await ctx.reply(f"Cant check ur profile now, try again later: {e}")

@bot.hybrid_command(name="helpimagine", description="shows all commands")
async def helpimagine(ctx):

    # Create buttons
    button1 = discord.ui.Button(label="Upgrade", style=discord.ButtonStyle.primary)
    #button2 = discord.ui.Button(label="upscale", style=discord.ButtonStyle.secondar>

    # Define callback functions for each button
    async def callback1(interaction):
        await interaction.response.send_message("check your DM", ephemeral=True)


        await interaction.user.send("Button 1 clicked!")

    #async def callback2(interaction):
        #await interaction.response.send_message("Button 2 clicked!")

    # Add the callbacks to the buttons
    button1.callback = callback1
    #button2.callback = callback2

    # Create a view and add the buttons
    view = discord.ui.View()
    view.add_item(button1)
    #view.add_item(button2)
    # Create a rich embed for the help message
    embed = discord.Embed(
        title="Helps you imagine",
        description="Here are the available commands:",
        color=0x00ff00  # Set the color of the embed (optional)
    )

    # Add information about available commands
    embed.add_field(
        name="/register",
        value="Registers ur self to server, so u can use the bot",
        inline=False
    )
    embed.add_field(
        name="/imagine",
        value="Generates image based on your prompt",
        inline=False
    )

    embed.add_field(
        name="/profile",
        value="Check ur plan and left credit",
        inline=False
    )

    embed.add_field(
        name="/helpimagine",
        value="Shows you this <3",
        inline=True
    )


    # Send the help message with the embed
    await ctx.send(embed=embed, view=view)

@bot.hybrid_command(name="upgrade", description="shows all commands")
async def upgrade(ctx):

    # Create buttons
    button1 = discord.ui.Button(label="Upgrade", style=discord.ButtonStyle.primary)
    # Define callback functions for each button
    async def callback1(interaction):
        await interaction.response.send_message("check your DM", ephemeral=True)
        await interaction.user.send("Upgraded")


    # Add the callbacks to the buttons
    button1.callback = callback1
    # Create a view and add the buttons
    view = discord.ui.View()
    view.add_item(button1)

    await ctx.send("check your DM", ephemeral=True)
    await ctx.author.send("upgraded")

@bot.hybrid_command(name="settings", description="change the model/style of the image")
async def settings(ctx):

    user_id = str(ctx.author.id)
    user = users_collection.find_one({'_id': user_id})
    if user:
        plan = user['plan']
        credits = user['credits']
        chosen_url = user['chosen_url']
        
    # Define custom option labels and values
    options = [
        discord.SelectOption(label="SDXL", value=0),
        discord.SelectOption(label="400GB Lora", value=1),
        discord.SelectOption(label="niji(Anime style)", value=2),
        discord.SelectOption(label="Hyper realism art", value=3)
        ]

    # Create a select menu with the custom options
    select = discord.ui.Select(placeholder="Select an option", options=options)

    # Create a view and add the select menu
    view = discord.ui.View()
    view.add_item(select)

    # Send a message with the custom dropdown menu
    await ctx.send("Please select an option:", view=view, ephemeral=True)

    # Define a callback function to handle the selected option
    async def callback(interaction):
        selected_option = int(interaction.data['values'][0])
        user_id = str(interaction.user.id)
        model = user['chosen_url']
        model_name = ['SDXL', '400GB Lora', 'niji(Anime style)', 'Hyper realism art']
        users_collection.update_one({'_id': user_id}, {'$set': {'chosen_url': selected_option}})
        chosed_model = model_name[selected_option]
        await interaction.response.send_message(f"You selected {chosed_model}", ephemeral=True)
    # Assign the callback function to the select menu
    select.callback = callback


# Replace 'Bot_Token' with actual bot token
bot.run('MTE2MjI3MjYyMjk2NTQ0MDUyMw.Gx5_XB.UbiRUubedN_JDkd8VNDOOQwY8ZXO5r2_1GWfyY')
