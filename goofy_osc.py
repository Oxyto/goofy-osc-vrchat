#!/usr/bin/env python3

'''
This is the main application in one file.
You must have Jinja2 and PythonOSC module in order to execute the program.
'''
import random
import multiprocessing
import os
import time
from typing import Callable
import jinja2
from pythonosc import udp_client  # type: ignore[attr-defined]


TIMEOUT_SEC = 5
MESSAGE_BUFFER_SIZE = 4096
HELP_MSG = '''\
[*] Usage:
- help (h)
- start (s)
- stat (st)
- kill (k)
- change (c)
- quit (q)
- write (w)
- write_block (W)
- print (p)
- clear (cl)
- load
- save
'''


class ModeException(BaseException):
    '''
    Exception when the mode selected is invalid.
    '''
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class GoofyOSC:
    '''
    The main application class.

    @param host: `str` - The host where VRChat runs.
    @param port: `int` - The port of the OSC channel.
    '''
    __slots__ = (
        'client',
        'message',
        'message_id',
        'process'
    )

    def __init__(self, host: str, port: int | str):
        if isinstance(port, int):
            self.client = udp_client.SimpleUDPClient(host, port)
        else:
            self.client = udp_client.SimpleUDPClient(host, int(port))
        self.message = multiprocessing.Array(
            'c', MESSAGE_BUFFER_SIZE, lock=False)
        self.message_id = multiprocessing.Value('i', 1, lock=False)
        self.process = multiprocessing.Process(
            target=self.runner,
            daemon=True
        )
        self.message.value = b'[placeholder]'

    def runner(self):
        '''
        The running process that sends the message every n seconds.
        '''
        try:
            while True:
                match self.message_id.value:
                    case 0:
                        output_message = str(self.message.value, 'utf-8')
                    case 1:
                        output_message: str = jinja2.Template(
                            str(self.message.value, 'utf-8')
                        ).render(os=os, time=time, random=random)
                    case _:
                        raise ModeException('[!] Error: Invalid mode.')
                self.client.send_message(  # type: ignore
                    '/chatbox/input', (output_message, True))  # type: ignore
                time.sleep(TIMEOUT_SEC)
        except (ModeException, jinja2.TemplateError) as e:
            with open('output.log', 'a', encoding='utf-8') as file:
                file.write(str(e))

    def start(self, _: list[str]):
        '''
        Starts the background process.
        '''
        if self.process.is_alive() or self.process.exitcode is not None:
            return
        self.process.start()
        print('[+] Started.')

    def kill(self, _: list[str]):
        '''
        Kills the background process.
        '''
        if not self.process.is_alive() and self.process.exitcode is None:
            return
        self.process.terminate()
        print('[-] Terminated.')
        self.process = multiprocessing.Process(
            target=self.runner,
            daemon=True
        )

    def stat(self, _: list[str]):
        '''
        Checks if the background process is running.
        '''
        if self.process.is_alive():
            print('[+] Process is running.')
            return
        if self.process.exitcode is not None:
            print(
                f'[!] Process exited with error code {self.process.exitcode}'
            )
            return
        print('[-] Process is not running.')

    def change(self, args: list[str]):
        '''
        Changes the chatbox's interpretation (plain text, formated, ...).
        '''
        if len(args) == 0:
            print('[!] Missing mode number')
            return
        try:
            nb = int(args[0])

            match nb:
                case 0:
                    print('[*] Plain text mode.')
                case 1:
                    print('[*] Formated mode.')
                case _:
                    print('[!] Invalid mode.')
                    return
            self.message_id.value = nb

        except ValueError as e:
            print('[!] Value must be a positive integer.')
            print(str(e))

    def write_block(self, _: list[str]):
        '''
        Very small chatbox editor (terminated by \'.\').
        '''
        self.message.value = b''
        while (msg := input('[W] > ')) != '.':
            self.message.value += bytes(msg, 'utf-8') + b'\n'
        print('[*] Message block written.')

    def write(self, args: list[str]):
        '''
        Writes a simple and constant message in the chatbox.
        '''
        if len(args) == 0:
            print('[!] You must supply a message.')
            return
        self.message.value = bytes(' '.join(args), 'utf-8')

    def save_to_file(self, args: list[str]):
        '''
        The chatbox's saver function.
        '''
        if len(args) == 0:
            print('[!] You must supply a filepath.')
            return
        try:
            with open(args[0], 'wb') as file:
                file.write(self.message.value)
                file.flush()
                print(f'[*] File save. ({file.tell()}) bytes.')
        except FileExistsError:
            print(f'[!] The filepath {args[0]} already exists.')

    def load_file(self, args: list[str]):
        '''
        The chatbox's loader function.
        '''
        if len(args) == 0:
            print('[!] You must supply a filepath.')
            return
        try:
            with open(args[0], 'rb') as file:
                self.message.value = file.read()
                print(f'[*] File loaded. ({file.tell()}) bytes.')
        except FileNotFoundError:
            print(f'[!] The filepath {args[0]} doesn\'t exists.')
        except ValueError:
            print('[!] Cannot read the file (or the file exceeds 4096 bytes).')

    def helper(self, _: list[str]):
        '''
        Prints help message.
        '''
        return print(HELP_MSG)

    def printer(self, _: list[str]):
        '''
        Prints the value of the current message of the chatbox.
        '''
        return print(self.message.value)

    def invalid(self, _: list[str]):
        '''
        Prints out an error message when command is not found.
        '''
        return print('[!] Invalid command, type \'help\' or \'h\' for hints.')

    def clear(self, _: list[str]):
        '''
        Clears the terminal.
        '''
        os.system('cls||clear')

    def ta_bouche(self, _: list[str]):
        '''
        Dinguerie.
        '''
        print('Dinguerie.')
        exit(42)

    def quit(self, _: list[str]):
        '''
        Exits the program.
        '''
        exit()

    def cli(self):
        '''
        The console interface of the application.
        '''
        lookup_table: dict[str, Callable[[list[str]], None]] = {
            'h': self.helper,
            '?': self.helper,
            'help': self.helper,
            'p': self.printer,
            'print': self.printer,
            'w': self.write,
            'write': self.write,
            'W': self.write_block,
            'write_block': self.write_block,
            's': self.start,
            'start': self.start,
            'st': self.stat,
            'stat': self.stat,
            'save': self.save_to_file,
            'load': self.load_file,
            'k': self.kill,
            'kill': self.kill,
            'c': self.change,
            'change': self.change,
            'cl': self.clear,
            'cls': self.clear,
            'clear': self.clear,
            'tb': self.ta_bouche,
            'ta_bouche': self.ta_bouche,
            'q': self.quit,
            'quit': self.quit
        }
        while True:
            tokens = input('> ').split()

            if not tokens:
                continue

            cmd = tokens[0]
            args = tokens[1:] if len(tokens) > 1 else []
            lookup_table.get(cmd, self.invalid)(args)


if __name__ == '__main__':
    goofy = GoofyOSC('127.0.0.1', 9000)
    goofy.cli()
