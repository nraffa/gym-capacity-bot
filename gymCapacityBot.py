from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import schedule
import telegram
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
)
import os
from dotenv import load_dotenv

# Define the list of gyms
GYMS = {
    "Laim": "https://www.fit-star.de/fitnessstudio/muenchen-laim",
    "Pasing": "https://www.fit-star.de/fitnessstudio/muenchen-pasing",
    "Neuhausen": "https://www.fit-star.de/fitnessstudio/muenchen-neuhausen/",
}
load_dotenv()

TOKEN = str(os.getenv("TOKEN"))
PORT = int(os.environ.get("PORT", 5000))
WEBHOOK_URL = "https://gym-capacity-bot.netlify.app/.netlify/functions/update"


def scrapeCapacity(URL):
    # create a new ChromeOptions object
    options = Options()

    # add the headless option to the ChromeOptions object
    options.add_argument("--headless")

    # create a new Chrome browser instance with the headless option
    driver = webdriver.Chrome(options=options)

    # navigate to the website
    driver.get(URL)

    # find the element with the id "fs-livedata-percentage"
    element = driver.find_element("id", "fs-livedata-percentage")

    # extract the text from the element
    percentage = element.text

    # print the percentage
    print(percentage)

    # close the browser
    driver.quit()

    return percentage


async def start(update: Update, context):
    # Create a list of gym options
    options = [f"{i+1}. {gym}" for i, gym in enumerate(GYMS.keys())]

    # Create a list of lists with the gym options for the custom keyboard
    keyboard = [[option] for option in options]

    # Create a custom keyboard with the gym options
    reply_markup = telegram.ReplyKeyboardMarkup(keyboard)

    # Send a message to the user with the gym options and the custom keyboard
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Which gym do you want to check?",
        reply_markup=reply_markup,
    )


async def selectGym(update: Update, context):
    # Get the selected gym option from the user message
    option = int(update.message.text.split(".")[0])

    # Get the gym URL from the selected option
    gym_url = list(GYMS.values())[option - 1]

    # Scrape the live capacity for the selected gym
    capacity = scrapeCapacity(gym_url)

    # Send a message to the user with the live capacity
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"The live capacity for {list(GYMS.keys())[option-1]} is {capacity}",
    )


def scheduleCapacityCheck():
    # Define the frequency and time for the capacity check
    frequency = "weekday"
    time = "06:00"

    # Schedule the capacity check using the `schedule` library
    schedule.every().monday.to_friday().at(time).do(sendCapacity)

    # Start the schedule loop
    while True:
        schedule.run_pending()
        time.sleep(1)


async def sendCapacity(update: Update, context):
    # Scrape the live capacity for each gym
    capacities = [scrapeCapacity(url) for url in GYMS.values()]

    # Create a message with the live capacities
    message = "Live capacities:\n" + "\n".join(
        [f"{gym}: {capacity}" for gym, capacity in zip(GYMS.keys(), capacities)]
    )

    # Send the message to the user
    await context.bot.send_message(chat_id=update.effective_chat.id, text=message)


if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    start_handler = CommandHandler("start", start)
    app.add_handler(start_handler)

    select_gym_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, selectGym)
    app.add_handler(select_gym_handler)

    app.run_webhook(
        listen="0.0.0.0", port=PORT, url_path=TOKEN, webhook_url=WEBHOOK_URL
    )

    scheduleCapacityCheck()
