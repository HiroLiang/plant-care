/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.c
  * @brief          : Main program body
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2026 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  *
  ******************************************************************************
  */
/* USER CODE END Header */
/* Includes ------------------------------------------------------------------*/
#include "main.h"
#include "can.h"
#include "i2c.h"
#include "usart.h"
#include "gpio.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
#include <stdio.h>
#include "sht31.h"
#include "can_app.h"
/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */

/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */

/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/

/* USER CODE BEGIN PV */

/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
/* USER CODE BEGIN PFP */
static void PrintBootBanner(HAL_StatusTypeDef recovery_status,
                            HAL_StatusTypeDef probe_44,
                            HAL_StatusTypeDef probe_45);
static void PrintI2cSnapshot(const char *tag);
static void PrintSht31Reading(const SHT31_Data *data);
static void PrintSht31Error(HAL_StatusTypeDef hal_status, uint8_t sensor_status);
static const char *Sht31StatusToString(uint8_t status);
static const char *HalStatusToString(HAL_StatusTypeDef status);
static const char *I2cStateToString(HAL_I2C_StateTypeDef state);
static const char *PinStateToString(GPIO_PinState state);
static long ToCentiUnits(float value);

/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */
  int __io_putchar(int ch)
  {
    HAL_UART_Transmit(&huart2, (uint8_t *)&ch, 1, HAL_MAX_DELAY);
    return ch;
  }
/* USER CODE END 0 */

/**
  * @brief  The application entry point.
  * @retval int
  */
int main(void)
{

  /* USER CODE BEGIN 1 */

  /* USER CODE END 1 */

  /* MCU Configuration--------------------------------------------------------*/

  /* Reset of all peripherals, Initializes the Flash interface and the Systick. */
  HAL_Init();

  /* USER CODE BEGIN Init */

  /* USER CODE END Init */

  /* Configure the system clock */
  SystemClock_Config();

  /* USER CODE BEGIN SysInit */

  /* USER CODE END SysInit */

  /* Initialize all configured peripherals */
  MX_GPIO_Init();
  MX_USART2_UART_Init();
  GPIO_PinState pre_recover_scl = GPIO_PIN_RESET;
  GPIO_PinState pre_recover_sda = GPIO_PIN_RESET;
  HAL_StatusTypeDef recovery_status;
  HAL_StatusTypeDef probe_44;
  HAL_StatusTypeDef probe_45;

  I2C1_GetBusLevels(&pre_recover_scl, &pre_recover_sda);
  recovery_status = I2C1_AttemptBusRecovery();
  MX_CAN1_Init();
  MX_I2C1_Init();
  /* USER CODE BEGIN 2 */
  probe_44 = HAL_I2C_IsDeviceReady(&hi2c1, (0x44U << 1), 2U, 50U);
  probe_45 = HAL_I2C_IsDeviceReady(&hi2c1, (0x45U << 1), 2U, 50U);
  printf("\r\npre-recover bus scl=%s sda=%s\r\n",
         PinStateToString(pre_recover_scl),
         PinStateToString(pre_recover_sda));
  PrintBootBanner(recovery_status, probe_44, probe_45);
  PrintI2cSnapshot("boot");
//  if (CAN_App_Init(&hcan1) != HAL_OK) {
//    Error_Handler();
//  }
  /* USER CODE END 2 */

  /* Infinite loop */
  /* USER CODE BEGIN WHILE */
  uint32_t last_sensor_tick = 0;
  uint32_t last_hb_tick = 0;
  const uint32_t start_tick = HAL_GetTick();
  uint8_t heartbeat_status = 0;

  while (1)
  {
    uint32_t now = HAL_GetTick();

    /* SHT31 poll every 2 s */
    if ((now - last_sensor_tick) >= 2000U) {
      SHT31_Data data = {0};
      HAL_StatusTypeDef sensor_ret;

      last_sensor_tick = now;
      HAL_GPIO_TogglePin(LD2_GPIO_Port, LD2_Pin);

      sensor_ret = SHT31_Read(&hi2c1, &data);
      heartbeat_status = data.status;

      if (sensor_ret == HAL_OK) {
        PrintSht31Reading(&data);
      } else {
        PrintSht31Error(sensor_ret, data.status);
      }
    }

    /* Heartbeat/CAN bring-up is intentionally disabled for sensor-only debug. */
    (void)last_hb_tick;
    (void)start_tick;
    HAL_Delay(50);
    /* USER CODE END WHILE */

    /* USER CODE BEGIN 3 */
  }
  /* USER CODE END 3 */
}

/**
  * @brief System Clock Configuration
  * @retval None
  */
void SystemClock_Config(void)
{
  RCC_OscInitTypeDef RCC_OscInitStruct = {0};
  RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};

  /** Configure the main internal regulator output voltage
  */
  __HAL_RCC_PWR_CLK_ENABLE();
  __HAL_PWR_VOLTAGESCALING_CONFIG(PWR_REGULATOR_VOLTAGE_SCALE3);

  /** Initializes the RCC Oscillators according to the specified parameters
  * in the RCC_OscInitTypeDef structure.
  */
  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSI;
  RCC_OscInitStruct.HSIState = RCC_HSI_ON;
  RCC_OscInitStruct.HSICalibrationValue = RCC_HSICALIBRATION_DEFAULT;
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_ON;
  RCC_OscInitStruct.PLL.PLLSource = RCC_PLLSOURCE_HSI;
  RCC_OscInitStruct.PLL.PLLM = 16;
  RCC_OscInitStruct.PLL.PLLN = 336;
  RCC_OscInitStruct.PLL.PLLP = RCC_PLLP_DIV4;
  RCC_OscInitStruct.PLL.PLLQ = 2;
  RCC_OscInitStruct.PLL.PLLR = 2;
  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK)
  {
    Error_Handler();
  }

  /** Initializes the CPU, AHB and APB buses clocks
  */
  RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK|RCC_CLOCKTYPE_SYSCLK
                              |RCC_CLOCKTYPE_PCLK1|RCC_CLOCKTYPE_PCLK2;
  RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
  RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
  RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV2;
  RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV1;

  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_2) != HAL_OK)
  {
    Error_Handler();
  }
}

