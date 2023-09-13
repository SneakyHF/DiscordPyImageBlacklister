import discord
from discord.ext import commands
import cv2
import numpy as np
import mysql.connector
from skimage.metrics import structural_similarity as compare_ssim

intents = discord.Intents.all()

class ImageBot(commands.Bot):
    def __init__(self, command_prefix, token, verbose_mode=True):
        super().__init__(command_prefix, intents=intents)
        self.token = token
        self.verbose_mode = verbose_mode

    async def on_ready(self):
        if self.verbose_mode:
            print(f'Logged in as {self.user.name}')

    async def on_message(self, message):
        if message.author == self.user:
            return

        for attachment in message.attachments:
            if self.is_image(attachment):
                if self.verbose_mode:
                    print(f"Received an image attachment from {message.author}")

                image_bytes = await attachment.read()
                image_np = np.frombuffer(image_bytes, np.uint8)
                image = cv2.imdecode(image_np, cv2.IMREAD_COLOR)

                if self.compare_images(image):
                    await message.reply("Your message with an unauthorized image has been deleted.")
                    await message.delete()
                    if self.verbose_mode:
                        print(f"Deleted a message from {message.author} with an unauthorized image.")
                else:
                    if self.verbose_mode:
                        print(f"Message from {message.author} contains an image but is not unauthorized.")

        await self.process_commands(message)

    def is_image(self, attachment):
        return attachment.content_type.startswith('image')

    def compare_images(self, uploaded_image):
        try:
            threshold = 0.7

            self.cursor.execute("SELECT image_data FROM images")
            for (db_image_data,) in self.cursor:
                db_image = cv2.imdecode(np.frombuffer(db_image_data, np.uint8), cv2.IMREAD_COLOR)

                uploaded_image_resized = cv2.resize(uploaded_image, (db_image.shape[1], db_image.shape[0]))

                db_image = cv2.cvtColor(db_image, cv2.COLOR_BGR2GRAY)
                uploaded_image_resized = cv2.cvtColor(uploaded_image_resized, cv2.COLOR_BGR2GRAY)

                ssim = compare_ssim(uploaded_image_resized, db_image)

                if ssim >= threshold:
                    return True

            return False
        except Exception as e:
            if self.verbose_mode:
                print(f"Error comparing images: {e}")
            return False

    def run_bot(self):
        self.run(self.token)

if __name__ == '__main__':
    TOKEN = 'TOKEN'
    verbose_mode = True

    try:
        bot = ImageBot(command_prefix='!', token=TOKEN, verbose_mode=verbose_mode)

        if bot.verbose_mode:
            print("Attempting to establish a database connection...")

        bot.db = mysql.connector.connect(
            host='',
            user='',
            password='',
            database='' #SET DB INFO
        )
        bot.cursor = bot.db.cursor()

        if bot.verbose_mode:
            print("Database connection established successfully.")

        bot.run_bot()
    except Exception as e:
        if verbose_mode:
            print(f"An error occurred while setting up the bot: {e}")
