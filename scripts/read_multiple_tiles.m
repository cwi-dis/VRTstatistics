%% check that we plot the same results

clearvars
% selfolder = dir('./session*');
close all

sessions = dir('../data/unsynced-tiled-5fps*');

sessions = sessions([sessions.isdir]);

roles = {'sender', 'receiver'};

for i=size(sessions, 1)
    
    text = fileread(['../data/' sessions(i).name '/combined.json']);
    A = jsondecode(text);
    plyr = A(contains( cellfun( @(sas) sas.component, A, 'uni', false ), 'PointBufferRenderer'));
    
    figure
    for j=1:size(roles,2)
        
        
        
        if strcmp(roles{j}, 'sender')
            sessiontime =  cell2mat(cellfun( @(sas) sas.sessiontime, plyr(strcmp(cellfun(@(sas) sas.role, plyr, 'uni', false), roles{j})), 'uni', false ));
            
            %         rolecheck =  string(cellfun( @(sas) sas.role, plyr(strcmp(cellfun(@(sas) sas.role, plyr, 'uni', false), roles{j})), 'uni', false ));
            
            pc_latency =  cell2mat(cellfun( @(sas) sas.pc_latency_ms, plyr(strcmp(cellfun(@(sas) sas.role, plyr, 'uni', false), roles{j})), 'uni', false ));
            %             figure
            points_sender = cell2mat(cellfun( @(sas) sas.points_per_cloud, plyr(strcmp(cellfun(@(sas) sas.role, plyr, 'uni', false), roles{j})), 'uni', false ));
            
%             plot(sessiontime, points_sender, 'LineWidth', 1.4);
            plot(sessiontime, pc_latency, 'LineWidth', 1.4);
            
            pcount_sender = timeseries(points_sender, sessiontime);
            
            hold on
            %             ylabel('latency [ms]');
            
        elseif strcmp(roles{j}, 'receiver') %we have multiple buffer renderers
            %             yyaxis right
            for k=0:3
                
                %                 pbr = plyr(contains( cellfun( @(sas) sas.component, plyr(strcmp(cellfun(@(sas) sas.role, plyr, 'uni', false), roles{j})), 'uni', false ), sprintf('PointBufferRenderer#%01d', k)));
                pbr = plyr(strcmp(cellfun(@(sas) sas.role, plyr, 'uni', false), roles{j}));
                
                pbr = pbr(strcmp( cellfun( @(sas) sas.component, pbr, 'uni', false), sprintf('PointBufferRenderer#%01d', k)));
                
                sessiontime_r =  cell2mat(cellfun( @(sas) sas.sessiontime, pbr(strcmp(cellfun(@(sas) sas.role, pbr, 'uni', false), roles{j})), 'uni', false ));
                pc_latency_r =  cell2mat(cellfun( @(sas) sas.pc_latency_ms, pbr(strcmp(cellfun(@(sas) sas.role, pbr, 'uni', false), roles{j})), 'uni', false ));
                
                points_r = cell2mat(cellfun( @(sas) sas.points_per_cloud, pbr(strcmp(cellfun(@(sas) sas.role, pbr, 'uni', false), roles{j})), 'uni', false ));
                
                
                %                 plot(sessiontime, pc_latency, 'LineWidth', 1.4)
                %             ylabel('max\_queue');
                %                 figure
%                 plot(sessiontime_r, points_r, 'LineWidth', 1.4);
                plot(sessiontime_r, pc_latency_r, 'LineWidth', 1.4);
                pcount(k+1) = timeseries(points_r, sessiontime_r);
                
                hold on
%                 ylabel('#points');
                ylabel('latency [ms]');
                
                %                 ptotal2 = ptotal2+points_r;
            end
        end
        
        
        
        
        %             if size(avg_queuesize) == size(sessiontime)
        %                 plot(sessiontime, avg_queuesize)
        %             end
        
    end
    
    %     legend(roles)
    set(gca, 'FontSize', 14);
    
end

