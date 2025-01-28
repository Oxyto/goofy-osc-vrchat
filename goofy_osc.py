import random
import multiprocessing
import threading
import os
import time
import ctypes
import jinja2
import itertools
from pythonosc import udp_client


TIMEOUT_SEC = 5


class GoofyOSC:
  __slots__ = (
      'client',
      'message',
      'message_id',
      'process'
  )

  def __init__(self, host: str, port: int):
    self.client = udp_client.SimpleUDPClient(host, port)
    self.message = multiprocessing.Array('c', 4096, lock=False)
    self.message_id = multiprocessing.Value('i', 0, lock=False)
    self.process = multiprocessing.Process(
        target=self.runner,
        daemon=True
    )
    self.message.value = b'[placeholder]'

  def runner(self):
    try:
      while True:
        match self.message_id.value:
          case 0:
            output_message = str(self.message.value, 'utf-8')
          case 1:
            output_message = jinja2.Template(
                str(self.message.value, "utf-8")).render(os=os, time=time, random=random)
          case _:
            raise BaseException('[!] Error: Invalid mode.')
        self.client.send_message(
            '/chatbox/input', (output_message, True))
        time.sleep(TIMEOUT_SEC)
    except BaseException as e:
      with open('output.log', 'a') as file:
        file.write(str(e))

  def start(self):
    if self.process.exitcode is not None or self.process.is_alive():
      return
    self.process.start()

  def kill(self):
    if self.process.exitcode is None and not self.process.is_alive():
      return
    self.process.terminate()
    print('[*] Terminated.')
    self.process = multiprocessing.Process(
        target=self.runner,
        daemon=True
    )

  def stat(self):
    if self.process.is_alive():
      print('[+] Process is running.')
      return
    if self.process.exitcode is not None:
      print(
          f'[!] Process exited with error code {self.process.exitcode}'
      )
      return
    print('[-] Process is not running.')

  def change(self, args: str):
    if len(args) == 0:
      print('[!] Missing mode number')
      return
    try:
      nb = int(args[0])

      match nb:
        case 0:
          print('[*] Default mode.')
        case 1:
          print('[*] Formated mode.')
        case _:
          print('[!] Invalid mode.')
          return
      self.message_id.value = nb
      
    except ValueError as e:
      print('[!] Value must be a positive integer.')
      print(str(e))

  def write_block(self, args: str):
    self.message.value = b''
    while (msg := input('[W] > ')) != '.':
      self.message.value += bytes(msg, 'utf-8') + b'\n'
    print('[*] Message block written.')

  def write(self, args: str):
    if len(args) == 0:
      print('[!] You must supply a message.')
      return
    self.message.value = bytes(' '.join(args), 'utf-8')

  def save_to_file(self, args: str):
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

  def load_file(self, args: str):
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
      print(f'[!] Cannot read the file (or the file exceeds 4096 bytes).')

  def cli(self):
    stop = False

    while not stop:
      tokens: list[str] | str = input("> ").split()

      if len(tokens) == 0:
        continue

      cmd = tokens[0]
      args = tokens[1:] if len(tokens) > 1 else []

      if cmd in ('h', 'help', '?'):
        print(
            '[*] Usage: help, start, stat, kill, stop, change, quit, write(_block), print, clear, load, save'
        )
        continue
      if cmd in ('p', 'print'):
        print(self.message.value)
        continue
      if cmd in ('w', 'write'):
        self.write(args)
        continue
      if cmd in ('W', 'write_block'):
        self.write_block(args)
        continue
      if cmd in ('s', 'start'):
        self.start()
        continue
      if cmd in ('st', 'stat'):
        self.stat()
        continue
      if cmd in ('save'):
        threading.Thread(target=self.save_to_file,
                         args=(args,), daemon=True).start()
        continue
      if cmd in ('load'):
        threading.Thread(target=self.load_file,
                         args=(args,), daemon=True).start()
        continue
      if cmd in ('k', 'kill', 'stop'):
        self.kill()
        continue
      if cmd in ('c', 'change'):
        self.change(args)
        continue
      if cmd in ('cls', 'cl', 'clear'):
        os.system('cls||clear')
        continue
      if cmd in ('tb', 'ta_bouche'):
        print('TOI TA BOUCHE.')
        exit(42)
      if cmd in ('q', 'quit'):
        stop = True
      else:
        print('[!] Invalid command, type "help" or "h" for hints.')


if __name__ == '__main__':
  goofy = GoofyOSC('127.0.0.1', 9000)
  goofy.cli()
