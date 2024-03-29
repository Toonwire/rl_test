# -*- coding: utf-8 -*-
"""
Created on Tue Jun 08 10:01:34 2019

@author: Toonw
"""

import numpy as np


# State setup from state X to state Y with a reward r from taking the path: x --r--> y  

#0 --0--> 4
#
#1 --100--> 5
#1 --0--> 3
#
#2 --0--> 3
#
#3 --0--> 1
#3 --0--> 2
#3 --0--> 4
#
#4 --100--> 5
#4 --0--> 3
#4 --0--> 0
#
#5 --0--> 1
#5 --0--> 4


# R- Matrix
R = np.matrix([[-1, -1, -1, -1, 0, -1],
               [-1, -1, -1, 0, -1, 100],
               [-1, -1, -1, 0, -1, -1],
               [-1, 0, 0, -1, 0, -1],
               [-1, 0, 0, -1, -1, 100],
               [-1, 0, -1, -1, 0, -1]])

Q = np.matrix(np.zeros([6,6]))

# Gamma - learning parameters
gamma = 0.8

# Initial State (usually chosen at random)
initial_state = 1

# this function returns all available actions in the state given as an argument
def available_actions(state):
    current_state_row = R[state,]
    av_act = np.where(current_state_row >= 0)[1]
    return av_act

# get available actions in the current state
available_act = available_actions(initial_state)

# this function chooses at random which action to be performed within the range of all the available actions
def sample_next_action(available_actions_range):
    next_action = int(np.random.choice(available_act, 1))
    return next_action

# sample next action to be performed
action = sample_next_action(available_act)

# this function updates the Q matric according to the path selected and the Q learning algorithm
def update(current_state, action, gamma):
    max_index = np.where(Q[action,] == np.max(Q[action,]))[1]
    
    if max_index.shape[0] > 1:
        max_index = int(np.random.choice(max_index, size=1))
    else:
        max_index = int(max_index)
    max_value = Q[action, max_index]
    
    # QU-learning formula
    Q[current_state, action] = R[current_state, action] + gamma * max_value
    
# update the Q matrix
update(initial_state, action, gamma)


#-----------------
# Training
#-----------------

# train over 10k iterations, re-iterating the process above
for i in range(10000):
    current_state = np.random.randint(0, int(Q.shape[0]))
    available_act = available_actions(current_state)
    action = sample_next_action(available_act)
    update(current_state, action, gamma)
    

# Normalize the "trained" Q matrix
print("Trained Q matrix")
print(Q / np.max(Q) * 100)


#-----------------
# Testing
#-----------------

# Goal state = 5
# Best sequence path starting from 2: 2 -> 3 -> 1 -> 5

current_state = 1
end_state = 5
steps = [current_state]

while current_state != end_state:
    next_step_index = np.where(Q[current_state,] == np.max(Q[current_state, ]))[1]
    if next_step_index.shape[0] > 1:
        next_step_index = int(np.random.choice(next_step_index, size=1))
    else:
        next_step_index = int(next_step_index)
    
    steps.append(next_step_index)
    current_state = next_step_index
    
print("Selected path:")
print(steps)










































