%%
for i=size(sessions, 1)
    
    text = fileread(['../data/' sessions(i).name '/combined.json']);
    A = jsondecode(text);
    plyr = A(contains( cellfun( @(sas) sas.component, A, 'uni', false ), 'PointBufferRenderer'));
    
    figure
    for j=1:size(roles,2)
        
        
        
        if strcmp(roles{j}, 'sender')
            sessiontime =  cell2mat(cellfun( @(sas) sas.sessiontime, plyr(strcmp(cellfun(@(sas) sas.role, plyr, 'uni', false), roles{j})), 'uni', false ));
            
            %         rolecheck =  string(cellfun( @(sas) sas.role, plyr(strcmp(cellfun(@(sas) sas.role, plyr, 'uni', false), roles{j})), 'uni', false ));
            
            pc_latency =  cell2mat(cellfun( @(sas) sas.pc_latency_ms, plyr(strcmp(cellfun(@(sas) sas.role, plyr, 'uni', false), roles{j})), 'uni', false ));
            
            max_queue = cell2mat(cellfun( @(sas) sas.max_queuesize, plyr(strcmp(cellfun(@(sas) sas.role, plyr, 'uni', false), roles{j})), 'uni', false ));
            %             figure
            points_sender = cell2mat(cellfun( @(sas) sas.points_per_cloud, plyr(strcmp(cellfun(@(sas) sas.role, plyr, 'uni', false), roles{j})), 'uni', false ));
            
%             plot(sessiontime, points_sender, 'LineWidth', 1.4);
%             plot(sessiontime, pc_latency, 'LineWidth', 1.4);
            plot(sessiontime, max_queue, 'LineWidth', 1.4);
            
            pcount_sender = timeseries(points_sender, sessiontime);
            
            hold on
            %             ylabel('latency [ms]');
            
        elseif strcmp(roles{j}, 'receiver') %we have multiple buffer renderers
            %             yyaxis right
            for k=0:3
                
                %                 pbr = plyr(contains( cellfun( @(sas) sas.component, plyr(strcmp(cellfun(@(sas) sas.role, plyr, 'uni', false), roles{j})), 'uni', false ), sprintf('PointBufferRenderer#%01d', k)));
                pbr = plyr(strcmp(cellfun(@(sas) sas.role, plyr, 'uni', false), roles{j}));
                
                pbr = pbr(strcmp( cellfun( @(sas) sas.component, pbr, 'uni', false), sprintf('PointBufferRenderer#%01d', k)));
                
                sessiontime_r =  cell2mat(cellfun( @(sas) sas.sessiontime, pbr(strcmp(cellfun(@(sas) sas.role, pbr, 'uni', false), roles{j})), 'uni', false ));
                pc_latency_r =  cell2mat(cellfun( @(sas) sas.pc_latency_ms, pbr(strcmp(cellfun(@(sas) sas.role, pbr, 'uni', false), roles{j})), 'uni', false ));
                
                points_r = cell2mat(cellfun( @(sas) sas.points_per_cloud, pbr(strcmp(cellfun(@(sas) sas.role, pbr, 'uni', false), roles{j})), 'uni', false ));
                
                max_queue_r =  cell2mat(cellfun( @(sas) sas.max_queuesize, pbr(strcmp(cellfun(@(sas) sas.role, pbr, 'uni', false), roles{j})), 'uni', false ));

                
                %                 plot(sessiontime, pc_latency, 'LineWidth', 1.4)
                %             ylabel('max\_queue');
                %                 figure
%                 plot(sessiontime_r, points_r, 'LineWidth', 1.4);
%                 plot(sessiontime_r, pc_latency_r, 'LineWidth', 1.4);
                plot(sessiontime_r, max_queue_r, 'LineWidth', 1.4);
                pcount(k+1) = timeseries(points_r, sessiontime_r);
                
                hold on
%                 ylabel('#points');
                ylabel('max queue');
                
                %                 ptotal2 = ptotal2+points_r;
            end
        end
        
        
        
        
        %             if size(avg_queuesize) == size(sessiontime)
        %                 plot(sessiontime, avg_queuesize)
        %             end
        
    end
    
    %     legend(roles)
    set(gca, 'FontSize', 14);
    
end

%%
ptotal = [];
for k=1:3
    [temp1, pcount(k+1)] = synchronize(pcount(k), pcount(k+1), 'union', 'KeepOriginalTimes',true);
    ptotal = temp1.Data + pcount(k+1).Data;
    pcount(k+1).Data = ptotal;
end