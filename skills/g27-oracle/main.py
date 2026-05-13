#!/usr/bin/env python3
'''
G27 Oracle Trading System - Kivy Mobile App
'''

import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput

class G27OracleApp(App):
    def build(self):
        main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Title
        title = Label(text='G27 Oracle Trading', size_hint_y=0.1, font_size='20sp')
        main_layout.add_widget(title)
        
        # Status
        status = Label(text='System Ready', size_hint_y=0.1)
        main_layout.add_widget(status)
        
        # Run Button
        run_btn = Button(text='Run G27 Oracle', size_hint_y=0.1)
        run_btn.bind(on_press=lambda x: self.run_oracle())
        main_layout.add_widget(run_btn)
        
        # Log area
        log_label = Label(text='Log output:', size_hint_y=0.1)
        main_layout.add_widget(log_label)
        
        self.log_area = TextInput(text='G27 Oracle Trading System
', multiline=True, size_hint_y=0.5, readonly=True)
        main_layout.add_widget(self.log_area)
        
        return main_layout
    
    def run_oracle(self):
        self.log_area.text += 'Running G27 Oracle...
'
        # Import and run the main script
        try:
            import sys
            sys.path.insert(0, 'scripts')
            exec(open('scripts/g27_autonomous.py').read())
        except Exception as e:
            self.log_area.text += f'Error: {e}
'

if __name__ == '__main__':
    G27OracleApp().run()
