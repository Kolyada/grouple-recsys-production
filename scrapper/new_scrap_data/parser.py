from lxml import etree
from lxml import html
from web_components.table import Table


class Parser:
    def __init__(self):
        self.stop_symbs = ['\n', '  ']

    def parse(self, page_str, verbose=False):
        assert type(page_str) == str
        for symb in self.stop_symbs:
            page_str = page_str.replace(symb, '')

        data = {}
        etree_obj = html.fromstring(page_str)
        etree_tables = etree_obj.xpath('//table')

        username = self._get_username(etree_obj)
        table_names = self._get_tables_names(etree_obj)
        for i, tname in enumerate(table_names):
            try: #hotfix
                t = Table(etree_tables[i])
            except IndexError:
                return {'username': None, 'data': []}
            # avoid using . in table names cause of mongoDB errors
            tname = tname.replace('.', '<dot>')
            data[tname] = []
            for j in range(len(t)):
                data[tname].append(t.gather_row_info(j))
                if verbose:
                    print(j, data[tname][-1])

        return {'username': username, 'data': data}

    def _get_tables_names(self, etree_obj):
        tnames = []
        for i, th in enumerate(etree_obj.xpath('//th')):
            if i % 2 == 0:
                tnames.append(th.text_content())
        return tnames

    def _get_username(self, etree_obj):
        try:
            return etree_obj.xpath("//div[@class='leftContent']/h1")[0].text.replace('Пользователь ', '')
        except IndexError:
            return None
