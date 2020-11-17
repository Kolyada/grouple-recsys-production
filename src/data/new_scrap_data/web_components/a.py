def self_path(el):
    return el.getroottree().getpath(el)

class A:
    def __init__(self, etree_elem):
        self.e = etree_elem

    def get_title_name(self):
        try:
            return self.e.xpath(self_path(self.e) + '/a')[1].attrib['data-title']
        except (IndexError, KeyError):
            return self.e.xpath(self_path(self.e) + '/a')[0].text
        
    def get_link(self):
        links = [x[2] for x in self.e.iterlinks()]
        return links[0]
