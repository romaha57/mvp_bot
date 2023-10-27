from bot.users.service import UserService


class UserKeyboard:
    def __init__(self):
        self.db = UserService()
