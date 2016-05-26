from tornado.websocket import WebSocketHandler
from zmq.eventloop.zmqstream import ZMQStream

from pocs.utils.logger import get_logger

clients = []


class PanWebSocket(WebSocketHandler):

    def open(self, channel):
        """ Client opening connection to unit """
        self.logger = get_logger(self)

        if channel is None:
            channel = self.settings['name']

        self.logger.info("Setting up listener for channel: {}".format(channel))

        try:
            messaging = self.settings['messaging']

            self.listener = messaging.register_listener(channel=channel, port=6501, connect=True)
            self.publisher = messaging.create_publisher(port=6500, connect=True)
            self.stream = ZMQStream(self.listener)

            # Register the callback
            self.stream.on_recv(self.on_data)
            self.logger.info("WS opened for channel {}".format(channel))

            # Add this client to our list
            clients.append(self)
        except Exception as e:
            self.logger.warning("Problem establishing websocket for {}: {}".format(self, e))

    def on_data(self, data):
        """ From the PANOPTES unit """
        msg = data[0].decode('UTF-8')
        self.logger.debug("WS Received: {}".format(msg))
        self.write_message(msg)

    def on_message(self, message):
        """ From the client """
        self.logger.info("WS Sent: {}".format(message))
        messaging = self.settings['messaging']
        messaging.send_message('PAWS', message)

    def on_close(self):
        """ When client closes """
        clients.remove(self)
        self.logger.info("WS Closed")