/* USER CODE BEGIN 4 */
static void PrintBootBanner(HAL_StatusTypeDef recovery_status,
                            HAL_StatusTypeDef probe_44,
                            HAL_StatusTypeDef probe_45)
{
  printf("\r\n=== plant-care-mcu boot ===\r\n");
  printf("uart=USART2@115200 i2c=I2C1(PB6/PB7) addr_default=0x44 recover=%s probe44=%s probe45=%s\r\n",
         HalStatusToString(recovery_status),
         HalStatusToString(probe_44),
         HalStatusToString(probe_45));
}

static void PrintI2cSnapshot(const char *tag)
{
  GPIO_PinState scl = GPIO_PIN_RESET;
  GPIO_PinState sda = GPIO_PIN_RESET;

  I2C1_GetBusLevels(&scl, &sda);

  printf("i2c %s scl=%s sda=%s state=%s(0x%02X) err=0x%08lX\r\n",
         tag,
         PinStateToString(scl),
         PinStateToString(sda),
         I2cStateToString(HAL_I2C_GetState(&hi2c1)),
         (unsigned int)HAL_I2C_GetState(&hi2c1),
         HAL_I2C_GetError(&hi2c1));
}

static void PrintSht31Reading(const SHT31_Data *data)
{
  long temp_centi = ToCentiUnits(data->temperature);
  long hum_centi = ToCentiUnits(data->humidity);
  long temp_abs = (temp_centi < 0) ? -temp_centi : temp_centi;

  printf("sht31 ok temp=%ld.%02ldC hum=%ld.%02ld%% status=%s\r\n",
         temp_centi / 100L,
         temp_abs % 100L,
         hum_centi / 100L,
         hum_centi % 100L,
         Sht31StatusToString(data->status));
}

static void PrintSht31Error(HAL_StatusTypeDef hal_status, uint8_t sensor_status)
{
  printf("sht31 err hal=%d status=%s\r\n",
         (int)hal_status,
         Sht31StatusToString(sensor_status));
  PrintI2cSnapshot("error");
}

static const char *Sht31StatusToString(uint8_t status)
{
  switch (status) {
    case SHT31_STATUS_OK:
      return "ok";
    case SHT31_STATUS_I2C_TX_ERROR:
      return "i2c_tx";
    case SHT31_STATUS_I2C_RX_ERROR:
      return "i2c_rx";
    case SHT31_STATUS_CRC_ERROR:
      return "crc";
    case SHT31_STATUS_NOT_READY:
      return "not_ready";
    default:
      return "unknown";
  }
}

static const char *HalStatusToString(HAL_StatusTypeDef status)
{
  switch (status) {
    case HAL_OK:
      return "ok";
    case HAL_ERROR:
      return "error";
    case HAL_BUSY:
      return "busy";
    case HAL_TIMEOUT:
      return "timeout";
    default:
      return "unknown";
  }
}

static const char *I2cStateToString(HAL_I2C_StateTypeDef state)
{
  switch (state) {
    case HAL_I2C_STATE_RESET:
      return "reset";
    case HAL_I2C_STATE_READY:
      return "ready";
    case HAL_I2C_STATE_BUSY:
      return "busy";
    case HAL_I2C_STATE_BUSY_TX:
      return "busy_tx";
    case HAL_I2C_STATE_BUSY_RX:
      return "busy_rx";
    case HAL_I2C_STATE_LISTEN:
      return "listen";
    case HAL_I2C_STATE_BUSY_TX_LISTEN:
      return "busy_tx_listen";
    case HAL_I2C_STATE_BUSY_RX_LISTEN:
      return "busy_rx_listen";
    case HAL_I2C_STATE_ABORT:
      return "abort";
    case HAL_I2C_STATE_TIMEOUT:
      return "timeout";
    case HAL_I2C_STATE_ERROR:
      return "error";
    default:
      return "unknown";
  }
}

static const char *PinStateToString(GPIO_PinState state)
{
  return (state == GPIO_PIN_SET) ? "high" : "low";
}

static long ToCentiUnits(float value)
{
  if (value >= 0.0f) {
    return (long)(value * 100.0f + 0.5f);
  }

  return (long)(value * 100.0f - 0.5f);
}

/* USER CODE END 4 */

/**
  * @brief  This function is executed in case of error occurrence.
  * @retval None
  */
void Error_Handler(void)
{
  /* USER CODE BEGIN Error_Handler_Debug */
  /* User can add his own implementation to report the HAL error return state */
  __disable_irq();
  while (1)
  {
  }
  /* USER CODE END Error_Handler_Debug */
}
#ifdef USE_FULL_ASSERT
/**
  * @brief  Reports the name of the source file and the source line number
  *         where the assert_param error has occurred.
  * @param  file: pointer to the source file name
  * @param  line: assert_param error line source number
  * @retval None
  */
void assert_failed(uint8_t *file, uint32_t line)
{
  /* USER CODE BEGIN 6 */
  /* User can add his own implementation to report the file name and line number,
     ex: printf("Wrong parameters value: file %s on line %d\r\n", file, line) */
  /* USER CODE END 6 */
}
#endif /* USE_FULL_ASSERT */
