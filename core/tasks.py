from background_task import background
from core.db import DataBase


@background(schedule=120)
def update_db():
    DataBase().update()
    print('Success RUN')


update_db(repeat=120, repeat_until=None)
