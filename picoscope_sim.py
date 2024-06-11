# picoscope_sim.py
def pico_init(handle):
    print("Simulating pico_init")

def pico_block(handle, channel, dataFile, nbSamples, timebase, verbose, triggerChan=None, noOfPreTriggerSamples=0):
    print(f"Simulating pico_block: Writing simulated data to {dataFile}")
    with open(dataFile, 'w') as f:
        f.write("Simulated data")

def pico_close(handle):
    print("Simulating pico_close")

