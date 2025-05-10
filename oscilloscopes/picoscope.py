# coding=utf-8
"""
 # File: picoscope.py 
 # Project: data-acquisition
 # Last Modified: 2021-9-30
 # Created Date: 2021-8-2
 # Copyright (c) 2021
 # Author: AHMA project (Univ Rennes, CNRS, Inria, IRISA)
 # Modified By: Duy-Phuc Pham (duy-phuc.pham@irisa.fr)
 
"""

from ctypes import *
from picosdk.ps5000a import ps5000a as ps
from picosdk.functions import adc2mV, assert_pico_ok
import struct
import logging

#Link with the C API
PS5000timeUnit = {"fs":0, "ps":1, "ns":2, "us":3, "ms":4, "s":5}
timeUnitsInSeconde = [1e15, 1e12, 1e9, 1e6, 1e3, 1]
timeUnit = PS5000timeUnit["ps"]
PS5000channel= {"A":0, "B":1, "C":2, "D":3 , "AUX": 5}
coupling = ps.PS5000A_COUPLING['PS5000A_DC']                    # DC50
Vrange = 3                      #100mV
enable = 1
offset = 0
bdwl = 0
autoStop = 0
#downSampleRatioMode = 2        # PS5000_RATIO_MODE_AVERAGE
downSampleRatioMode = 0         # None
downSampleRatio = 1
g_trigger = False # Global trigger enable flag
g_triggered = False # Global triggered flag

logger = logging.getLogger("anon-sca")  # Centralized log
# Resolution set to 12 Bit
resolution =ps.PS5000A_DEVICE_RESOLUTION["PS5000A_DR_12BIT"]

def pico_init(handle):
    ret = ps.ps5000aOpenUnit(byref(handle), None, resolution)
    assert_pico_ok(ret)
    ret = ps.ps5000aSetChannel(handle, 0, 0, coupling, Vrange, offset)
    assert_pico_ok(ret)
    ret = ps.ps5000aSetChannel(handle, 1, 0, coupling, Vrange, offset)
    assert_pico_ok(ret)
    ret = ps.ps5000aSetChannel(handle, 2, 0, coupling, Vrange, offset)
    assert_pico_ok(ret)
    ret = ps.ps5000aSetChannel(handle, 3, 0, coupling, Vrange, offset)
    assert_pico_ok(ret)

def pico_close(handle):
    ret = ps.ps5000aStop(handle)
    assert_pico_ok(ret)
    ret = ps.ps5000aCloseUnit(handle)
    assert_pico_ok(ret)

#The callback function used by ps5000GetStreamingLatestValues
@CFUNCTYPE(None, c_int16, c_int32,  c_uint32, c_int16,  c_uint32,  c_int16,   c_int16,  c_void_p)
def callback(handle,  nSamples, startIndex, overflow, triggerAt, triggered, autoStop, pParameter):
    global dataFileHandler, totalNumberOfSamples, buff, g_triggered, g_trigger
    if (not g_trigger) or (g_trigger and g_triggered) or triggered:
        # print(triggerAt, triggered, autoStop)
        if g_trigger and (not g_triggered):
            logger.debug('Triggered!')
            g_triggered = True
        for i in range(nSamples):
            s = buff[i+startIndex]
            #y = (s * Vrange) / 32512.
            dataFileHandler.write(struct.pack('h', s)) #thread unsafe
        totalNumberOfSamples += nSamples
        logger.debug('Got %i samples at index %i.' % (nSamples, startIndex))

