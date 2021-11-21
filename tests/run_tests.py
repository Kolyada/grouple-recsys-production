import os
import unittest
import recommendations


if __name__ == '__main__':
    os.environ['DATABASE_URL'] = "postgresql://root:root@localhost:5432/music"
    suits = []
    suits.append(unittest.TestLoader().loadTestsFromModule(recommendations))
    for suite in suits:
        unittest.TextTestRunner(verbosity=2).run(suite)
