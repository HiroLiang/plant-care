#include "sht31.h"

#define SHT31_I2C_ADDR   (0x44U << 1)  /* 7-bit addr 0x44, shifted for HAL */
#define SHT31_MEAS_DELAY_MS  15U

HAL_StatusTypeDef SHT31_Read(I2C_HandleTypeDef *hi2c, SHT31_Data *out)
{
    HAL_StatusTypeDef ret;
    uint8_t cmd[2] = {0x24, 0x00};  /* single-shot, medium repeatability, no clock-stretch */
    uint8_t buf[6];
    uint16_t raw_t, raw_h;

    ret = HAL_I2C_Master_Transmit(hi2c, SHT31_I2C_ADDR, cmd, sizeof(cmd), HAL_MAX_DELAY);
    if (ret != HAL_OK) {
        out->status = 1;
        return ret;
    }

    HAL_Delay(SHT31_MEAS_DELAY_MS);

    ret = HAL_I2C_Master_Receive(hi2c, SHT31_I2C_ADDR, buf, sizeof(buf), HAL_MAX_DELAY);
    if (ret != HAL_OK) {
        out->status = 1;
        return ret;
    }

    raw_t = ((uint16_t)buf[0] << 8) | buf[1];
    raw_h = ((uint16_t)buf[3] << 8) | buf[4];

    out->temperature = 175.0f * (float)raw_t / 65535.0f - 45.0f;
    out->humidity    = 100.0f * (float)raw_h / 65535.0f;
    out->status      = 0;

    return HAL_OK;
}
