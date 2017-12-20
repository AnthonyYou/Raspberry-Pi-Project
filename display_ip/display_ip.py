#!/usr/bin/python
# coding: utf-8

import RPi.GPIO as GPIO
import time
import threading
import math
import socket
import fcntl
import struct

gpios = (2, 3, 4, 14, 15, 17, 18, 27, 22, 23, 24, 10)

class RefreshThread(threading.Thread):
	'''刷新屏幕的线程'''
        def __init__(self, x_gpios, y_gpios):
		'''初始化 
		x_gpios: 每一列的gpio
		y_gpio: 每一行的gpio'''
                super(RefreshThread, self).__init__(name='refresh_thread')
                self.x_gpios = x_gpios
                self.y_gpios = y_gpios
                self.pixels = []
                for i in range(0, 2):
                        self.pixels.append([0] * 10)	# 每行10个像素点的缓存，共两行

                self.stopped = True
                self.require_stopped = False

        def set_pixel(self, x, y, value):
		'''设置单个像素的值'''
                if y < 0 or y >= len(self.pixels):
                        return
                if x < 0 or x >= 10:
                        return
                self.pixels[y][x]= 0 if value == '0' else 1

        def set_pixels(self, y, value):
		'''设置某一行的状态值
		y: 第几行
		value: 0和1组成的字符串'''
                if y < 0 or y >= len(self.pixels):
                        return
                index = -1
                for i in range(10):
                        self.pixels[y][i] = 0 if value[index] == '0' else 1
                        index = index - 1

        def start(self):
		'''启动刷新线程'''
                if self.stopped:
                        self.stopped = False
                        self.requre_stopped = False
                        super(RefreshThread, self).start()

        def stop(self):
		'''停止刷新线程'''
                self.require_stopped = True
                while not self.stopped:
                        time.sleep(0.01)

        def is_stopped(self):
                return self.stopped

        def run(self):
		'''刷新线程，一行行的扫描刷新'''
                while True:
                        if self.require_stopped:
                                break
                        y_index = 0
                        for y_gpio in self.y_gpios:
                                x_index = 0
                                GPIO.output(y_gpio, GPIO.LOW)
                                time.sleep(0.009)
                                for x_gpio in self.x_gpios:
                                        status = GPIO.HIGH if self.pixels[y_index][x_index] == 1 else GPIO.LOW
                                        GPIO.output(x_gpio, status)
                                        x_index = x_index + 1
                                GPIO.output(y_gpio, GPIO.HIGH)
                                y_index = y_index + 1
                for x_gpio in self.x_gpios:
                        GPIO.output(x_gpio, GPIO.LOW)
                for y_gpio in self.y_gpios:
                        GPIO.output(y_gpio, GPIO.LOW)
                self.stopped = True


def get_ip_address(ifname):
	'''获取ip地址
	ifname: 接口名，如eth0、wlan0，可以执行ifconfig查看'''
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return socket.inet_ntoa(fcntl.ioctl(
                s.fileno(),
                0x8915,
                struct.pack('256s', ifname[:15])
        )[20:24])

def init():
	GPIO.setmode(GPIO.BCM) # 设置mode为GPIO.BCM
	
	# 初始化将所有gpio设置为GPIO.LOW，这样所有灯都熄灭
	for gpio in gpios:
		GPIO.setup(gpio, GPIO.OUT)
		GPIO.output(gpio, GPIO.LOW)

def display_num(n, refresh_thread):
	'''将某个数字以二进制显示在显示器的第二列
	n:要显示的数字'''
        binary = bin(n)[2:]
        if len(binary) < 10:
                binary = '%s%s' % ('0' * (10 - len(binary)), binary)
        refresh_thread.set_pixels(1, binary)

def display_ip(ip, refresh_thread):
	'''按顺序依次显示ip的四位'''
        try:
                refresh_thread.set_pixels(0, '0000000001')
                display_num(ip[0], refresh_thread)
                time.sleep(3)

                refresh_thread.set_pixels(0, '0000000010')
                display_num(ip[1], refresh_thread)
                time.sleep(3)

                refresh_thread.set_pixels(0, '0000000100')
                display_num(ip[2], refresh_thread)
                time.sleep(3)

                refresh_thread.set_pixels(0, '0000001000')
                display_num(ip[3], refresh_thread)
                time.sleep(3)
        except:
                pass

def test():
        refresh_thread = RefreshThread((2, 3, 4, 14, 15, 17, 18, 27, 22, 23), (24, 10))
        refresh_thread.start()

        ip = get_ip_address('wlan0')
        for i in range(3):
                display_ip([int(elem) for elem in ip.split('.')], refresh_thread)

        refresh_thread.stop()

if __name__ == '__main__':
        init()
        test()
        GPIO.cleanup()
