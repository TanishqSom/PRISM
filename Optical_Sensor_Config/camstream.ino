

#include "esp_camera.h"
#include <WiFi.h>

// Replace with your network credentials
const char* ssid = "";
const char* password = "";

void startCameraServer();

void setup() {
  Serial.begin(115200);
  Serial.println();
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer   = LEDC_TIMER_0;
  config.pin_d0       = 5;
  config.pin_d1       = 18;
  config.pin_d2       = 19;
  config.pin_d3       = 21;
  config.pin_d4       = 36;
  config.pin_d5       = 39;
  config.pin_d6       = 34;
  config.pin_d7       = 35;
  config.pin_xclk     = 0;
  config.pin_pclk     = 22;
  config.pin_vsync    = 25;
  config.pin_href     = 23;
  config.pin_sscb_sda = 26;
  config.pin_sscb_scl = 27;
  config.pin_pwdn     = 32;
  config.pin_reset    = -1;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;

  // init with high resolution but you can lower for speed
  if(psramFound()){
    config.frame_size = FRAMESIZE_SVGA; // 800x600
    config.jpeg_quality = 12;
    config.fb_count = 2;
  } else {
    config.frame_size = FRAMESIZE_VGA; // 640x480
    config.jpeg_quality = 18;
    config.fb_count = 1;
  }

  // camera init
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed with error 0x%x", err);
    return;
  }

  WiFi.begin(ssid, password);
  Serial.printf("Connecting to %s ", ssid);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println();
  Serial.print("Camera Ready! Go to: http://");
  Serial.println(WiFi.localIP());

  startCameraServer();
  Serial.println("Camera Stream Ready");
}

void loop() {
  // nothing here; webserver handles streaming
}

/* --- startCameraServer implementation (standard) --- */
#include "esp_http_server.h"

static esp_err_t stream_handler(httpd_req_t *req){
  camera_fb_t * fb = NULL;
  esp_err_t res = ESP_OK;
  size_t _jpg_buf_len = 0;
  uint8_t * _jpg_buf = NULL;
  char * part_buf[64];
  static const char* _STREAM_CONTENT_TYPE = "multipart/x-mixed-replace;boundary=123456";
  static const char* _STREAM_BOUNDARY = "\r\n--123456\r\n";
  static const char* _STREAM_PART = "Content-Type: image/jpeg\r\nContent-Length: %u\r\n\r\n";

  res = httpd_resp_set_type(req, _STREAM_CONTENT_TYPE);
  if(res != ESP_OK) return res;

  while(true){
    fb = esp_camera_fb_get();
    if (!fb) {
      Serial.println("Camera capture failed");
      res = ESP_FAIL;
    } else {
      _jpg_buf = fb->buf;
      _jpg_buf_len = fb->len;
      size_t hlen = snprintf((char *)part_buf, 64, _STREAM_PART, (int)_jpg_buf_len);
      res = httpd_resp_send_chunk(req, _STREAM_BOUNDARY, strlen(_STREAM_BOUNDARY));
      res = httpd_resp_send_chunk(req, (const char *)part_buf, hlen);
      res = httpd_resp_send_chunk(req, (const char *)_jpg_buf, _jpg_buf_len);
      esp_camera_fb_return(fb);
      if(res != ESP_OK) break;
    }
    // small delay
    if(!psramFound()) delay(50);
  }
  return res;
}

void startCameraServer(){
  httpd_config_t config = HTTPD_DEFAULT_CONFIG();
  httpd_uri_t stream_uri = {
    .uri       = "/stream",
    .method    = HTTP_GET,
    .handler   = stream_handler,
    .user_ctx  = NULL
  };
  if (httpd_start(&config, &config) == ESP_OK) {
    httpd_register_uri_handler(config.server, &stream_uri);
  }
}
