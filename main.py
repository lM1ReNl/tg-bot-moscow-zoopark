import telebot
from telebot import types
from config import (TOKEN, QUESTIONS, COMMANDS, ANIMAL_IMAGES,
                    ADMIN_CHAT_ID, UserData, get_animal_facts,
                    validate_animal, send_animal_info, start_text,
                    help_text, care_text, contact_text, send_email,
                    generate_result_text, CONTACT_EMAIL)
from extensions import (BOTException, AnimalNotFoundException,
                        AnimalImageNotFoundException, InvalidCommandException)


bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, start_text(message.chat.first_name))


@bot.message_handler(commands=['help'])
def help_message(message: telebot.types.Message):
    bot.send_message(message.chat.id, help_text())


@bot.message_handler(commands=['care'])
def info(message: telebot.types.Message):
    bot.reply_to(message, care_text())


@bot.message_handler(commands=['contact'])
def contact(message: telebot.types.Message):
    bot.reply_to(message, contact_text())


@bot.message_handler(commands=['feedback'])
def feedback(message: telebot.types.Message):
    feedback_message = bot.reply_to(message, 'Пожалуйста, напишите Ваш отзыв: ')
    bot.register_next_step_handler(feedback_message, process_feedback)


def process_feedback(message: telebot.types.Message):
    feedback = message.text
    bot.send_message(ADMIN_CHAT_ID, f'Ваш отзыв: {feedback}')
    bot.reply_to(message, 'Спасибо за Ваш отзыв!')


quiz_data = {}

@bot.message_handler(commands=['quiz'])
def start_quiz(message):
    user_id = message.from_user.id

    if user_id not in quiz_data:
        quiz_data[user_id] = UserData(user_id)
    else:
        quiz_data[user_id].reset()

    send_question(user_id)

def send_question(user_id):
    user = quiz_data[user_id]
    question_index = user.current_question

    if question_index < len(QUESTIONS):
        question_data = QUESTIONS[question_index]
        question_text = question_data['question']
        answers = question_data['answers']

        markup = types.InlineKeyboardMarkup()
        for answer in answers.keys():
            markup.add(types.InlineKeyboardButton(text=answer, callback_data=f'{question_index}:{answer}'))

        bot.send_message(user_id, question_text, reply_markup=markup)
    else:
        determine_winner(user_id)


@bot.callback_query_handler(func=lambda call: call.data == 'restart')
def restart_quiz(call):
    user_id = call.from_user.id
    quiz_data[user_id].reset()
    start_quiz(call)


@bot.callback_query_handler(func=lambda call: True)
def generic_callback_handler(call):
    if call.data in ['send_email', 'contact_info']:
        handle_contact_option(call)
    else:
        handle_answer(call)


@bot.callback_query_handler(func=lambda call: True)
def handle_answer(call):
    user_id = call.from_user.id
    user = quiz_data[user_id]
    question_index = user.current_question

    if user.quiz_complete:
        return

    if question_index < len(QUESTIONS):
        question_data = QUESTIONS[question_index]
        answers = question_data['answers']

        _, selected_answer = call.data.split(':')
        selected_answer = next((key for key in answers if key.startswith(selected_answer)))

        if selected_answer:
            user.score(answers[selected_answer])

        user.current_question += 1

        if user.current_question < len(QUESTIONS):
            send_question(user_id)
        else:
            determine_winner(user_id)
    else:
        determine_winner(user_id)


def determine_winner(user_id):
    user = quiz_data[user_id]
    if user.quiz_complete:
        return

    user.quiz_complete = True
    winner = user.get_winner()
    image_path = ANIMAL_IMAGES.get(winner)
    facts = get_animal_facts(winner)

    bot.send_message(user_id, 'Ваше тотемное животное: ')
    send_animal_info(bot, user_id, winner, image_path, facts)

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text='Попробовать ещё раз', callback_data='restart'))

    bot.send_message(user_id, 'Если хочешь узнать интересные факты о других животных, \
то напиши /animals и получишь полный список животных', reply_markup=markup)

    bot.send_message(ADMIN_CHAT_ID, f"Пользователь {user_id} прошел викторину. "
                                    f"Его тотемное животное: {winner}")

    social_markup = types.InlineKeyboardMarkup()
    social_markup.add(types.InlineKeyboardButton(text='Поделиться в соцсетях',
                                                 url=f'https://t.me/share/url?url=Я%20выяснил(а)%20что%20моё%20тотемное%20животное%20{winner}!%20Пройди%20тест%20и%20ты: t.me/MoscowZooBot'))
    bot.send_message(user_id, 'Поделитесь вашим результатом в соцсетях:', reply_markup=social_markup)

    contact_markup = types.InlineKeyboardMarkup()
    contact_markup.add(types.InlineKeyboardButton(text='Отправить результат сотруднику', callback_data='send_email'))
    contact_markup.add(types.InlineKeyboardButton(text='Свяжусь сам', callback_data='contact_info'))
    bot.send_message(user_id, 'Выберите способ связи: ', reply_markup=contact_markup)

    bot.send_message(user_id, 'Не забудьте ознакомиться с нашей программой опеки /care ')


def process_email(message: telebot.types.Message):
    print('Processing email...')
    user_email = message.text
    user_id = message.from_user.id
    print(f'User email: {user_email}')
    user = quiz_data.get(user_id)

    if user:
        winner = user.get_winner()
        result_text = generate_result_text(message.chat.username, user_email, winner)
        send_email('Результат прохождения викторины', result_text, CONTACT_EMAIL)
        bot.reply_to(message, 'Ваш результат викторины был отправлен сотруднику на email.\n \n'
                              'Свяжемся с Вами в течение трёх рабочих дней.')
    else:
        bot.reply_to(message, 'Произошла ошибка. Пожалуйста, пройдите викторину заново.')


@bot.callback_query_handler(func=lambda call: call.data in ['send_email', 'contact_info'])
def handle_contact_option(call):
    if call.data == 'send_email':
        msg = bot.send_message(call.message.chat.id, 'Пожалуйста, введите ваш email: ')
        bot.register_next_step_handler(msg, process_email)
    elif call.data == 'contact_info':
        bot.send_message(call.message.chat.id, contact_text())


@bot.message_handler(commands=['animals'])
def animals_list(message):
    animals = '\n'.join(ANIMAL_IMAGES.keys())
    text = ('Чтобы узнать интересные факты об интересуюшем тебя животном, просто напиши мне его название!')
    bot.send_message(message.chat.id, f'Доступные животные:\n \n{animals} \n \n {text}')


@bot.message_handler(content_types=['text'])
def handle_text(message: telebot.types.Message):
    animal = message.text.lower()
    try:
        if message.text.startswith('/'):
            command = message.text.split()[0]
            if command not in COMMANDS:
                raise InvalidCommandException(command)

        validate_animal(animal, ANIMAL_IMAGES)
        facts = get_animal_facts(animal)
        image_path = ANIMAL_IMAGES.get(animal)

        if not image_path:
            raise AnimalImageNotFoundException(animal)

        send_animal_info(bot, message.chat.id, animal, image_path, facts)

    except AnimalNotFoundException as e:
        bot.reply_to(message, str(e))
    except InvalidCommandException as e:
        bot.reply_to(message, e)
    except BOTException as e:
        bot.reply_to(message, e)


bot.polling(none_stop=True)