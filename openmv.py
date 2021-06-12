import sensor, image, time, math, pyb, os, tf

GRAYSCALE_THRESHOLD = [(200,255)]



ROIS = [ # [ROI, weight]
        #(0, 60, 160, 20, 0.1), # 你需要为你的应用程序调整权重
        (0, 40, 160, 20, 0.3), # 取决于你的机器人是如何设置的。
        (0, 0, 160, 20, 0.7)
       ]
#roi代表三个取样区域，（x,y,w,h,weight）,代表左上顶点（x,y）宽高分别为w和h的矩形，
#weight为当前矩形的权值。注意本例程采用的QQVGA图像大小为160x120，roi即把图像横分成三个矩形。
#三个矩形的阈值要根据实际情况进行调整，离机器人视野最近的矩形权值要最大，
#如上图的最下方的矩形，即(0, 100, 160, 20, 0.7)

# Compute the weight divisor (we're computing this so you don't have to make weights add to 1).
weight_sum = 0 #权值和初始化
for r in ROIS: weight_sum += r[4] # r[4] is the roi weight.
#计算权值和。遍历上面的三个矩形，r[4]即每个矩形的权值。

sensor.reset() # 初始化sensor

sensor.set_pixformat(sensor.GRAYSCALE) # use grayscale.
#设置图像色彩格式，有RGB565色彩图和GRAYSCALE灰度图两种

sensor.set_framesize(sensor.QQVGA) # 使用QQVGA的速度。
#设置图像像素大小

sensor.skip_frames(30) # 让新的设置生效。
sensor.set_auto_gain(False) # 颜色跟踪必须关闭自动增益
sensor.set_auto_whitebal(False) # 颜色跟踪必须关闭白平衡
clock = time.clock() # 跟踪FPS帧率

uart = pyb.UART(3,9600,timeout_char=1000)
uart.init(9600,bits=8,parity = None, stop=1, timeout_char=1000)

status = -1  #-1 still 0 straight 1 right 2 left
turn = -1

count = 0

c = 'X'

mode = 0

f_x = (2.8 / 3.984) * 160 # find_apriltags defaults to this if not set
f_y = (2.8 / 2.952) * 120 # find_apriltags defaults to this if not set
c_x = 160 * 0.5 # find_apriltags defaults to this if not set (the image.w * 0.5)
c_y = 120 * 0.5 # find_apriltags defaults to this if not set (the image.h * 0.5)


net = "trained.tflite"
labels = [line.rstrip('\n') for line in open("labels.txt")]



def degrees(radians):
   return (180 * radians) / math.pi


def change_status(blocks):
    global status
    global turn
    n = len(blocks)
    x = []
    y = []
    for b in blocks:
        x.append(b[0])
        y.append(b[1])
    if(n >= 2 and (status == 0 or status == -1)):
        if(x[0] - x[1]) >= 40:
            status = 0
            turn = 2
        elif(x[1] - x[0] >= 40):
            status = 0
            turn = 1
        elif(x[0] <= 20 and x[1] <= 20):
            status = 1
            turn = 1
        elif(x[0] >= 110 and x[1] >= 110):
            status = 2
            turn = 2
    elif(n == 0 and status == 0):
        time.sleep(1)
        status = turn
    elif(n == 2 and ((status == 1) or (status == 2))):
        dx = abs(x[0] - x[1])
        dy = abs(y[0] - y[1])
        if(dx != 0 and (dy/dx >= 1 and abs(x[0] - 80) <= 15)):
            status = 0

def mode0(img):
    centroid_sum = 0
    most_pixels = 0
    blocks = []

    for r in ROIS:
        blobs = img.find_blobs(GRAYSCALE_THRESHOLD, roi=r[0:4], merge=True)
        if blobs:
            # 查找像素最多的blob的索引。
            largest_blob = 0
            for i in range(len(blobs)):
            #目标区域找到的颜色块（线段块）可能不止一个，找到最大的一个，作为本区域内的目标直线
                if blobs[i].pixels() > most_pixels:
                    most_pixels = blobs[i].pixels()
                    #merged_blobs[i][4]是这个颜色块的像素总数，如果此颜色块像素总数大于
                    #most_pixels，则把本区域作为像素总数最大的颜色块。更新most_pixels和largest_blob
                    largest_blob = i

            # 在色块周围画一个矩形。
            if(blobs[largest_blob].cy() <= 80):
                img.draw_rectangle(blobs[largest_blob].rect())
                # 将此区域的像素数最大的颜色块画矩形和十字形标记出来
                img.draw_cross(blobs[largest_blob].cx(),
                               blobs[largest_blob].cy())
                blocks.append((blobs[largest_blob].cx(), blobs[largest_blob].cy()))

                centroid_sum += blobs[largest_blob].cx() * r[4] # r[4] is the roi weight.


    change_status(blocks)
    s = str(status)
    print(s)
    uart.write(s.encode())

def mode1(img):
    for tag in img.find_apriltags(fx=f_x, fy=f_y, cx=c_x, cy=c_y): # defaults to TAG36H11
          img.draw_rectangle(tag.rect(), color = (255, 0, 0))
          img.draw_cross(tag.cx(), tag.cy(), color = (0, 255, 0))
          # The conversion is nearly 6.2cm to 1 -> translation
          print_args = (tag.x_translation(), tag.y_translation(), tag.z_translation(), \
                degrees(tag.x_rotation()), degrees(tag.y_rotation()), degrees(tag.z_rotation()))
          # Translation units are unknown. Rotation units are in degrees.
          uart.write(("Tx: %f, Ty %f, Tz %f, Rx %f, Ry %f, Rz %f N"% print_args).encode())
          print(("Tx: %f, Ty %f, Tz %f, Rx %f, Ry %f, Rz %f" % print_args))

def mode2(img):
    for obj in tf.classify(net, img, min_scale=1.0, scale_mul=0.5, x_overlap=0.0, y_overlap=0.0):
        #print("This is : ",labels[obj.output().index(max(obj.output()))])
        s = "This is : " + labels[obj.output().index(max(obj.output()))] + 'N'
        print(s)
        uart.write(s.encode())

while(True):
    clock.tick() # 追踪两个snapshots()之间经过的毫秒数.
    c = uart.readchar()
    if(c != -1 and chr(c) == '1'):
        mode = 1
    elif(c != -1 and chr(c) == '0'):
        mode = 0
        status = -1
    elif(c != -1 and chr(c) == '2'):
        mode = 2
        status = -1
    img = sensor.snapshot() # 拍一张照片并返回图像。
    if(mode == 0):
       mode0(img)
    if(mode == 1):
       mode1(img)
    if(mode == 2):
       mode2(img)


