import re
from tqdm import tqdm

BUFFER_SIZE = 1500

def read_dump(dump_filename, target_table, csv_path):
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
                    # (3,10,21719,2,'2012-06-14 15:17:10')
                    try:
                        row = obj[1:-1]#.split(',')
                        if len(row.split(',')) != 5 and len(row.split(',')) != 6:
                            continue
                        
                        # drop date_created
                        row = ','.join(row.split(',')[:-1])
                        buffer.append(row)
                        if len(buffer) > BUFFER_SIZE:
                            fout.write('\n'.join(buffer) + '\n') # write out
                            buffer = []
                            
                    except Exception as e:
                        pass#raise e
                    
            fout.write('\n'.join(buffer)) # last data writing
    return 0