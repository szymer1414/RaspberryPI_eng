#Komentarze są losowo z chatugpt więc idk czy są dobre a nie mam siły sprawdzać


# Importowanie modułów i klas z biblioteki Kivy niezbędnych do tworzenia interfejsu użytkownika
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.slider import Slider
from kivy.uix.checkbox import CheckBox
from kivy.uix.label import Label
from kivy.clock import Clock
import matplotlib.pyplot as plt
from kivy.core.window import Window
from kivy.garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg
from datetime import datetime
from kivy.uix.boxlayout import BoxLayout
from kivy.graphics import Color, Line
from kivy.uix.popup import Popup
import time
from time import sleep
from kivy.uix.screenmanager import SlideTransition
from kivy.config import Config
#Config.set('graphics', 'width', '1600') 
#Config.set('graphics', 'height', '1000')  
import serial
import random

uart_connection = serial.Serial ("/dev/ttyAMA0", 9600)
Window.size = (1600, 1000)
#Window.fullscreen = True

# Inicjalizacja zmiennych do przechowywania danych i ustawień
mode = 0
global_vital_capacity = 0

connection_status = 0
data_to_send = [0]*9
volume = 0
pressure = 0
PEEP = 1
inhale_exhale_ratio = 1
breath_per_minute = 1
oxygen = 0
flow = 0
inhale_time = 0
exhale_time = 0

# Global variables to store popup values
global_age = 30
global_height = 160
global_mode = 1  # Default value
global_sex = 1  # Default value

# Ustawienie początkowego czasu
time_0 = datetime.now()

write_timeout = 1
#funkcje do kontroli zegara do komunikacji UART

def clear_uart_buffer(dt):
        if uart_connection.in_waiting:
                uart_connection.reset_input_buffer()
Clock.schedule_interval(clear_uart_buffer, 10)

def start_graph_update():
        Clock.schedule_interval(Graph_layout.update_data_instance, 0.1)
def stop_graph_update():
        Clock.unschedule(Graph_layout.update_data_instance)

