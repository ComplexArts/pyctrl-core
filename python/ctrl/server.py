import warnings
import socketserver

from . import packet
import ctrl

verbose_level = 0
controller = ctrl.Controller()
commands = {}

def verbose(value = 1):
    global verbose_level
    verbose_level = value

def version():
    return '1.0'

def help(value):

    global commands
    help_str = ''

    if value:
        function = commands.get(value, ('', '', None, ''))[2]
        if not function:
            help_str += "Error: '{}' is not a command\n".format(value)
        if function.__doc__:
            return function.__doc__
        else:
            return 'Help not available'

    # else:
    help_str += "\n".join([' ' + k + ': ' + v[3] 
                           for (k,v) in 
                           zip(commands.keys(), commands.values())])
    help_str = """
Controller Server, version {}
Available commands:
""".format(version()) + help_str

    return help_str
        
def set_controller(_controller = ctrl.Controller()):

    # initialize controller
    global controller, commands
    controller = _controller
        
    # TODO: Complete public controller methods
    commands = { 
        'h': ('S',  'S', help,
              'Help'),

        'i': ('S',  'S', controller.info,
              'Controller info'),

        'G': ('S', '', controller.add_signal,
              'Add signal'),
        'A': ('SD', '', controller.set_signal,
              'Set signal'),
        'L': ('S', '', controller.remove_signal,
              'Remove signal'),

        'S': ('SPP', '', controller.add_sink,
              'Add sink'),
        'I': ('SSP', '', controller.set_sink,
              'Set sink'),
        'N': ('S', 'P', controller.read_sink,
              'Read sink'),
        'K': ('S', '', controller.remove_sink,
              'Remove sink'),

        'O': ('SPP', '', controller.add_source,
              'Add source'),
        'U': ('SSP', '', controller.set_source,
              'Set source'),
        'R': ('S', '', controller.remove_source,
              'Remove source'),

        'F': ('SPPP', '', controller.add_filter,
              'Add filter'),
        'T': ('SSP', '', controller.set_filter,
              'Set filter'),
        'E': ('S', '', controller.remove_filter,
              'Remove sink'),


        's': ('',  '',  controller.start,
              'Start control loop'),
        't': ('',  '',  controller.stop,
              'Stop control loop'),
        
        'p': ('',  'D', controller.get_period,
              'Get period'),

    }

# Initialize default controller
set_controller(controller)

class Handler(socketserver.StreamRequestHandler):

    #def __init__(self, request, client_address, server):
    #    super().__init__(request, client_address, server)

    def handle(self):
        
        global verbose_level, controller, commands

        if verbose_level > 0:
            print('> Connected to {}'.format(self.client_address))

        # Read command
        while True:
            
            try:
                (type, code) = packet.unpack_stream(self.rfile)
            except NameError as e:
                # TODO: Differentiate closed socket from error
                if verbose_level > 0:
                    print('> Closed connection to {}'.format(self.client_address))
                break
            
            if type == 'C':

                if verbose_level > 1:
                    print(">> Got '{}'".format(code))

                (argument_type, output_type, function,
                 short_help) = commands.get(code, ('', '', None, ''))
                
                if verbose_level > 2:
                    print(">>> Will execute '{}({})'".format(code, argument_type))
                
                # Handle input arguments
                argument = []
                for letter in argument_type:
                    (type, arg) = packet.unpack_stream(self.rfile)
                    argument.append(arg)

                if verbose_level > 2:
                    print('>>> Argument = {}'.format(argument))

                try:
                    # Call function
                    message = function(*argument)

                except:
                    # TODO: Handle errors
                    warnings.warn('ERROR')
                    pass

                # Wrap outupt 
                if output_type == '':
                    message = None
                else:
                    message = (output_type, message)

                if verbose_level > 2:
                    print('>>> Message = {}'.format(message))

            else:
                message = ('S', 
                           "Command expected, '{}' received".format(type))

            if message is not None:
                # Send message back
                if verbose_level > 2:
                    print('>>> Sending message = ', *message)
                    if verbose_level > 3:
                        print('>>>> Message content = ', packet.pack(*message))
                self.wfile.write(packet.pack(*message))

            message = ('A', code)
            if verbose_level > 2:
                print(">>> Acknowledge '{}'\n".format(code))
            self.wfile.write(packet.pack(*message))
