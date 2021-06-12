# final <br>

1.compile main.cpp into mbed <br>
2.save openmv.py into openmv <br>
3.sudo python server.py <br>
4.按下reset <br>

任務說明與講解：<br>
一開始，車子會follow line前進(透過openmv.py運算，uart傳送字元指令給mbed接收)，mbed端每2秒會用ping測量與牆壁的距離<br>
如果距離小於20cm，mbed會透過uart送指令給openmv進入mode2，openmv會偵測牆壁上的tag，透過xbee傳給pc端tag的位置資訊(Tx,Rx,Ty,Ry,Tz,Rz)<br>
server.py會持續print出來，等待20秒後，車子會原地旋轉90度，辨識牆上的數字並透過Xbee回傳給server.py，任務結束。<br>

demo 影片連結：https://drive.google.com/file/d/1L3ewv0GTZ05PQaJKundug29N3p8zZaYe/view?usp=sharing <br>
