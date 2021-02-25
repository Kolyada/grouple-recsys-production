from .row import Row


class Table:
    def __init__(self, etree_elem):
        self.e = etree_elem
        self.etree_rows = self.e.getchildren()[1:]
        self.rows = [Row(el) for el in self.etree_rows]

    def gather_row_info(self, row_index):
        row = self.rows[row_index]
        d = {'title': row.get_title(),
             'link': row.get_link(),
             'rate': row.get_rate()}
        return d


    def __iter__(self):
        return self

    def __next__(self):
        for row in self.rows:
            yield row

    def __len__(self):
        return len(self.rows)
