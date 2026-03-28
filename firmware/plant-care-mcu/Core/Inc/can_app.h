#ifndef CAN_APP_H
#define CAN_APP_H

#include "main.h"

#define MCU_NODE_ID  0x01U

HAL_StatusTypeDef CAN_App_Init(CAN_HandleTypeDef *hcan);
HAL_StatusTypeDef CAN_Send_TempHum(CAN_HandleTypeDef *hcan, float temp, float hum, uint8_t status);
HAL_StatusTypeDef CAN_Send_Heartbeat(CAN_HandleTypeDef *hcan, uint8_t status, uint16_t voltage_mv, uint32_t uptime_s);

#endif /* CAN_APP_H */
