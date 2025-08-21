import win32serviceutil
import win32service
import win32event
import subprocess
import os

class AlloyCraftService(win32serviceutil.ServiceFramework):
    _svc_name_ = "AlloyCraftBackend"
    _svc_display_name_ = "AlloyCraft Backend Service"
    
    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.process = None
    
    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        if self.process:
            self.process.terminate()
        win32event.SetEvent(self.hWaitStop)
    
    def SvcDoRun(self):
        backend_path = os.path.join(os.path.dirname(__file__), "main.exe")
        self.process = subprocess.Popen([backend_path])
        win32event.WaitForSingleObject(self.hWaitStop, win32event.INFINITE)

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(AlloyCraftService)