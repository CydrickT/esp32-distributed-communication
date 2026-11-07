#include <WiFi.h>
#include <WiFiUdp.h>
#include "secrets.h"

// UDP Settings
WiFiUDP udp;
const unsigned int udpPort = 4210;
char incomingPacket[255];
unsigned long lastSendTime = 0;

void setup() {
  // Initialize Serial Monitor at 115200 baud
  Serial.begin(115200);
  delay(1000);

  Serial.println("\n--- ESP32 UDP Broadcast Demo ---");
  Serial.println("1. Setting Wi-Fi Mode...");
  
  WiFi.mode(WIFI_STA);

  Serial.print("2. Connecting to Wi-Fi SSID: ");
  Serial.println(WIFI_SSID);

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  // Connection retry loop with visual progress
  int retries = 0;
  while (WiFi.status() != WL_CONNECTED && retries < 30) {
    delay(500);
    Serial.print(".");
    retries++;
  }

  Serial.println(); // Newline

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("3. Wi-Fi Connected Successfully!");
    Serial.print("   IP Address: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("3. Wi-Fi Connection Failed!");
    Serial.println("   Please check your SSID/Password in secrets.h.");
  }

  // Start UDP listener
  udp.begin(udpPort);
  Serial.printf("4. UDP server listening on port %d...\n\n", udpPort);
}

void loop() {
  // 1. LISTEN FOR INCOMING UDP MESSAGES
  int packetSize = udp.parsePacket();
  if (packetSize) {
    int len = udp.read(incomingPacket, 255);
    if (len > 0) {
      incomingPacket[len] = '\0';
    }

    // Ignore packets sent by this specific ESP32
    if (udp.remoteIP() != WiFi.localIP()) {
      Serial.printf("[RECV] Message from %s: %s\n", 
                    udp.remoteIP().toString().c_str(), 
                    incomingPacket);
    }
  }

  // 2. BROADCAST A MESSAGE EVERY 3 SECONDS
  if (millis() - lastSendTime > 3000) {
    lastSendTime = millis();

    if (WiFi.status() == WL_CONNECTED) {
      IPAddress broadcastIP = WiFi.localIP();
      broadcastIP[3] = 255; // Converts 192.168.1.X -> 192.168.1.255

      udp.beginPacket(broadcastIP, udpPort);
      udp.printf("Hello from ESP32 at %s!", WiFi.localIP().toString().c_str());
      udp.endPacket();

      Serial.println("[SENT] UDP Broadcast ping emitted.");
    } else {
      Serial.println("[WARN] Skipped broadcast: Wi-Fi Disconnected.");
    }
  }
}