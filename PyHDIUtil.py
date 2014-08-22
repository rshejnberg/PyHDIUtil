###################################################
#                                                 #
#                                                 #
#                     PyHDIUtil                   #
#      A module for interacting with OS X's       #
#                 hdiutil utility                 #
#                                                 #
#               Author: Raphael Shejnberg         #
#                                                 #
###################################################

import os, subprocess, plistlib

commands = {'create' : 
                {   'uid' : None,
                    'gid' : None,
                    'size': None, 
                    'encryption' : [False, 'AES-128', 'AES-256'], 
                    'type' : ['UDIF', 'SPARSE', 'SPARSEBUNDLE'] , 
                    'volname' : None, 
                    'fs' : ['HFS+', 'HFS+J' '(JHFS+)', 'HFSX', 'JHFS+X', 'MS-DOS', 'UDF']
                },
            'imageinfo' :
                {    'plist' : None     },
            'info' :
                {    'plist' : None     }

            }
utility = 'hdiutil'
def valid_arg(cmd, option, arg):
    if arg in commands[cmd][option]:
        return True
    else:
        return False
        
def get_valid_args(cmd, option):
    return commands[cmd][option]

class HDIUtil(object):

    ####################################### DEFAULT SETTINGS ############################################
    
    NAME = 'hdiutil'

    # Set default options here                
    DEFAULT_FS_INDEX = 0
    DEFAULT_TYPE_INDEX = 0
    
    # Shortcuts
    DEFAULT_FS = get_valid_args('create', 'fs')[DEFAULT_FS_INDEX]
    DEFAULT_TYPE = get_valid_args('create', 'type')[DEFAULT_TYPE_INDEX]
    
    def __init__(self):
        # Hash representing the default values for given options
        self._default_options = {
                     'size' : '100m', 
                     'volname' : 'Volume', 
                     'path' : '~', 
                     'encryption' : False,
                     'fs' : self.DEFAULT_FS, 
                     'type' : self.DEFAULT_TYPE,
                     'create_new' : True}
                     
    # Default options when creating DiskImages            
    @property
    def default_options(self):
        return self._default_options
        
    @default_options.setter
    def default_options(self, **kwargs):
        for k in kwargs.keys():
            if k in self.default_options():
                self._default_options[k] = kwargs[k]
            else:
                raise Exception('Invalid option argument: ' + k)
            
    
    
    # Remainder of option arg validation occurs here
	
    ####################################### DISK IMAGE FACTORY #############################
    ## Validation: Option-types
    ## Usage: create(path='/my/path', size='1024b', type='SPARSE')
    ## Contains: Subclasses of DiskImage: UDIF, Sparse, Sparsebundle
    def create(self, *args, **kwargs):
        ## Disk Image Class
    	class DiskImage(object):
                UTILITY_NAME = 'hdiutil'
                
                def __init__(self, options):
                    # Deep-copy options to hash where keys match member vars and vals set to None
                    if 'create_new' in options:
                        create_new = False if options.pop('create_new') is 'False' else True
                    
                    # Set path and retrieve info from dmg (process dependent on self.path)

                    if not create_new:

                        self.path = options.pop('path')
                        options = self.generate_data_model(self.diskutil_info())

                    init_options = self.obj_format(options)
                    
                    # Initialize to none
                    self.__dict__.update(dict([(k, None) for k in init_options.keys()]))

                    # Copy values to self
                    for k in init_options.keys():
                        setattr(self, k, init_options[k])

                    # Execute hdiutil create command
                    if create_new is True:
                        self.create_command()

                
                def __repr__(self):
                    str = ''
                    for k in self.__dict__.keys():
                        str += ("{0:20}:\t\t{1:<10}\n".format(k[1:], self.__dict__[k]))
                    return str
            

                # Setters & getters
                
                # Encryption settings
                # Values: False, AES-128, AES-256
                @property
                def encryption(self):
                    return self._encryption
                
                @encryption.setter
                def encryption(self, encryption):
                    if self._encryption is None:
                        if valid_arg('create', 'encryption', encryption):
                            self._encryption = encryption
                        else:
                            raise Exception('Invalid arg for encryption: ' + encryption)
                    else:
                        raise Exception('Cannot reassign encryption value.')
            
    
                
                # Returns this disks mounting point
                def mounting_point(self):
                    output = self.run_hdiutil_command('info', plist=None)
                    image_info = plistlib.readPlistFromString(output)
                    for image in image_info['images']:
                        if self.path.split('/')[-1] in image['image-path']:
                            return image['system-entities'][1]['dev-entry']
                
                # Size of disk image in bytes. This does not include overhead
                @property
                def size_in_bytes(self):
                    return self._size_in_bytes
       
                @size_in_bytes.setter
                def size_in_bytes(self, size):
                    # General validation testing that size is an int and that space is available on disk
                    if not is_float(size):
                        raise Exception('Invalid argument. Size must be an integer')
                    elif size >= sys_space_available():
                        raise Exception('Invalid argument. Size is too large, not enough space.')
                
                    # Different handling cases depending on if size has been assigned before
                    if not self._size_in_bytes:
                        self._size_in_bytes = size
                    else:
                        raise Exception('Disk image size already assigned. Call DiskImage.resize() to change disk size.')
            
  
                # Path to the name of the volume (what appears when its mounted)
                @property
                def volname(self):
                    return self._volanme
        
                @volname.setter
                def volname(self, volname):
                    self._volname = volname
            
    
                # Path to disk image
                @property
                def path(self):
                    return self._path
        
                @path.setter
                def path(self, path):
                    path_ar = path.split('/')
                    if len(path_ar) > 1:
                        filename = path_ar[-1]
                        if not os.path.exists(os.path.expanduser('/'.join(path_ar[:-1]))):
                            raise Exception('Invalid argument. Path cannot be found')
                            
                    self._path = path
                
    
                # File-system type
                # Values: HFS+, 
                @property
                def fs(self):
                    return self._fs
                @fs.setter
                def fs(self, fs):
                    if not valid_arg('create', 'fs', fs):
                        raise Exception('Invalid argument. File-system (fs) arg must be among the following: ' + ', '.join(valid_args('create', 'fs')))
                    else:
                        self._fs = fs
    
                # Disk image type
                # Values: UDIF, SPARSE, SPARSEBUNDLE
                @property
                def type(self):
                    return self._type
                @type.setter
                def type(self, type):
                    if not valid_arg('create', 'type', type):
                        raise Exception('Invalid argument. Type arg must be among the following ' + ', '.join(valid_args('create')))
    
                
                ############################### os.system helpers ##########################
                
                # Generates a string containing a series of args and options formatted for bash
                def generate_command_str(self, *args, **kwargs):
                    args_str = kwargs_str = ''
                    # Format args and k-args into command
                    # All kwargs are prepended with a dash (-)
                    if len(args) > 1:
                        args_str += ' '.join(args)
    
                    if kwargs:
                        for k in kwargs.keys():
                            if kwargs[k] is None:
                                kwargs[k] = ''
                            kwargs['-' + k] = kwargs.pop(k)
                        kwargs_str = ' '.join(kwargs)
                    command = ' '.join([args_str, kwargs_str])
                    return command
                    
                # Converts a dict representing an instance of this object to a standardized format where keys 
                # are the same as those used in bash commands
                def standard_format(self):
                    options = dict(self)
                    for k in options.keys():
                        options[k[1:]] = options.pop(k)
                    options['size'] = options.pop('size_in_bytes')
                    if not options['encryption']:
                        del options['encryption']
                    return options
                # Converts bash style options to a format for this object type
                def obj_format(self, data):
                    options = dict(data)
                    options['size_in_bytes'] = options.pop('size')
                    for k in options.keys():
                        options['_' + k] = options.pop(k)
                        
                    return options
                    
                                    
                # Format options for commands
                # Retrieves options from member variables ensuring that they've undergone validation
                def create_command(self):
                    # Copy relevant options from member vars

                   options = self.__dict__
                   # Remove or change vars that don't match terminal side options
                   options = self.standard_format()
                   
                   command = run_hdiutil_command('create', options.pop('path'), **options)
                   
                   
            
                # Runs command in new process via subprocess.Popen accepting popen options via options dict
                def system(self, command, **options):
                    
                    try:
                        proc = subprocess.Popen(command, **options)
                        (out, err) = proc.communicate()
                    except OSError:
                        raise Exception('OSError, Command not found: ' + args[0])

                    if err:
                        raise Exception('Problem ocurred running command: {}. {}'.format(command, err ))
                    else:
                        return out
                        
                def run_hdiutil_command(self, *args, **kwargs):
                    
                    args = ['hdiutil'] + list(args)
                    return self.run_command(*args, **kwargs)
                    
                # Interface for executing hdiutil commands
                def run_command(self, *args, **kwargs):
                    
                    system_options = {
                        'shell' : True, 
                        'stdout' : subprocess.PIPE, 
                        'stderr' : subprocess.PIPE, 
                        'stdin' : subprocess.PIPE
                    }
                    command = self.generate_command_str(*args, **kwargs)
                    return self.system(command, **system_options)
                    
                ############## Info Extraction ################


                # Returns the path to the mounting point of the disk
                def get_mounting_point(self):
                    info = self.info()
                    if info:
                        return info['system-entities'][1]['dev-entry']
                    else:
                        raise Exception('Disk not found. Mount the image and try again.')

                
                # Helper method lets you know if the disk is mounted
                def is_mounted(self):
                    if self.info():
                        return True
                    else:
                        return False
                ############## Mounting Related ##############
                # Attaches a disk
                def attach(self):
                    cmd = 'attach'
                    self.run_hdiutil_command(cmd, self.path)
                    if self.is_encrypted():
                        read_password()
                
                # Detaches a disk
                def detach(self):
                    cmd = 'detach'
                    self.run_hdiutil_command(cmd, self.mounting_point())
                
                ############## Utility Commands ############
                # hdiutil isencrypted
                def is_encrypted(self):
                    if self.is_mounted():
                        self.info()['image-encrypted']
                    else:
                        output = self.run_command('isencrypted', self.path)
                        is_encrypted = output.split(' ')[-1]
                        if is_encrypted in ['NO']:
                            return False
                        else:
                            return True
                        
                
                # Returns relevant portion of output to command: hdiutil info 
                # Returns None if disk not mounted
                def info(self):
                    output = self.run_hdiutil_command('info', plist=None)
                    info = plistlib.readPlistFromString(output)
                    for image in info['images']:
                        if self.path.split('/')[-1] in image['image-path']:
                            return image
                # Returns output of command: hdiutil imageinfo
                def imageinfo(self):
                    output = self.run_command('imageinfo', self.path, plist=None)
                    if self.is_mounted():
                        raise Exception('Command: hdiutil imageinfo cannot be run unless the disk is mounted')
                    else:
                        return plistlib.readPlistFromString(output)
                # Returns relevant portion of command: diskutil info                
                def diskutil_info(self):
                    UTILITY_NAME = 'diskutil'
                    self.attach()
                         
                    response = self.run_command(UTILITY_NAME, 'info', self.get_mounting_point())
                    info = {}
                    for line in filter(lambda content: content != '', response.splitlines()):
                        info[line.split(':')[0].lstrip()] = line.split(':')[-1].strip()
                    return info
                    
                # Generate a dict of info used in DiskImage initialization
                # image_info arg must be
                def generate_data_model(self, image_info):
                    ext = self.path.split('.')[-1]
                    options = {
                        'volname' : 'Volume Name',
                        'fs' : 'File System Personality',
                        'size' : 'Total Size'
                    }

                    for k in options.keys():
                        options[k] = image_info[options[k]]
                    str_size = ' '.join(options['size'].split(' ')[:2])

                    options['size'] = get_bytes(str_size)
                    options['type'] = ext if ext != 'dmg' else 'UDIF'
                    
                    return options
                    
                # Extracts info of existing dmg and sets instance vars to match
                def update(self):
                    info = self.generate_data_model(self.diskutil_info())
                    for k in info.keys():
                        setattr(self, k, info[k])
                        
                # Resets the password for the disk image
                # hdiutil - chpass
                def change_password(self):
                    self.run_command('chpass')
                    read_password()
                
           
                # Resize a disk image if possible
                # hdiutil - resize
                # Include max new_size and min new_size
                def resize(self, new_size):
                    self.size_in_bytes = get_bytes(new_size)
                    print self.size
                    
                 
    
        
        
        ## Subclassed disk-image types
        class UDIF(DiskImage):
            format = 'UDRW'
        class Sparse(DiskImage):
            format = 'UDSP'
        class SparseBundle(DiskImage):
            format = 'UDSB'
            DEFAULT_BAND_SIZE = 1024 * 8
            def __init__(self, options):
                
                self._sparse_band_size = self.DEFAULT_BAND_SIZE
                super(SparseBundle, self).__init__(options)
                
            def prep_for_command(self):
                options = super(SparseBundle, self).prep_for_command()
                options += '{}={}'.format(self.sparse_band_size[1:].replace('_', '-'), self.sparse_band_size)
            
            @property
            def sparse_band_size(self):
                return _sparse_band_size
                
            #'Valid values for SPARSEBUNDLE range from 2048 to 16777216 sectors (1 MB to 8 GB)'
            # Include support for changing band sizes
            @sparse_band_size.setter
            def sparse_band_size(self, size):
                if self.sparse_band_size is None:
                    self._sparse_band_size = size
                else:
                    raise Exception('Band-size of Sparse-bundle cannot be changed.')
        
        
        
        

        
        # Merge create properly formatted option dict and copy in default values
        options = dict(self.default_options)  
            
        for k in kwargs.keys():
            if k not in self.default_options:
                raise Exception('Invalid option: ' + k)
    
        for k in options:
            if k in kwargs and kwargs[k] is not None:
                options[k] = str(kwargs[k])
        
        types = {
            'dmg' : UDIF,
            'sparse' : Sparse,
            'sparsebundle' : SparseBundle
        }
        return types[options['path'].split('.')[-1]](options)
            

    # Works like create but builds a DiskImage object from a preexisting disk image
    def load(self, path):
        if not os.path.exists(os.path.expanduser(path)):
            raise Exception('Disk image not found.')
        else:
            return self.create(path=path, create_new=False)      
    # Still necessary??
    def format_plist(self, plist):
        for k in plist.keys():
            plist[k.replace(' ', '-')] = plist.pop(k)
        return plist
        
    def flatten_plist(self, plist, flattened_plist={}, parent_key='', delimiter='_'):
        if isinstance(plist, dict):
            for k in plist.keys():
                is_dict = isinstance(plist[k], dict)
                if self.is_mutable_obj(plist[k]):

                    flattened_plist.update(self.flatten_plist(plist[k], flattened_plist, k))
                else:

                    new_key = parent_key + delimiter + k if parent_key else k
                    flattened_plist[new_key] = plist[k]
       #     print flattened_plist
        elif isinstance(plist, list):
           for index, el in enumerate(plist):
               new_key = parent_key + delimiter + str(index) if parent_key else el
               if self.is_mutable_obj(el):
                   flattened_plist.update(self.flatten_plist(el, flattened_plist, new_key))
               else:
                   flattened_plist[new_key] = el

        return flattened_plist
        
    def is_mutable_obj(self, obj):
        if isinstance(obj, dict) or isinstance(obj, list):
            return True
        else:
            return False
        

    
    ### These are helper methods directly related to DiskImage that could possibly be moved into the class later
    



