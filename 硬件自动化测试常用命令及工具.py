#! /usr/bin/python
# _*_coding:utf8_*_

"""
硬件自动化测试常用命令及工具

#1. 查看dmeg日志
dmesg -t

#2. 查看系统启动日志
cat /var/log/messages

#3. 查看内核信息
uname -a

#4. 查看操作系统信息
cat /etc/*release

#5. lsxxx
lscpu  --> 查看cpu信息      --> cat /proc/cpuinfo
lsusb  --> 查看usb信息      --> cat /proc/meminfo
lspci  --> 查看pci设备信息
lsmod  --> 查看加载的内核模块

#6. 硬盘
lsblk -l
fdisk
df -h

#7. 内存
free -m
cat /proc/meminfo

#8. dmidecode -t memory/processor/xxx 查看dmi信息

#9. 网卡
ifconfig

#10. 查看设备实时使用状态
iostat

#11. 查看进程
ps -aux/[ef]
top

#12. 查看、设置时间
date 可同步网络时间或硬件时间
hwclock 硬件时间

#13. 常用硬件测试工具
fio 硬盘压力测试
  - 跑完压力会输出测试日志，关注iops和bandwide是否与厂家宣称一致, 是否有误码 err
  - 压力可分为动态压力和静态压力，可编写脚本控制。静态压力：连续跑N个小时; 动态压力：每跑5分钟，停一分钟，再跑5分钟，循环跑压力。
iperf 网卡压力测试
  - 按照通信协议分为TCP/UDF压力测试；按照设备环境搭建的不同可分为对跑压力测试和回环压力测试
  - 对跑压力测试即两台服务器网口串联，一台发包，一台收包
  - 回环压力测试即一台服务器上网卡有多个网口，网口之间用网线串联，使用两个网口进行收发包测试
  - 关注收发包是否稳定，是否有误码
netperf 网卡压力测试工具
ptugen/stress  cpu压力测试工具
 - ptugen是inter的工具，目前只支持x86架构cpu的测试
 - stree既可用于x86，也可用于ARM平台
memtester 内存压力测试
 - 跑内存压力，产看系统有无异常日志产生
 - 可使用taskset进行绑核操作

当前大部分服务器都会有一个BMC芯片，可以用来带外管理服务器（linux系统上的操作称为带内管理）
服务器的开机流程： bmc上电 --> bios上电 --> 引导系统 --> 操作系统
"""