import multiprocessing
import string
import sys
from faker import Faker
from psplpy.random_data import RandomData

import django
from django.contrib import auth
from django.core.management import BaseCommand

# 手动调用django.setup()，在此之后，可以使用Django的各种功能、模型和设置
django.setup()


def populate(number, lock):
    rd = RandomData(string.ascii_lowercase)
    f = Faker()
    for _ in range(number):
        # get a unique username and email
        count = 0
        random_str = ''
        while True:
            if count < 8:
                random_str = ''
            elif 8 <= count < 32:
                random_str = rd.random_str(1)
            elif 32 <= count < 128:
                random_str = rd.random_str(3)
            elif 128 <= count:
                random_str = rd.random_str(9)

            name = f.name()
            first_name = name.split()[0] + random_str
            username = first_name.lower()
            last_name = name.split()[1] + random_str
            if not auth.get_user_model().objects.filter(username=username):
                break
            count += 1
        while True:
            email = random_str + f.email()
            if not auth.get_user_model().objects.filter(email=email):
                break
        password = username
        try:
            user = auth.get_user_model().objects.create_user(username=username, email=email, password=password,
                                                             first_name=first_name, last_name=last_name)
        except Exception as e:
            sys.stdout.write(f'Create Failure, will recreate: {str(e)}')
        lock.acquire()
        sys.stdout.write(f'Created user: username={username}, email={email}, password={password}\n')
        lock.release()


class Command(BaseCommand):
    help = 'Create random users for test usage.'

    def __init__(self):
        super().__init__()

    def add_arguments(self, parser):
        parser.add_argument('-n', type=int, help='The number of being populated.')
        parser.add_argument('-p', type=int, help='The number of populate processes.')

    @staticmethod
    def split_integer(num: int, n: int) -> list:
        quotient = num // n  # 整数除法，计算每个数的基本值
        remainder = num % n  # 余数，用于确定前面几个数需要加 1
        # 创建一个包含 n 个整数的列表，初始值是基本值
        result = [quotient] * n
        # 将前面的几个数增加 1
        for i in range(remainder):
            result[i] += 1
        return result

    def handle(self, *args, **options):
        number_of_users = options['n'] if options['n'] else 1
        number_of_processes = options['p'] if options['p'] else 1
        lock = multiprocessing.Lock()
        number_list = self.split_integer(number_of_users, number_of_processes)
        process_list = []

        self.stdout.write('Start populate users')
        for i in range(number_of_processes):
            p = multiprocessing.Process(target=populate, args=(number_list[i], lock))
            process_list.append(p)
            p.start()

        for p in process_list:
            p.join()
