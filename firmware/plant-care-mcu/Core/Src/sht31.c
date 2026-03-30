#include "sht31.h"

#define SHT31_I2C_ADDR   (0x44U << 1)  /* 7-bit addr 0x44, shifted for HAL */
#define SHT31_MEAS_DELAY_MS  15U
#define SHT31_READY_TRIALS   2U
#define SHT31_READY_TIMEOUT_MS  50U

static uint8_t SHT31_CalculateCrc(const uint8_t *data, uint8_t length)
{
    uint8_t crc = 0xFFU;

    for (uint8_t i = 0; i < length; ++i) {
        crc ^= data[i];
        for (uint8_t bit = 0; bit < 8U; ++bit) {
            if ((crc & 0x80U) != 0U) {
                crc = (uint8_t)((crc << 1U) ^ 0x31U);
            } else {
                crc <<= 1U;
            }
        }
    }

    return crc;
}

HAL_StatusTypeDef SHT31_IsReady(I2C_HandleTypeDef *hi2c)
{
    return HAL_I2C_IsDeviceReady(hi2c, SHT31_I2C_ADDR, SHT31_READY_TRIALS, SHT31_READY_TIMEOUT_MS);
}

HAL_StatusTypeDef SHT31_Read(I2C_HandleTypeDef *hi2c, SHT31_Data *out)
{
    HAL_StatusTypeDef ret;
    uint8_t cmd[2] = {0x24, 0x00};  /* single-shot, medium repeatability, no clock-stretch */
    uint8_t buf[6];
    uint16_t raw_t, raw_h;

    ret = SHT31_IsReady(hi2c);
    if (ret != HAL_OK) {
        out->status = SHT31_STATUS_NOT_READY;
        return ret;
    }

    ret = HAL_I2C_Master_Transmit(hi2c, SHT31_I2C_ADDR, cmd, sizeof(cmd), HAL_MAX_DELAY);
    if (ret != HAL_OK) {
        out->status = SHT31_STATUS_I2C_TX_ERROR;
        return ret;
    }

    HAL_Delay(SHT31_MEAS_DELAY_MS);

    ret = HAL_I2C_Master_Receive(hi2c, SHT31_I2C_ADDR, buf, sizeof(buf), HAL_MAX_DELAY);
    if (ret != HAL_OK) {
        out->status = SHT31_STATUS_I2C_RX_ERROR;
        return ret;
    }

    if ((SHT31_CalculateCrc(&buf[0], 2U) != buf[2]) ||
        (SHT31_CalculateCrc(&buf[3], 2U) != buf[5])) {
        out->status = SHT31_STATUS_CRC_ERROR;
        return ret;
    }

    raw_t = ((uint16_t)buf[0] << 8) | buf[1];
    raw_h = ((uint16_t)buf[3] << 8) | buf[4];

    out->temperature = 175.0f * (float)raw_t / 65535.0f - 45.0f;
    out->humidity    = 100.0f * (float)raw_h / 65535.0f;
    out->status      = SHT31_STATUS_OK;

    return HAL_OK;
}
