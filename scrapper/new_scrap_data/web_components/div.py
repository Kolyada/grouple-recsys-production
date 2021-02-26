def self_path(el):
    return el.getroottree().getpath(el)

class Div:
    def __init__(self, etree_elem):
        self.e = etree_elem

    def get_rate(self):
        try:
            n_of_m = self.e.xpath(self_path(self.e) + '/div/div')[0].attrib['title']
            n, m = n_of_m.split(' из ')
        except IndexError:
            n = None
        return n
