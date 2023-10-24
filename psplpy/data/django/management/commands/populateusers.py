from django.contrib import auth
from faker import Faker
from django.core.management import BaseCommand


class Command(BaseCommand):
    help = 'Create random users for test usage.'

    def add_arguments(self, parser):
        parser.add_argument('-n', type=int, help='The number of being populated.')

    def handle(self, *args, **options):
        number_of_users = options['n'] if options['n'] else 1
        f = Faker()
        for _ in range(number_of_users):
            # get a unique username and email
            while True:
                name = f.name()
                first_name = name.split()[0]
                username = first_name.lower()
                last_name = name.split()[1]
                if not auth.get_user_model().objects.filter(username=username):
                    break
            while True:
                email = f.email()
                if not auth.get_user_model().objects.filter(email=email):
                    break
            password = username
            user = auth.get_user_model().objects.create_user(username=username, email=email, password=password,
                                                             first_name=first_name, last_name=last_name)
            self.stdout.write(f'Created user: username={username}, email={email}, password={password}\n')
