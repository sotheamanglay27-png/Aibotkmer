import os
import time
import telebot
import replicate

# បញ្ចូល Token របស់អ្នកនៅទីនេះ
BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
REPLICATE_API_TOKEN = "YOUR_REPLICATE_API_TOKEN"

os.environ["REPLICATE_API_TOKEN"] = REPLICATE_API_TOKEN
bot = telebot.TeleBot(BOT_TOKEN)

# เก็บข้อมูลชั่วคราวสำหรับผู้ใช้แต่ละคน
user_data = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "សួស្តី! សូមផ្ញើ **រូបថតមុខ** របស់អ្នកមកก่อน រួចค่อยផ្ញើ **វីដេអូ** តាមหลัง ដើម្បីធ្វើ Face Swap។")

# ទទួលយករូបថតមុខ (Source Image)
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id = message.from_user.id
    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    
    # យករូបថតរក្សាទុកជាไฟล์ชั่วคราว
    image_path = f"temp_{user_id}.jpg"
    with open(image_path, 'wb') as new_file:
        new_file.write(downloaded_file)
        
    user_data[user_id] = {"image": image_path}
    bot.reply_to(message, "ទទួលបានរូបថតមុខហើយ! ឥឡូវนี้សូមផ្ញើ **វីដេអូ** មកបន្តទៀត។")

# ទទួលយកវីដេអូ និងចាប់ផ្តើមทำ Face Swap
@bot.message_handler(content_types=['video'])
def handle_video(message):
    user_id = message.from_user.id
    
    if user_id not in user_data or "image" not in user_data[user_id]:
        bot.reply_to(message, "សូមផ្ញើ **រូបថតមុខ** របស់អ្នកមកមុនសិន ទើបផ្ញើវីដេអូតាមหลัง!");
        return
        
    bot.reply_to(message, "กำลังរៀបចំវីដេអូ... AI កំពុងដំណើរការ Face Swap សូមរង់ចាំបន្តិច (ប្រហែល ១ ទៅ ២ នាទី)!")
    
    try:
        # ទាញយកវីដេអូ
        file_info = bot.get_file(message.video.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        video_path = f"temp_{user_id}.mp4"
        with open(video_path, 'wb') as new_file:
            new_file.write(downloaded_file)
            
        image_path = user_data[user_id]["image"]
        
        # ហៅប្រើប្រាស់ AI Model ពី Replicate សម្រាប់ Face Swap
        # (ឧទាហរណ៍ប្រើប្រាស់ Model ជំនាញខាង Video Face Swap)
        output = replicate.run(
            "cuuupid/multiface-swap:...", # ឬ Model AI ផ្សេងទៀតដែលรองรับ
            input={
                "target_video": open(video_path, "rb"),
                "source_image": open(image_path, "rb")
            }
        )
        
        # ផ្ញើវីដេអូដែលដូររួចត្រឡប់ទៅ Telegram វិញ
        bot.send_video(message.chat.id, output)
        
        # លុបไฟล์ชั่วคราวចេញពី Server
        os.remove(video_path)
        os.remove(image_path)
        del user_data[user_id]
        
    except Exception as e:
        bot.reply_to(message, f"មានបញ្តុកើតឡើង៖ {str(e)}")

# ចាប់ផ្តើម Bot
print("Bot កំពុងដំណើរការ...")
bot.polling()
