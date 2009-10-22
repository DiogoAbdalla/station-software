import sys
import os
import time
import random
import calendar
from Observer import Observer
from threading import Lock
from hslog import log
from NagiosResult import NagiosResult

OK = 0
WARNING = 1
CRITICAL = 2            		
UNKNOWN = 3

class Check:
    def __init__(self):
        self.nagiosResult = NagiosResult()
	self.nagiosResult.status_code = UNKNOWN
            
    def check(self, sched, config):
        OK = 0

    def parse_range(self, range):
        """
        Maak een tuple van een range string. 'min:max' -> (min, max) 
        """
        try:
            a = range.split(':')
            min = float(a[0])
            max = float(a[1])
            return (min, max)
        except:
            log ('Wrong arguments given! %s' %(range))
            sys.exit(CRITICAL)



class TriggerRate(Check):
    def __init__(self, interpreter):
        Check.__init__(self)
        self.nagiosResult.serviceName = "TriggerRate"
        self.interpreter = interpreter
                		
    def check(self, sched, config):
        while True:
            try:
                warnRange = config['triggerrate_warn']
                warn = self.parse_range(warnRange)
                critRange = config['triggerrate_crit']
                crit = self.parse_range(critRange)
            except:
                log ("Unable to read config.ini in %s" %(self.nagiosResult.serviceName))
                self.nagiosResult.status_code = CRITICAL

            wmin, wmax = warn
            cmin, cmax = crit    

            self.triggerRateValues = self.interpreter.getTriggerRate()
            self.lastupdate = self.triggerRateValues.date
            self.trate = self.triggerRateValues.triggerRate
                    
            if self.trate <= cmin or self.trate >= cmax:
                self.nagiosResult.status_code = CRITICAL
            elif self.trate <= wmin or self.trate >= wmax:
                self.nagiosResult.status_code = WARNING
            else:
                self.nagiosResult.status_code = OK

            if self.lastupdate:
                t = time.strptime(str(self.lastupdate), '%Y-%m-%d %H:%M:%S')
                # sqlite's timestamp is in UTC, so use calendar.timegm (see python time
                # library reference)
                t = calendar.timegm(t)
                dt = time.time() - t
            else:
                #'Never updated, make dt very large'
                dt = 1e6
           
            # if last update was significantly longer than time between monitor
            # upload checks, detector is probably stalled
            interval = int(config['triggerrate_interval'])
            if dt > (2 * interval):
                self.nagiosResult.description = "No recent triggers. Trigger rate: %.2f Last update: %d seconds ago" % (self.trate, dt)
                self.nagiosResult.status_code = CRITICAL

            else:
                self.nagiosResult.description = "Trigger rate: %.2f Last update: %d seconds ago" % (self.trate, dt)
                                            
            yield (self.nagiosResult)
#end TriggerRate



class StorageSize(Check):
    def __init__(self,storageManager):
        Check.__init__(self)
        self.nagiosResult.serviceName = "StorageSize"
        self.storageManager = storageManager
        
        
    def check(self, sched, config):
		
##    """
##    Check de buffer size
##    cmin <= wmin <= OK >= wmax >= cmax
##    """
        while True:
			
            try:
                warnRange = config['storagesize_warn']
                warn = self.parse_range(warnRange)
                critRange = config['storagesize_crit']
                crit = self.parse_range(critRange)
            except:
                log ("Unable to read config.ini in %s" %(self.nagiosResult.serviceName))
                self.nagiosResult.status_code = CRITICAL

            wmin, wmax = warn
            cmin, cmax = crit
                    
            self.storageSize = self.storageManager.getNumEvents()

            if self.storageSize <= cmin or self.storageSize >= cmax:
                self.nagiosResult.status_code = CRITICAL
            elif self.storageSize <= wmin or self.storageSize >= wmax:
                self.nagiosResult.status_code = WARNING
            else:
                self.nagiosResult.status_code = OK

            if not self.storageSize:
                self.storageSize = 0

            self.nagiosResult.description = "Storage size: %d events" % (self.storageSize)
            
            yield (self.nagiosResult)
#end BufferSize
			

class EventRate(Check, Observer):
    def __init__(self):
        Check.__init__(self)
        self.nagiosResult.serviceName = "EventRate"
        self.eventCount = 0
        self.oldCountTime = 0
        self.eventRate = 0
        self.lock = Lock()
                
    def check(self):
        pass

    #Add number of events
    def notify(self, count):
        self.lock.acquire()
        self.eventCount = self.eventCount + count
        self.lock.release()
                       
    def check(self, sched, config):
        isCritical = config['eventrate_crit']

        while True:
            if self.oldCountTime == 0:
                self.oldCountTime = time.time()
            else:
                self.timeDifference = time.time() - self.oldCountTime
                self.oldCountTime = time.time()
                
                self.lock.acquire()
                self.eventRate = float(self.eventCount)/float(self.timeDifference)
                self.eventCount = 0
                self.lock.release()

                if self.eventRate < isCritical:
                    self.nagiosResult.status_code = OK
                else:
                    self.nagiosResult.status_code = CRITICAL
                self.nagiosResult.description = "Event rate for a period of %.2f seconds is %.2f" % (self.timeDifference,self.eventRate)
                
            yield (self.nagiosResult)
#end Event rate

class StorageGrowth(Check):
    def __init__(self,storageManager):
        Check.__init__(self)
        self.nagiosResult.serviceName = "StorageGrowth"
        self.newStorageSize = 0
        self.oldStorageSize = 0
        self.storageGrowth = 0
        
        self.storageManager = storageManager

    def check(self, sched, config):
        self.interval = config['storagegrowth_interval']
        while True:
            try:
                warn = float(config['storagegrowth_warn'])
                crit = float(config['storagegrowth_crit'])
            except:
                log ("Unable to read config.ini in %s" %(self.nagiosResult.serviceName))
                self.nagiosResult.status_code = CRITICAL
                
            self.newStorageSize = self.storageManager.getNumEvents()
            self.storageGrowth = ((self.newStorageSize - self.oldStorageSize)/float(self.interval))
            self.oldStorageSize = self.newStorageSize

            if self.storageGrowth < warn:
                self.nagiosResult.status_code = OK
            elif self.storageGrowth < crit:
                self.nagiosResult.status_code = WARNING
            else:
                self.nagiosResult.status_code = CRITICAL


            self.nagiosResult.description = "Storage growth: %d" % (self.storageGrowth)
                        
            yield (self.nagiosResult)
#end Storage growth