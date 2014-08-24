#
#                                                    Raphael Shejnberg, 8/21/14
#

import os, plistlib
from HDIUtil_Constants import Constants
from utils import Helpers

# Methods to possibly be move over into seperate diskutil class
def change_volname(old_name, new_name):
    Helpers.run_command('diskutil', 'rename', old_name, new_name)
    
class HDIUtil(object):

    # Utility name
    NAME = 'hdiutil'
    
    def __init__(self):
        # Hash of default values for given options
        self._default_options = {
                     'size' : '100m', 
                     'volname' : 'Volume', 
                     'path' : '~', 
                     'encryption' : False,
                     'fs' : 'HFS+', 
                     'type' : 'UDIF',
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
	
    ## Disk Image Factory
    #
    ## Usage: create(path='/my/path', size='1024b', type='SPARSE') 
    ## All disk-image classes are contained in this method to provide regulation over object creation
    #
    def create(self, *args, **kwargs):
        ## DiskImage Class
        # 
        ## All base logic for disk image actions contained in here
    	class DiskImage(object):
                UTILITY_NAME = 'hdiutil'
                
                ## Usage: Has multiple use-cases regarding disk-images
                ##    Case 1: Create a disk-image
                ##       DiskImage(path='some/path', size='1024', type='SPARSE')
                ##    Case 2: Generate an object from an existing disk-image
                ##       DiskImage(path='some/path.dmg', create_new=False)
                def __init__(self, options):
                    create_new = False if 'create_new' in options and options.pop('create_new') is 'False' else True
                    # Set path and retrieve info from disk-image (process dependent on self.path)
                    if not create_new:
                        self.path = options.pop('path')
                        options = self.generate_data_model(self.diskutil_info())

                    init_options = self.obj_format(options)
                    
                    # Initialize all fields to None
                    # Validation of member variables that occurs in the setters does not happen on the initial assignment of variables
                    # this ensures that all field will be validated on initialization
                    self.__dict__.update(dict([(k, None) for k in init_options.keys()]))

                    # Copy values to self
                    { k: setattr(self, k, v) for k, v in init_options.items() }
                    

                    # Execute hdiutil create command
                    if create_new:
                        self.create_command()

                
                def __repr__(self):
                    str = ''
                    
                    for k in self.__dict__.keys():
                        str += ("{0:20}:\t\t{1:<10}\n".format(k[1:], self.__dict__[k]))
                    return str


                # Setters and getters
                
                # Encryption settings
                # Values: False, AES-128, AES-256
                @property
                def encryption(self):
                    return self._encryption
                
                @encryption.setter
                def encryption(self, encryption):
                    if self._encryption is None:
                        if encryption in Constants.valid_args('create', 'encryption'):
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
                def size(self):
                    return self._size
       
                @size.setter
                def size(self, size):
                    
                    size = Helpers.get_bytes(size) if isinstance(size, str) else size
                        
                    # General validation testing that size is an int and that space is available on disk
                    if not Helpers.is_float(size):
                        raise Exception('Invalid argument. Size must be an integer')
                    elif size >= Helpers.bytes_available():
                        raise Exception('Invalid argument. Size is too large, not enough space.')
                
                    # Different handling cases depending on if size has been assigned before
                    if self._size:
                        self.run_hdiutil_command('resize', self.path, size=Helpers.hr_bytes(size))
                    self._size = size
                    
  
                # Path to the name of the volume (what appears when its mounted)
                @property
                def volname(self):
                    return self._volname
        
                @volname.setter
                def volname(self, volname):
                    change_volname(self.volname, volname)
                    self._volname = volname
            
    
                # Path to disk image
                @property
                def path(self): return self._path
        
                @path.setter
                def path(self, path):
                    path_ar = path.split('/')
                    if len(path_ar) > 1:
                        filename = path_ar[-1]
                        if not os.path.exists(os.path.expanduser('/'.join(path_ar[:-1]))):
                            raise Exception('Invalid argument. Path cannot be found.')
                            
                    self._path = path
                
    
                # File-system type
                # Values: HFS+, 
                @property
                def fs(self): return self._fs
                
                @fs.setter
                def fs(self, fs):
                    if fs not in Constants.valid_args('create', 'fs'):
                        raise Exception('Invalid argument. File-system (fs) arg must be among the following: ' + ', '.join(valid_args('create', 'fs')))
                    else:
                        self._fs = fs
    
                # Disk image type
                # Values: UDIF, SPARSE, SPARSEBUNDLE
                @property
                def type(self): return self._type
                
                @type.setter
                def type(self, type):
                    if not type in Constants.valid_args('create', 'type'):
                        raise Exception('Invalid argument. Type arg must be among the following ' + ', '.join(valid_args('create')))
    
                

                # Formatting Helpers
                #
                # Converts a dict representing an instance of this object to a standardized format where keys 
                # are the same as those used in bash commands
                def standard_format(self):
                    # Generate list form dict(self) but with leading underscore removed
                    options = {k[1:]: v for k, v in self.__dict__}
                    if not options['encryption']:
                        del options['encryption']
                    return options
                # Converts bash style options to a format for this object type
                def obj_format(self, data): return {'_' + k: v for k, v in dict(data).items()}
                                    
                def run_disk_util_command(self, *args, **kwargs):
                    out = Helpers.run_command(*args, **kwargs)
                # Runs an hdiutil command
                def run_hdiutil_command(self, *args, **kwargs):
                    args = ['hdiutil'] + list(args)
                    try:
                        out = Helpers.run_command(*args, **kwargs)
                    except Exception, e:
                        # Some commands require the disk-image to be mounted/unmounted. If ran when it isn't it returns
                        # saying 'Resource temporarily unavailable'
                        if 'Resource temporarily unavailable' in str(e):
                            self.detach() if self.is_mounted() else self.attach()
   
                        out = Helpers.run_command(*args, **kwargs)
                    return out
                    
                # Create a disk image from self
                def create_command(self):

                   options = self.standard_format()
                   command = run_hdiutil_command('create', options.pop('path'), **options)
                   
                   
            

                # Info Extraction Helpers
                #
                # Extracts info of existing dmg and sets instance vars to match
                def update(self):
                    info = self.generate_data_model(self.diskutil_info())
                    {k: setattr(self, k, v) for k, v in info.items()}

                # Returns the path to the mounting point of the disk
                def get_mounting_point(self):
                    info = self.info()
                    if info:
                        return info['system-entities'][1]['dev-entry']
                    else:
                        raise Exception('Disk not found. Mount the image and try again.')

                
                # Helper method lets you know if the disk is mounted
                def is_mounted(self): return True if self.info() else False

                # Generate a dict of info used in DiskImage initialization
                # image_info arg must be
                def generate_data_model(self, image_info):
                    ext = self.path.split('.')[-1]
                    options = {
                        'volname' : 'Volume Name',
                        'fs' : 'File System Personality',
                        'size' : 'Total Size'
                    }
                    options = {k: image_info[v] for k, v in options.items()}
                    str_size = ' '.join(options['size'].split(' ')[:2])

                    options['size'] = Helpers.get_bytes(str_size)
                    options['type'] = ext if ext != 'dmg' else 'UDIF'
                    
                    return options
                
                # Commands
                #
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
                
                # hdiutil isencrypted
                def is_encrypted(self):
                    if self.is_mounted(): self.info()['image-encrypted']
                    else:
                        output = self.run_command('isencrypted', self.path)
                        is_encrypted = output.split(' ')[-1]
                        return False if is_encrypted in ['NO'] else True
     
                        
                
                # Returns relevant portion of output to command: hdiutil info 
                # Returns None if disk not mounted
                def info(self):
                    output = self.run_hdiutil_command('info', plist=None)
                    info = plistlib.readPlistFromString(output)
                    return [image for image in info['images'] if self.path.split('/')[-1] in image['image-path']][0]

                # Returns output of command: hdiutil imageinfo
                def imageinfo(self):
                    output = self.run_command('imageinfo', self.path, plist=None)
                    if self.is_mounted(): raise Exception('Command: hdiutil imageinfo cannot be run unless the disk is mounted')
                    else: return plistlib.readPlistFromString(output)
                # Returns relevant portion of command: diskutil info                
                def diskutil_info(self):
                    UTILITY_NAME = 'diskutil'
                    self.attach()
                         
                    response = Helpers.run_command(UTILITY_NAME, 'info', self.get_mounting_point())
                    non_empty_lines = [line for line in response.splitlines() if line != '']
                    return {line.split(':')[0].lstrip() : line.split(':')[-1].strip() for line in non_empty_lines}
                # Resets the password for the disk image
                # hdiutil - chpass
                def change_password(self):
                    self.run_command('chpass')
                    read_password()
                
           

                    
                 
    
        
        
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
        invalid_options = [el for el in options if el not in self.default_options]
        if invalid_options:
            raise Exception('Invalid option: ' + ', '.join(invalid_options)) 
        
        
        options = {k: str(kwargs[k]) for k, v in options.items() if k in kwargs and kwargs[k] is not None}

        
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

# Driver Code
if __name__ == '__main__':
    hdiutil = HDIUtil()
    kwargs = {'size': '10m', 'volname':'poop', 'type':'UDIF'}
    disk_image = hdiutil.load('~/desktop/mydmg2.dmg')
    disk_image.volname = 'poopy'

    print disk_image