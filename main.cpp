#include <string.h>
#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_wifi.h"
#include "esp_event.h"
#include "esp_log.h"
#include "nvs_flash.h"
#include "mqtt_client.h"
#include "esp_netif.h"
#include "lwip/inet.h"
#include "ping/ping_sock.h"

static const char *TAG = "mqtt_example";

#define WIFI_SSID "CMU-DEVICE"
#define MQTT_BROKER_URI "mqtt://172.26.49.86"
#define MQTT_TOPIC "test/topic"
#define TARGET_IP_ADDRESS "172.26.49.243"

static esp_mqtt_client_handle_t mqtt_client;

static void wifi_event_handler(void* arg, esp_event_base_t event_base,
                               int32_t event_id, void* event_data)
{
    if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_START) {
        esp_wifi_connect();
        ESP_LOGI(TAG, "Connecting...");
    } else if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_DISCONNECTED) {
        ESP_LOGI(TAG, "Disconnected. Retrying...");
        esp_wifi_connect();
    } else if (event_base == IP_EVENT && event_id == IP_EVENT_STA_GOT_IP) {
        ip_event_got_ip_t* event = (ip_event_got_ip_t*) event_data;
        ESP_LOGI(TAG, "Connected with IP Address: " IPSTR, IP2STR(&event->ip_info.ip));

        esp_mqtt_client_start(mqtt_client);
    }
}

static void mqtt_event_handler(void *handler_args, esp_event_base_t base, int32_t event_id, void *event_data)
{
    ESP_LOGI(TAG, "MQTT event id: %ld", event_id);
    if (event_id == MQTT_EVENT_CONNECTED) {
        ESP_LOGI(TAG, "MQTT connected. Publishing message...");
        esp_mqtt_client_publish(mqtt_client, MQTT_TOPIC, "ESP CONNECTED", 0, 1, 0);
    }
}

static void ping_task(void *pvParameter)
{
    esp_ping_config_t ping_config = ESP_PING_DEFAULT_CONFIG();
    ip_addr_t target_addr;
    ipaddr_aton(TARGET_IP_ADDRESS, &target_addr);
    ping_config.target_addr = target_addr;
    ping_config.count = 1;
    ping_config.interval_ms = 1000;

    esp_ping_callbacks_t cbs = {};
    esp_ping_handle_t ping;

    esp_ping_new_session(&ping_config, &cbs, &ping);

    char message[64];
    uint32_t elapsed_time_ms;

    while (true) {
        esp_ping_start(ping);
        vTaskDelay(pdMS_TO_TICKS(1500));  // Wait for ping to complete

        esp_ping_get_profile(ping, ESP_PING_PROF_DURATION, &elapsed_time_ms, sizeof(elapsed_time_ms));
        snprintf(message, sizeof(message), "Ping %s: %lu ms", TARGET_IP_ADDRESS, elapsed_time_ms);
        ESP_LOGI(TAG, "%s", message);
        esp_mqtt_client_publish(mqtt_client, MQTT_TOPIC, message, 0, 1, 0);

        vTaskDelay(pdMS_TO_TICKS(2000));  // Publish every 2 seconds
    }

    esp_ping_delete_session(ping);
}

extern "C" void app_main()
{
    nvs_flash_init();

    ESP_ERROR_CHECK(esp_netif_init());
    ESP_ERROR_CHECK(esp_event_loop_create_default());

    esp_netif_create_default_wifi_sta();

    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&cfg));

    esp_event_handler_instance_t instance_any_id;
    esp_event_handler_instance_t instance_got_ip;

    ESP_ERROR_CHECK(esp_event_handler_instance_register(WIFI_EVENT,
                                                        ESP_EVENT_ANY_ID,
                                                        &wifi_event_handler,
                                                        NULL,
                                                        &instance_any_id));
    ESP_ERROR_CHECK(esp_event_handler_instance_register(IP_EVENT,
                                                        IP_EVENT_STA_GOT_IP,
                                                        &wifi_event_handler,
                                                        NULL,
                                                        &instance_got_ip));

    wifi_config_t wifi_config = {};
    strcpy((char*)wifi_config.sta.ssid, WIFI_SSID);
    wifi_config.sta.threshold.authmode = WIFI_AUTH_OPEN;

    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
    ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_STA, &wifi_config));
    ESP_ERROR_CHECK(esp_wifi_start());

    ESP_LOGI(TAG, "wifi_init_sta finished.");

    esp_mqtt_client_config_t mqtt_cfg = {};
    mqtt_cfg.broker.address.uri = MQTT_BROKER_URI;

    mqtt_client = esp_mqtt_client_init(&mqtt_cfg);
    esp_mqtt_client_register_event(mqtt_client, MQTT_EVENT_ANY, mqtt_event_handler, NULL);

    xTaskCreate(&ping_task, "ping_task", 4096, NULL, 5, NULL);

    while (true) {
        vTaskDelay(pdMS_TO_TICKS(1000));
    }
}




