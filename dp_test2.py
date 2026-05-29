import jmri
from jmri.jmrit.dispatcher import DispatcherFrame, TrainInfo, ActiveTrain
from jmri import TransitSection, Section

out = open('/tmp/dp_test2.txt', 'w')

def log(s):
    out.write(str(s) + '\n')
    out.flush()

log("=== DP Static Transit Test ===")

DispatcherFrame.dispatcherSystemSchedulingInOperation = True

bm = jmri.InstanceManager.getDefault(jmri.BlockManager)
sm = jmri.InstanceManager.getDefault(jmri.SectionManager)
tm = jmri.InstanceManager.getDefault(jmri.TransitManager)
df = jmri.InstanceManager.getDefault(DispatcherFrame)
tb = jmri.InstanceManager.getDefault(jmri.Timebase)
pm = jmri.InstanceManager.getDefault(jmri.PowerManager)

log("Timebase running: %s, rate: %s" % (tb.getRun(), tb.getRate()))
log("PowerManager state: %s" % pm.getPower())
log("ON=%d OFF=%d UNKNOWN=%d" % (jmri.PowerManager.ON, jmri.PowerManager.OFF, jmri.PowerManager.UNKNOWN))

# --- Test A: pause/resume fast clock ---
log("\n--- Test A: pause/resume ---")
try:
    log("Before stop: run=%s" % tb.getRun())
    tb.setRun(False)
    log("After stop: run=%s" % tb.getRun())
    tb.setRun(True)
    log("After restart: run=%s" % tb.getRun())
except:
    import sys; log("Timebase error: %s" % sys.exc_info()[1])

# --- Cleanup: terminate any leftover active trains from prior runs ---
for at in list(df.getActiveTrainsList()):
    log("Terminating leftover AT: %s" % at.getTrainName())
    at.setDispatcher(df)   # may be null if prior run failed mid-load
    df.terminateActiveTrain(at, True, False)

# --- Test B: static transit from scratch ---
log("\n--- Test B: static transit (blocks + section + transit + train) ---")
try:
    b1 = bm.provideBlock("IB:AUTO:0001")
    b1.setUserName("WestStaging")
    b2 = bm.provideBlock("IB:AUTO:0002")
    b2.setUserName("EastStaging")
    log("Blocks: %s (%s), %s (%s)" % (b1.getSystemName(), b1.getUserName(), b2.getSystemName(), b2.getUserName()))

    sec = sm.createNewSection("TestSection-WE")
    sec.setUserName("WE-Section")
    sec.addBlock(b1)
    sec.addBlock(b2)
    log("Section: %s, blocks=%d" % (sec, sec.getNumBlocks()))

    transit = tm.createNewTransit("TestTransit-WE")
    transit.setUserName("WE-Transit")
    ts = TransitSection(sec, 1, Section.FORWARD)
    transit.addTransitSection(ts)
    log("Transit: %s, sections=%d" % (transit, transit.getTransitSectionList().size()))

    ti = TrainInfo()
    # loadTrainFromTrainInfo uses the *Id fields, not the *Name fields
    ti.setTransitName(transit.getUserName())
    ti.setTransitId(transit.getUserName())       # KEY: dispatcher looks this up
    ti.setTrainUserName("TEST-GW-1")
    ti.setDccAddress("2103")
    ti.setTrainFromRoster(False)   # default is True, must explicitly clear it
    ti.setTrainFromUser(True)
    ti.setAutoRun(False)
    ti.setDelayedStart(ActiveTrain.NODELAY)
    ti.setStartBlockName(b1.getUserName())
    ti.setStartBlockId(b1.getUserName())         # KEY: dispatcher looks this up
    ti.setStartBlockSeq(1)
    ti.setDestinationBlockName(b2.getUserName())
    ti.setDestinationBlockId(b2.getUserName())   # KEY: dispatcher looks this up
    ti.setDestinationBlockSeq(1)
    ti.setTerminateWhenDone(True)
    log("TransitId=%s StartBlockId=%s DestBlockId=%s" % (
        ti.getTransitId(), ti.getStartBlockId(), ti.getDestinationBlockId()))

    log("Calling loadTrainFromTrainInfo...")
    result = df.loadTrainFromTrainInfo(ti)
    log("Result: %d" % result)

    active = list(df.getActiveTrainsList())
    log("Active trains count: %d" % len(active))
    for at in active:
        log("  Train: name=%s status=%s mode=%s" % (at.getTrainName(), at.getStatus(), at.getMode()))

except:
    import sys; log("Exception: %s" % sys.exc_info()[1])

log("\nDONE")
out.close()