## Accepts args and kewyord-args in same format as subprocess.Popen does
## Usage: run_command('hdiutil', '~/desktop/mydmg.dmg', size=100000)
##        run_command('hdiutil', 'imageinfo', plist=None)
## For options that lack arguments such as ' -plist ' pass value of None

def read_password(self):
    print('Enter a password:')
    p1 = input()                
    print('Reenter the password:')
    p2 = input()
    if p1 == p2:
        os.system('read -s ' + input())
        os.system('read -s ' + input())
        return True
    return False
## Returns a human-readable representation of bytes
def hr_bytes(bytes):
    for x in ['b','k','m','g','t']:
        if bytes < 1024.0:
            return "%3.1f%s" % (bytes, x)
        bytes /= 1024.0
        
## Converts a human-readable byte string in the formnat '12 KB' to bytes
def get_bytes(hr_size):
    # size_format 1 : 100 MB
    # size_format 2 : 100m
    byte_units = {'b' : 1, 'k' : 1000, 'm' : 1000000, 'g' : 1000000000, 't' : 1000000000000}
    
    size_format = 1 if hr_size[-2:][0].lower() in byte_units else ( 2 if hr_size[-1].lower() in byte_units else None)

    if size_format == 1:
        unit = hr_size[-2].lower()
        num = hr_size[:-3]
    elif size_format == 2:
        unit = hr_size[-1:].lower()
        num = hr_size[:-1]
    else:
        raise Exception('Human-readable size not in recognized format: ' + hr_size)

    if not is_float(num):
        raise Exception("Size must be a number. Format the size like this: 100m or 100 MB")
    if unit not in byte_units:
        raise Exception("Human-readable byte unit must be one of the following: [{}]".format( ', '.join(byte_units.keys())))
    return float(num) * byte_units[unit]

def is_float(str):
    try: 
        float(str)
        return True
    except ValueError:
        return False

def sys_space_available():
    return os.system('du -sh ~')
# Driver Code
if __name__ == '__main__':
    hdiutil = HDIUtil()
    kwargs = {'size': '10m', 'volname':'poop', 'type':'UDIF'}
    disk_image = hdiutil.load('~/desktop/mydmg2.dmg')
    disk_image.detach()

    disk_image.resize('20 mb')
    print disk_image
    
