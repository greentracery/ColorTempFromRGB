##
## ColorTempFromRGB LogWriter module
## - Write logfile
##
## https://github.com/greentracery/ColorTempFromRGB
##

import traceback as tr
import logging
import os

class LogWriter():
    """ Create & write logfile 
    
        method: log_error: Write error message (with trace -  optional) into logfile
        method: log_warning: Write warning message into logfile
        method: log_info: Write info message into logfile
        method: exception_trace: Traceback of exception/error
    """
    
    def __init__(self, logname):
        """
            :param logname: name of log file
        """
        
        logger = logging.getLogger(logname)
        logger.setLevel(logging.INFO)
        logpath = os.path.join(os.getcwd(),'logs')
        if not os.path.exists(logpath):
            os.makedirs(logpath)
        logfile = os.path.join(logpath, logname)
        log_handler = logging.FileHandler(logfile, mode='w')
        log_formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
        log_handler.setFormatter(log_formatter)
        logger.addHandler(log_handler)
        self.logger = logger

    def log_error(self, e, trace_error: bool = False):
        """ Write error message (with trace -  optional) into logfile 
        
            :param e: Exception/Error
            :param trace_error: Start traceback for exception/error if True
        """
        self.logger.error(e)
        if trace_error:
            e_trace = self.exception_trace(e)
            msg = f"See also: file {e_trace.filename}, line {e_trace.lineno}, string `{e_trace.line}`"
            self.logger.error(msg)
    
    def log_warning(self, msg):
        """ Write warning message into logfile 
        
            :param msg: Message text
        """
        self.logger.warning(msg)
    
    def log_info(self, msg):
        """ Write info message into logfile 
        
            :param msg: Message text
        """
        self.logger.info(msg)
        
    def exception_trace(self, e):
        """ Traceback of exception/error 
            
            :param e: Exception or error
        """
        e_trace = tr.TracebackException(exc_type =type(e),exc_traceback = e.__traceback__ , exc_value =e).stack[-1]
        return e_trace

