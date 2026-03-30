#ifndef SHT31_H
#define SHT31_H

#include "main.h"

typedef enum {
    SHT31_STATUS_OK = 0,
    SHT31_STATUS_I2C_TX_ERROR = 1,
    SHT31_STATUS_I2C_RX_ERROR = 2,
    SHT31_STATUS_CRC_ERROR = 3,
    SHT31_STATUS_NOT_READY = 4,
} SHT31_Status;

typedef struct {
    float temperature;
    float humidity;
    uint8_t status;
} SHT31_Data;

HAL_StatusTypeDef SHT31_IsReady(I2C_HandleTypeDef *hi2c);
HAL_StatusTypeDef SHT31_Read(I2C_HandleTypeDef *hi2c, SHT31_Data *out);

#endif /* SHT31_H */
