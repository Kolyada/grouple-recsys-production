import re
from tqdm import tqdm

BUFFER_SIZE = 1500



from datetime import datetime as dt
def to_timestamp(timestr):
    dtobj = dt.strptime(timestr, '%Y-%m-%d %H:%M:%S')
    timestamp = int(dtobj.timestamp())
    return timestamp



def read_dump(dump_filename, target_table, csv_path, required_fields, n_fields):
    """
    Parses .sql dump to records format. Uses small buffer when writing data to file
    @param dump_filename: path to .sql dump file
    @param target_table: name of table in dump file
    @param csv_path: path to resulted .csv file
    @param required_fields: tuple of field ixs
    @param n_fields: filters records with other number of items
    """
    fast_forward = True
    buffer = []
    
    with open(dump_filename, 'r') as fin:
        with open(csv_path, 'w') as fout:
            
            for line in tqdm(fin):
                line = line.strip()
                if line.lower().startswith('insert') and target_table in line:
                    fast_forward = False
                if fast_forward:
                    continue
            
                data = re.findall('\([^\)]*\)', line)
                for i, obj in enumerate(data):
                    # id, site_id, rate, user_id, status, date
                    # (2583,3,1,15911,6,'2012-06-12 23:40:29')
                    try:
                        row = obj[1:-1] # drop brackets
                        if len(row.split(',')) != n_fields:
                            continue

                        # drop date_created
                        row = row.split(',')
                        row = [row[i] for i in range(len(row)) if i in required_fields]
                        row = ','.join(row)
                        buffer.append(row)

                        if len(buffer) > BUFFER_SIZE:
                            fout.write('\n'.join(buffer) + '\n') # write out
                            buffer = []

                    except Exception as e:
                        pass#raise e
                    
            fout.write('\n'.join(buffer)) # last data writing
    return 0
