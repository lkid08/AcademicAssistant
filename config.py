from telegram import InlineKeyboardMarkup, InlineKeyboardButton
import logging


# Variables
TASK = 'zero-shot-classification'
MODEL = 'MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7'
CANDIDATE_LABELS = ['literature', 'technology', 'history', 'linguistics', 'physics', 'biology', 'politics', 'law']
TOKEN=''


# Keyboards + CLF texts
clf_config_kb = [
        [InlineKeyboardButton('Modify the list', callback_data='modify')],
        [InlineKeyboardButton('Back to menu', callback_data='menu')]
    ]
CLF_MARKUP = InlineKeyboardMarkup(clf_config_kb)
CLF_TXT1 = 'At the moment, the classifier is using these classes:\n\n'
CLF_TXT2 = '\n\nYou can modify this list or return to the menu'


# logger
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logging.getLogger('httpx').setLevel(logging.WARNING)
logger = logging.getLogger(__name__)