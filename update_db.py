from django.conf import settings
from app.models import DataBase
from time import sleep


def update():
    settings.configure()
    while True:
        DataBase().run()
        sleep(30)


if __name__ == '__main__':
    update()