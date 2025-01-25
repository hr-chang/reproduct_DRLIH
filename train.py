# coding:utf-8
import math
import os
import sys

import torch
import torch.nn.functional as F
import torch.optim as optim
from matplotlib import pyplot as plt

from model import ActorCritic
from torch.autograd import Variable
from torchvision import datasets, transforms
from dataloader import Dataloader
import test_util
from sys import argv
import function

scrp, gpu, bit, batch, dataset = argv

steps = 10000
rate = 0.1
lamda = 0.001
observe = True

##setting
checkpoint_path = 'checkpoint-%s-%sbit' % (dataset, bit)
logpath = 'log-%s-%sbit.txt' % (dataset, bit)
if not os.path.exists(checkpoint_path):
    os.mkdir(checkpoint_path)
os.environ['CUDA_VISIBLE_DEVICES'] = gpu
batch_size = int(batch)
bit_len = int(bit)

####dataset
flag = True

if dataset == 'cifar':
    Dtest = Dataloader("test", 0, 5500, 0, 10)
    traintest = Dataloader("train", 0, 500, 0, 10)
    flag = False

if dataset == 'nus':
    traintest = Dataloader("train", 0, 500, 1, 22, 'nus')
    flag = False

if dataset == 'flk':
    traintest = Dataloader("None", 0, 500, 1, 1, 'flk')
    flag = False

if flag:
    print('undefined_dataset')
    quit()

###model
model = ActorCritic(bit_len, batch_size)
model.cuda()
print('model over')

###train

episode_length = 1
rewards_record = []
while True:

    if episode_length % steps == 0:
        model.low_lr(rate)

    if (episode_length % 2000 == 0) and (episode_length >= 20000):
        if dataset == 'cifar':
            model.eval()
            map = test_util.test(Dtest, model, batch_size, bit_len)

            print('#### map=' + str(map) + '\n')

            file = open(logpath, "a")
            file.write('#### map=' + str(map) + '\n')
            file.close()
        path = checkpoint_path + '/' + str(episode_length) + '.model';
        torch.save(model.state_dict(), path)

    model.train()

    if dataset == 'cifar':
        ori, pos, neg = traintest.get_batch_cifar_nus(batch_size)
    else:
        ori, pos, neg = traintest.get_batch_flk_nus(batch_size)

    ori = Variable(ori).cuda()
    pos = Variable(pos).cuda()
    neg = Variable(neg).cuda()

    hash_o = Variable(torch.zeros(batch_size, 1).cuda())
    hash_p = Variable(torch.zeros(batch_size, 1).cuda())
    hash_n = Variable(torch.zeros(batch_size, 1).cuda())
    probs_o = model(ori)
    probs_p = model(pos)
    probs_n = model(neg)

    for i in range(bit_len):
        hash_o = torch.cat([hash_o, probs_o[i]], 1)
        hash_p = torch.cat([hash_p, probs_p[i]], 1)
        hash_n = torch.cat([hash_n, probs_n[i]], 1)

    hash_o = hash_o[:, 1:]
    hash_p = hash_p[:, 1:]
    hash_n = hash_n[:, 1:]

    #### loss
    tri_loss = function.triplet_margin_loss(hash_o, hash_p, hash_n)

    tmp_prob = (function.log_porb(hash_o)) / (bit_len)
    loss_L = torch.mean(tmp_prob * tri_loss.detach())

    loss_R = torch.mean(tri_loss)

    final_loss = lamda * loss_L + loss_R * (1 - lamda)

    #### update

    model.zero_grad()

    final_loss.backward()

    model.step()

    if episode_length % 100 == 0:
        print(str(episode_length) + ' ' + str(final_loss.item()) + " " + str(loss_L.item()) + " " + str(
            loss_R.item()) + "\n")
        file = open(logpath, "a")
        file.write(str(episode_length) + ' ' + str(final_loss.item()) + " " + str(loss_L.item()) + " " + str(
            loss_R.item()) + "\n")
        file.close()

        rewards_record.append(-final_loss.item())

    if episode_length % steps == 0:
        plt.plot(list(range(1, len(rewards_record) + 1)), rewards_record)
        plt.xlabel('Episode')
        plt.ylabel('Reward')
        os.makedirs('results', exist_ok=True)
        plt.savefig(f'results/{episode_length}.png')
        plt.close()

    if episode_length == 10 * steps:
        break

    episode_length += 1

print("all over")
