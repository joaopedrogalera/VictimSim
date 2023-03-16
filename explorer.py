## EXPLORER AGENT
### @Author: Tacla, UTFPR
### It walks randomly in the environment looking for victims.

import sys
import os
import random
from abstract_agent import AbstractAgent
from physical_agent import PhysAgent
from abc import ABC, abstractmethod


class Explorer(AbstractAgent):
    def __init__(self, env, config_file, resc):
        """ Construtor do agente random on-line
        @param env referencia o ambiente
        @config_file: the absolute path to the explorer's config file
        @param resc referencia o rescuer para poder acorda-lo
        """

        super().__init__(env, config_file)

        # Specific initialization for the rescuer
        self.resc = resc           # reference to the rescuer agent
        self.rtime = self.TLIM     # remaining time to explore

        self.grid = {(0,0):{'visited':[],'backtrace':[],'type':''}}
        self.pos = (0,0)


    def chooseNextPoint(self):
        nextOptions = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]

        for opt in nextOptions:
            if not opt in self.grid[self.pos]['visited'] and not (opt[0]+self.pos[0],opt[1]+self.pos[1]) in self.grid[self.pos]['backtrace']:
                #print((opt[0]+self.pos[0],opt[1]+self.pos[1]),self.grid[self.pos]['backtrace'])
                self.grid[self.pos]['visited'].append(opt)
                return True, opt

        return False, (0,0)


    def deliberate(self) -> bool:
        """ The agent chooses the next action. The simulator calls this
        method at each cycle. Must be implemented in every agent"""
        nextAvaiable, move = self.chooseNextPoint()

        if nextAvaiable:
            nextPoint = (self.pos[0]+move[0],self.pos[1]+move[1])
            print(self.pos,self.grid[self.pos]['backtrace'],nextPoint)

            if not nextPoint in self.grid:
                self.grid[nextPoint] = {'visited':[],'backtrace':[],'type':''}

            result = self.body.walk(move[0], move[1])

            if result == PhysAgent.BUMPED:
                self.grid[nextPoint]['type'] = "parede"

            if result == PhysAgent.EXECUTED:
                self.grid[nextPoint]['type'] = "ok"
                self.grid[nextPoint]['backtrace'].append(self.pos)
                self.pos = nextPoint

        else:
            print('back')
            if self.grid[self.pos]['backtrace'] == []:
                return False

            nextPoint = self.grid[self.pos]['backtrace'][-1]
            del self.grid[self.pos]['backtrace'][-1]

            dx = nextPoint[0] - self.pos[0]
            dy = nextPoint[1] - self.pos[1]

            self.pos = nextPoint

            self.body.walk(dx, dy)
            '''
            # check for victim returns -1 if there is no victim or the sequential
            # the sequential number of a found victim
            seq = self.body.check_for_victim()
            if seq >= 0:
                vs = self.body.read_vital_signals(seq)
                self.rtime -= self.COST_READ
            # print("exp: read vital signals of " + str(seq))
            # print(vs)
            '''

        '''
        # No more actions, time almost ended
        if self.rtime < 10.0:
            # time to wake up the rescuer
            # pass the walls and the victims (here, they're empty)
            print(f"{self.NAME} I believe I've remaining time of {self.rtime:.1f}")
            self.resc.go_save_victims([],[])
            return False

        dx = random.choice([-1, 0, 1])

        if dx == 0:
           dy = random.choice([-1, 1])
        else:
           dy = random.choice([-1, 0, 1])

        # Moves the body to another position
        result = self.body.walk(dx, dy)

        # Update remaining time
        if dx != 0 and dy != 0:
            self.rtime -= self.COST_DIAG
        else:
            self.rtime -= self.COST_LINE

        # Test the result of the walk action
        if result == PhysAgent.BUMPED:
            walls = 1  # build the map- to do
            # print(self.name() + ": wall or grid limit reached")

        if result == PhysAgent.EXECUTED:
            # check for victim returns -1 if there is no victim or the sequential
            # the sequential number of a found victim
            seq = self.body.check_for_victim()
            if seq >= 0:
                vs = self.body.read_vital_signals(seq)
                self.rtime -= self.COST_READ
                # print("exp: read vital signals of " + str(seq))
                # print(vs)
        '''

        return True
