import os
import io
import warnings
import discord
from discord.ext import commands
from PIL import Image
from stability_sdk import client
import stability_sdk.interfaces.gooseai.generation.generation_pb2 as generation
import random
import asyncio

# Our Host URL should not be prepended with "https" nor should it have a trailing slash.
os.environ['STABILITY_HOST'] = 'grpc.stability.ai:443'

os.environ['STABILITY_KEY'] = 'sk-vSrydEGsrxufPqrq8r4eGwE5lS38TrrefZVKOhApN4txO2D6'

random_integer = random.randint(1, 1000000000)
file_extension = ".png"# Combine the random string with the file extension to create a unique filename
temp_file_path = f"{random_integer}{file_extension}"

async def Variation(ctx, prompt = "realistic", imagename = 6969):

    await ctx.reply("Variation starting...")
    actual_path = f"{imagename}.png"
    img = Image.open(actual_path)
    img.save((actual_path))
    # Set up our connection to the API.
    stability_api = client.StabilityInference(
        key=os.environ['STABILITY_KEY'], # API Key reference.
        verbose=True, # Print debug messages.
        engine="stable-diffusion-xl-1024-v1-0", # Set the engine to use for generation.
        # Check out the following link for a list of available engines: https://platform.stability.ai/docs/features/api-parameters#engine
    )
    # Set up our initial generation parameters.
    answers = stability_api.generate(
        prompt=prompt,
        init_image=img, # Assign our previously generated img as our Initial Image for transformation.
        start_schedule=0.65, # Set the strength of our prompt in relation to our initial image.
        steps=30, # Amount of inference steps performed on image generation. Defaults to 30.
        cfg_scale=7.0, # Influences how strongly your generation is guided to match your prompt. Setting this value higher increases the strength in which it tries to match your prompt. Defaults to 7.0 if not specified.
        width=1024, # Generation width, if not included defaults to 512 or 1024 depending on the engine.
        height=1024, # Generation height, if not included defaults to 512 or 1024 depending on the engine.
        samples=4, # Number of images to generate, defaults to 1 if not included.
        sampler=generation.SAMPLER_K_DPMPP_2M # Choose which sampler we want to denoise our generation with.
                                                     # Defaults to k_dpmpp_2m if not specified. Clip Guidance only supports ancestral samplers.
                                                     # (Available Samplers: ddim, plms, k_euler, k_euler_ancestral, k_heun, k_dpm_2, k_dpm_2_ancestral, k_dpmpp_2s_ancestral, k_lms, k_dpmpp_2m, k_dpmpp_sde)
    )
    # Set up our warning to print to the console if the adult content classifier is tripped. If adult content classifier is not tripped, save generated image. 
    for resp in answers:
        for artifact in resp.artifacts:
            if artifact.finish_reason == generation.FILTER:
                warnings.warn(
                    "Your request activated the API's safety filters and could not be processed."
                    "Please modify the prompt and try again.")
            if artifact.type == generation.ARTIFACT_IMAGE:
                global Variate
                Variate = Image.open(io.BytesIO(artifact.binary)) # Set our resulting initial image generations as 'img2' to avoid overwriting our previous 'img' generation.
                Variate.save(temp_file_path) # Save our generated images with their seed number as the filename.
                return True
            
#asyncio.run(Variation(imagename=54579075))
