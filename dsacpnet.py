from __future__ import print_function
import numpy as np
import torch
import torch.nn as nn
import torch.nn.parallel
import torch.utils.data
import torch.nn.functional as F
import utils


class STN(nn.Module):
    def __init__(self, num_points=500, dim=3 ):
        super(STN, self).__init__()

        self.dim = dim
        #self.num_scales = num_scales

        self.num_points = num_points

        self.conv1 = torch.nn.Conv1d(self.dim, 64, 1)
        self.conv2 = torch.nn.Conv1d(64, 128, 1)
        self.conv3 = torch.nn.Conv1d(128, 1024, 1)
        self.mp1 = torch.nn.MaxPool1d(num_points)

        self.fc1 = nn.Linear(1024, 512)
        self.fc2 = nn.Linear(512, 256)
        self.fc3 = nn.Linear(256, 4)

        self.bn1 = nn.BatchNorm1d(64)
        self.bn2 = nn.BatchNorm1d(128)
        self.bn3 = nn.BatchNorm1d(1024)
        self.bn4 = nn.BatchNorm1d(512)
        self.bn5 = nn.BatchNorm1d(256)


    def forward(self, x):
        batchsize = x.size()[0]
        x = F.relu(self.bn1(self.conv1(x)))

        x = F.relu(self.bn2(self.conv2(x)))

        x = F.relu(self.bn3(self.conv3(x)))

        x = self.mp1(x)

        x = x.view(-1, 1024)

        x = F.relu(self.bn4(self.fc1(x)))

        x = F.relu(self.bn5(self.fc2(x)))

        x1 = self.fc3(x)


        #x1,x2=torch.split(x,[self.dim*self.dim,self.num_points],1)
        #x2 = F.relu(x2)
        #iden = torch.eye(self.dim, dtype=x.dtype, device=x.device).view(1, self.dim*self.dim).repeat(batchsize, 1)
        iden = x.new_tensor([1, 0, 0, 0])
        x1 = x1 + iden
        #x1 = x1.view(-1, self.dim, self.dim)
        x1 = utils.batch_quat_to_rotmat(x1)
        #print("matrix")
        #print(x)
        #x2 = x2.view(batchsize,self.num_points,1)
        return x1#,x2



class MASK(nn.Module):
    def __init__(self, num_points=500, dim=3 ):
        super(MASK, self).__init__()

        self.dim = dim
        #self.num_scales = num_scales

        self.num_points = num_points

        self.conv1 = torch.nn.Conv1d(self.dim, 64, 1)
        self.conv2 = torch.nn.Conv1d(64, 128, 1)
        self.conv3 = torch.nn.Conv1d(128, 1024, 1)
        self.mp1 = torch.nn.MaxPool1d(num_points)

        self.fc1 = nn.Linear(1024, 512)
        self.fc2 = nn.Linear(512,num_points)
        #self.fc3 = nn.Linear(256, 4)

        self.bn1 = nn.BatchNorm1d(64)
        self.bn2 = nn.BatchNorm1d(128)
        self.bn3 = nn.BatchNorm1d(1024)
        self.bn4 = nn.BatchNorm1d(512)
        #self.bn5 = nn.BatchNorm1d(256)


    def forward(self, x):
        batchsize = x.size()[0]
        x = F.relu(self.bn1(self.conv1(x)))

        x = F.relu(self.bn2(self.conv2(x)))

        x = F.relu(self.bn3(self.conv3(x)))

        x = self.mp1(x)

        x = x.view(-1, 1024)

        x = F.relu(self.bn4(self.fc1(x)))

        #x = F.relu(self.bn5(self.fc2(x)))

        x = F.relu(self.fc2(x))
        x=x.view(batchsize,self.num_points,1)
        return x#,x2

class DSACPNet(nn.Module):
    def __init__(self, num_points=500):
        super(DSACPNet, self).__init__()
        self.num_points = num_points



        #self.point_tuple = point_tuple
        self.mask = MASK( num_points=num_points, dim=3)
        self.stn1 = STN( num_points=num_points, dim=3)


    def forward(self, x):

        x = x.view(x.size(0), 3, -1)
        trans = self.stn1(x)
        x = x.transpose(2, 1)
        x = torch.bmm(x, trans)
        x = x.transpose(2, 1)
        mask=self.mask(x)
        x = x.transpose(2, 1)
        x = torch.mul(mask,x)
        
        
        
        return x, trans
 
