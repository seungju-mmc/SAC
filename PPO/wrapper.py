import torch
import numpy as np
import PPO.Trainer


def MLPBatch(self, step, epoch, f) -> None:
    self: PPO.Trainer.PPOOnPolicyTrainer
    rstate, action, reward, done = \
        [], [], [], []
    tState = []
    for data in self.replayMemory[0]:
        s, a, r, ns, d = data
        rstate.append(s[0])
        action.append(a)
        reward.append(r)
        done.append(d)
    for data in self.ReplayMemory_Trajectory:
        ts = data
        tState.append(ts)
    state = torch.cat(rstate, dim=0)
    nstate = torch.cat((state, ns[0]), dim=0)
    reward = np.array(reward)
    done = np.array(done)
    action = torch.tensor(action).to(self.device).view(-1, self.aSize)
    state = tuple([state])
    for _ in range(epoch):

        value = self.agent.critic.forward(tuple([nstate]))[0]  # . step, nAgent, 1 -> -1, 1
        nvalue = value[self.nAgent:]
        value = value[:-self.nAgent]
        gT, gAE = self.getReturn(reward, value, nvalue, done)

        self.zeroGrad()
        f(self, state, action, gT, gAE, value, step, epoch)
        self.step(step+_, epoch)


def MLPState(self, obs) -> list:
    rState = torch.tensor(obs[:, :6]).float().to(self.device)
    lidarPt = torch.tensor(obs[:, 8:8+self.sSize[-1]]).float().to(self.device)
    state = tuple([torch.cat((rState, lidarPt), dim=1)])
    return state


def CNN1DLTMPState(self, obs) -> tuple:
    rState = torch.tensor(obs[:, :6]).to(self.device)
    lidarPt = torch.tensor(obs[:, 8:self.sSize[-1]+8]).to(self.device)
    lidarPt = torch.unsqueeze(lidarPt, dim=1)
    state = (rState, lidarPt)
    return state


def CNN1DLTMPBatch(self, step, epoch, f):
    self: PPO.Trainer.PPOOnPolicyTrainer
    k1 = 160
    k2 = 10
    div = int(k1/k2)
    rstate, lidarPt, action, reward, done = \
        [], [], [], [], []
    trstate, tlidarPt = [], []
    for data in self.replayMemory[0]:
        s, a, r, ns, d = data
        rstate.append(s[0])
        lidarPt.append(s[1])
        action.append(a)
        reward.append(r)
        done.append(d)
    for data in self.ReplayMemory_Trajectory:
        ts = data
        trstate.append(ts[0])
        tlidarPt.append(ts[1])
    if len(trstate) == k1:
        zeroMode = True
    else:
        tState = (torch.cat(trstate[:-k1], dim=0), torch.cat(tlidarPt[:-k1], dim=0))
        zeroMode = False
    if (len(trstate) == (self.data['env']['MaxStep']-1)):
        lastMode = True
    else:
        lastMode = False
    rstate = torch.cat(rstate, dim=0)
    lidarPt = torch.cat(lidarPt, dim=0)
    nrstate, nlidarPt = ns
    nrstate, nlidarPt = torch.cat((rstate, nrstate), dim=0), torch.cat((lidarPt, nlidarPt), dim=0)
    lidarPt = lidarPt.view((-1, self.nAgent, 1, self.sSize[-1]))
    rstate = rstate.view((-1, self.nAgent, 6))
   
    nstate = (nrstate, nlidarPt)

    reward = np.array(reward)
    done = np.array(done)
    action = torch.tensor(action).to(self.device)

    self.agent.actor.zeroCellState()
    self.agent.critic.zeroCellState()
    self.copyAgent.actor.zeroCellState()
    self.copyAgent.critic.zeroCellState()

    if zeroMode is False:
        self.agent.critic.forward(tState)
        self.copyAgent.critic.forward(tState)
        self.agent.actor.forward(tState)
        self.copyAgent.actor.forward(tState)

    # 1. calculate the target value for actor and critic
    self.agent.actor.detachCellState()
    InitActorCellState = self.agent.actor.getCellState()
    InitCopyActorCellState = self.copyAgent.actor.getCellState()

    self.agent.critic.detachCellState()
    InitCriticCellState = self.agent.critic.getCellState()
    InitCopyCriticCellState = self.copyAgent.critic.getCellState()

    # 2. implemented the training using the truncated BPTT
    for _ in range(epoch):
        self.agent.actor.setCellState(InitActorCellState)
        self.agent.critic.setCellState(InitCriticCellState)

        value = self.agent.critic.forward(nstate)[0]  # . step, nAgent, 1 -> -1, 1
        value = value.view(k1+1, self.nAgent, 1)
        nvalue = value[1:]
        value = value[:-1]
        gT, gAE = self.getReturn(reward, value, nvalue, done, lastMode=lastMode)
        gT = gT.view(k1, self.nAgent)
        gAE = gAE.view(k1, self.nAgent)

        self.agent.critic.setCellState(InitCriticCellState)
        self.copyAgent.actor.setCellState(InitCopyActorCellState)
        self.copyAgent.critic.setCellState(InitCopyCriticCellState)
        self.zeroGrad()
        for i in range(div):
            _rstate = rstate[i*k2:(i+1)*k2].view(-1, 6)
            _lidarpt = lidarPt[i*k2:(1+i)*k2].view(-1, 1, self.sSize[-1])
            _state = (_rstate, _lidarpt)
            _action = action[i*k2:(i+1)*k2].view((-1, 2))
            _gT = gT[i*k2:(i+1)*k2].view(-1, 1)
            _gAE = gAE[i*k2:(i+1)*k2].view(-1, 1)
            _value = value[i*k2:(i+1)*k2].view(-1, 1)
            f(self, _state, _action, _gT, _gAE, _value, step, epoch)
            self.agent.actor.detachCellState()
            self.agent.critic.detachCellState()
        self.step(step+i, epoch)
        self.agent.actor.zeroCellState()
        self.agent.critic.zeroCellState()
        if zeroMode is False:
            self.agent.critic.forward(tState)
            self.agent.actor.forward(tState)
        InitActorCellState = self.agent.actor.getCellState()
        InitCriticCellState = self.agent.critic.getCellState()


def preprocessBatch(f):
    def wrapper(self, step, epoch):
        # MLPBatch(self, step, epoch, f)
        CNN1DLTMPBatch(self, step, epoch, f)
    return wrapper


def preprocessState(f):
    def wrapper(self, obs):
        # return self, MLPState(self, obs)
        return CNN1DLTMPState(self, obs)
    return wrapper
