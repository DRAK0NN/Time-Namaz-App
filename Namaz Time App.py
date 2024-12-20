import sys
import json
from PyQt5.QtWidgets import (
    QApplication, QLabel, QVBoxLayout, QWidget, QPushButton, QDialog, QFormLayout, QLineEdit
)
from PyQt5.QtCore import Qt, QTimer, QDateTime
import requests
from datetime import datetime

# Weather function
def get_weather(city="Moscow"):
    api_key = "c891718ed41c16f6d05ccd667850beef"
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    try:
        response = requests.get(url).json()
        if response.get("main"):
            return f"{response['main']['temp']}°C, {response['weather'][0]['description']}"
        return "Погода недоступна"
    except Exception:
        return "Ошибка получения погоды"

# Prayer times function
from bs4 import BeautifulSoup

def get_prayer_times(country="russia", city="samara"):
    try:
        url = f"https://www.salahtimes.com/{country}/{city}"
        response = requests.get(url)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            today_row = soup.find("tr", {"class": "friday"})
            if today_row:
                times = today_row.find_all("td")[1:]  # Пропускаем дату
                prayer_names = ["Fajr", "Sunrise", "Dhuhr", "Asr", "Maghrib", "Isha"]
                prayer_times = {name: time.text.strip() for name, time in zip(prayer_names, times)}
                return prayer_times
            return "Ошибка: Не удалось найти данные для текущей даты."
        else:
            return f"Ошибка: Сайт вернул статус {response.status_code}."
    except Exception as e:
        return f"Ошибка получения времени намаза: {e}"

class PrayerWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Namaz Time App")

        # Load settings
        self.settings_file = "settings.json"
        self.load_settings()

        # Create layout
        self.layout = QVBoxLayout()
        self.prayer_label = QLabel("Время намаза: Загрузка...")
        self.weather_label = QLabel("Погода: Загрузка...")
        self.date_time_label = QLabel("Дата и время: Загрузка...")
        self.change_city_button = QPushButton("Сменить страну и город")
        self.change_city_button.clicked.connect(self.change_city)

        # Настройка шрифта
        from PyQt5.QtGui import QFont
        font = QFont("Arial", 12)
        font.setWeight(QFont.Bold)  # Устанавливаем жирный шрифт
        self.prayer_label.setFont(font)
        self.weather_label.setFont(font)
        self.date_time_label.setFont(font)

        button_font = QFont("Arial", 10)
        button_font.setWeight(QFont.Bold)  # Устанавливаем жирный шрифт для кнопки
        self.change_city_button.setFont(button_font)

        # Добавление виджетов в макет
        self.layout.addWidget(self.date_time_label)
        self.layout.addWidget(self.weather_label)
        self.layout.addWidget(self.prayer_label)
        self.layout.addWidget(self.change_city_button)
        self.setLayout(self.layout)

        # Timer for updating date/time and prayer times
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_date_time)
        self.timer.start(1000)  # Update every second

        self.update_prayer_times()
        self.update_weather()


    def load_settings(self):
        """Load settings from file or set default."""
        try:
            with open(self.settings_file, "r") as f:
                settings = json.load(f)
                self.country = settings.get("country", "russia")
                self.city = settings.get("city", "samara")
        except FileNotFoundError:
            self.country = "russia"
            self.city = "samara"

    def save_settings(self):
        """Save current settings to file."""
        settings = {"country": self.country, "city": self.city}
        with open(self.settings_file, "w") as f:
            json.dump(settings, f)

    def update_prayer_times(self):
        """Update prayer times."""
        prayer_times = get_prayer_times(self.country, self.city)
        if isinstance(prayer_times, dict):
            times_text = "\n".join([f"{prayer}: {time}" for prayer, time in prayer_times.items()])
            self.prayer_label.setText(f"Время намаза ({self.city.capitalize()}, {self.country.capitalize()}):\n{times_text}")
        else:
            self.prayer_label.setText(prayer_times)

    def update_weather(self):
        """Update weather information."""
        weather = get_weather(self.city)
        self.weather_label.setText(f"Погода ({self.city.capitalize()}): {weather}")

    def update_date_time(self):
        """Update date and time."""
        now = datetime.now()
        formatted_time = now.strftime("%Y-%m-%d %H:%M:%S")
        self.date_time_label.setText(f"Дата и время: {formatted_time}")

    def change_city(self):
        """Open dialog to change city and country."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Сменить страну и город")
        form_layout = QFormLayout(dialog)

        country_input = QLineEdit()
        country_input.setText(self.country)
        city_input = QLineEdit()
        city_input.setText(self.city)

        form_layout.addRow("Страна:", country_input)
        form_layout.addRow("Город:", city_input)

        ok_button = QPushButton("OK")
        ok_button.clicked.connect(lambda: self.set_new_location(dialog, country_input.text(), city_input.text()))
        form_layout.addWidget(ok_button)

        dialog.setLayout(form_layout)
        dialog.exec_()

    def set_new_location(self, dialog, country, city):
        """Set a new country and city."""
        self.country = country.strip().lower()
        self.city = city.strip().lower()
        dialog.accept()
        self.save_settings()  # Save to file
        self.update_prayer_times()
        self.update_weather()

# Main function
def main():
    app = QApplication(sys.argv)
    widget = PrayerWidget()
    widget.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
