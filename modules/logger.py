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
    
    def __init__(self, logname):
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
        """ Отправляем ошибку (error) в лог """
        self.logger.error(e)
        if trace_error:
            e_trace = self.exception_trace(e)
            msg = f"See also: file {e_trace.filename}, line {e_trace.lineno}, string `{e_trace.line}`"
            self.logger.error(msg)
    
    def log_warning(self, msg):
        """ Отправляем ошибку (warning) в лог """
        self.logger.warning(msg)
    
    def log_info(self, msg):
        """ Отправляем сообщение в лог """
        self.logger.info(msg)
        
    def exception_trace(self, e):
        """ Трассировка исключения """
        e_trace = tr.TracebackException(exc_type =type(e),exc_traceback = e.__traceback__ , exc_value =e).stack[-1]
        return e_trace

