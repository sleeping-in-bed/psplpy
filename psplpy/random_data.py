import random
import string


class RandomData:
    digits = string.digits
    ascii_lowercase = string.ascii_lowercase
    ascii_uppercase = string.ascii_uppercase

    def __init__(self, char_sets=None):
        if not char_sets:
            self.char_sets = self.digits + self.ascii_uppercase + self.ascii_lowercase
        else:
            self.char_sets = char_sets

    def random_str(self, length: int = 10):
        return ''.join(random.choice(self.char_sets) for _ in range(length))
