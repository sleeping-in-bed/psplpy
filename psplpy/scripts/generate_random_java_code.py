import os
import random

existing_variables = []  # 用于存储已存在的变量名


# 随机从已存在的变量中选择一个变量名
def choose_existing_variable():
    if existing_variables:
        return random.choice(existing_variables)
    return None


# 随机生成整数
def generate_random_integer(min: int = 1, max: int = 2**31):
    return random.randint(min, max)


# 随机生成变量名
def generate_variable_name(length=generate_random_integer(1000, 1000), add_var=True):
    letters = "abcdefghijklmnopqrstuvwxyz"
    while True:
        new_variable_name = ''.join(random.choice(letters) for _ in range(length))
        if new_variable_name not in existing_variables:
            break
    if add_var:
        existing_variables.append(new_variable_name)
    return new_variable_name


# 随机生成 Java 代码
def generate_random_java_code(class_name, num, show_process=True):
    java_code = f"public class {class_name} {{\n"
    java_code += "    public static void main(String[] args) {\n"

    for _ in range(num):
        if show_process:
            if _ % 100 == 0:
                print(_)
        random_choice = random.randint(1, 4)

        if random_choice == 1 or not existing_variables:  # 生成变量定义
            var_name = generate_variable_name()
            var_value = generate_random_integer()
            line = f"        int {var_name} = {var_value};"
            java_code += line + "\n"
        elif random_choice == 2:  # 生成条件语句
            var_name = choose_existing_variable()
            if var_name:
                line = f"        if ({var_name} > 50) {{\n            System.out.println(\"{var_name} is greater than 50\");\n        }}"
                java_code += line + "\n"
        elif random_choice == 3:  # 生成循环语句
            var_name = generate_variable_name(add_var=False)
            if var_name:
                line = f"        for (int {var_name} = 0; {var_name} < 10; {var_name}++) {{\n            System.out.println({var_name});\n        }}"
                java_code += line + "\n"
        else:  # 生成switch语句和while语句
            var_name = choose_existing_variable()
            if var_name:
                case_statements = "\n".join(
                    [f"            case {i}:\n                System.out.println(\"Case {i}\");" for i in range(1, 4)])
                switch_code = f"        switch ({var_name}) {{\n{case_statements}\n            default:\n                System.out.println(\"Default case\");\n        }}"
                while_var = generate_variable_name()
                while_code = f"        int {while_var} = 0;\n        while ({while_var} < 5) {{\n            System.out.println(\"While loop: \" + {while_var});\n            {while_var}++;"
                java_code += switch_code + "\n" + while_code + "\n        }\n"

    java_code += "    }\n}"
    return java_code


if __name__ == '__main__':
    class_name = 'RandomJavaCode'
    num = 1500
    save_dir = r'D:\WorkSpace\Code\IdeaProjects\Study\src\study\code'
    # 生成并输出 Java 代码
    java_code = generate_random_java_code(class_name, num)
    with open(os.path.join(save_dir, class_name + '.java'), 'w') as f:
        f.write(java_code)
    print(java_code)
