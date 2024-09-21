import docx
import os
import smtplib
from dotenv import load_dotenv
from extensions import AnimalNotFoundException
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

load_dotenv()

TOKEN = os.getenv('TOKEN')
ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID')
CONTACT_EMAIL = os.getenv('CONTACT_EMAIL')
EMAIL_SMTP_SERVER = os.getenv('EMAIL_SMTP_SERVER')
EMAIL_FROM = os.getenv('EMAIL_FROM')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')

ANIMAL_IMAGES = {
    'капибара': 'images/kapibara.jpeg',
    'медоед': 'images/medoed.jpeg',
    'альпака': 'images/alpaka.jpeg',
    'малая панда': 'images/panda.jpeg',
    'сурикат': 'images/surikat.jpeg',
    'выдра': 'images/vqdra.jpeg',
    'пингвин': 'images/pingvin.jpeg',
    'морж': 'images/morz.jpeg'
}

QUESTIONS = [
    {
        'question' : '1. Когда вы наиболее работоспособны?',
        'answers' : {
            'Днём' : ['сурикат', 'морж', 'альпака', 'капибара', 'пингвин'],
            'Ночью' : ['медоед', 'малая панда', 'выдра']
        }
    },
    {
        'question' : '2.Что для вас важнее?',
        'answers' : {
            'Семья' : ['сурикат', 'выдра', 'альпака', 'капибара', 'морж', 'пингвин'],
            'Карьера' : ['медоед', 'малая панда']
        }
    },
    {
        'question' : '3. Без чего вы не можете обойтись в питании?',
        'answers' : {
            'Без мяса' : ['сурикат', 'медоед'],
            'Без овощей': ['капибара', 'альпака', 'малая панда' ],
            'Без Морепродуктов': ['морж', 'выдра', 'пингвин' ]

        }
    },
    {
        'question': '4. Какой цвет вам больше нравится?',
        'answers': {
            'Чёрный': ['медоед', 'пингвин'],
            'Оранжевый': ['малая панда', 'сурикат'],
            'Коричневый': ['капибара', 'альпака', 'выдра', 'морж']
        }
    },
    {
        'question': '5. Куда бы вы хотели отправиться в путешествие?',
        'answers': {
            'Арктика': ['морж', 'пингвин'],
            'Европа': ['выдра', 'альпака'],
            'Азия': ['малая панда', 'медоед'],
            'Африка': ['сурикат', 'капибара']
        }
    },
    {
        'question': '6. Что вы хотите от жизни?',
        'answers': {
            'Оставаться здоровым и сильным': ['медоед', 'морж'],
            'Никогда не скучать': ['выдра', 'сурикат'],
            'Известность и популярность': ['альпака', 'малая панда'],
            'Познать себя и мир вокруг': ['капибара', 'пингвин']
        }
    },
    {
        'question': '7. Вы купили новый шкаф. Чтобы собрать его, я...',
        'answers': {
            'обращусь к специалисту': ['капибара', 'пингвин', 'альпака', 'морж'],
            'найду дома инструменты ': ['выдра', 'медоед', 'малая панда', 'сурикат']
        }
    },
    {
        'question': '8. Вы бы хотели уметь: ',
        'answers': {
            'дышать под водой и хорошо плавать': ['выдра', 'морж', 'пингвин'],
            'быстро бегать и хорошо прятаться': ['сурикат', 'медоед'],
            'быть любимцем всех': ['капибара', 'альпака', 'малая панда']
        }
    },
    {
        'question': '9. Какое качество вы хотели бы в себе развить?',
        'answers': {
            'Стрессоустойчивость': ['медоед', 'морж'],
            'Бескорыстие': ['капибара', 'альпака'],
            'Общительность ': ['выдра', 'сурикат'],
            'Сила воли ': ['малая панда', 'пингвин']
        }
    }
    ]


COMMANDS = {
    '/start': 'начинает работу бота',
    '/help': 'показывает доступные команды бота',
    '/quiz': 'запускает викторину',
    '/care': 'ссылка на программу опеки',
    '/animals': 'список животных, о которых могу рассказать интересные факты',
    '/contact': 'связаться с сотрудником зоопарка',
    '/feedback': 'оставить отзыв',
}


