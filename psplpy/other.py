class GateCircuitCal:
    def __init__(self):
        pass

    @staticmethod
    def xor_gate(a, b) -> int:
        return int(int(a) ^ int(b))

    @staticmethod
    def and_gate(a, b) -> int:
        return int(int(a) and int(b))

    @staticmethod
    def binarization(number):
        return bin(number)[2:]

    @staticmethod
    def decimalization(binary_digit):
        return int(binary_digit, 2)

    @staticmethod
    def add_cal(a, b):
        """A super inefficient addition based on gate circuits"""
        binary_digit_a = GateCircuitCal.binarization(a)
        binary_digit_b = GateCircuitCal.binarization(b)
        if len(binary_digit_a) < len(binary_digit_b):
            binary_digit_a = (len(binary_digit_b) - len(binary_digit_a)) * '0' + binary_digit_a
        else:
            binary_digit_b = (len(binary_digit_a) - len(binary_digit_b)) * '0' + binary_digit_b
        result = ''
        carry_bit = 0
        for bit_a, bit_b in zip(reversed(binary_digit_a), reversed(binary_digit_b)):
            intermediate_result = GateCircuitCal.xor_gate(bit_a, bit_b)
            result = str(GateCircuitCal.xor_gate(intermediate_result, carry_bit)) + result
            carry_bit = GateCircuitCal.xor_gate(GateCircuitCal.and_gate(carry_bit, intermediate_result),
                                                GateCircuitCal.and_gate(bit_a, bit_b))
        if carry_bit == 1:
            result = str(carry_bit) + result
        return GateCircuitCal.decimalization(result)


if __name__ == '__main__':
    print(GateCircuitCal.add_cal(356398653846386259623, 38567856348926273567285))
    print(356398653846386259623 + 38567856348926273567285)
