import datetime


class Field:
    def __init__(self, name, request, type='string', init_value=None,
                 value=None, p=False):
        self.name = name
        self.type = type
        self.request = request
        self.p = p
        self.init_value = init_value
        self.value = value
        self.process_input()

    def process_input(self):
        data = self.raw_value()
        if self.p:
            print(data, type(data))

        if self.type == "string":
            if isinstance(data, str):
                self.value = str(data)
                self.init_value = self.value

        elif self.type == "number":
            if not self.is_none(data):
                try:
                    self.value = float(data)
                    self.init_value = self.value
                    if self.p:
                        print(f"{self.name}: {self.value}")
                except (ValueError, TypeError) as er:
                    if self.p:
                        print(data, type(data), er)
                    self.value = None
            else:
                self.value = None
                if self.p:
                    print(data, type(data))

        elif self.type == "date":
            if not self.is_none(data):
                self.value = self.parse_date(data)
                self.init_value = data
                if self.p:
                    print('data:', data, type(data))
                    print('self.value:', self.value, type(self.value))

    def parse_date(self, date):
        year, month, day = date.split('-')
        data = datetime.date(int(year), int(month), int(day))
        return data

    def raw_value(self):
        if self.p:
            print(self.name, 'raw: ', self.request.get(self.name))
        return self.request.get(self.name)

    def is_valid(self):
        data = self.value != '' and self.value is not None
        if self.p:
            print(f"{self.name}: {data}")
        return data

    def is_none(self, value):
        return value == '' or value is None
