from faker import Faker

fake = Faker()

random_email = fake.email()
print(random_email)

random_password = fake.password(length=10)
print(random_password)

fake = Faker(locale='zh_CN')

# 生成包含中文字符的随机字符串
random_chinese_text = fake.text()
print(random_chinese_text)
print(fake.name())
print(fake.address())