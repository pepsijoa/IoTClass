/*
 * FreeRTOS: UART String Command 
 * - SerialTask (Priority 1)
 * - MotorTask (Priority 2)
 *
 * 두 태스크가 Queue를 통해 통신합니다.
 */

#include <Arduino_FreeRTOS.h>
#include <queue.h> // Queue API 헤더

//--- 1. 하드웨어/핀 정의 ---
// (모터 핀들을 여기에 정의하세요)
// #define MOTOR_A_IN1 9
// #define MOTOR_A_IN2 10
// ...

#define MOTOR_A_IN1 9
#define MOTOR_A_IN2 10

#define MOTOR_B_IN1 11
#define MOTOR_B_IN2 12 

//--- 2. Queue 핸들 정의 ---
QueueHandle_t xMotorQueue;

//--- 3. Queue로 보낼 데이터 타입 정의 ---
typedef enum {
  CMD_STOP,
  CMD_UP,
  CMD_DOWN,
  CMD_LEFT,
  CMD_RIGHT,
  CMD_INVALID
} MotorCommand_t; // MotorCommand_t 라는 새로운 타입을 만듦


//==================================================
// setup() : C언어의 main() 함수 역할
//==================================================
void setup() {
  Serial.begin(115200);
  while (!Serial) { ; } // 시리얼 포트 대기

  pinMode(MOTOR_A_IN1, OUTPUT);
  pinMode(MOTOR_A_IN2, OUTPUT);
  pinMode(MOTOR_B_IN1, OUTPUT);
  pinMode(MOTOR_B_IN2, OUTPUT);
  
  Serial.println("--- FreeRTOS UART Motor Control ---");
  Serial.println("명령을 입력하세요: UP, DOWN, LEFT, RIGHT, STOP");

  //--- 1. 큐 생성 ---
  xMotorQueue = xQueueCreate(1, sizeof(MotorCommand_t));

  if (xMotorQueue == NULL) {
    Serial.println("큐 생성 실패!");
    while(1); // 시스템 정지
  }

  //--- 2. 태스크 생성 ---
  xTaskCreate(
    prvSerialTask,    // 태스크 함수 포인터
    "SerialTask",     // 태스크 이름
    128,              // 스택 크기 (word 단위)
    NULL,             // 태스크 파라미터
    1,                // 우선순위 (낮음)
    NULL);            // 태스크 핸들 (안 씀)

  xTaskCreate(
    prvMotorTask,     // 태스크 함수 포인터
    "MotorTask",      // 태스크 이름
    128,              // 스택 크기
    NULL,             // 태스크 파라미터
    2,                // 우선순위 (높음)
    &Motor_Control);  // 태스크 핸들

  //--- 3. 스케줄러 시작 ---
  // 이 시점부터 setup()은 끝나고 제어권은 RTOS로 넘어감
  vTaskStartScheduler();
}

//==================================================
// loop() : 절대로 실행되지 않음
//==================================================
void loop() {
  // 비워둠
}


