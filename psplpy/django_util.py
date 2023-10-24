import requests
from bs4 import BeautifulSoup


def receive_django_form(url: str):
    response = requests.get(url)
    response.raise_for_status()
    html_source = response.text
    soup = BeautifulSoup(html_source, 'html.parser')
    forms = soup.find_all('form')

    inputs_dict = {}
    for form in forms:
        inputs = form.find_all('input')
        for input_element in inputs:
            input_name = input_element.get('name')
            input_value = input_element.get('value', '')
            if input_name:
                inputs_dict[input_name] = input_value
    return inputs_dict


def send_django_form(url: str, data_dict: dict, test_func):
    cookies = {'csrftoken': data_dict['csrfmiddlewaretoken']}
    response = requests.post(url, data=data_dict, cookies=cookies)
    return test_func(response)


def test_redirection(redirection_url: str):
    def _test_redirection(response: requests.Response):
        if response.url == redirection_url:
            return True
        else:
            return False
    return _test_redirection
