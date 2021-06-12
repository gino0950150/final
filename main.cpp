#include"mbed.h"
#include <vector>
#include "bbcar.h"
using namespace std;

BufferedSerial pc(USBTX,USBRX); //tx,rx
BufferedSerial uart(D1,D0); //tx,rx
BufferedSerial xbee(D10,D9);

Ticker servo_ticker;
Ticker encoder_ticker;
PwmOut pin5(D5), pin6(D6);
DigitalIn encoder(D11);
DigitalInOut ping(D13);

BBCar car(pin5, pin6, servo_ticker);
int mode = 0;
float PingDis = 8000;

Ticker flipper;
bool PingVar = 0;

Timer t;
int countvar = 0;
void flip() {
   if(mode == 0)
      PingVar = 1;
   else if(mode == 1)
      countvar += 1;
}


void Pinging();

int i='0';
char pre[1];
int main(){
   uart.set_baud(9600);
   pc.set_baud(9600);
   flipper.attach(&flip, 1s);
   char buf[1] = {'0'};
   uart.write(buf, 1);
   while(1){
      if(mode == 0) {
         if(PingVar) Pinging();
         if(uart.readable()){
               char recv[1];
               uart.read(recv, sizeof(recv));
               char c = recv[0];
               printf("c: %c\n", c);
               if (c != pre[0]){
                  switch (c){
                     case '0':
                     printf("!\n");
                        car.goStraight(20, 20);
                        break;
                     case '1':
                        car.goStraight(20, 0);
                        break;
                     case '2':
                        car.goStraight(0, 20);
                        break;
                  }
                  pre[0] = c;
               }
         }
         if(PingDis <= 20) {
            car.stop();
            mode = 1;
            char buf[1] = {'1'};
            uart.write(buf, 1);
         }
      } else if(mode == 1) {
         if(uart.readable()){
               char recv[1];
               uart.read(recv, sizeof(recv));
               char c = recv[0];
               printf("c: %c", c);
               xbee.write(recv,1);
         }
         if(countvar >= 20) {
            car.goStraight(0, 20);
            printf("t1");
            ThisThread::sleep_for(6s);
            car.stop();
            printf("t2");
            mode = 2;
            char buf[1] = {'2'};
            uart.write(buf, 1);
         }
      } else if(mode == 2) {
         if(uart.readable()){
               char recv[1];
               uart.read(recv, sizeof(recv));
               char c = recv[0];
               printf("c: %c", c);
               xbee.write(recv,1);
         }
      }
      
   }
}

void Pinging(){
      float val;
      ping.output();
      ping = 0; wait_us(200);
      ping = 1; wait_us(5);
      ping = 0; wait_us(5);
      ping.input();
      while(ping.read() == 0);
      t.start();
      while(ping.read() == 1);
      val = t.read();
      printf("Ping = %lf\r\n", val*17700.4f);
      PingDis = val*17700.4f;
      t.stop();
      t.reset();
      PingVar = 0;
}
