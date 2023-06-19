import threading
import tkinter as tk
import json
import time
import datetime
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.common.by import By


class App:
    def __init__(self, master):
        self.http_okto = "http://app.okto.ru/companies/"
        self.http_order_new = "/oms_bussiness_orders/new"
        self.http_order = "/oms_bussiness_orders"
        # уникальное значение продукта
        self.SKU = ""
        # список продуктов
        self.list_products = []
        # имя личного кабинета
        self.workshop_name = None
        # уникальный номер личного кабинета(ЛК)
        self.workshop_id = None
        # логин личного кабинета
        self.workshop_login = None
        # пароль личного кабинета
        self.workshop_password = None
        # флаг на поток
        self.thread = None
        # Количество кодов для заказа
        self.quantity_codes = 0
        # id кода
        self.code_id = 0
        # Последний продукт в заказе
        self.last_workshop_name = ""
        self.last_product_name = ""
        self.last_product_id = ""
        # Заказ кодов, или отмена заказа
        self.code_ordered = False
        # Флаг для проверки остановки по кнопке
        self.button_stop_flag = False
        # Текст для проверки готовности заказа
        self.code_ready = "Готов (в наличии активные буферы КМ)"
        # Запуск потока, или его остановка
        self.start_thread = True
        self.master = master
        self.master.iconbitmap("icon.ico")
        self.master.title("Заказ кодов")
        self.master.geometry("400x800")
        self.master.resizable(False, False)

        # Чтение JSON файлов во время запуска
        # -----------------------------------
        # Получение ЛК
        with open("lk.json", "r", encoding="UTF-8") as f:
            self.data_lk = json.load(f)

        # Получение продукта
        with open("products.json", "r", encoding="UTF-8") as f:
            self.data_products = json.load(f)

        # Создание контейнера для текста/отображения выполнения задачи
        self.frame_displaying = tk.Frame(self.master)
        self.frame_displaying.pack(side=tk.TOP, fill=tk.X)

        self.label_text = tk.Label(self.frame_displaying, text="Добро пожаловать!", wraplength=350)
        self.label_text.pack(pady=10)

        self.label_info = tk.Label(self.frame_displaying, text="Сведения и предупреждения\nотсутствуют", wraplength=350)
        self.label_info.pack(pady=20)

        self.codes_info = tk.Label(self.frame_displaying, text="Кодов в заказе", wraplength=200)
        self.codes_info.pack()

        self.codes = tk.Entry(self.frame_displaying, width=10)
        self.codes.pack()
        self.codes.insert(150000, "150000")

        # Создание контейнера для кнопок
        self.frame_button = tk.Frame(self.master)
        self.frame_button.pack(side=tk.BOTTOM)

        self.button_0 = tk.Button(self.frame_button, text="Не используемая кнопка", command=lambda: self.run_in_thread(self.button_0.cget("text")))
        self.button_0.pack(pady=10)

        self.button_1 = tk.Button(self.frame_button, text="Не используемая кнопка", command=lambda: self.run_in_thread(self.button_1.cget("text")))
        self.button_1.pack(pady=10)

        self.button_2 = tk.Button(self.frame_button, text="Не используемая кнопка", command=lambda: self.run_in_thread(self.button_2.cget("text")))
        self.button_2.pack(pady=10)

        self.button_3 = tk.Button(self.frame_button, text="Не используемая кнопка", command=lambda: self.run_in_thread(self.button_3.cget("text")))
        self.button_3.pack(pady=10)

        self.button_stop = tk.Button(self.frame_button, text="Остановить заказ", command=self.stop_thread, state=tk.DISABLED)
        self.button_stop.pack(pady=20)

        # Переименовывание кнопок, согласно Json
        for index, value in enumerate(self.data_lk):
            if index > 3:
                break
            if index == 0:
                self.button_0.config(text=value)
            elif index == 1:
                self.button_1.config(text=value)
            elif index == 2:
                self.button_2.config(text=value)
            elif index == 3:
                self.button_3.config(text=value)

    # Запуск функции в отедбном потоке
    def run_in_thread(self, workshop):
        self.start_thread = True
        self.thread = threading.Thread(target=self.run_task, args=(workshop,))
        self.thread.daemon = True
        self.thread.start()

        # Выключение всех кнопок
        for button in (self.button_0, self.button_1, self.button_2, self.button_3):
            button.config(state=tk.DISABLED)
        self.codes_info.config(text=f"Коды для цеха {workshop} в заказе")
        self.button_stop.config(state=tk.NORMAL)

    # функция для остановки задачи
    def stop_thread(self):
        self.start_thread = False
        for button in (self.button_0, self.button_1, self.button_2, self.button_3):
            button.config(state=tk.NORMAL)
        self.label_info.config(text="Заказ остановлен")
        self.button_stop.config(state=tk.DISABLED)
        self.button_stop_flag = True

    def run_task(self, workshop):
        # Выключение всех кнопок
        for button in (self.button_0, self.button_1, self.button_2, self.button_3):
            button.config(state=tk.DISABLED)
        self.button_stop.config(state=tk.ACTIVE)
        self.workshop_name = workshop
        self.workshop_login = self.data_lk[self.workshop_name]["login"]
        self.workshop_password = self.data_lk[self.workshop_name]["password"]
        self.workshop_id = self.data_lk[self.workshop_name]["id"]
        self.quantity_codes = int(self.codes.get())
        options = webdriver.ChromeOptions()
        options.add_extension("extension_1_2_13_0.crx")
        options.add_argument("--start-maximized") # окно на весь экран
        options.add_argument('--headless=new') # скрытая работа
        options.add_argument("--disable-gpu") # уменьшение использования графического процессора
        options.add_argument("--disable-infobars") # отключение информационной панели
        options.add_argument("--disable-notifications") # отключение уведомлений
        options.add_argument("--disable-dev-shm-usage") # отключает использование /dev/shm в Chrome
        options.add_argument("--no-sandbox") # отключение режима песочницы
        driver = webdriver.Chrome(options=options)

        # Пауза с помощью Selenium 10 секунд
        wait = WebDriverWait(driver, 10)
        # Если была остановка заказа
        if len(self.list_products) == 0 or workshop != self.last_workshop_name:
            self.list_products.clear()
            for value in self.data_products[workshop]:
                if self.data_products[workshop][str(value)]["order"] and self.start_thread:
                    self.list_products.append(value)
        else:
            self.list_products = self.list_products[self.list_products.index(self.last_product_name):]

        for product in self.list_products:
            # Заказываем только необходимые коды
            if self.data_products[workshop][str(product)]["order"] and self.start_thread:
                self.code_ordered = False
                self.last_product_name = product
                self.last_workshop_name = workshop
                self.code_id = self.data_products[workshop][f"{product}"]["id"]
                self.codes_info.config(text=f"Продукты в заказе:\n" + "\n".join(str(i) for i in self.list_products))
                # Входим в систему
                try:
                    self.label_info.config(text=f"Выполняется заказ для цеха {workshop}")
                    driver.get("http://app.okto.ru/users/sign_in")
                    driver.find_element(By.ID, "user_email").send_keys(self.workshop_login)
                    driver.find_element(By.ID, "user_password").send_keys(self.workshop_password)
                    # Кнопка Sing in
                    driver.find_element(By.ID, "sign_in_btn").click()
                except Exception:
                    self.label_info.config(text="Не удалось зайти на сайт ОКТО")
                try:
                    # Переход на страницу заказов для проверки текущего заказа кодов
                    driver.get(self.http_okto + self.workshop_id + self.http_order)
                    # Проверка на уже сделанный заказ. Только первый из всего списка
                    while not self.code_ordered:
                        if wait.until(EC.presence_of_element_located((By.CLASS_NAME, "report-status"))).text == self.code_ready:
                            self.label_info.config(text="Ожидание завершения прошлого заказа...\n"
                                                        "Повторная попытка заказа через 30 секунд")
                            time.sleep(20)
                            driver.refresh()
                        else:
                            # Выходим из цикла проверки
                            self.code_ordered = True
                    self.code_ordered = False
                    # Отображение текущего заказа кодов
                    self.label_text.config(text="Идёт заказ:\n" + self.data_products[workshop][f"{product}"]["name"])
                    # Переход на страницу заказов
                    driver.get(self.http_okto + self.workshop_id + self.http_order_new)
                    # Очищаем поле кодов
                    wait.until(EC.presence_of_element_located((By.ID, "quantity"))).clear()
                    # Указываем количество кодов для заказа
                    wait.until(EC.presence_of_element_located((By.ID, "quantity"))).send_keys(self.quantity_codes)
                    self.SKU = wait.until(EC.presence_of_element_located((By.ID, "product_id")))
                    driver.execute_script(f"arguments[0].setAttribute('value', '{self.code_id}')", self.SKU)
                    # Отправка кодов
                    wait.until(EC.presence_of_element_located((By.NAME, "commit"))).click()
                    time.sleep(2)
                    # Переход на страницу заказов
                    driver.get(self.http_okto + self.workshop_id + self.http_order)
                    while self.start_thread and not self.code_ordered:
                        driver.refresh()
                        if wait.until(EC.presence_of_element_located((By.CLASS_NAME, "report-status"))).text == self.code_ready and self.start_thread:
                            # выбираем новый заказ
                            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "order-id"))).click()
                            time.sleep(2)
                            # ставим галочку, что хотим получить коды
                            wait.until(EC.presence_of_element_located((By.NAME, "check_gtin"))).click()
                            time.sleep(2)
                            driver.find_element(By.ID, value="obtain_identification_codes").click()
                            time.sleep(2)
                            # Нажимаем на кнопку для ввода количества кодов
                            quantity = driver.find_element(By.ID, value="quantity")
                            time.sleep(2)
                            quantity.clear()
                            quantity.send_keys(self.quantity_codes)
                            time.sleep(2)
                            driver.find_element(By.ID, value="submit_codes_form").click() # получение кодов из заказа
                            self.code_ordered = True
                        else:
                            self.label_info.config(text="Ожидание появления заказа...")
                        time.sleep(5)
                except Exception as e:
                    self.label_info.config(text="Не удалось выполнить задачу\nОбъект для заказа не найдет")
                    with open("logs.txt", "a", encoding="UTF-8") as self.f:
                        self.f.write(str(datetime.datetime.now()))
                        self.f.write(str(e))
                    self.label_text.config(text="Во время заказа кодов продукта:\n"
                                                + self.data_products[workshop][str(product)]["name"]
                                                + "\nВозникла ошибка" + "\nСообщите разработчику")
                    self.start_thread = False
                    for button in (self.button_0, self.button_1, self.button_2, self.button_3):
                        button.config(state=tk.NORMAL)
                    self.button_stop.config(state=tk.DISABLED)
                finally:
                    self.label_info.config(text="Заказ " + self.data_products[workshop][str(product)]["name"] + " завершен")
                    time.sleep(2)
                    driver.find_element(By.ID, value="logout_link").click()
        driver.quit()
        for button in (self.button_0, self.button_1, self.button_2, self.button_3):
            button.config(state=tk.NORMAL)
        if self.button_stop_flag:
            self.label_text.config(text=f"Заказы для цеха {workshop} были приостановлены")
            self.label_info.config(text="Не удалось полностью заказать коды")
            self.codes_info.config(text=f"Введите количество кодов в заказе")
        else:
            self.label_text.config(text=f"Заказы для цеха {workshop} завершены")
            self.label_info.config(text="Выберите другой цех для заказа кодов")
            self.codes_info.config(text=f"Все коды были получены!")
        self.button_stop.config(state=tk.DISABLED)
        self.list_products.clear()


# Создание главного окнка
root = tk.Tk()
app = App(root)

# Запуск главного окна в бесконечном цикле
root.mainloop()
