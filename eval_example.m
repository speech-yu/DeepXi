% AUTHOR:         Aaron Nicolson
% AFFILIATION:    Signal Processing Laboratory, Griffith University
%
% This Source Code Form is subject to the terms of the Mozilla Public
% License, v. 2.0. If a copy of the MPL was not distributed with this
% file, You can obtain one at http://mozilla.org/MPL/2.0/.

clear all; close all; clc

% TO DO: REVERSE Y-AXIS TICKS!


%
% In main.py, set deepxi.train(..., save_example=True) to get .mat training 
% mini-batch example.
%

load('x_STMS_batch.mat')
load('xi_bar_batch.mat')
load('seq_mask_batch.mat')

for i = 1:size(x_STMS_batch, 1)
    figure (i)
       
    % Observation/input: noisy-speech short-time magnitude spectrum. 
    x_STMS = rot90(squeeze(x_STMS_batch(i,:,:)));
    x_STMS_dB = 20*log10(x_STMS);

    % Target: mapped a priori SNR. 
    xi_bar = rot90(squeeze(xi_bar_batch(i,:,:)));

    % Sequence mask.
    seq_mask = seq_mask_batch(i,:,:);
       
    subplot(2,2,1); imagesc(flipud(x_STMS)); colorbar;
    xlabel('Time-frame bin')
    ylabel('Frequency bin')
    title('Noisy-speech short-time magnitude spectrum')
    set(gca,'YDir','normal')
    
    subplot(2,2,2); imagesc(flipud(x_STMS_dB)); colorbar;
    xlabel('Time-frame bin')
    ylabel('Frequency bin')
    title('Noisy-speech short-time magnitude spectrum (dB)')
    set(gca,'YDir','normal')

    subplot(2,2,3); imagesc(seq_mask); colorbar;
    xlabel('Time-frame bin')
    title('Sequence mask')
    colorbar('XTick', [0, 1]);
    set(gca,'ytick',[])
    set(gca,'yticklabel',[])
    
    subplot(2,2,4); imagesc(flipud(xi_bar)); colorbar;
    xlabel('Time-frame bin')
    ylabel('Frequency bin')
    title('Mapped{\it a priori} SNR')
    set(gca,'YDir','normal')

    set(gcf, 'Position', get(0, 'Screensize'));
end
