import time_it


# more example naming rules: setup / main_statement + positive integer
def setup1():
    def xor_gate(a, b) -> int:
        return int(int(a) ^ int(b))

    def and_gate(a, b) -> int:
        return int(int(a) and int(b))

    def binarization(number):
        return bin(number)[2:]

    def decimalization(binary_digit):
        return int(binary_digit, 2)

    def add_calculation(a, b):
        binary_digit_a = binarization(a)
        binary_digit_b = binarization(b)
        if len(binary_digit_a) < len(binary_digit_b):
            binary_digit_a = (len(binary_digit_b) - len(binary_digit_a)) * '0' + binary_digit_a
        else:
            binary_digit_b = (len(binary_digit_a) - len(binary_digit_b)) * '0' + binary_digit_b
        result = ''
        carry_bit = 0
        for bit_a, bit_b in zip(reversed(binary_digit_a), reversed(binary_digit_b)):
            intermediate_result = xor_gate(bit_a, bit_b)
            result = str(xor_gate(intermediate_result, carry_bit)) + result
            carry_bit = xor_gate(and_gate(carry_bit, intermediate_result), and_gate(bit_a, bit_b))
        if carry_bit == 1:
            result = str(carry_bit) + result
        return decimalization(result)


def main_statement1():
    add_calculation(47853758326457465372653275738532784632875328458352,
                    375327857583264574653726532757385327846328753284583326)


def main_statement2():
    47853758326457465372653275738532784632875328458352 + 375327857583264574653726532757385327846328753284583326

if __name__ == '__main__':
    # if test_num=0, will automatically test the longest example for about 1 second
    test_num = 0
    test_time_dic, test_time_dic_str, test_time_dic_ratio = time_it.time_it(__file__, test_num)

    print('# (setup_id, main_id): time_usage(line1, seconds) / ratio(line2)')
    print(test_time_dic)
    print(test_time_dic_str)
    print(test_time_dic_ratio)