//==================================================
// 태스크 1: SerialTask (통신병)
//==================================================
void prvSerialTask(void *pvParameters) {
  (void) pvParameters;

  // C언어 스타일의 무한 루프
  for (;;) {
    // 버퍼는 이 태스크 내에서만 사용 (static으로 선언)
    static char command_buffer[20];
    static int index = 0;

    // 시리얼 포트에 읽을 데이터가 있는지 확인 (논블로킹)
    if (Serial.available() > 0) {
      char c = Serial.read();

      // 줄바꿈 문자(\n 또는 \r)를 받으면 명령 처리 시작
      if (c == '\n' || c == '\r') {
        if (index > 0) { // 버퍼에 무언가 쓰여있다면
          command_buffer[index] = '\0'; // 문자열의 끝을 표시

          MotorCommand_t cmd_to_send;

          //--- 문자열을 enum으로 변환 ---
          if (strcmp(command_buffer, "UP") == 0) {
            cmd_to_send = CMD_UP;
          } else if (strcmp(command_buffer, "DOWN") == 0) {
            cmd_to_send = CMD_DOWN;
          } else if (strcmp(command_buffer, "LEFT") == 0) {
            cmd_to_send = CMD_LEFT;
          } else if (strcmp(command_buffer, "RIGHT") == 0) {
            cmd_to_send = CMD_RIGHT;
          } else if (strcmp(command_buffer, "STOP") == 0) {
            cmd_to_send = CMD_STOP;
          } else {
            cmd_to_send = CMD_INVALID;
          }
          
          Serial.print("명령 수신: ");
          Serial.println(command_buffer);

          //--- 큐(메일박스)에 명령 전송 ---
          xQueueSend(xMotorQueue, &cmd_to_send, portMAX_DELAY);
          
          // 버퍼 인덱스 초기화
          index = 0;
        }
      } 
      // 일반 문자이고 버퍼가 꽉 차지 않았다면
      else if (index < (sizeof(command_buffer) - 1)) {
        command_buffer[index++] = c; // 버퍼에 문자 추가
      }
    }
    
    // 이 태스크를 잠시(10ms) 재워서 다른 태스크(MotorTask)가 실행될 시간을 줌
    vTaskDelay(10 / portTICK_PERIOD_MS);
  }
}

void prvMotorTask(void *pvParameters) {
  (void) pvParameters;
  MotorCommand_t received_cmd;

  // C언어 스타일의 무한 루프
  for (;;) {
    //--- 큐에서 명령이 올 때까지 무한정 대기 (Blocked 상태) ---
    // 큐에 데이터가 들어오면 이 태스크는 즉시 'Ready' 상태가 됨
    if (xQueueReceive(xMotorQueue, &received_cmd, portMAX_DELAY) == pdPASS) {
      switch (received_cmd) {
        case CMD_UP:
          Motor_UP();
          Serial.println("===> 모터: 위로 이동");
          break;
        case CMD_DOWN:
          Motor_DOWN();
          Serial.println("===> 모터: 아래로 이동");
          break;
        case CMD_LEFT:
          Motor_LEFT();
          Serial.println("===> 모터: 왼쪽으로 이동");
          break;
        case CMD_RIGHT:
          Motor_RIGHT();
          Serial.println("===> 모터: 오른쪽으로 이동");
          break;
        case CMD_STOP:
          Motor_STOP();
          Serial.println("===> 모터: 정지");
          break;
        case CMD_INVALID:
        default:
          Serial.println("===> 에러: 알 수 없는 명령");
          // 추후 protocol 작성 후 에러 값 표출 
          break;
      }
    }
  }
}

void Motor_UP() {
  digitalWrite(MOTOR_A_IN1, HIGH);
  digitalWrite(MOTOR_A_IN2, LOW);

  digitalWrite(MOTOR_B_IN1, HIGH);
  digitalWrite(MOTOR_B_IN2, LOW);
}

void Motor_STOP() {
  digitalWrite(MOTOR_A_IN1, LOW);
  digitalWrite(MOTOR_A_IN2, LOW);

  digitalWrite(MOTOR_B_IN1, LOW);
  digitalWrite(MOTOR_B_IN2, LOW);
}

void Motor_LEFT() {
  digitalWrite(MOTOR_A_IN1, HIGH);
  digitalWrite(MOTOR_A_IN2, LOW);

  digitalWrite(MOTOR_B_IN1, LOW);
  digitalWrite(MOTOR_B_IN2, HIGH);
}

void Motor_RIGHT() {
  digitalWrite(MOTOR_A_IN1, LOW);
  digitalWrite(MOTOR_A_IN2, HIGH);

  digitalWrite(MOTOR_B_IN1, HIGH);
  digitalWrite(MOTOR_B_IN2, LOW);
}

void Motor_DOWN() {
  digitalWrite(MOTOR_A_IN1, LOW);
  digitalWrite(MOTOR_A_IN2, HIGH);

  digitalWrite(MOTOR_B_IN1, LOW);
  digitalWrite(MOTOR_B_IN2, HIGH);
}
