class BOTException(Exception):
    pass


class AnimalNotFoundException(BOTException):
    def __init__(self, animal):
        self.animal = animal
    def __str__(self):
        return (f'Животное {self.animal} не найдено. Проверьте правильность '
                'написания или выберите одно из доступных животных '
                'командой /animals.')


class AnimalImageNotFoundException(BOTException):
    def __init__(self, animal):
        self.animal = animal
    def __str__(self):
        return f'Изображение животного {self.animal} не найдено.'


class InvalidCommandException(BOTException):
    def __init__(self, command):
        self.command = command
    def __str__(self):
        return (f'Команда {self.command} не распознана. Используйте /help '
                f'для списка доступных команд.')
