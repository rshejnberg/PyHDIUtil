import subprocess

# Class consisting of various helper methods
class Helpers:
    @staticmethod
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
    @staticmethod
    def hr_bytes(bytes):
        for x in ['b','k','m','g','t']:
            if bytes < 1000.0:
                return "%3.1f%s" % (bytes, x)
            bytes /= 1000.0
        
    ## Converts a human-readable byte string in the formnat '12 KB' to bytes
    @staticmethod
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

        if not Helpers.is_float(num):
            raise Exception("Size must be a number. Format the size like this: 100m or 100 MB")
        if unit not in byte_units:
            raise Exception("Human-readable byte unit must be one of the following: [{}]".format( ', '.join(byte_units.keys())))
        return float(num) * byte_units[unit]
    @staticmethod
    def is_float(str):
        try: 
            float(str)
            return True
        except ValueError:
            return False    
    
    @staticmethod
    def bytes_available():
        out = Helpers.run_command('du', '-sh ~').split('\t')[0]
        return Helpers.get_bytes(out)
    # Generates a string containing a series of args and options formatted for bash
    @staticmethod
    def generate_command_str(*args, **kwargs):
        args_str = kwargs_str = ''
        # Format args and k-args into command
        # All kwargs are prepended with a dash (-)
        if len(args) >= 1:
            args_str += ' '.join(args)
        
        if kwargs:
            for k in kwargs.keys():
                dash_k = '-' + k
                kwargs_str += dash_k
                if kwargs[k] is not None:
                    kwargs_str += ' ' + kwargs[k]

        command = ' '.join([args_str, kwargs_str])
        return command
        
    # Runs command in new process via subprocess.Popen accepting popen options via options dict
    @staticmethod
    def system(command, **options):
        
        try:
            proc = subprocess.Popen(command, **options)
            (out, err) = proc.communicate()
        except OSError:
            raise Exception('OSError, Command not found: ' + args[0])
    
        if err:
            raise Exception(err)
        else:
            return out

        
    # Interface for executing hdiutil commands
    # Accepts args and kewyord-args in same format as subprocess.Popen does
    # Usage: run_command('hdiutil', '~/desktop/mydmg.dmg', size=100000)
    #        run_command('hdiutil', 'imageinfo', plist=None)
    # For options that lack arguments such as ' -plist ' pass value of None
    @staticmethod
    def run_command(*args, **kwargs):
        
        system_options = {
            'shell' : True, 
            'stdout' : subprocess.PIPE, 
            'stderr' : subprocess.PIPE, 
            'stdin' : subprocess.PIPE
        }
        command = Helpers.generate_command_str(*args, **kwargs)
        return Helpers.system(command, **system_options)
    