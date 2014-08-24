class Constants:
    @staticmethod
    def valid_args(cmd, option):
        return commands[cmd][option]
        
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