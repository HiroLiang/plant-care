#ifndef SHT31_H
#define SHT31_H

#include "main.h"

typedef struct {
    float temperature;
    float humidity;
    uint8_t status;  /* 0 = OK, 1 = error */
} SHT31_Data;

HAL_StatusTypeDef SHT31_Read(I2C_HandleTypeDef *hi2c, SHT31_Data *out);

#endif /* SHT31_H */
