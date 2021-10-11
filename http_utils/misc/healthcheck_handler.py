from tornado.web import RequestHandler


class HealthcheckHandler(RequestHandler):
    def get(self):
        return self.write({'status': 'UP'})
