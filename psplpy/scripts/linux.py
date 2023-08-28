from psplpy import linux


def install_software(software_list, install_package_list):

    for software in software_list:
        linux.apt_get(software)


    for package in install_package_list:
        linux.dpkg(package)


if __name__ == '__main__':
    software_list = ['git', ]
    install_package_list = []