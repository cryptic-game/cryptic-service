from resources.service import handle, handle_mircoservice_requests
from cryptic import MicroService


if __name__ == '__main__':
    m = MicroService('service', handle, handle_mircoservice_requests)
    m.run()
