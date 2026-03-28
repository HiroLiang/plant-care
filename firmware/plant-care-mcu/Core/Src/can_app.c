#include "can_app.h"
#include <string.h>

/* CAN ID = (node_id << 7) | data_type */
#define CAN_ID_TEMP_HUM    ((MCU_NODE_ID << 7) | 0x03U)  /* 0x83 */
#define CAN_ID_HEARTBEAT   ((MCU_NODE_ID << 7) | 0x22U)  /* 0xA2 */

HAL_StatusTypeDef CAN_App_Init(CAN_HandleTypeDef *hcan)
{
    CAN_FilterTypeDef filter = {0};
    filter.FilterBank           = 0;
    filter.FilterMode           = CAN_FILTERMODE_IDMASK;
    filter.FilterScale          = CAN_FILTERSCALE_32BIT;
    filter.FilterIdHigh         = 0x0000;
    filter.FilterIdLow          = 0x0000;
    filter.FilterMaskIdHigh     = 0x0000;  /* mask = 0 → accept all */
    filter.FilterMaskIdLow      = 0x0000;
    filter.FilterFIFOAssignment = CAN_RX_FIFO0;
    filter.FilterActivation     = ENABLE;

    HAL_StatusTypeDef ret = HAL_CAN_ConfigFilter(hcan, &filter);
    if (ret != HAL_OK) return ret;

    return HAL_CAN_Start(hcan);
}

HAL_StatusTypeDef CAN_Send_TempHum(CAN_HandleTypeDef *hcan, float temp, float hum, uint8_t status)
{
    CAN_TxHeaderTypeDef header = {0};
    header.StdId = CAN_ID_TEMP_HUM;
    header.IDE   = CAN_ID_STD;
    header.RTR   = CAN_RTR_DATA;
    header.DLC   = 5;

    /* Pack little-endian: int16 temp*100, uint16 hum*100, uint8 status */
    uint8_t payload[5];
    int16_t  t100 = (int16_t)(temp * 100.0f);
    uint16_t h100 = (uint16_t)(hum  * 100.0f);
    memcpy(&payload[0], &t100, 2);
    memcpy(&payload[2], &h100, 2);
    payload[4] = status;

    uint32_t mailbox;
    return HAL_CAN_AddTxMessage(hcan, &header, payload, &mailbox);
}

HAL_StatusTypeDef CAN_Send_Heartbeat(CAN_HandleTypeDef *hcan, uint8_t status, uint16_t voltage_mv, uint32_t uptime_s)
{
    CAN_TxHeaderTypeDef header = {0};
    header.StdId = CAN_ID_HEARTBEAT;
    header.IDE   = CAN_ID_STD;
    header.RTR   = CAN_RTR_DATA;
    header.DLC   = 8;

    /* Pack little-endian: uint8 node_id, uint8 status, uint16 voltage_mV, uint32 uptime_s */
    uint8_t payload[8];
    payload[0] = MCU_NODE_ID;
    payload[1] = status;
    memcpy(&payload[2], &voltage_mv, 2);
    memcpy(&payload[4], &uptime_s,   4);

    uint32_t mailbox;
    return HAL_CAN_AddTxMessage(hcan, &header, payload, &mailbox);
}
