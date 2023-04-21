## EXPLORER AGENT
### @Author: Tacla, UTFPR
### It walks randomly in the environment looking for victims.

import sys
import os
import random
from abstract_agent import AbstractAgent
from physical_agent import PhysAgent
from abc import ABC, abstractmethod
from math import sqrt


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

        self.grid = {(0,0):{'backtrace':[],'type':''}}
        self.pos = (0,0)
        self.walls = []
        self.victims = {}

        self.min_dx = 0
        self.max_dx = 0
        self.min_dy = 0
        self.max_dy = 0

        self.backHome = False
        self.caminhoHome = {'caminho':[],'custo':0}

    def __custoH(self, pos, dest):
        return sqrt((pos[0]-dest[0])**2+(pos[1]-dest[1])**2)

    def __Aestrela(self,pos,dest):
        avaiable = {}
        checked = {}

        avaiable[pos] = {'G':0,'H':self.__custoH(pos,dest),'pai':None}

        while True:
            corrente = None
            custoF = 99999
            for i in avaiable.keys():
                if (avaiable[i]['G'] + avaiable[i]['H']) < custoF:
                    custoF = avaiable[i]['G'] + avaiable[i]['H']
                    corrente = i

            if not corrente:
                break

            checked[corrente] = avaiable[corrente]
            del avaiable[corrente]
            if corrente == dest:
                break

            nextOptions = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
            for opt in nextOptions:
                nextPosOpt = (corrente[0]+opt[0],corrente[1]+opt[1])
                if nextPosOpt in checked.keys() or nextPosOpt in self.walls or nextPosOpt[0] < self.min_dx or nextPosOpt[0] > self.max_dx or nextPosOpt[1] < self.min_dy or nextPosOpt[1] > self.max_dy:
                    continue

                if opt[0] != 0 and opt[1] != 0:
                    movCost = self.COST_DIAG
                else:
                    movCost = self.COST_LINE

                if nextPosOpt not in avaiable.keys():
                    avaiable[nextPosOpt] = {'G':checked[corrente]['G']+movCost,'H':self.__custoH(nextPosOpt,dest),'pai':corrente}
                elif (checked[corrente]['G']+movCost) < avaiable[nextPosOpt]['G']:
                    avaiable[nextPosOpt]['G'] = checked[corrente]['G']+movCost
                    avaiable[nextPosOpt]['pai'] = corrente

        #Monta o caminho
        if not corrente:
            return False

        atual = dest
        caminho = []

        while not atual == pos:
            novoMov = (atual[0] - checked[atual]['pai'][0], atual[1] - checked[atual]['pai'][1])
            caminho.append(novoMov)
            atual = checked[atual]['pai']
        return {'caminho':list(reversed(caminho)),'custo':checked[dest]['G']}


    def chooseNextPoint(self):
        nextOptions = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]

        for opt in nextOptions:
            if not (opt[0]+self.pos[0],opt[1]+self.pos[1]) in self.grid.keys():
                return True, opt

        return False, (0,0)


    def deliberate(self) -> bool:
        """ The agent chooses the next action. The simulator calls this
        method at each cycle. Must be implemented in every agent"""

        if not self.backHome and self.caminhoHome['custo'] < (self.rtime - (self.COST_DIAG if self.COST_DIAG > self.COST_LINE else self.COST_LINE) - self.COST_READ ):
            nextAvaiable, move = self.chooseNextPoint()

            if nextAvaiable:
                nextPoint = (self.pos[0]+move[0],self.pos[1]+move[1])

                if not nextPoint in self.grid.keys():
                    self.grid[nextPoint] = {'backtrace':[],'type':''}

                result = self.body.walk(move[0], move[1])

                if move[0] != 0 and move[1] != 0:
                    self.rtime -= self.COST_DIAG
                else:
                    self.rtime -= self.COST_LINE

                if result == PhysAgent.BUMPED:
                    self.grid[nextPoint]['type'] = "parede"
                    self.walls.append(nextPoint)

                if result == PhysAgent.EXECUTED:
                    self.grid[nextPoint]['type'] = "ok"
                    self.grid[nextPoint]['backtrace'].append(self.pos)
                    self.pos = nextPoint

                    if self.pos[0] < self.min_dx:
                        self.min_dx = self.pos[0]
                    elif self.pos[0] > self.max_dx:
                        self.max_dx = self.pos[0]

                    if self.pos[1] < self.min_dy:
                        self.min_dy = self.pos[1]
                    elif self.pos[1] > self.max_dy:
                        self.max_dy = self.pos[1]

                    # check for victim returns -1 if there is no victim or the sequential
                    # the sequential number of a found victim
                    seq = self.body.check_for_victim()
                    if seq >= 0:
                        vs = self.body.read_vital_signals(seq)
                        self.rtime -= self.COST_READ

                        self.victims[self.pos] = vs
                        #print("exp: read vital signals of " + str(seq))
                        #print(vs)

            else:
                if self.grid[self.pos]['backtrace'] == []:
                    self.resc.go_save_victims(self.walls,self.victims)
                    return False

                nextPoint = self.grid[self.pos]['backtrace'][-1]
                del self.grid[self.pos]['backtrace'][-1]

                dx = nextPoint[0] - self.pos[0]
                dy = nextPoint[1] - self.pos[1]

                self.pos = nextPoint

                self.body.walk(dx, dy)

                if dx != 0 and dy != 0:
                    self.rtime -= self.COST_DIAG
                else:
                    self.rtime -= self.COST_LINE
        else:
            if not self.backHome:
                self.backHome = True
                print("Pouco tempo restante. Voltando à base")

            if not self.caminhoHome['caminho']:
                self.resc.go_save_victims(self.walls,self.victims)
                return False

            dx = self.caminhoHome['caminho'][0][0]
            dy = self.caminhoHome['caminho'][0][1]
            del self.caminhoHome['caminho'][0]

            if dx != 0 and dy != 0:
                self.rtime -= self.COST_DIAG
            else:
                self.rtime -= self.COST_LINE

            self.body.walk(dx,dy)

        #Atualiza caminho para a base
        if not self.backHome:
            self.caminhoHome = self.__Aestrela(self.pos,(0,0))

        return True
