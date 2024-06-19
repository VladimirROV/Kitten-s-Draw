from colorama import Fore
def warning(text):
    print(Fore.YELLOW + "[Варн]{}".format(text))
def error(text):
    print(Fore.RED + "[Ошибка]{}".format(text))
def good(text):
    print(Fore.GREEN + "[Отладка]{}".format(text))