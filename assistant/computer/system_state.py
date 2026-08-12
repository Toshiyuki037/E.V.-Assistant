import os,platform,socket,sys,time

def get_basic_system_state():
    return {'platform':platform.system(),'platform_release':platform.release(),'platform_version':platform.version(),'hostname':socket.gethostname(),'architecture':platform.machine(),'python_executable':sys.executable,'process_id':os.getpid(),'current_directory':os.getcwd(),'timestamp':time.time()}
