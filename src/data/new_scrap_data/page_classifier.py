import re
from arqtty_scrapper.page_types import Page_types


class Classifier:
    def __init__(self, page_str):
        self.page = page_str

    def _is_404(self):
        marker1 = 'Ой, ой, страничка потерялась'
        marker2 = 'Спокойно! Логи записаны. Все будет исправлено.'

        return re.search(marker1, self.page) and re.search(marker2, self.page)

    def _is_user_blocked(self):
        marker1 = "Пользователь '[\w\W]*' заблокирован"

        return re.search(marker1, self.page)

    def _is_alive(self):
        marker1 = 'Лента действий'

        return re.search(marker1, self.page)

    def get_type(self):
        if self._is_404():
            return Page_types.E_404
        elif self._is_user_blocked():
            return Page_types.USER_BANNED
        elif self._is_alive():
            return Page_types.CORRECT
        else:
            return Page_types.UNDEFINED
