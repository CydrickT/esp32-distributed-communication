import network
import espnow
import time
from machine import Pin, SPI
import st7789py as st7789  # pure-Python driver in st7789py.py
import vga1_8x8 as font  # Standard 8x8 bitmap font for the st7789 driver

class CYDTransceiver:
    def __init__(self, timer_delay=5000):
        self.timer_delay = timer_delay
        self.last_time = time.ticks_ms()
        self.line_y = 40
        
        # Initialize hardware components
        self._init_display()
        self._init_espnow()

    def _init_display(self):
        """Sets up the standalone ST7789 display wiring."""
        # Optional: control backlight via GPIO 21, or leave it tied to 3.3V on the module
        self.backlight = Pin(21, Pin.OUT)
        self.backlight.value(1) 

        # Initialize SPI using standard ESP32 VSPI pins (SCK=18, MOSI=23, MISO can be omitted/unused since display is write-only)
        self.spi = SPI(2, baudrate=40000000, sck=Pin(18), mosi=Pin(23))
        
        # Initialize ST7789 display matching your module pins
        self.tft = st7789.ST7789(
            self.spi, 
            240, 320, 
            reset=Pin(4, Pin.OUT), 
            dc=Pin(2, Pin.OUT), 
            cs=Pin(5, Pin.OUT), 
            rotation=1
        )
        
        self.draw_header()

    def _init_espnow(self):
        """Sets up Wi-Fi station mode and initializes ESP-NOW."""
        self.sta = network.WLAN(network.STA_IF)
        self.sta.active(True)
        self.sta.disconnect()

        self.e = espnow.ESPNow()
        self.e.active(True)

        self.broadcast_mac = b'\xff\xff\xff\xff\xff\xff'
        self.e.add_peer(self.broadcast_mac)
        
        print("ESP-NOW Transceiver Initialized...")

    def draw_header(self):
        """Clears the screen and draws the title header."""
        self.tft.fill(st7789.color565(0, 0, 0)) # Clear screen to black
        self.tft.text(font, "CYD ST7789 Transceiver", 10, 10, st7789.color565(255, 255, 0), st7789.color565(0, 0, 0))
        self.tft.hline(10, 25, 300, st7789.color565(255, 255, 255))

    def handle_receive(self):
        """Checks for incoming ESP-NOW packets and triggers display updates."""
        host, msg = self.e.recv(100) # Non-blocking check with 100ms timeout
        if host:
            mac_str = ":".join("{:02x}".format(b) for b in host)
            try:
                message_text = msg.decode('utf-8') if msg else ""
            except UnicodeError:
                message_text = repr(msg)  # MicroPython's decode() has no errors= option
            
            print(f"Packet received from {mac_str}: {message_text}")
            self.display_message(mac_str, message_text)

    def display_message(self, mac_str, message_text):
        """Renders incoming messages onto the CYD screen and handles vertical scrolling reset."""
        sender_info = f"From: {mac_str[-16:]}"
        content_info = f"Msg: {message_text}"
        
        # Render text using the ST7789 text method with font and background color
        self.tft.text(font, sender_info, 10, self.line_y, st7789.color565(0, 255, 255), st7789.color565(0, 0, 0))
        self.tft.text(font, content_info, 10, self.line_y + 12, st7789.color565(255, 255, 255), st7789.color565(0, 0, 0))
        
        self.line_y += 30
        
        # Reset position if we run out of vertical space
        if self.line_y > 200:
            self.draw_header()
            self.line_y = 40

    def handle_send(self):
        """Sends a periodic broadcast message based on the timer delay."""
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, self.last_time) > self.timer_delay:
            message = "Hello from ESP32 transceiver Number Two!"
            
            try:
                self.e.send(self.broadcast_mac, message.encode('utf-8'))
                print("Broadcast message sent successfully")
            except OSError as err:
                print("Error sending broadcast:", err)
                
            self.last_time = current_time

    def run(self):
        """Main execution loop."""
        while True:
            self.handle_receive()
            self.handle_send()

# --- Execution ---
if __name__ == "__main__":
    transceiver = CYDTransceiver(timer_delay=5000)
    transceiver.run()