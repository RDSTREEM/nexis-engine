class Time:
    delta_time = 0.0
    last_time = 0.0

    @classmethod
    def update(cls, current_time):
        cls.delta_time = current_time - cls.last_time
        cls.last_time = current_time
