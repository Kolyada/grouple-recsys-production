from .div import Div
from .a import A


class Row:
    def __init__(self, etree_elem):
        self.e = etree_elem
        self.etree_name_a = self.e.getchildren()[0]
        self.name_a = A(self.etree_name_a)
        self.etree_rate_div = self.e.getchildren()[1]
        self.rate_div = Div(self.etree_rate_div)

    def get_rate(self):
        return self.rate_div.get_rate()

    def get_link(self):
        return self.name_a.get_link()

    def get_title(self):
        return self.name_a.get_title_name()
