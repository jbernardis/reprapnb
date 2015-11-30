from threading import Timer

class TimeLapse:
    def __init__(self, handler):
        self.timeout = 30
        self.handler = handler
        self.running = False
        
    def delete(self):
        if self.running:
            self.stop()

    def setInterval(self, seconds):
        self.timeout = seconds

    def timerHandler(self):
        self.handler()
        if self.running:
            self.resume()

    def start(self, immediateTrigger = False):
        self.running = False
        if immediateTrigger:
            self.handler()
        
        self.resume()
        
    def resume(self):
        self.running = True
        self.thread = Timer(self.timeout, self.timerHandler)
        self.thread.start()

    def stop(self):
        self.running = False
        self.thread.cancel()
        
    def pause(self):
        self.running = False
        
    def isRunning(self):
        return self.running
# 
# def printer():
#     print 'ipsem lorem'
# 
# t = TimeLapse(5,printer)
# t.start()
