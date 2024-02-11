from telegram import (
    Update, 
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder, 
    ContextTypes, 
    CommandHandler, 
    filters, 
    MessageHandler, 
    CallbackQueryHandler, 
    ConversationHandler
)

from classes import *
from config import *

# states
NAME, EMAIL, MENU, CHOOSING, TEXT, CLF_CONFIG, MODIFY, AUTHOR, AUTHOR_TEXT, MY_TEXTS = range(10)

# classifier initialization 
classifier = ClassifierSingleton()

# dicts for class storage
users = {}
articles = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    username = update.effective_user.first_name
    if user_id not in users:
        users[user_id] = User(username=username, uid=user_id)

    logger.info(f"User {users[user_id].username} launched the bot")

    await update.message.reply_text(
        'Welcome! I am your Academic Assistant!\n\n'
        'Before you bgein working,\n'
        'please identify yourself\n\n'
        'Input your name:\n'
    )

    return NAME


async def change_name(update: Update, context:ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    await query.message.reply_text(
        text='Input your name:'
    )
    
    return NAME


async def name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    users[user_id].name = update.message.text

    logger.info(f"Name of user {users[user_id].username}: {users[user_id].name}")
    
    await update.message.reply_text(
        text='Input your email:'
    )
    
    return EMAIL


async def email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    users[user_id].email = update.message.text

    logger.info(f"Email of user {users[user_id].username}: {users[user_id].email}")
    
    email_kb = [
        [InlineKeyboardButton('Accept', callback_data='menu')],
        [InlineKeyboardButton('Change info', callback_data='change_name')]
        ]
    email_markup = InlineKeyboardMarkup(email_kb)

    await update.message.reply_text(
        'Please check your information below\n'
        'If it is not correct, you can change it\n\n'
        f'Name: {users[user_id].name}\n'
        f'Email: {users[user_id].email}',
        reply_markup=email_markup
    )
    
    return MENU


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    logger.info(f"User {users[user_id].username} disconnected from the bot.")
    await update.message.reply_text(
        'The connection was interrupted.\n'
        'Please restart the Assistant'
    )

    return ConversationHandler.END
    

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    logger.info(f"Information of user {users[user_id].username} is updated: |{users[user_id].name}, {users[user_id].email}|")

    menu_kb = [
        ['Add article', 'My articles'],
        ['Settings', 'Help']
        ]
    reply_markup=ReplyKeyboardMarkup(menu_kb, one_time_keyboard=True, resize_keyboard=True)

    await query.message.reply_text(
            text=f'Welcome to the main menu!\n'
            'Choose one of the options below\n\n'
            'If you need help, press "Help"',
            reply_markup=reply_markup
            )
    
    return CHOOSING


async def clf_config(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        text=CLF_TXT1 + classifier.get_candidate_labels() + CLF_TXT2,
        reply_markup=CLF_MARKUP

    )

    return CLF_CONFIG


async def modify(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    await query.message.reply_text(
        text='The new class name must be one word\n'
        'describing a theme or subject matter\n\n'
        'To add a new class\n'
        'please input it in the following format:\n\n'
        '+history\n\n'
        'To remove a class from the list\n'
        'please input it in the following format:\n\n'
        '-culture'
    )

    return MODIFY


async def handle_modifications(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if '+' in (text := update.message.text):
        classifier.add_candidate_label((text.replace('+', '')).strip())
        await update.message.reply_text(
            text=CLF_TXT1 + classifier.get_candidate_labels() + CLF_TXT2,
            reply_markup=CLF_MARKUP
            )

    elif '-' in (text := update.message.text):
        classifier.remove_candidate_label((text.replace('-', '')).strip())
        await update.message.reply_text(
            text=CLF_TXT1 + classifier.get_candidate_labels() + CLF_TXT2,
            reply_markup=CLF_MARKUP
            )

    else:
        await update.message.reply_text(
            text=f'{CLF_TXT1} + {classifier.get_candidate_labels()} + {CLF_TXT2}'
            '-----|ERROR|-----\n\n'
            'Please, input the class name according to the rules',
            reply_markup=CLF_MARKUP
            )
    
    user_id = update.effective_user.id
    logger.info(f"User {users[user_id].username} changed the list of classes")

    return CLF_CONFIG
    

async def classify(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        text='Adding new article\n\n'
        "Input the article's text:"
    )

    return TEXT


async def inline_classify(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    await query.message.reply_text(
        text='Adding new article\n\n'
        "Input the article's text:"
    )

    return TEXT


async def process(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    
    wait_msg = await update.message.reply_text(
        text='Classifying article\n\n'
        'Please wait...'
    )

    classes = classifier.classify_text(text)
    table = classifier.pretty_table(classes)

    user_id = update.effective_user.id
    if user_id not in articles:
        articles[user_id] = []

    new_article = Article(text=text, category=classes[0][0])
    articles[user_id].append(new_article)

    process_kb = [
        [InlineKeyboardButton('Add author of article', callback_data='author')]
        ]
    process_markup=InlineKeyboardMarkup(process_kb)

    await wait_msg.edit_text(
        text='Classification result:\n\n'
        f'{table}',
        reply_markup=process_markup
    )

    logger.info(f"User {users[user_id].username} classified a new article")

    return AUTHOR


async def author(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    await query.message.reply_text(
        text="Add the author's name\n"
    )

    return AUTHOR_TEXT


async def add_author(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    author = update.message.text
    articles[user_id][-1].author = author

    add_author_kb = [
        [InlineKeyboardButton("Change author's name", callback_data='author')],
        [InlineKeyboardButton('Accept', callback_data='menu')]
    ]
    add_author_markup = InlineKeyboardMarkup(add_author_kb)

    await update.message.reply_text(
        text="Check author's name:\n\n"
        f"Name: {articles[user_id][-1].author}",
        reply_markup=add_author_markup
        )
    
    logger.info(f"User {users[user_id].username} added an article's author")

    return AUTHOR


async def my_texts(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    my_texts_kb = [
        [InlineKeyboardButton('Add article', callback_data='inline_classify')],
        [InlineKeyboardButton('Back to menu', callback_data='menu')]
        ]
    my_texts_markup=InlineKeyboardMarkup(my_texts_kb)
    
    user_id = update.effective_user.id
    try:
        user_history = articles[user_id]
        response = 'Your texts:\n\n'
        for i, article in enumerate(user_history):
            response += f'Article number {i+1}: {article.category}\n- author: {article.author}\n- content: {"".join(article.text[:60])}...\n- time and date: {article.pretty_creation_time()}\n\n\n'
        
        await update.message.reply_text(
            text=response,
            reply_markup=my_texts_markup
        )

    except:
        await update.message.reply_text(
            text='Your texts:\n\n'
            'Currently you have no texts.\n'
            'Please classify an article first.',
            reply_markup=my_texts_markup
        )


    return MY_TEXTS


async def help_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    return_kb = [[InlineKeyboardButton('Back to menu', callback_data='menu')]]
    return_markup=InlineKeyboardMarkup(return_kb)

    await update.message.reply_text(
        text='The Academic Assistant is made for classifying articles\n'
        'To classify an article press\n\n'
        '"Add article"\n\n'
        'And follow the instructions\n\n\n'
        'To view your classified articles press\n\n'
        '"My articles"\n\n',
        reply_markup=return_markup
    )

    return MENU


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text( 
        text='I do not understand this command...\n'
        'If you need help, press "Back to menu" and "Help"'
        'If you have not registered yet - write /start'
        )


if __name__ == '__main__':
    application = ApplicationBuilder().token(TOKEN).build()
    
    start_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, name)],

            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, email)],

            MENU: [
                CallbackQueryHandler(menu, pattern="menu"),
                CallbackQueryHandler(change_name, pattern="change_name")
                ],

            CHOOSING: [
                MessageHandler(filters.Regex("^Add article$"), classify),
                MessageHandler(filters.Regex("^My articles$"), my_texts),
                MessageHandler(filters.Regex("^Settings$"), clf_config),
                MessageHandler(filters.Regex("^Help$"), help_list)
            ],

            CLF_CONFIG: [
                CallbackQueryHandler(modify, pattern="modify"),
                CallbackQueryHandler(menu, pattern="menu")
            ],

            MODIFY: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_modifications)],

            TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, process)],

            AUTHOR: [
                CallbackQueryHandler(author, pattern="author"),
                CallbackQueryHandler(menu, pattern="menu")
                ],

            AUTHOR_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_author)],

            MY_TEXTS: [
                CallbackQueryHandler(menu, pattern="menu"),
                CallbackQueryHandler(inline_classify, pattern="inline_classify")
                ]

        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    application.add_handler(start_handler)

    unknown_handler = MessageHandler(filters.COMMAND, unknown)
    application.add_handler(unknown_handler)

    application.run_polling()