class CheckboxPopup(Popup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = 'Ustawienia Stałe'
        self.size_hint = (None, None)
        self.size = (1000, 800)
        self.auto_dismiss = False
        self.background_color = [0, 0, 2, 1]
        self.overlay_color = [0, 0, 0, 0.7]
        self.content = Checkbox_layout()
        close_button = Button(text='Zapisz', font_size= 30, bold=True,size_hint=(1, 0.2))
        close_button.bind(on_release=self.dismiss)
        self.content.add_widget(close_button)
        self.bind(on_open=self.hide_widgets)
        self.bind(on_dismiss=self.show_widgets)
        
        # Wyłącz wszystkie przyciski i slidery na ekranie podczas otwierania Popup
        self.bind(on_open=self.disable_settings)
        # Włącz ponownie wszystkie przyciski i slidery na ekranie po zamknięciu Popup
        self.bind(on_dismiss=self.enable_settings)

    def disable_settings(self, *args):
        # Iterujemy przez wszystkie widgety na ekranie ustawień i je wyłączamy
        for widget in App.get_running_app().root.get_screen('settings_screen').walk():
            if isinstance(widget, (Button, Slider)):
                widget.disabled = True

    def enable_settings(self, *args):
        # Iterujemy przez wszystkie widgety na ekranie ustawień i je włączamy
        for widget in App.get_running_app().root.get_screen('settings_screen').walk():
            if isinstance(widget, (Button, Slider)):
                widget.disabled = False
    def hide_widgets(self, *args):
        # Ukryj widgety na ekranie settings
        for widget in App.get_running_app().root.get_screen('settings_screen').walk():
            widget.opacity = 0  # Ustaw przezroczystość na 0

    def show_widgets(self, *args):
        # Pokaż widgety na ekranie settings
        for widget in App.get_running_app().root.get_screen('settings_screen').walk():
            widget.opacity = 1

    def vital_capacity_calc(self, *args):
        global global_vital_capacity
        if (global_sex == 1):
                global_vital_capacity = int(self.content.height_slider.value * (21.78 - (0.101 * self.content.age_slider.value)))
        else:
                global_vital_capacity = int(self.content.height_slider.value * (27.63 - (0.112 * self.content.age_slider.value)))
                
    def on_dismiss(self):
        global global_mode, global_height, global_age, global_sex
 
        global_height = self.content.height_slider.value
        global_age = self.content.age_slider.value
        global_sex = 1 if self.content.sex_checkbox_mezczyzna.active else 0
        global_mode = 1 if self.content.mode_checkbox_cisnienie.active else 0
        
        self.vital_capacity_calc()
        super().on_dismiss()

 # Konstruktor dla klasy BoxLayout z komponentami do wyboru opcji
class Checkbox_layout(BoxLayout):
    def __init__(self, **kwargs):
        global global_mode, global_sex
        
        super(Checkbox_layout, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 60
        self.spacing = 40
    
        # Initialize Checkboxes
        self.mode_checkbox_cisnienie = CheckBox(group='mode', active=(global_mode == 1), allow_no_selection=False, color=[1,1,1,5])
        self.mode_checkbox_objetosc = CheckBox(group='mode', active=(global_mode == 0), allow_no_selection=False, color=[1,1,1,5])
        self.sex_checkbox_mezczyzna = CheckBox(group='sex', active=(global_sex == 1), allow_no_selection=False, color=[1,1,1,5])
        self.sex_checkbox_kobieta = CheckBox(group='sex', active=(global_sex == 0), allow_no_selection=False, color=[1,1,1,5])

        # Initialize Sliders
        self.age_slider = Slider(min=0, max=99, value=global_age, size_hint_y=None, height=50)
        self.height_slider = Slider(min=120, max=200, value=global_height, size_hint_y=None, height=50)

        # Bind the sliders to the label update function
        self.age_slider.bind(value=self.update_slider_labels)
        self.height_slider.bind(value=self.update_slider_labels)

        # Create the layout for sliders with labels
        sliders_layout = GridLayout(cols=2, size_hint=(1, None), height='100dp', spacing=30)
        self.age_label = Label(text=f'Wiek: {int(self.age_slider.value)}', font_size= 24, size_hint_y=None, height=50)
        self.height_label = Label(text=f'Wzrost [cm]: {int(self.height_slider.value)}', font_size= 24, size_hint_y=None, height=50)

        sliders_layout.add_widget(self.age_label)
        sliders_layout.add_widget(self.age_slider)
        sliders_layout.add_widget(self.height_label)
        sliders_layout.add_widget(self.height_slider)

        # Create and add the layouts for gender and mode
        top_container = BoxLayout(orientation='horizontal', size_hint_y=0.6)
        top_container.add_widget(self.create_gender_layout())
        top_container.add_widget(self.create_mode_layout())

        # Add all components to the main layout
        self.add_widget(top_container)
        self.add_widget(sliders_layout)

        # Bind mode checkboxes to the mode change handler
        self.mode_checkbox_cisnienie.bind(active=self.on_mode_change)
        self.mode_checkbox_objetosc.bind(active=self.on_mode_change)
#
    def on_mode_change(self, checkbox, value):
        if value:  # Check if the checkbox is being activated
            global global_mode
            global_mode = 1 if checkbox == self.mode_checkbox_cisnienie else 0
            App.get_running_app().root.get_screen('settings_screen').settings_layout.reset_variable_slider()
        settings_layout = App.get_running_app().root.get_screen('settings_screen').settings_layout


    def update_slider_labels(self, instance, value):
        # Updates the labels with the slider values
        self.age_label.text = f'Wiek: {int(self.age_slider.value)}'
        self.height_label.text = f'Wzrost [cm]: {int(self.height_slider.value)}'

    def create_gender_layout(self):
        gender_layout = GridLayout(cols=2, size_hint_x=0.5)
        gender_layout.add_widget(Label(text='Płeć:', font_size=30, bold=True, size_hint_y=None, height=40))
        gender_layout.add_widget(Label())  # Empty space for alignment
        gender_layout.add_widget(self.sex_checkbox_mezczyzna)
        gender_layout.add_widget(Label(text='Mężczyzna',font_size= 24 ))
        gender_layout.add_widget(self.sex_checkbox_kobieta)
        gender_layout.add_widget(Label(text='Kobieta',font_size= 24))
        return gender_layout

    def create_mode_layout(self):
        mode_layout = GridLayout(cols=2, size_hint_x=0.5)
        mode_layout.add_widget(Label(text='Tryb:', font_size=30, bold=True, size_hint_y=None, height=40))
        mode_layout.add_widget(Label())  # Empty space for alignment
        mode_layout.add_widget(Label(text='Stałe ciśnienie',font_size= 24))
        mode_layout.add_widget(self.mode_checkbox_cisnienie)
        mode_layout.add_widget(Label(text='Stała objętość',font_size= 24))
        mode_layout.add_widget(self.mode_checkbox_objetosc)
        return mode_layout

    def dismiss_popup(self, instance):
        self.parent.dismiss()

    def go_to_next_screen(self, instance):
        self.parent.parent.current = 'settings_screen'


# Konstruktor dla klasy GridLayout z suwakami do ustawień
class Settings_layout(GridLayout):
    def __init__(self, **kwargs):
        super(Settings_layout, self).__init__(**kwargs)
        self.cols = 2 
        # Create the sliders and labels
        self.create_widgets()
        self.bind_sliders()

    def reset_variable_slider(self):
        """Reset the variable slider to 0."""
        self.variable_slider.value = 0
        self.update_labels(None, None)
        
    def create_widgets(self):
        # Initialize sliders and labels for various settings
        self.breath_per_minute_label = Label(text="Częstotliwość oddechów na minutę: 1", font_size= 30)
        self.breath_per_minute_slider = Slider(value=1, min=0, max=40,  step=1)

        self.ie_ratio_label = Label(text="I:E: 1", font_size= 30)
        self.ie_ratio_slider = Slider(value=1, min=0.1, max=4.0, step=0.1)

        self.peep_label = Label(text="PEEP: 1", font_size= 30)
        self.peep_slider = Slider(value=1, min=0, max=20, step=1)

        # This slider's range is variable and depends on the selected mode
        self.variable_label = Label(text="Ciśnienie: 0 cmH2O", font_size= 30)
        self.variable_slider = Slider(value_track=True, min=0, max=40, step=1)

        # Add the widgets to the GridLayout
        self.add_widget(self.breath_per_minute_label)
        self.add_widget(self.breath_per_minute_slider)
        self.add_widget(self.ie_ratio_label)
        self.add_widget(self.ie_ratio_slider)
        self.add_widget(self.peep_label)
        self.add_widget(self.peep_slider)
        self.add_widget(self.variable_label)
        self.add_widget(self.variable_slider)

    def bind_sliders(self):
        # Bind the sliders to a method for updating their corresponding labels
        self.breath_per_minute_slider.bind(value=self.update_labels)
        self.ie_ratio_slider.bind(value=self.update_labels)
        self.peep_slider.bind(value=self.update_labels)
        self.variable_slider.bind(value=self.update_labels)

    def update_labels(self, instance, value):
        global PEEP, breath_per_minute, inhale_exhale_ratio
        # Update the text of each label to display the value of its corresponding slider
        self.breath_per_minute_label.text = f"Częstotliwość oddechów na minutę: {int(self.breath_per_minute_slider.value)}"
        breath_per_minute = self.breath_per_minute_slider.value
        self.ie_ratio_label.text = f"I:E: {self.ie_ratio_slider.value:.1f}"
        inhale_exhale_ratio = self.ie_ratio_slider.value
        self.peep_label.text = f"PEEP: {int(self.peep_slider.value)}"
        PEEP = int(self.peep_slider.value)

        if global_mode == 1:
            self.variable_label.text = f"Ciśnienie: {int(self.variable_slider.value)} cmH2O"
            self.variable_slider.max = 40
            self.value_track_color=[0, 1, 0, 1]
            pressure = self.variable_slider.value
        elif global_mode == 0:
            self.variable_label.text = f"Objętość: {int(self.variable_slider.value)} ml"
            self.variable_slider.max = 500
            self.value_track_color=[0, 0, 1, 1]
            volume = self.variable_slider.value

 # Konstruktor dla klasy GridLayout do umieszczania wykresów (używając matplotlib)
class Graph_layout(GridLayout):
    def __init__(self, **kwargs):
        super(Graph_layout, self).__init__(**kwargs)
        
        Graph_layout.update_data_instance = self.update_data
        self.cols = 2
        self.rows = 2
        
        self.package_count = 0
        self.time_data =        [0]
        self.volume_data =      [0]
        self.pressure_data =    [0]
        self.flow_data =        [0]
        self.graph_widgets = []
        self.update_graphs()
        self.volume  =0
    def create_graph(self,x_data,y_data,custom_label,x_label,y_label):
        fig, ax = plt.subplots()
        ax.plot(x_data, y_data, label=custom_label)
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        ax.legend(loc='upper left')
        return FigureCanvasKivyAgg(fig)
        
    def update_graphs(self):
        self.graph_data = [
                (self.time_data, self.pressure_data,'Pressure over Time','Time','Pressure'),
                (self.time_data, self.flow_data,'Flow overTime','Time','Flow'),
                (self.time_data, self.volume_data,'Volume over Time','Time','Volume')]
        for widget in self.graph_widgets:
                self.remove_widget(widget)
        self.graph_widgets.clear()
        
        for data in self.graph_data:
                graph_widget = self.create_graph(*data)
                self.add_widget(graph_widget)
                self.graph_widgets.append(graph_widget)
                
    
    def read_from_uart (self):
        if uart_connection.in_waiting:
            #self.package_count +=1
            #if self.package_count ==1:
            for i in range(10):
              if int.from_bytes(uart_connection.read(),"big") == 255:      
                flow = int.from_bytes(uart_connection.read(),"big", signed = True)
                pressure = int.from_bytes(uart_connection.read(),"big")
                self.volume += 1
                try:
                        self.volume_data.append(self.volume)
                        self.pressure_data.append(pressure)
                        self.flow_data.append(flow)
                        self.time_data.append(self.time_data[-1]+0.1)
                except:
                        pass
                self.package_count = 0
                
    def update_data(self,dt):
        self.read_from_uart()
        if len(self.time_data) > 50:
                self.time_data = self.time_data[10:]
                self.volume_data=self.volume_data[10:]
                self.pressure_data= self.pressure_data[10:]
                self.flow_data = self.flow_data[10:]
        self.update_graphs()
        

class SettingsScreen(Screen):
    def __init__(self, **kwargs):
        super(SettingsScreen, self).__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical')

        # Create an instance of Settings_layout
        self.settings_layout = Settings_layout()

        # Navigation buttons
        nav_layout = self.create_nav_layout()

        # Add navigation and settings layout to the main layout
        self.layout.add_widget(nav_layout)
        self.layout.add_widget(self.settings_layout)

        # Show popup button
        self.show_popup_button = Button(text='Pokaż Ustawienia Dodatkowe', font_size= 40, size_hint_y=0.2)
        self.show_popup_button.bind(on_release=self.show_popup)
        self.layout.add_widget(self.show_popup_button)

        # Add the main layout to the screen
        self.add_widget(self.layout)

    def create_nav_layout(self):
        # Create a layout for navigation buttons
        nav_layout = BoxLayout(size_hint_y=0.2)
        self.settings_button = Button(text='Settings', disabled=True, font_size= 30)
        self.graph_button = Button(text='Graph', on_release=self.go_to_graph , font_size= 30)
        nav_layout.add_widget(self.settings_button)
        nav_layout.add_widget(self.graph_button)
        return nav_layout

    def write_on_uart(self):
        global PEEP, global_mode, breath_per_minute
        inhale_time = int((inhale_exhale_ratio * (60000/breath_per_minute)) / (1 + inhale_exhale_ratio))
        exhale_time = int((60000/breath_per_minute) - inhale_time)
        data_to_send[0] = 255
        data_to_send[1] = global_mode
        data_to_send[2] = inhale_time & 0xFF
        data_to_send[3] = (inhale_time >> 8) & 0xFF
        data_to_send[4] = exhale_time & 0xFF
        data_to_send[5] = (exhale_time >> 8) & 0xFF
        data_to_send[6] = PEEP
        data_to_send[7] = global_vital_capacity & 0xFF
        data_to_send[8] = (global_vital_capacity >> 8) & 0xFF

        uart_connection.write(bytes(data_to_send))
       
                        
    def go_to_graph(self, instance):
        self.write_on_uart()
        self.manager.transition = SlideTransition(direction='left')
        self.manager.current = 'graph_screen'
        graph_screen = self.manager.get_screen('graph_screen')
        graph_screen.settings_button.disabled = False
        graph_screen.graph_button.disabled = True
        start_graph_update()
                        
    def show_popup(self, instance):
        popup = CheckboxPopup()
        popup.open()

class GraphScreen(Screen):
    def __init__(self, **kwargs):
        super(GraphScreen, self).__init__(**kwargs)
        
        layout = BoxLayout(orientation='vertical')
        
        # Pole nawigacji z przyciskami
        nav_layout = self.create_nav_layout()
        # Dodanie wszystkiego do głównego layoutu
        layout.add_widget(nav_layout)
        layout.add_widget(Graph_layout())
        self.add_widget(layout)
        self.graph_layout = Graph_layout

        
    def create_nav_layout(self):
        # Create a layout for navigation buttons
        nav_layout = BoxLayout(size_hint_y=0.2)
        self.settings_button = Button(text='Settings', on_release=self.go_to_settings, font_size= 30)
        self.graph_button = Button(text='Graph', disabled=True, font_size= 30)  # Przycisk 'Graph' nieaktywny, bo jesteśmy na tej stronie
        nav_layout.add_widget(self.settings_button)
        nav_layout.add_widget(self.graph_button)
        return nav_layout
        
    def go_to_settings(self, instance):
        # Switch back to the settings screen and update button states
        self.manager.transition = SlideTransition(direction='right')
        self.manager.current = 'settings_screen'
        settings_screen = self.manager.get_screen('settings_screen')
        settings_screen.settings_button.disabled = True
        settings_screen.graph_button.disabled = False
        stop_graph_update()

# Główna klasa aplikacji ScreenManager z Kivy
class ControlApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(SettingsScreen(name='settings_screen'))
        sm.add_widget(GraphScreen(name='graph_screen'))
        self.show_checkbox_popup()
        return sm
    def show_checkbox_popup(self):
        popup = CheckboxPopup()
        popup.open()


# Uruchamianie aplikacji
if __name__ == '__main__':
    ControlApp().run()
