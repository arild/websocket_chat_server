
import os, datetime


bind_addr = ''
config = {
    
    # Path to the shared library between front-end, back-end and load-balancer
    'LIBRARY_ABSOLUTE_PATH': os.getcwd() + os.sep + os.pardir + os.sep + 'lib',  

    ##### NAMESERVER #####
    'NAME_SERVER_ADDR':'129.242.19.59',#'129.242.22.182',#'10.1.255.238',
    'NAME_SERVER_PORT': 9999,
        
    ##### FRONT-END SERVER #####    
    'WEB_SERVER_BIND_PORT': 8080,
    'WEB_SERVER_BIND_ADDR': '', # '' = use getaddrinfo()
    
    'MEM_CACHE_MAX_SIZE_BYTES': (2**20) * 200, # 200 MB
    'DISK_CACHE_ROOT_DIRECTORY_PATH': '/tmp/inf-3203/arild/disk_cache/',
    'DISK_CACHE_MAX_SIZE_BYTES': (2**20) * 3000, # 2GB

          
    ##### BACK-END SERVER #####
    
    # The name of the distributed object hading out images
    'IMAGE_OBJECT_NAME': 'image',
    
    # Absolute path to the images on the file system
    'IMAGES_FILE_PATH': '/home/shared/weather-images/',
    #'IMAGES_FILE_PATH': os.getcwd() + os.sep + 'images' + os.sep,
    
    # On Linux the Pyro daemon binds to the loopback addr. Hard-code the address here if needed
    'DAEMON_BIND_ADDR': '10.1.255.211', # '' = use getaddrinfo()
    'IMAGES_START_DATE': '2003/03/22/00/00',
    'IMAGES_END_DATE': '2005/12/30/23/45',

    
    
    ##### LOAD BALANCER #####
    'LOAD_BALANCER_RESOLVER_BIND_PORT': 5003,
    'LOAD_BALANCER_RESOLVER_BIND_ADDR': '', # '' = use getaddrinfo()
    'LOAD_BALANCER_WEB_SERVER_BIND_PORT': 8080,
    'LOAD_BALANCER_WEB_SERVER_BIND_ADDR': '',
    'FRONT_END_SERVER_LIST': [('localhost', 8001), ('localhost', 8002), ('localhost', 8003)],


    ##### Benchmarking #####
    'NUM_FILE_SYSTEM_READER_THREADS': 10,
    'FILE_SYSTEM_READ_DURATION_SECONDS': 15
}