class UserData:
    def __init__(self, user_id):
        self.user_id = user_id
        self.current_question = 0
        self.quiz_complete = False
        self.reset()

    def score(self, animals):
        for animal in animals:
            self.scores[animal] += 1

    def get_winner(self):
        return max(self.scores, key=self.scores.get)

    def reset(self):
        self.current_question = 0
        self.scores = {'капибара': 0,
                       'медоед': 0,
                       'альпака': 0,
                       'малая панда': 0,
                       'сурикат': 0,
                       'выдра': 0,
                       'пингвин' : 0,
                       'морж' : 0,
                       }
        self.quiz_complete = False


def get_animal_facts(animal):
    facts = []
    doc = docx.Document('info/animal_facts.docx')
    found = False
    for paragraph in doc.paragraphs:
         if paragraph.text.lower() == animal.lower() + ':':
             found = True
             continue
         if found:
             if paragraph.text.strip() =='':
                break
             facts.append(paragraph.text)
    return facts


def validate_animal(animal, available_animals):
    if animal not in available_animals:
        raise AnimalNotFoundException(animal)


def get_facts_text(animal, facts):
    if facts:
        return '\n \n'.join(facts[:3])
    else:
        return f'К сожалению, я не нашел фактов о животном {animal}'


def send_animal_info(bot, chat_id, animal, image_path, facts):
    if image_path:
        with open(image_path, 'rb') as photo:
            bot.send_photo(chat_id, photo, caption=f'{animal}')

    if facts:
        facts_text = get_facts_text(animal, facts)
        bot.send_message(chat_id, f'Вот три интересных факта о животном {animal}:\n\n{facts_text}')
    else:
        raise AnimalNotFoundException


def start_text(first_name):
    return (f'Привет, {first_name}! \n \n'
'\n'
'Данный бот создан для популяризации программы опеки Московского Зоопарка.\
Мы придумали для Вас викторину, на тему "Какое твоё тотемное животное?" \
Чтобы пройти тест, напиши мне /quiz и я скажу тебе, какое именно твоё тотемное животное. \
Для того, чтобы узнать больше возможностей данного бота, напиши /help.')


def help_text():
    text = 'Доступные команды бота: ' + '\n'
    for key, value in COMMANDS.items():
        text += f'{key}: {value};\n'
    return text


def care_text():
    return ('Участие в программе «Клуб друзей зоопарка» — это помощь в содержании \
наших обитателей, а также ваш личный вклад в дело сохранения биоразнообразия Земли \
и развитие нашего зоопарка. Традиция опекать животных в Московском зоопарке возникло \
с момента его создания в 1864г.'
"\n"
    'Опекать – значит помогать любимым животным. Взять под опеку можно разных \
обитателей зоопарка, например, слона, льва, суриката или фламинго. Почётный статус \
опекуна позволяет круглый год навещать подопечного, быть в курсе событий его жизни и самочувствия.'
"\n"
'Чтобы познакомиться получше с нашей программой опеки, \
предлагаю посетить нашу домашнюю страничку: https://moscowzoo.ru/about/guardianship')


def contact_text():
    return (f'Если у вас есть вопросы или предложения, вы можете связаться с нами: \n \n'
            'Email: zoopark@culture.mos.ru \n'
            'Телефон: +7 (499) 252-29-51 \n \n'
            'Больше контактов на страничке: \n'
            'https://moscowzoo.ru/contacts')


def send_email(subject, body, to_email):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_FROM
    msg['To'] = to_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP(EMAIL_SMTP_SERVER, 587)
        server.starttls()
        server.login(EMAIL_FROM, EMAIL_PASSWORD)
        text = msg.as_string()
        server.sendmail(EMAIL_FROM, to_email, text)
        server.quit()
        print('Email sent successfully')
    except Exception as e:
        print(f'Failed to send email: {e}')


def generate_result_text(username, user_email, winner):
    return (f'Пользователь {username} прошёл викторину.'
            f'Его тотемное животное: {winner}.'
            f'Контактный э-майл: {user_email}')

