import threading
import tkinter as tk
import json
import time
import datetime
import os
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium import webdriver
from selenium.webdriver.common.by import By


class App:
    def __init__(self, master):
        self.http_okto = "http://app.okto.ru/companies/"
        self.http_order_new = "/oms_bussiness_orders/new"
        self.http_order = "/oms_bussiness_orders"
        self.SKU = ""
        self.workshop_id = None
        self.workshop_login = None
        self.workshop_password = None
        # Количество кодов для заказа
        self.quantity_codes = 0
        # Заказ кодов, или отмена заказа
        self.code_ordered = False
        self.code_ready = "Готов (в наличии активные буферы КМ)"
        # Запуск потока, или его остановка
        self.start_thread = True
        self.master = master
        self.master.iconbitmap("icon.ico")
        self.master.title("Заказ кодов")
        self.master.geometry("400x600")
        self.master.resizable(False, False)

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

        self.button_c1 = tk.Button(self.frame_button, text="Первый цех", command=lambda: self.run_in_thread(self.button_c1.cget("text")))
        self.button_c1.pack(pady=10)

        self.button_kmc = tk.Button(self.frame_button, text="Кисломолочный цех", command=lambda: self.run_in_thread(self.button_kmc.cget("text")))
        self.button_kmc.pack(pady=10)

        self.button_csm = tk.Button(self.frame_button, text="Цех стерилизованного молока", command=lambda: self.run_in_thread(self.button_csm.cget("text")))
        self.button_csm.pack(pady=10)

        self.button_tv = tk.Button(self.frame_button, text="Творожный цех", command=lambda: self.run_in_thread(self.button_tv.cget("text")))
        self.button_tv.pack(pady=10)

        self.button_exit = tk.Button(self.frame_button, text="Выход", command=self.close_window)
        self.button_exit.pack(pady=10)

    def run_in_thread(self, button_name):
        thread = threading.Thread(target=self.open_json, args=(button_name,))
        thread.start()

    def close_window(self):
        self.start_thread = False
        self.master.destroy()

    def open_json(self, button_name):
        self.quantity_codes = int(self.codes.get())
        options = webdriver.ChromeOptions()
        options.add_extension("extension_1_2_13_0.crx")
        time.sleep(2)
        # options.add_argument("--headless")
        options.add_argument(f"user-data-dir={os.environ['LOCALAPPDATA']}\\Google\\Chrome\\User Data\\1")
        driver = webdriver.Chrome(options=options)
        driver.maximize_window()
        with open("lk.json", encoding="UTF-8") as f:
            data_id = json.load(f)
            self.workshop_id = data_id[button_name]["code"]
            self.workshop_login = data_id[button_name]["login"]
            self.workshop_password = data_id[button_name]["password"]

        with open("products.json", encoding="UTF-8") as f:
            data = json.load(f)
            # получение артикула и его использование как ключа
            for value in data["workshop"][button_name]:
                if data["workshop"][button_name][f"{value}"]["order"] and self.start_thread:
                    self.code_ordered = False
                    time.sleep(1)
                    self.label_text.config(text="Идёт заказ:\n" + data["workshop"][button_name][f"{value}"]["name"])
                    code_value = data["workshop"][button_name][f"{value}"]["id"]
                    driver.get("http://app.okto.ru/users/sign_in")
                    time.sleep(2)
                    try:
                        user_email = driver.find_element(by="id", value="user_email")
                        user_password = driver.find_element(by="id", value="user_password")
                        button_login = driver.find_element(by="id", value="sign_in_btn")
                        user_email.send_keys(self.workshop_login)
                        user_password.send_keys(self.workshop_password)
                        time.sleep(2)
                        button_login.click()
                        time.sleep(4)
                        driver.get(self.http_okto + self.workshop_id + self.http_order)
                        while not self.code_ordered:
                            if driver.find_element(By.CLASS_NAME, value="report-status").text == self.code_ready:
                                time.sleep(15)
                                self.label_info.config(text="Ожидание завершения прошлого заказа...\n"
                                                            "Повторная попытка заказа через 30 секунд")
                                time.sleep(15)
                                driver.refresh()
                            else:
                                # Выходим из цикла проверки
                                self.code_ordered = True
                        self.code_ordered = False
                        time.sleep(3)
                        # переход на страницу заказа кодов
                        driver.get(self.http_okto + self.workshop_id + self.http_order_new)
                        time.sleep(3)
                        quantity = driver.find_element(By.ID, value="quantity")
                        quantity.clear()
                        quantity.send_keys(self.quantity_codes)
                        time.sleep(4)
                        self.SKU = driver.find_element(By.ID, value="product_id")
                        driver.execute_script(
                            f"arguments[0].setAttribute('value', '{code_value}')", self.SKU)
                        driver.find_element(By.CSS_SELECTOR, value=".m-t-40px.btn.add_user").click() # заказ кодов
                        time.sleep(5)
                        driver.get(self.http_okto + self.workshop_id + self.http_order)
                        time.sleep(2)
                        while self.start_thread and not self.code_ordered:
                            driver.refresh()
                            report_status = driver.find_element(By.CLASS_NAME, value="report-status")
                            time.sleep(5)
                            if report_status.text == self.code_ready and self.start_thread:
                                driver.find_element(By.CLASS_NAME, value="order-id").click()
                                time.sleep(5)
                                WebDriverWait(driver, 10).until(expected_conditions.presence_of_element_located((By.NAME, "check_gtin"))).click()
                                time.sleep(5)
                                driver.find_element(By.ID, value="obtain_identification_codes").click()
                                quantity = driver.find_element(By.ID, value="quantity")
                                time.sleep(2)
                                quantity.clear()
                                quantity.send_keys(self.quantity_codes)
                                time.sleep(1)
                                driver.find_element(By.ID, value="submit_codes_form").click() # получение кодов из заказа
                                self.code_ordered = True
                            else:
                                self.label_info.config(text="Ожидание появления заказа...")
                            time.sleep(5)
                    except Exception as ex:
                        print(ex)
                        with open("logs.txt", "a", encoding="UTF-8") as self.f:
                            self.f.write(str(datetime.datetime.now()))
                            self.f.write(str(ex))
                        self.label_text.config(text="Во время заказа кодов продукта:\n"
                                                    + data["workshop"][button_name][f"{value}"]["name"]
                                                    + "\nВозникла ошибка" + "\nСообщите разработчику")
                        self.start_thread = False
                    finally:
                        self.label_info.config(text="Заказ " + data["workshop"][button_name][f"{value}"]["name"] + " завершен")
                        time.sleep(2)
                        driver.find_element(By.ID, value="logout_link").click()
            self.label_text.config(text="Заказы для " + str(button_name) + " завершены")
            self.label_info.config(text="Ошибок не возникло")
        driver.close()
        driver.quit()


# Создание главного окнка
root = tk.Tk()
app = App(root)

# Запуск главного окна в бесконечном цикле
root.mainloop()
