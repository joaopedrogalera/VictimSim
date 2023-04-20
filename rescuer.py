##  RESCUER AGENT
### @Author: Tacla (UTFPR)
### Demo of use of VictimSim

import os
import random
from abstract_agent import AbstractAgent
from physical_agent import PhysAgent
from abc import ABC, abstractmethod
from math import sqrt


## Classe que define o Agente Rescuer com um plano fixo
class Rescuer(AbstractAgent):
    def __init__(self, env, config_file):
        """
        @param env: a reference to an instance of the environment class
        @param config_file: the absolute path to the agent's config file"""

        super().__init__(env, config_file)

        # Specific initialization for the rescuer
        self.plan = []              # a list of planned actions
        self.rtime = self.TLIM      # for controlling the remaining time

        # Starts in IDLE state.
        # It changes to ACTIVE when the map arrives
        self.body.set_state(PhysAgent.IDLE)

    def go_save_victims(self, walls, victims):
        """ The explorer sends the map containing the walls and
        victims' location. The rescuer becomes ACTIVE. From now,
        the deliberate method is called by the environment"""
        self.walls = walls
        self.victims = victims

        #Monta o mapa descoberto
        self.min_dx = 0
        self.min_dy = 0
        self.max_dx = 0
        self.max_dy = 0

        for p in walls:
            if p[0] < self.min_dx:
                self.min_dx = p[0] + 1
            elif p[0] > self.max_dx:
                self.max_dx = p[0] - 1

            if p[1] < self.min_dy:
                self.min_dy = p[1] + 1
            elif p[1] > self.max_dy:
                self.max_dy = p[1] - 1

        for p in victims.keys():
            if p[0] < self.min_dx:
                self.min_dx = p[0]
            elif p[0] > self.max_dx:
                self.max_dx = p[0]

            if p[1] < self.min_dy:
                self.min_dy = p[1]
            elif p[1] > self.max_dy:
                self.max_dy = p[1]

        print(self.min_dx,self.max_dx,self.min_dy,self.max_dy)

        #planning
        self.__planner()
        self.body.set_state(PhysAgent.ACTIVE)

    def __custoH(self, pos, dest):
        return sqrt((pos[0]-dest[0])**2+(pos[1]-dest[1])**2)

    def __Aestrela(self,pos,victim):
        avaiable = {}
        checked = {}

        avaiable[pos] = {'G':0,'H':self.__custoH(pos,victim),'pai':None}

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
            if corrente == victim:
                break

            nextOptions = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
            for opt in nextOptions:
                nextPosOpt = (corrente[0]+opt[0],corrente[1]+opt[1])
                if nextPosOpt in checked.keys() or nextPosOpt in self.walls or nextPosOpt[0] < self.min_dx or nextPosOpt[0] > self.max_dx or nextPosOpt[1] < self.min_dy or nextPosOpt[1] > self.max_dy:
                    continue

                if nextPosOpt not in avaiable.keys():
                    avaiable[nextPosOpt] = {'G':checked[corrente]['G']+1,'H':self.__custoH(nextPosOpt,victim),'pai':corrente}
                elif (checked[corrente]['G']+1) < avaiable[nextPosOpt]['G']:
                    avaiable[nextPosOpt]['G'] = checked[corrente]['G']+1
                    avaiable[nextPosOpt]['pai'] = corrente

        #Monta o caminho
        if not corrente:
            return False

        atual = victim
        caminho = []

        while not atual == pos:
            novoMov = (atual[0] - checked[atual]['pai'][0], atual[1] - checked[atual]['pai'][1])
            caminho.append(novoMov)
            atual = checked[atual]['pai']
        return list(reversed(caminho))


    def __planner(self):
        """ A private method that calculates the walk actions to rescue the
        victims. Further actions may be necessary and should be added in the
        deliberata method"""

        auxVictims = self.victims
        pos = (0,0)
        while auxVictims:
            gravidade = 100
            distancia = 99999
            caminho = []
            for victim in auxVictims.keys():
                _caminho = self.__Aestrela(pos,victim)

                if int(auxVictims[victim][7]) < gravidade:
                    gravidade = int(auxVictims[victim][7])
                    distancia = len(_caminho)
                    escolha = victim
                    caminho = _caminho
                elif int(auxVictims[victim][7]) == gravidade and len(_caminho) < distancia:
                    distancia = len(_caminho)
                    escolha = victim
                    caminho = _caminho

            posAux = pos
            for i in caminho:
                self.plan.append(i)

                posAux = (posAux[0]+i[0],posAux[1]+i[1])
                if posAux in auxVictims.keys():
                    del auxVictims[posAux]

            pos = escolha

        #Retorna a origem
        _caminho = self.__Aestrela(pos,(0,0))
        for i in _caminho:
            self.plan.append(i)

    def deliberate(self) -> bool:
        """ This is the choice of the next action. The simulator calls this
        method at each reasonning cycle if the agent is ACTIVE.
        Must be implemented in every agent
        @return True: there's one or more actions to do
        @return False: there's no more action to do """

        # No more actions to do
        if self.plan == []:  # empty list, no more actions to do
           return False

        # Takes the first action of the plan (walk action) and removes it from the plan
        dx, dy = self.plan.pop(0)

        # Walk - just one step per deliberation
        result = self.body.walk(dx, dy)

        # Rescue the victim at the current position
        if result == PhysAgent.EXECUTED:
            # check if there is a victim at the current position
            seq = self.body.check_for_victim()
            if seq >= 0:
                res = self.body.first_aid(seq) # True when rescued

        return True