def pico_streaming(handle, channel, duration, sampleRate, bufferLth, dataFile, v, TriggerChannel=None, maxPreTriggerSamples = 0 ):
    global dataFileHandler, g_trigger
    dataFileHandler = open(dataFile, mode='wb')
    global buff
    buff = (c_int16 * bufferLth)()
    global totalNumberOfSamples
    totalNumberOfSamples = 0
    if v:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    channel = PS5000channel[channel]
    pParameter = c_void_p()
    sampleInterval = c_uint32(int(timeUnitsInSeconde[timeUnit]/sampleRate))    # Number of <timeUnit> to wait between each sampling
    ret = ps.ps5000aSetChannel(handle, channel, enable, coupling, Vrange, offset)
    assert_pico_ok(ret)
    if TriggerChannel:
        logger.debug('Starting trigger')
        g_trigger = True
        if (TriggerChannel != 'AUX'):
            ret = ps.ps5000aSetChannel(handle, PS5000channel[TriggerChannel], enable, coupling, Vrange, offset)
            assert_pico_ok(ret)
            ret = ps.ps5000aSetSimpleTrigger(handle, enable, PS5000channel[TriggerChannel], 0x3f00, 2, 0, 0) # 0x3f00: ~500mV, 2: PS5000_RISING, 4: PS5000_RISING_OR_FALLING, delay = 0 s, auto Trigger = 0 ms
            assert_pico_ok(ret)
        else:
            ret = ps.ps5000aSetSimpleTrigger(handle, enable, PS5000channel[TriggerChannel], 0x0f00, 4, 0, 0) # 0x0f00: ~100mv because of 50 Ohm impedence inside AuxIO, 2: PS5000_RISING, 4: PS5000_RISING_OR_FALLING, delay = 0 s, auto Trigger = 0 ms
            assert_pico_ok(ret)
    ret = ps.ps5000aSetDataBuffer(handle, channel, byref(buff), bufferLth,0, downSampleRatioMode)
    assert_pico_ok(ret)
    # ps.ps5000Stop(handle) #Stop any running trace might be conflicted (optional)
    ret = ps.ps5000aRunStreaming(handle, byref(sampleInterval),
            timeUnit, maxPreTriggerSamples, bufferLth, autoStop, downSampleRatio, downSampleRatioMode, bufferLth)
    assert_pico_ok(ret)
    dataLth = duration * sampleRate
    while totalNumberOfSamples < dataLth:
        ret = ps.ps5000aGetStreamingLatestValues(handle, callback, byref(pParameter))
        # assert_pico_ok(ret) # Ignore PICO_BUSY
    dataFileHandler.close()
    #return adc2mV(dataBuff, Vrange, c_int16(32512))


def pico_block(handle, channel, dataFile, nbSamples, timebase, v, TriggerChannel=None, noOfPreTriggerSamples = 0):
    dataFileHandler = open(dataFile, mode='wb')
    if v:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    channel = PS5000channel[channel]
    ret = ps.ps5000aSetChannel(handle, channel, enable, coupling, Vrange, offset)
    assert_pico_ok(ret)

    if TriggerChannel:
        logger.debug('Starting trigger')
        if (TriggerChannel != 'AUX'):
            ret = ps.ps5000aSetChannel(handle, PS5000channel[TriggerChannel], enable, coupling, Vrange, offset)
            assert_pico_ok(ret)
            ret = ps.ps5000aSetSimpleTrigger(handle, enable, PS5000channel[TriggerChannel], 0x3f00, 2, 0, 1) # 0x3f00: ~500mV, 2: PS5000_RISING, 4: PS5000_RISING_OR_FALLING, delay = 0 s, auto Trigger = 0 ms
            assert_pico_ok(ret)
        else:
            ret = ps.ps5000aSetSimpleTrigger(handle, enable, PS5000channel[TriggerChannel], 0x0800, 2, 0, 0) # 0x0f00: ~100mv because of 50 Ohm impedence inside AuxIO, 2: PS5000_RISING, 4: PS5000_RISING_OR_FALLING, delay = 0 s, auto Trigger = 0 ms
            assert_pico_ok(ret)
    if timebase < 5:
        freq = 5e9/2**timebase
    else:
        freq = 156250000/(timebase-4)
    timeIntervalns = c_float()
    maxSamples = c_int32()
    ret = ps.ps5000aGetTimebase2(handle, timebase, nbSamples, byref(timeIntervalns), byref(maxSamples), 0)
    assert_pico_ok(ret)
    logger.debug("Max number of samples: {:d}".format(maxSamples.value))
    if nbSamples == 0:
        nbSamples = maxSamples.value
    logger.debug("Sample rate: {}Mss".format(int(freq/1e6)))
    logger.debug("Number of samples: {:d}".format(nbSamples))
    logger.debug("Capture length: {:.3f}us".format(timeIntervalns.value*nbSamples/1e3))

    noOfPostTriggerSamples = nbSamples - noOfPreTriggerSamples
    ret = ps.ps5000aRunBlock(handle, noOfPreTriggerSamples, noOfPostTriggerSamples, timebase, None, 0, None, None)
    assert_pico_ok(ret)

    # Check for data collection to finish using ps5000IsReady
    ready = c_int16(0)
    check = c_int16(0)
    while ready.value == check.value:
        ret = ps.ps5000aIsReady(handle, byref(ready))

    buff = (c_int16 * nbSamples)()
    ret = ps.ps5000aSetDataBuffer(handle, channel, byref(buff), nbSamples, 0, downSampleRatioMode)
    assert_pico_ok(ret)

    c_nbSamples = c_int32(nbSamples)
    ret = ps.ps5000aGetValues(handle, channel, byref(c_nbSamples), 1, 0, 0, None)
    assert_pico_ok(ret)
    logger.debug("Captured {:d} samples".format(c_nbSamples.value))

    for i in range(c_nbSamples.value):
        dataFileHandler.write(struct.pack('h', buff[i]))