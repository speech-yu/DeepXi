% AUTHOR:         Aaron Nicolson
% AFFILIATION:    Signal Processing Laboratory, Griffith University
%
% This Source Code Form is subject to the terms of the Mozilla Public
% License, v. 2.0. If a copy of the MPL was not distributed with this
% file, You can obtain one at http://mozilla.org/MPL/2.0/.

clear all; close all; clc

% ver = {'resnet-1.0c', 'resnet-1.0n', 'mhanet-0.1c', 'mhanet-0.1n', 'mhanet-0.2n'};

ver = {
    'mhanet-0.1c',...
    'mhanet-0.3c',...
    'mhanet-0.4c',...
    'mhanet-0.1n',...
    'mhanet-0.4n',...
    'mhanet-0.5n',...
    };

for i = 1:length(ver)
    T = readtable([ver{i}, '.csv']);
    epoch = 1:height(T);
    subplot(1,2,1); plot(epoch, T.loss, 'LineWidth', 1); xlabel('Epoch'); ylabel('Training loss'); hold on;
    subplot(1,2,2); plot(epoch, T.val_loss, 'LineWidth', 1); xlabel('Epoch'); ylabel('Validation loss'); hold on;
end
legend(ver);
hold off;
