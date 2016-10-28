#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import socket, select, re

class IRCBot:
    '''A simple IRC bot skeleton.'''
    def __init__(self, nickname, password, debug = False):
        self.nickname = nickname
        self.password = password
        self.debug    = debug

        self.socket   = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


    def connect(self, server, channel):
        '''Connect to the specified IRC server.'''
        print("Connecting to: " + server)
        self.socket.connect((server, 6667))
        self.socket.setblocking(0)

        # We want sock_file for readline().
        self.sock_file = self.socket.makefile()
        print("Connected.")
        self.send("USER %s 0 * :Experimental bot." % self.nickname)
        self.get_line(2)
        self.send("NICK " + self.nickname)
        self.get_line(2)
        self.send("PRIVMSG NickServ :IDENTIFY %s %s" % (self.nickname,
                                                        self.password))
        self.get_line(2)
        self.send("JOIN " + channel)
        self.get_line(2)


    def debug_print(self, msg):
        '''Print a debugging message, but only when in debug mode.'''
        if (self.debug):
            print(msg)

        
    def send(self, msg):
        '''Low level function which sends a message to the socket.'''
        self.socket.send(bytearray(msg + "\r\n", "utf-8"))
        self.debug_print("-> " + msg.rstrip())

        
    def privmsg(self, channel, msg):
        '''Send a PRIVMSG to a channel or user.'''
        self.send("PRIVMSG " + channel + " :" + msg)


    def make_operator(self, channel, user):
        '''Make user an operator on channel. Only works if the bot is
already an operator.'''
        self.send("MODE %s +o %s" % (channel, user))


    def join_channel(self, channel):
        '''Have the bot join a channel.'''
        self.send("JOIN " + channel)
        
        
    def get_line(self, timeout = 10):
        '''Low level function which reads one line from the server.
If the timeout is reached, None is returned instead. get_msg() is a
higher level function which returns a parsed output.'''
        inputs  = [ self.socket ]
        outputs = [ ]

        readable, writable, exceptional = select.select(inputs,
                                                        outputs,
                                                        inputs,
                                                        timeout)
        
        if self.socket not in readable:
            # Our socket never became readable, which means we got
            # here because select timed out (see the timeout var).
            return None

        #try:
        line = self.sock_file.readline()
        #except socket.timeout:
        #    return None

        line = line.rstrip()
        self.debug_print("<- " + line)

        if line.startswith("PING "):
            # The server has sent us a PING to see if we're still
            # alive and connected. We must respond with a PONG, or
            # the server will disconnect us.
            self.send("PONG " + line.split()[1] + "\r\n")
            return None

        return line


    def get_msg(self, timeout = 10):
        '''Higher level function than get_line(). get_msg() returns a
list (sender, msg_type, channel, msg_text). Any of these could be
None.'''
        return self.parse_irc_msg(self.get_line(timeout))


    def parse_irc_msg(self, line):
        '''Low level IRC protocol parsing function.'''
        sender   = None
        msg_type = None
        channel  = None
        msg_text = None

        if not line:
            return None, None, None, None
        # <L3viathan> enfors: ":enfors!foo".split("!")[0][1:]
        match = re.search("^:([^!]*)!" \
                          "[^ ]* ([^ ]+) " \
                          "([^ ]+) ?" \
                          "(:(.*))?$", line)

        if match:
            sender    = match.group(1)
            msg_type  = match.group(2)
            channel   = match.group(3)
            msg_text  = match.group(5)
            
        if sender:
            self.debug_print("   SENDER:    '%s'" % sender)

        if msg_type:
            self.debug_print("   MSG_TYPE:  '%s'" % msg_type)
            
        if channel:
            self.debug_print("   CHANNEL:   '%s'" % channel)

        if msg_text:
            self.debug_print("   MSG_TEXT:  '%s'" % msg_text)

        return sender, msg_type, channel, msg_text