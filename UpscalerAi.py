import io
import os
from PIL import Image
import warnings
from PIL import Image
from stability_sdk import client
import stability_sdk.interfaces.gooseai.generation.generation_pb2 as generation
import random
import asyncio
import discord
import pymongo

os.environ['STABILITY_HOST'] = 'grpc.stability.ai:443'
os.environ['STABILITY_KEY'] = 'sk-ikEGsMXlEyCh6JmEFVbKY3CUZ7AcUd8qGw4PrLiRwv9zeuaZ'


async def UpscaleImg(ctx, prompt = "realistic", imagename = "path"):
    try:
        actual_path = str(f"{imagename}.png")
        global promt_txt
        promt_txt = prompt
        user_id = str(ctx.author.id)
        
        await ctx.send("Upscale requested...", ephemeral=True)

        # Set up our connection to the API.
        stability_api = client.StabilityInference(
            key="sk-vSrydEGsrxufPqrq8r4eGwE5lS38TrrefZVKOhApN4txO2D6", # API Key reference.
            verbose=False, # Print debug messages.
            engine="stable-diffusion-xl-1024-v1-0", # Set the engine to use for generation.
            # Check out the following link for a list of available engines: https://platform.stability.ai/docs/features/api-parameters#engine
        )
        global image
        global temp_file_path
        image = Image.open(actual_path)  # Replace "image.jpg" with the path to your image file.
        random_integer = random.randint(1, 1000000000)
        # Define the file extension
        file_extension = ".png"
        # Combine the random string with the file extension to create a unique filename
        temp_file_path = f"{random_integer}{file_extension}"
        # Set up our initial generation parameters.
        answers = stability_api.generate(
            
            prompt=prompt,
            init_image=image, # Assign our previously generated img as our Initial Image for transformation.
            start_schedule=0.65, # Set the strength of our prompt in relation to our initial image.
            steps=50, # Amount of inference steps performed on image generation. Defaults to 30.
            cfg_scale=8.0, # Influences how strongly your generation is guided to match your prompt. Setting this value higher increases the strength in which it tries to match your prompt. Defaults to 7.0 if not specified.
            width=1024, # Generation width, if not included defaults to 512 or 1024 depending on the engine.
            height=1024, # Generation height, if not included defaults to 512 or 1024 depending on the engine.
            samples=4, # Number of images to generate, defaults to 1 if not included.
            sampler=generation.SAMPLER_K_DPMPP_2M # Choose which sampler we want to denoise our generation with.
                                                         # Defaults to k_dpmpp_2m if not specified. Clip Guidance only supports ancestral samplers.
                                                         # (Available Samplers: ddim, plms, k_euler, k_euler_ancestral, k_heun, k_dpm_2, k_dpm_2_ancestral, k_dpmpp_2s_ancestral, k_lms, k_dpmpp_2m, k_dpmpp_sde)
)       

        

        # Set up our warning to print to the console if the adult content classifier is tripped.
        # If adult content classifier is not tripped, save generated image.
        for resp in answers:
            for artifact in resp.artifacts:
                if artifact.finish_reason == generation.FILTER:
                    warnings.warn(
                        "Your request activated the API's safety filters and could not be processed."
                        "Please modify the prompt and try again.")
                if artifact.type == generation.ARTIFACT_IMAGE:
                    # Save the generated image with the unique filename
                    image = Image.open(io.BytesIO(artifact.binary))
                    image.save(temp_file_path)
                    # Set a timer to delete the temporary file after 5 minutes
                    #asyncio.get_event_loop().call_later(300, os.remove, temp_file_path)
                    #await ctx.reply("here is what I imagined:", file=discord.File(temp_file_path, filename='generated_image.png'))
                    return True
                
    except Exception as e:
        await ctx.reply(e)
