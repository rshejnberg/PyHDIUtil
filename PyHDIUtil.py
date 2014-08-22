#
#                                                    Raphael Shejnberg, 8/21/14
#

import os, plistlib
from HDIUtil_Constants import Constants
from utils import Helpers

class HDIUtil(object):

    # Utility name
    NAME = 'hdiutil'

    # Set default options here                
    DEFAULT_FS_INDEX = 0
    DEFAULT_TYPE_INDEX = 0

    DEFAULT_FS = get_valid_args('create', 'fs')[DEFAULT_FS_INDEX]
    DEFAULT_TYPE = get_valid_args('create', 'type')[DEFAULT_TYPE_INDEX]
    
    def __init__(self):
        # Hash of default values for given options
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

                    if 'create_new' in options:
                        create_new = False if options.pop('create_new') is 'False' else True
                    
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


                # Setters and getters
                
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
                def size(self):
                    return self._size
       
                @size.setter
                def size(self, size):
                    
                    if isinstance(size, str):
                        size = Helpers.get_bytes(size)
                        
                    # General validation testing that size is an int and that space is available on disk
                    if not Helpers.is_float(size):
                        raise Exception('Invalid argument. Size must be an integer')
                    elif size >= Helpers.bytes_available():
                        raise Exception('Invalid argument. Size is too large, not enough space.')
                
                    # Different handling cases depending on if size has been assigned before
                    if self._size:
                        self.run_hdiutil_command('resize', self.path, size=Helpers.hr_bytes(size))
                        print('Disk image resized to ' + Helpers.hr_bytes(size))
                    self._size = size
            
  
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
    
                

                # Formatting Helpers
                #
                # Converts a dict representing an instance of this object to a standardized format where keys 
                # are the same as those used in bash commands
                def standard_format(self):
                    options = dict(self)
                    for k in options.keys():
                        options[k[1:]] = options.pop(k)
                    if not options['encryption']:
                        del options['encryption']
                    return options
                # Converts bash style options to a format for this object type
                def obj_format(self, data):
                    options = dict(data)
                    for k in options.keys():
                        options['_' + k] = options.pop(k)
                        
                    return options
                    
                                    

                # Runs an hdiutil command
                def run_hdiutil_command(self, *args, **kwargs):
    
                    args = ['hdiutil'] + list(args)
                    try:
                        out = Helpers.run_command(*args, **kwargs)
                    except Exception, e:
                        # Some commands require the disk-image to be mounted/unmounted. If ran when it isn't it returns
                        # saying 'Resource temporarily unavailable'
                        if 'Resource temporarily unavailable' in str(e):
                            if self.is_mounted():
                                self.detach()
                            else:
                                self.attach()
                        out = Helpers.run_command(*args, **kwargs)
                    return out
                    
                # Create a disk image from self
                def create_command(self):
                   options = self.__dict__
                   options = self.standard_format()
                   command = run_hdiutil_command('create', options.pop('path'), **options)
                   
                   
            

                # Info Extraction Helpers
                #
                # Extracts info of existing dmg and sets instance vars to match
                def update(self):
                    info = self.generate_data_model(self.diskutil_info())
                    for k in info.keys():
                        setattr(self, k, info[k])
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
                         
                    response = Helpers.run_command(UTILITY_NAME, 'info', self.get_mounting_point())
                    info = {}
                    for line in filter(lambda content: content != '', response.splitlines()):
                        info[line.split(':')[0].lstrip()] = line.split(':')[-1].strip()
                    return info
                        
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
        

# Driver Code
if __name__ == '__main__':
    hdiutil = HDIUtil()
    kwargs = {'size': '10m', 'volname':'poop', 'type':'UDIF'}
    disk_image = hdiutil.load('~/desktop/mydmg2.dmg')
    disk_image.size = '20m'

    print disk_image