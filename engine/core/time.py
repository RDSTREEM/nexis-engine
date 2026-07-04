import time


class Time:

    delta_time = 0.0
    last_time = 0.0
    time = 0.0
    frame_count = 0

    @classmethod
    def update(cls):
        now = time.perf_counter()

        if cls.last_time == 0:
            cls.last_time = now

        cls.delta_time = min(now - cls.last_time, 0.1)
        cls.last_time = now

        cls.time += cls.delta_time
        cls.frame_count += 1
