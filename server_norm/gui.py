import tkinter as tk
from tkinter import ttk
import socket
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
import ast
import matplotlib
import math
import time
matplotlib.use('TkAgg')  # Установка backend перед импортом pyplot
#from client import Client


class SimulationGUI:
    def __init__(self, client):
        """Инициализация GUI"""
        self.client = client
        self.root = tk.Tk()
        self.root.title("Симуляция частиц")
        
        # Добавляем переменные для управления анимацией
        self.animation_running = False
        self.last_frame_time = 0
        self.frame_interval = 33  # ~30 FPS в миллисекундах
        
        # Сохраняем текущий размер окна для отслеживания изменений
        self.current_width = self.root.winfo_width()
        self.current_height = self.root.winfo_height()
        
        # Создаем главный контейнер
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        
        # Настраиваем веса строк и столбцов для главного окна
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Настраиваем веса для main_frame
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=1)
        
        # Создаем фрейм для элементов управления
        self.control_frame = ttk.Frame(self.main_frame)
        self.control_frame.grid(row=0, column=0, sticky="ns", padx=5, pady=5)
        
        # Создаем фрейм для графика
        self.plot_frame = ttk.Frame(self.main_frame)
        self.plot_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        
        self.client.gui = self
        
        # Создаем слайдеры и кнопки
        self.create_controls()
        
        # Создаем график
        self.create_plot()
        
        # Привязываем обработчик изменения размера окна
        self.root.bind('<Configure>', self.on_window_resize)
        
        # Сохраняем базовый размер шрифта
        self.base_font_size = 10
        
    def create_controls(self):
        # Создаем стиль для меток
        style = ttk.Style()
        style.configure('Controls.TLabel', padding=5)
        
        # Создаем фрейм для каждого слайдера с меткой и единицами измерения
        def create_slider_with_units(parent, text, unit, min_val, max_val, is_int=False):
            frame = ttk.Frame(parent)
            frame.pack(fill='x', padx=5, pady=2)
            
            # Метка слева
            label = ttk.Label(frame, text=text, style='Controls.TLabel', width=15)
            label.pack(side='left')
            
            # Слайдер в центре
            slider = ttk.Scale(frame, from_=0, to=100, orient='horizontal', length=200)
            slider.set(50)  # Начальное положение
            slider.pack(side='left', padx=5)
            
            # Метка справа со значением и единицами измерения
            value_label = ttk.Label(frame, style='Controls.TLabel', width=25)
            value_label.pack(side='left')
            
            # Функция обновления значения
            def update_value(event=None):
                value = self.get_slider_value(slider, min_val, max_val)
                if is_int:
                    value = int(value)
                formatted_value = str(value) if is_int else self.format_scientific(value)
                value_label.config(text=f"{formatted_value} {unit}")
            
            slider.bind('<Motion>', update_value)
            slider.bind('<Button-1>', update_value)
            slider.bind('<ButtonRelease-1>', update_value)
            update_value()  # Начальное значение
            
            return slider
        
        # Температура
        self.temperature_slider = create_slider_with_units(
            self.control_frame, "Температура (T):", "К", 1e1, 1e4)
        
        # Вязкость
        self.viscosity_slider = create_slider_with_units(
            self.control_frame, "Вязкость (η):", "Па·с", 1e-5, 1e-1)
        
        # Радиус частицы
        self.size_slider = create_slider_with_units(
            self.control_frame, "Радиус (r):", "м", 1e-9, 1e-4)
        
        # Масса частицы
        self.mass_slider = create_slider_with_units(
            self.control_frame, "Масса (m):", "кг", 1e-21, 1e-15)
        
        # Количество частиц
        self.frequency_slider = create_slider_with_units(
            self.control_frame, "Количество (N):", "шт", 1e0, 1e6, is_int=True)
        
        # Кнопки управления
        button_frame = ttk.Frame(self.control_frame)
        button_frame.pack(fill='x', padx=5, pady=10)
        
        # Кнопка для запуска симуляции
        self.start_button = ttk.Button(button_frame, text="Старт", command=self.start_simulation)
        self.start_button.pack(side='left', padx=5)
        
        # Кнопка для остановки симуляции
        self.stop_button = ttk.Button(button_frame, text="Стоп", command=self.stop_simulation)
        self.stop_button.pack(side='left', padx=5)
        self.stop_button.config(state='disabled')
        
        # Кнопка для применения параметров
        self.apply_button = ttk.Button(button_frame, text="Применить", command=self.apply_settings)
        self.apply_button.pack(side='left', padx=5)
        
        # Кнопка для перезапуска с новыми параметрами
        self.restart_button = ttk.Button(button_frame, text="Перезапустить", command=self.restart_simulation)
        self.restart_button.pack(side='left', padx=5)
        
        # Лог
        self.log_frame = ttk.Frame(self.control_frame)
        self.log_frame.pack(fill='both', expand=True, pady=10)
        
        self.log_text = tk.Text(self.log_frame, height=10, width=30)
        self.log_text.pack(side='left', fill='both', expand=True)
        
        scrollbar = ttk.Scrollbar(self.log_frame, orient='vertical', command=self.log_text.yview)
        scrollbar.pack(side='right', fill='y')
        self.log_text['yscrollcommand'] = scrollbar.set
        
    def format_scientific(self, value):
        """Форматирует число в научную нотацию вида a × 10^n"""
        if value == 0:
            return "0"
        exponent = int(math.floor(math.log10(abs(value))))
        mantissa = value / (10 ** exponent)
        # Округляем мантиссу до 2 знаков после запятой
        mantissa = round(mantissa, 2)
        return f"{mantissa} × 10^{exponent}"

    def create_plot(self):
        """Создание графика"""
        self.figure = plt.Figure(figsize=(6, 6), dpi=100)
        self.ax = self.figure.add_subplot(111, projection='3d')
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.plot_frame)
        self.canvas.get_tk_widget().pack(fill='both', expand=True)
        
        # Начальная настройка графика
        self.ax.set_xlim([0, 1])
        self.ax.set_ylim([0, 1])
        self.ax.set_zlim([0, 1])
        self.ax.set_xlabel('X')
        self.ax.set_ylabel('Y')
        self.ax.set_zlabel('Z')
        self.ax.set_title('Симуляция частиц')
        
        # Создаем начальный scatter plot
        self.particles_plot = self.ax.scatter([], [], [], c='b', marker='o', alpha=0.6)
        
        # Добавляем обработчики событий для вращения
        self.canvas.mpl_connect('button_press_event', self.on_mouse_press)
        self.canvas.mpl_connect('button_release_event', self.on_mouse_release)
        self.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)
        
        # Флаги для отслеживания состояния
        self.rotating = False
        self.last_x = 0
        self.last_y = 0
        self.current_azim = 0
        self.current_elev = 0
        
        # Переменные для контроля частоты обновления
        self.last_update_time = time.time()
        self.update_interval = 0.033  # ~30 FPS

    def on_window_resize(self, event=None):
        """Обработка изменения размера окна"""
        try:
            # Получаем размер окна
            width = self.plot_frame.winfo_width()
            height = self.plot_frame.winfo_height()
            
            # Ограничиваем максимальный размер
            max_size = 1000
            width = min(width, max_size)
            height = min(height, max_size)
            
            # Вычисляем масштаб, сохраняя квадратную форму
            size = min(width, height) / 100  # делим на 100 для уменьшения размера
            
            # Обновляем размер графика
            self.figure.set_size_inches(size, size)
            self.canvas.draw()
            
        except Exception as e:
            print(f"Ошибка при изменении размера: {e}")

    def on_mouse_press(self, event):
        if event.button == 1:  # Левая кнопка мыши
            self.rotating = True
            self.last_x = event.xdata if event.xdata else 0
            self.last_y = event.ydata if event.ydata else 0
            self.current_azim = self.ax.azim
            self.current_elev = self.ax.elev

    def on_mouse_release(self, event):
        if event.button == 1:
            self.rotating = False

    def on_mouse_move(self, event):
        if self.rotating and event.xdata and event.ydata:
            dx = event.xdata - self.last_x
            dy = event.ydata - self.last_y
            
            # Плавное вращение
            self.current_azim += dx * -50
            self.current_elev += dy * 50
            
            # Ограничиваем углы возвышения
            self.current_elev = max(-90, min(90, self.current_elev))
            
            # Применяем вращение
            self.ax.view_init(elev=self.current_elev, azim=self.current_azim)
            
            # Перерисовываем только при вращении
            self.canvas.draw()
            
            self.last_x = event.xdata
            self.last_y = event.ydata

    def update_plot(self, coordinates):
        """Обновление графика с новыми координатами"""
        try:
            if not coordinates or self.rotating:
                return
                
            current_time = time.time()
            if current_time - self.last_update_time < self.update_interval:
                return
                
            self.last_update_time = current_time
            
            # Получаем координаты
            x = [p['x'] for p in coordinates]
            y = [p['y'] for p in coordinates]
            z = [p['z'] for p in coordinates]
            
            # Обновляем данные существующего scatter plot
            self.particles_plot._offsets3d = (x, y, z)
            
            # Обновляем только если окно существует
            if self.root.winfo_exists():
                self.canvas.draw_idle()
                
        except Exception as e:
            print(f"Ошибка при обновлении графика: {e}")

    def get_slider_value(self, slider, min_val, max_val):
        """Преобразует значение слайдера (0-100) в логарифмическую шкалу"""
        normalized = slider.get() / 100.0
        return min_val * (max_val/min_val) ** normalized

    def apply_settings(self):
        """Применение новых параметров"""
        try:
            settings = {
                'temperature': self.get_slider_value(self.temperature_slider, 1e1, 1e4),
                'viscosity': self.get_slider_value(self.viscosity_slider, 1e-5, 1e-1),
                'size': self.get_slider_value(self.size_slider, 1e-9, 1e-4),
                'mass': self.get_slider_value(self.mass_slider, 1e-21, 1e-15),
                'frequency': int(self.get_slider_value(self.frequency_slider, 1e0, 1e6))
            }
            self.client.send_settings(settings)
            self.log_text.insert(tk.END, "Параметры успешно применены.\n")
        except Exception as e:
            self.log_text.insert(tk.END, f"Ошибка при применении параметров: {e}\n")

    def reset_settings(self):
        # Сброс настроек
        self.log_text.insert(tk.END, "Параметры сброшены\n")
        self.temperature_slider.set(0)
        self.viscosity_slider.set(0)
        self.size_slider.set(0)
        self.mass_slider.set(0)
        self.frequency_slider.set(0)

    def update_settings(self, *args):
        """Обновление настроек при изменении слайдеров"""
        try:
            # Получаем значения со слайдеров
            settings = {
                'temperature': self.temperature_slider.get(),
                'viscosity': self.viscosity_slider.get(),
                'size': self.size_slider.get(),
                'mass': self.mass_slider.get(),
                'frequency': int(self.frequency_slider.get())
            }
            
            # Обновляем отображение значений
            self.update_value_labels()
            
            # Если симуляция запущена, останавливаем её и запускаем с новыми параметрами
            if self.client and self.client.running:
                # Отправляем новые настройки
                if self.client.send_settings(settings):
                    print("[DEBUG] Запуск симуляции...")
                else:
                    print("Ошибка при отправке настроек")
                    
        except Exception as e:
            print(f"Ошибка при обновлении настроек: {e}")

    def start_simulation(self):
        """Запуск симуляции"""
        try:
            self.animation_running = True
            if self.client.start_simulation():
                self.start_button.config(state='disabled')
                self.stop_button.config(state='normal')  # Активируем кнопку стоп
                self.restart_button.config(state='normal')
                self.log_text.insert(tk.END, "Симуляция запущена\n")
            else:
                self.log_text.insert(tk.END, "Ошибка при запуске симуляции\n")
        except Exception as e:
            print(f"Ошибка при запуске симуляции: {e}")
            messagebox.showerror("Ошибка", f"Не удалось запустить симуляцию: {e}")

    def stop_simulation(self):
        """Остановка симуляции"""
        try:
            self.animation_running = False
            if self.client.stop_simulation():
                self.start_button.config(state='normal')
                self.stop_button.config(state='disabled')  # Деактивируем кнопку стоп
                self.restart_button.config(state='normal')
                self.log_text.insert(tk.END, "Симуляция остановлена\n")
            else:
                self.log_text.insert(tk.END, "Ошибка при остановке симуляции\n")
        except Exception as e:
            print(f"Ошибка при остановке симуляции: {e}")
            messagebox.showerror("Ошибка", f"Не удалось остановить симуляцию: {e}")

    def restart_simulation(self):
        """Перезапуск симуляции с новыми параметрами"""
        try:
            # Останавливаем текущую симуляцию
            self.stop_simulation()
            time.sleep(0.5)  # Даем время на полную остановку
            
            # Очищаем график
            if hasattr(self, 'particles_plot') and self.particles_plot:
                self.particles_plot.remove()
            
            # Создаем новый scatter plot
            self.particles_plot = self.ax.scatter([], [], [], c='b', marker='o', alpha=0.6)
            self.canvas.draw()
            
            # Получаем текущие настройки
            settings = {
                'temperature': self.get_slider_value(self.temperature_slider, 1e1, 1e4),
                'viscosity': self.get_slider_value(self.viscosity_slider, 1e-5, 1e-1),
                'size': self.get_slider_value(self.size_slider, 1e-9, 1e-4),
                'mass': self.get_slider_value(self.mass_slider, 1e-21, 1e-15),
                'frequency': int(self.get_slider_value(self.frequency_slider, 1e0, 1e6))
            }
            
            # Отправляем новые настройки
            if self.client.send_settings(settings):
                # Запускаем симуляцию с новыми параметрами
                if self.client.start_simulation():
                    self.animation_running = True
                    self.start_button.config(state='disabled')
                    self.stop_button.config(state='normal')
                    self.restart_button.config(state='normal')
                    self.log_text.insert(tk.END, "Симуляция успешно перезапущена\n")
                else:
                    self.log_text.insert(tk.END, "Ошибка при запуске симуляции\n")
            else:
                self.log_text.insert(tk.END, "Ошибка при отправке настроек\n")
                
        except Exception as e:
            print(f"Ошибка при перезапуске симуляции: {e}")
            self.log_text.insert(tk.END, f"Ошибка при перезапуске симуляции: {e}\n")

    def on_closing(self):
        """Обработчик закрытия окна."""
        # Закрываем соединение с клиентом
        if hasattr(self, 'client') and self.client:
            try:
                self.client.close()
            except Exception as e:
                print(f"Ошибка при закрытии соединения: {e}")
        
        # Закрываем matplotlib figure, чтобы освободить ресурсы
        try:
            plt.close('all')
        except Exception as e:
            print(f"Ошибка при закрытии графиков: {e}")
        
        # Закрываем основное окно
        self.root.quit()
        self.root.destroy()
        
# Основная логика для запуска приложения
# if __name__ == "__main__":
#     client = Client()
#     gui = SimulationGUI(client)
#     gui.mainloop()
