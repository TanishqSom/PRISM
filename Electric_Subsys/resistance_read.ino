// resistance_read.ino
// Simple analog read of electrode node and LDR.
// Sends "LDR,Electrode\n" via Serial at 115200 baud.

const int LDR_PIN = A0;         // LDR voltage divider node
const int ELECT_PIN = A1;       // Electrode node (between series resistor and electrode)
const unsigned long SAMPLE_MS = 50; // 20 Hz sampling

unsigned long last = 0;

void setup() {
  Serial.begin(115200);
  delay(200);
  Serial.println("ARDUINO_READY");
}

void loop() {
  unsigned long now = millis();
  if (now - last >= SAMPLE_MS) {
    last = now;
    int ldr = analogRead(LDR_PIN);       // 0-1023
    int elec = analogRead(ELECT_PIN);    // 0-1023
    Serial.print(ldr);
    Serial.print(",");
    Serial.println(elec);
  }
}
