from collections import deque
import logging


class ProxyManager:
    def __init__(self, proxies_list=None, proxies_file=None):
        if proxies_file:
            proxies_list = self._load_proxies_from_file(proxies_file)
        elif proxies_list == None:
            raise AttributeError("No proxies provided")

        self.proxies_deque = deque(proxies_list)


    def delete_proxy_address(self, proxy):
        with open("bad_proxylist.txt", 'a') as fout:
            fout.write(str(proxy) + '\n')
        try:
            self.proxies_deque.remove(proxy)
        except:
            logging.error("Can delete proxy "+str(proxy)+" from proxylist. No entry")


    def __iter__(self):
        return self


    def __next__(self):
        if len(self.proxies_deque) == 0:
            logging.error("Cant yield proxy. No proxies left")
            raise RuntimeError

        proxy = self.proxies_deque.popleft()
        self.proxies_deque.append(proxy)

        return proxy


    def _load_proxies_from_file(self, filename):
        proxies = set()
        bad_proxies = set()
        with open(filename, 'r') as fin:
            for line in fin:
                line = line.replace("\n", '')
                line = line.split(':')
                proxies.add(tuple(line))
        with open('bad_proxylist.txt', 'r') as fin:
            for line in fin:
                line = line.replace("\n", '')
                if len(line) > 8:
                    bad_proxies.add(line)
        proxies_list = list(proxies.difference(bad_proxies))
        print("Load %d proxies" % len(proxies_list))
        return proxies_list
