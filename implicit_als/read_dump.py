from io import StringIO
import re

def read_dump(dump_filename, target_table):
    sio = StringIO()
        
    fast_forward = True
    with open(dump_filename, 'r') as f:
        for line in f:
            line = line.strip()
            if line.lower().startswith('insert') and target_table in line:
                fast_forward = False
            if fast_forward:
                continue
            data = re.findall('\([^\)]*\)', line)
            for i, obj in enumerate(data):
                # (3,10,21719,2,'2012-06-14 15:17:10')
                try:
                    row = obj[1:-1]#.split(',')
                    if len(row.split(',')) != 5:
                        continue
                    sio.write(row)
                    sio.write("\n")
                except:
                    pass
    sio.pos = 0
    return sio